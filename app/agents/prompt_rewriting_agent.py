"""Prompt改写Agent - 使用LangChain实现"""
import json
import re
import uuid
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.schemas.data_part import DataPart, DataPartType
from app.schemas.block import Block, BlockStore
from app.tools.vector_store import VectorStore, get_vector_store


# 时间表达式映射
TIME_EXPRESSION_MAP = {
    r"今天|当日": "today",
    r"昨天": "yesterday",
    r"最近?一周|上周|最近七天": "last_week",
    r"最近?一月|本月|最近三十天": "last_month",
    r"最近?三月|最近三个月": "last_quarter",
    r"最近?(?:半|一)年": "last_half_year",
}


def parse_time_expression(prompt: str) -> tuple[str | None, dict[str, Any]]:
    """从prompt中解析时间表达式"""
    params = {}

    for pattern, time_value in TIME_EXPRESSION_MAP.items():
        if re.search(pattern, prompt):
            params["time_range"] = time_value
            return time_value, params

    return None, params


def extract_limit_from_prompt(prompt: str) -> int | None:
    """从prompt中提取数量限制"""
    patterns = [
        r"Top\s*(\d+)",
        r"前\s*(\d+)",
        r"排名\s*(\d+)",
        r"多少|几个": None,  # 没有具体数字
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match and match.group(1):
            return int(match.group(1))

    return None


class PromptRewritingAgent:
    """
    Prompt改写Agent

    职责：
    1. 将用户prompt拆解为n个查询调用 + m个分析调用
    2. 进行工具匹配（预制件优先，其次向量检索）
    3. 生成标准化的rewritten_prompt
    """

    def __init__(self, vector_store: VectorStore | None = None, llm: ChatOpenAI | None = None):
        settings = get_settings()

        self._llm = llm or ChatOpenAI(
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            api_key=settings.llm.api_key,
        )

        self._vector_store = vector_store or get_vector_store()

        # 系统提示
        self._system_prompt = """你是一个专业的安全运营分析师。你的职责是将用户的自然语言prompt改写为结构化的查询指令。

你需要：
1. 分析用户意图，识别需要执行的查询类型
2. 识别时间范围（如"最近一周"、"本月"等）
3. 识别数量限制（如"Top10"等）
4. 判断是否需要分析步骤

输出JSON格式：
{
    "data_parts": [
        {
            "type": "query" | "analyze",
            "original_prompt": "原始用户输入",
            "rewritten_prompt": "标准化的查询描述",
            "tool_id": "工具ID（查询类型必须有）",
            "params": {"time_range": "时间范围", "limit": 数量限制},
            "depends_on": []
        }
    ]
}

注意：
- 查询类型需要匹配工具注册表中的工具
- 分析类型通常依赖前面的查询结果
- rewritten_prompt应该简洁明确，便于后续工具匹配"""

        self._prompt = ChatPromptTemplate.from_messages([
            ("system", self._system_prompt),
            ("human", "{input}"),
        ])

        self._output_parser = JsonOutputParser()
        self._chain = self._prompt | self._llm | self._output_parser

    def rewrite(self, user_prompt: str) -> list[DataPart]:
        """
        将用户prompt改写为DataPart列表

        Args:
            user_prompt: 用户原始输入

        Returns:
            DataPart列表
        """
        # 1. 先尝试在预制件中匹配
        matched_block = self._match_block(user_prompt)
        if matched_block:
            return self._create_data_parts_from_block(matched_block, user_prompt)

        # 2. 调用LLM进行改写
        raw_output = self._chain.invoke({"input": user_prompt})
        data_parts = self._parse_llm_output(raw_output)

        # 3. 进行工具匹配
        for dp in data_parts:
            if dp.type == DataPartType.QUERY and not dp.tool_id:
                self._match_tool(dp)

        # 4. 解析时间参数
        for dp in data_parts:
            time_value, time_params = parse_time_expression(dp.original_prompt)
            if time_value:
                dp.params["time_range"] = time_value

            limit = extract_limit_from_prompt(dp.original_prompt)
            if limit:
                dp.params["limit"] = limit

        return data_parts

    def _match_block(self, prompt: str) -> Block | None:
        """在预制件中匹配"""
        blocks = BlockStore.search(prompt)
        if blocks:
            # 返回匹配度最高的
            return blocks[0]
        return None

    def _create_data_parts_from_block(self, block: Block, original_prompt: str) -> list[DataPart]:
        """从预制件创建DataPart列表"""
        data_parts = []
        dp_id = f"dp_{uuid.uuid4().hex[:8]}"

        dp = DataPart(
            id=dp_id,
            type=DataPartType.QUERY,
            original_prompt=original_prompt,
            rewritten_prompt=block.rewritten_prompt,
            tool_id=block.tool_chain[0]["tool_id"] if block.tool_chain else None,
            params=block.tool_chain[0].get("params", {}) if block.tool_chain else {},
            result_type=block.result_type,
        )
        data_parts.append(dp)

        # 处理分析类型的DataPart（如果有）
        for i, tool_call in enumerate(block.tool_chain[1:], start=1):
            dp_id = f"dp_{uuid.uuid4().hex[:8]}"
            dp = DataPart(
                id=dp_id,
                type=DataPartType.ANALYZE,
                original_prompt=original_prompt,
                rewritten_prompt=f"分析结果 {i}",
                depends_on=[data_parts[0].id],
                result_type="text",
            )
            data_parts.append(dp)

        return data_parts

    def _parse_llm_output(self, raw_output: dict[str, Any]) -> list[DataPart]:
        """解析LLM输出"""
        data_parts = []
        raw_dps = raw_output.get("data_parts", [])

        for i, raw_dp in enumerate(raw_dps):
            dp_id = f"dp_{uuid.uuid4().hex[:8]}"
            dp = DataPart(
                id=dp_id,
                type=DataPartType(raw_dp.get("type", "query")),
                original_prompt=raw_dp.get("original_prompt", ""),
                rewritten_prompt=raw_dp.get("rewritten_prompt", ""),
                tool_id=raw_dp.get("tool_id"),
                params=raw_dp.get("params", {}),
                depends_on=raw_dp.get("depends_on", []),
                result_type="table",  # 默认
            )
            data_parts.append(dp)

        return data_parts

    def _match_tool(self, data_part: DataPart) -> None:
        """通过向量检索匹配工具"""
        if not data_part.rewritten_prompt:
            data_part.rewritten_prompt = data_part.original_prompt

        matches = self._vector_store.search(data_part.rewritten_prompt, top_k=1)
        if matches and matches[0].similarity > 0.5:  # 阈值
            data_part.tool_id = matches[0].tool.id


# 全局实例
_prompt_rewriting_agent: PromptRewritingAgent | None = None


def get_prompt_rewriting_agent() -> PromptRewritingAgent:
    """获取Prompt改写Agent实例"""
    global _prompt_rewriting_agent
    if _prompt_rewriting_agent is None:
        _prompt_rewriting_agent = PromptRewritingAgent()
    return _prompt_rewriting_agent
