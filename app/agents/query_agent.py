"""查询Agent - 负责执行数据查询"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import get_settings
from app.schemas.tool import Tool, ToolType


class QueryExecutor(ABC):
    """查询执行器基类"""

    @abstractmethod
    async def execute(self, tool: Tool, params: dict[str, Any]) -> Any:
        """执行查询"""
        ...


class HTTPQueryExecutor(QueryExecutor):
    """基于HTTP API的查询执行器"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    async def execute(self, tool: Tool, params: dict[str, Any]) -> Any:
        """执行HTTP查询"""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/{tool.id}",
                json=params,
                headers={"Authorization": f"Bearer {self._api_key}"}
            )
            response.raise_for_status()
            return response.json()


class MockQueryExecutor(QueryExecutor):
    """Mock查询执行器 - 用于测试"""

    async def execute(self, tool: Tool, params: dict[str, Any]) -> Any:
        """返回模拟数据"""
        await asyncio.sleep(0.1)  # 模拟延迟

        # 根据工具ID返回不同的模拟数据
        if tool.id == "asset_attacks":
            return [
                {"asset": "Web Server 01", "attacks": 1523, "source": "外部"},
                {"asset": "DB Server 02", "attacks": 987, "source": "外部"},
                {"asset": "Mail Server 03", "attacks": 654, "source": "内部"},
                {"asset": "File Server 04", "attacks": 432, "source": "外部"},
                {"asset": "PC-001", "attacks": 321, "source": "内部"},
            ]
        elif tool.id == "threat_stats":
            time_range = params.get("time_range", "last_week")
            return [
                {"type": "恶意软件", "count": 125, "percentage": 35.2},
                {"type": "钓鱼攻击", "count": 89, "percentage": 25.1},
                {"type": "DDoS攻击", "count": 67, "percentage": 18.9},
                {"type": "SQL注入", "count": 34, "percentage": 9.6},
                {"type": "XSS攻击", "count": 23, "percentage": 6.5},
            ]
        elif tool.id == "vulnerability_scan":
            return [
                {"severity": "Critical", "count": 5, "vulns": ["CVE-2024-0001", "CVE-2024-0002"]},
                {"severity": "High", "count": 23, "vulns": ["CVE-2024-0011"]},
                {"severity": "Medium", "count": 67, "vulns": []},
                {"severity": "Low", "count": 156, "vulns": []},
            ]
        else:
            return [{"result": f"Mock data for {tool.id}"}]


class QueryAgent:
    """
    查询Agent

    职责：
    1. 根据tool_id路由到对应的执行器
    2. 执行查询并返回结果
    3. 处理异常和超时
    """

    def __init__(self, executor: QueryExecutor | None = None):
        settings = get_settings()

        if executor is None:
            # 根据配置选择执行器
            if settings.data_platform.base_url:
                self._executor = HTTPQueryExecutor(
                    base_url=settings.data_platform.base_url,
                    api_key=settings.data_platform.api_key,
                    timeout=settings.data_platform.timeout,
                )
            else:
                # 使用Mock执行器
                self._executor = MockQueryExecutor()
        else:
            self._executor = executor

    async def execute(self, tool_id: str, params: dict[str, Any], tool_registry) -> Any:
        """
        执行查询

        Args:
            tool_id: 工具ID
            params: 查询参数
            tool_registry: 工具注册表

        Returns:
            查询结果
        """
        tool = tool_registry.get(tool_id)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_id}")

        if tool.tool_type != ToolType.QUERY:
            raise ValueError(f"Tool {tool_id} is not a query type")

        start_time = time.time()
        try:
            result = await self._executor.execute(tool, params)
            return result
        finally:
            execution_time = int((time.time() - start_time) * 1000)
            # 可以在这里记录执行时间

    async def batch_execute(
        self,
        queries: list[tuple[str, dict[str, Any]]],
        tool_registry
    ) -> list[Any]:
        """
        批量执行查询

        Args:
            queries: [(tool_id, params), ...]
            tool_registry: 工具注册表

        Returns:
            结果列表
        """
        tasks = [
            self.execute(tool_id, params, tool_registry)
            for tool_id, params in queries
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 全局实例
_query_agent: QueryAgent | None = None


def get_query_agent() -> QueryAgent:
    """获取查询Agent实例"""
    global _query_agent
    if _query_agent is None:
        _query_agent = QueryAgent()
    return _query_agent
