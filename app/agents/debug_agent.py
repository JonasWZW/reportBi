"""调试模式Agent"""
import uuid
from datetime import datetime
from typing import Any

from app.agents.prompt_rewriting_agent import get_prompt_rewriting_agent
from app.agents.query_agent import get_query_agent
from app.agents.analysis_agent import get_analysis_agent
from app.schemas.data_part import DataPart, DataPartState, DataPartType, DataPartResult
from app.schemas.report import DebugSession, DataPartExecutionRequest
from app.schemas.tool import ToolRegistry
from app.tools.chart_generator import ChartGenerator


class DebugAgent:
    """
    调试模式Agent

    职责：
    1. 单独执行单个Data Part
    2. 预览执行结果
    3. 支持Prompt调整和重执行
    4. 记录执行历史
    5. 结果对比
    """

    def __init__(self):
        self._prompt_rewriting_agent = get_prompt_rewriting_agent()
        self._query_agent = get_query_agent()
        self._analysis_agent = get_analysis_agent()
        self._chart_generator = ChartGenerator

        # 会话存储
        self._sessions: dict[str, DebugSession] = {}

    def create_session(self, user_id: str = "anonymous") -> DebugSession:
        """创建调试会话"""
        session = DebugSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            history=[],
            current_data_part=None,
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> DebugSession | None:
        """获取调试会话"""
        return self._sessions.get(session_id)

    async def execute_single(
        self,
        request: DataPartExecutionRequest,
        session_id: str | None = None,
    ) -> DataPartResult:
        """
        执行单个Data Part

        Args:
            request: 执行请求
            session_id: 调试会话ID（可选）

        Returns:
            执行结果
        """
        dp_id = str(uuid.uuid4())
        data_part = DataPart(
            id=dp_id,
            type=DataPartType.QUERY,
            original_prompt=request.prompt,
            rewritten_prompt=request.prompt,
            tool_id=request.tool_id,
            params=request.params,
        )

        # 如果有会话，更新当前Data Part
        if session_id:
            session = self._sessions.get(session_id)
            if session:
                session.current_data_part = data_part

        # 执行
        try:
            data_part.state = DataPartState.RUNNING

            if data_part.type == DataPartType.QUERY:
                result = await self._query_agent.execute(
                    data_part.tool_id,
                    data_part.params,
                    ToolRegistry
                )
                data_part.result = result
                data_part.result_type = "table"

            data_part.state = DataPartState.COMPLETED
            data_part.completed_at = datetime.now()

        except Exception as e:
            data_part.state = DataPartState.FAILED
            data_part.error = str(e)

        # 如果有会话，记录到历史
        if session_id:
            session = self._sessions.get(session_id)
            if session:
                session.history.append(data_part)

        return DataPartResult(
            data_part_id=data_part.id,
            state=data_part.state,
            result=data_part.result,
            result_type=data_part.result_type,
            error=data_part.error,
        )

    async def rewrite_and_execute(
        self,
        prompt: str,
        session_id: str | None = None,
    ) -> tuple[DataPart, DataPartResult]:
        """
        改写Prompt并执行

        Args:
            prompt: 用户prompt
            session_id: 调试会话ID

        Returns:
            (改写后的DataPart, 执行结果)
        """
        # 改写
        data_parts = self._prompt_rewriting_agent.rewrite(prompt)
        if not data_parts:
            raise ValueError("无法改写prompt")

        data_part = data_parts[0]

        # 执行
        try:
            data_part.state = DataPartState.RUNNING

            if data_part.type == DataPartType.QUERY:
                result = await self._query_agent.execute(
                    data_part.tool_id,
                    data_part.params,
                    ToolRegistry
                )
                data_part.result = result
                data_part.result_type = "table"

            data_part.state = DataPartState.COMPLETED
            data_part.completed_at = datetime.now()

        except Exception as e:
            data_part.state = DataPartState.FAILED
            data_part.error = str(e)

        # 记录到会话
        if session_id:
            session = self._sessions.get(session_id)
            if session:
                session.history.append(data_part)
                session.current_data_part = data_part

        result = DataPartResult(
            data_part_id=data_part.id,
            state=data_part.state,
            result=data_part.result,
            result_type=data_part.result_type,
            error=data_part.error,
        )

        return data_part, result

    def get_history(self, session_id: str) -> list[DataPart]:
        """获取执行历史"""
        session = self._sessions.get(session_id)
        if session:
            return session.history
        return []

    def compare_results(
        self,
        session_id: str,
        data_part_id_1: str,
        data_part_id_2: str,
    ) -> dict[str, Any]:
        """对比两个Data Part的执行结果"""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        dp1 = next((dp for dp in session.history if dp.id == data_part_id_1), None)
        dp2 = next((dp for dp in session.history if dp.id == data_part_id_2), None)

        if not dp1 or not dp2:
            return {"error": "DataPart not found"}

        return {
            "data_part_1": {
                "id": dp1.id,
                "original_prompt": dp1.original_prompt,
                "rewritten_prompt": dp1.rewritten_prompt,
                "result": dp1.result,
                "state": dp1.state,
            },
            "data_part_2": {
                "id": dp2.id,
                "original_prompt": dp2.original_prompt,
                "rewritten_prompt": dp2.rewritten_prompt,
                "result": dp2.result,
                "state": dp2.state,
            },
        }


# 全局实例
_debug_agent: DebugAgent | None = None


def get_debug_agent() -> DebugAgent:
    """获取调试Agent实例"""
    global _debug_agent
    if _debug_agent is None:
        _debug_agent = DebugAgent()
    return _debug_agent
