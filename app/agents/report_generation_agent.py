"""主报表生成Agent - 使用LangGraph实现"""
import uuid
from datetime import datetime
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.prompt_rewriting_agent import get_prompt_rewriting_agent
from app.agents.query_agent import get_query_agent, QueryAgent
from app.agents.analysis_agent import get_analysis_agent, AnalysisAgent
from app.schemas.data_part import DataPart, DataPartState, DataPartType, DataPartResult
from app.schemas.template import Template, Chapter
from app.schemas.report import (
    ReportGenerationRequest,
    ReportGenerationResult,
    ReportChapterResult,
)
from app.schemas.tool import ToolRegistry, get_default_tools
from app.tools.chart_generator import ChartGenerator


class ReportGenerationState(dict):
    """报表生成状态"""
    request: ReportGenerationRequest
    template: Template | None
    data_parts: list[DataPart]
    chapter_results: list[ReportChapterResult]
    errors: list[str]
    current_chapter_index: int = 0
    current_data_part_index: int = 0


class ReportGenerationAgent:
    """
    主报表生成Agent

    使用LangGraph编排整个报表生成流程：
    1. Prompt改写 → 2. Data Part执行 → 3. 章节组装 → 4. 报告生成
    """

    def __init__(self):
        self._prompt_rewriting_agent = get_prompt_rewriting_agent()
        self._query_agent = get_query_agent()
        self._analysis_agent = get_analysis_agent()
        self._tool_registry = ToolRegistry
        self._chart_generator = ChartGenerator

        # 初始化工具注册表
        self._init_tool_registry()

        # 构建LangGraph
        self._graph = self._build_graph()

    def _init_tool_registry(self) -> None:
        """初始化工具注册表"""
        # 注册默认工具
        for tool in get_default_tools():
            ToolRegistry.register(tool)

    def _build_graph(self) -> StateGraph:
        """构建LangGraph"""
        graph = StateGraph(ReportGenerationState)

        # 添加节点
        graph.add_node("parse_request", self._parse_request_node)
        graph.add_node("rewrite_prompts", self._rewrite_prompts_node)
        graph.add_node("execute_data_parts", self._execute_data_parts_node)
        graph.add_node("assemble_chapters", self._assemble_chapters_node)
        graph.add_node("generate_report", self._generate_report_node)

        # 添加边
        graph.add_edge("parse_request", "rewrite_prompts")
        graph.add_edge("rewrite_prompts", "execute_data_parts")
        graph.add_edge("execute_data_parts", "assemble_chapters")
        graph.add_edge("assemble_chapters", "generate_report")
        graph.add_edge("generate_report", END)

        # 设置入口
        graph.set_entry_point("parse_request")

        return graph.compile()

    async def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        """
        生成报表

        Args:
            request: 报表生成请求

        Returns:
            报表生成结果
        """
        # 初始化状态
        initial_state: ReportGenerationState = {
            "request": request,
            "template": None,
            "data_parts": [],
            "chapter_results": [],
            "errors": [],
            "current_chapter_index": 0,
            "current_data_part_index": 0,
        }

        # 执行图
        result = await self._graph.ainvoke(initial_state)

        # 构建返回结果
        return ReportGenerationResult(
            template_id=result.get("template")?.id if result.get("template") else request.template_id,
            template_name=result.get("template")?.name if result.get("template") else None,
            chapters=result.get("chapter_results", []),
            total_execution_time_ms=0,  # TODO: 计算总时间
        )

    # === LangGraph 节点 ===

    async def _parse_request_node(self, state: ReportGenerationState) -> ReportGenerationState:
        """解析请求节点"""
        request = state["request"]

        if request.template_id:
            # 从模板加载
            from app.schemas.template import get_built_in_templates
            templates = get_built_in_templates()
            template = next((t for t in templates if t.id == request.template_id), None)
            state["template"] = template
        elif request.custom_prompt:
            # 自定义prompt，需要先改写
            pass

        return state

    async def _rewrite_prompts_node(self, state: ReportGenerationState) -> ReportGenerationState:
        """改写Prompt节点"""
        request = state["request"]

        if request.custom_prompt:
            # 自定义prompt需要改写
            data_parts = self._prompt_rewriting_agent.rewrite(request.custom_prompt)
            state["data_parts"] = data_parts
        elif state["template"]:
            # 使用模板，从模板中提取data_parts配置
            # TODO: 模板需要有预定义的data_part配置
            state["data_parts"] = []

        return state

    async def _execute_data_parts_node(self, state: ReportGenerationState) -> ReportGenerationState:
        """执行Data Parts节点"""
        data_parts = state["data_parts"]

        for dp in data_parts:
            dp.state = DataPartState.RUNNING

            try:
                if dp.type == DataPartType.QUERY:
                    # 执行查询
                    result = await self._query_agent.execute(
                        dp.tool_id,
                        dp.params,
                        self._tool_registry
                    )
                    dp.result = result
                    dp.result_type = "table"

                elif dp.type == DataPartType.ANALYZE:
                    # 执行分析
                    # 先获取依赖的数据
                    deps_results = []
                    for dep_id in dp.depends_on:
                        dep_dp = next((d for d in data_parts if d.id == dep_id), None)
                        if dep_dp and dep_dp.result:
                            deps_results.append(dep_dp.result)

                    if deps_results:
                        summary = await self._analysis_agent.summarize(deps_results)
                        dp.result = summary
                    dp.result_type = "text"

                dp.state = DataPartState.COMPLETED
                dp.completed_at = datetime.now()

            except Exception as e:
                dp.state = DataPartState.FAILED
                dp.error = str(e)
                state["errors"].append(f"DataPart {dp.id} failed: {e}")

        return state

    async def _assemble_chapters_node(self, state: ReportGenerationState) -> ReportGenerationState:
        """组装章节节点"""
        template = state.get("template")
        data_parts = state["data_parts"]

        if not template:
            # 无模板，创建一个默认章节
            chapter_result = ReportChapterResult(
                chapter=Chapter(
                    id="ch_default",
                    title="分析结果",
                    order=1,
                ),
                data_part_results=[
                    DataPartResult(
                        data_part_id=dp.id,
                        state=dp.state,
                        result=dp.result,
                        result_type=dp.result_type,
                    )
                    for dp in data_parts
                ],
            )
            state["chapter_results"] = [chapter_result]
        else:
            # 按模板章节组装
            for chapter in template.chapters:
                chapter_dps = [
                    dp for dp in data_parts
                    if dp.id in chapter.data_parts
                ]
                chapter_result = ReportChapterResult(
                    chapter=chapter,
                    data_part_results=[
                        DataPartResult(
                            data_part_id=dp.id,
                            state=dp.state,
                            result=dp.result,
                            result_type=dp.result_type,
                        )
                        for dp in chapter_dps
                    ],
                )
                state["chapter_results"].append(chapter_result)

        return state

    async def _generate_report_node(self, state: ReportGenerationState) -> ReportGenerationState:
        """生成报告节点"""
        chapter_results = state["chapter_results"]

        # 为每个章节生成内容
        for cr in chapter_results:
            content_parts = []

            for dp_result in cr.data_part_results:
                if dp_result.state == DataPartState.COMPLETED:
                    if dp_result.result_type == "table":
                        content_parts.append(f"### {dp_result.data_part_id}\n\n")
                        content_parts.append(self._format_table(dp_result.result))
                    elif dp_result.result_type == "text":
                        content_parts.append(f"\n{dp_result.result}\n")

            cr.content = "\n".join(content_parts)

        return state

    def _format_table(self, data: Any) -> str:
        """格式化表格为Markdown"""
        if not isinstance(data, list) or not data:
            return ""

        if not isinstance(data[0], dict):
            return str(data)

        headers = list(data[0].keys())
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("|" + "|".join(["---"] * len(headers)) + "|")

        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)


# 全局实例
_report_generation_agent: ReportGenerationAgent | None = None


def get_report_generation_agent() -> ReportGenerationAgent:
    """获取报表生成Agent实例"""
    global _report_generation_agent
    if _report_generation_agent is None:
        _report_generation_agent = ReportGenerationAgent()
    return _report_generation_agent
