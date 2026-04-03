"""工具相关的数据模型"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    QUERY = "query"
    CHART = "chart"
    ANALYZE = "analyze"
    DOCUMENT = "document"


class ResultType(str, Enum):
    TABLE = "table"
    CHART = "chart"
    TEXT = "text"


class Tool(BaseModel):
    """工具定义"""
    id: str = Field(..., description="工具唯一标识")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述（用于语义匹配）")
    tool_type: ToolType = Field(..., description="工具类型")
    params_schema: dict[str, Any] = Field(default_factory=dict, description="参数JSON Schema")
    result_type: ResultType = Field(..., description="结果类型")
    enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "asset_attacks",
                "name": "资产攻击查询",
                "description": "查询资产被攻击的情况，返回攻击次数、来源等",
                "tool_type": "query",
                "params_schema": {
                    "time_range": {"type": "string", "enum": ["today", "last_week", "last_month"]},
                    "limit": {"type": "integer", "default": 10}
                },
                "result_type": "table"
            }
        }


class ToolInvocation(BaseModel):
    """工具调用记录"""
    tool_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None
    error: str | None = None
    execution_time_ms: int | None = None


class ToolRegistry:
    """工具注册表（内存中）"""
    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        cls._tools[tool.id] = tool

    @classmethod
    def get(cls, tool_id: str) -> Tool | None:
        return cls._tools.get(tool_id)

    @classmethod
    def list_all(cls) -> list[Tool]:
        return list(cls._tools.values())

    @classmethod
    def unregister(cls, tool_id: str) -> bool:
        return cls._tools.pop(tool_id, None) is not None

    @classmethod
    def search_by_type(cls, tool_type: ToolType) -> list[Tool]:
        return [t for t in cls._tools.values() if t.tool_type == tool_type]


def get_default_tools() -> list[Tool]:
    """获取默认工具列表"""
    return [
        Tool(
            id="asset_attacks",
            name="资产攻击查询",
            description="查询资产被攻击的情况，返回攻击次数、来源、攻击类型等信息",
            tool_type=ToolType.QUERY,
            params_schema={
                "time_range": {"type": "string", "enum": ["today", "last_week", "last_month", "custom"]},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            result_type=ResultType.TABLE
        ),
        Tool(
            id="threat_stats",
            name="威胁事件统计",
            description="查询威胁事件的统计数据，按类型、来源、严重程度分布统计",
            tool_type=ToolType.QUERY,
            params_schema={
                "time_range": {"type": "string", "enum": ["today", "last_week", "last_month", "custom"]},
                "group_by": {"type": "string", "enum": ["type", "source", "severity"]},
                "limit": {"type": "integer", "default": 10}
            },
            result_type=ResultType.TABLE
        ),
        Tool(
            id="vulnerability_scan",
            name="漏洞扫描查询",
            description="查询漏洞扫描结果，包括漏洞数量、类型、严重等级分布",
            tool_type=ToolType.QUERY,
            params_schema={
                "time_range": {"type": "string", "enum": ["today", "last_week", "last_month", "custom"]},
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                "limit": {"type": "integer", "default": 10}
            },
            result_type=ResultType.TABLE
        ),
        Tool(
            id="log_query",
            name="日志查询",
            description="查询系统日志，支持关键词搜索和时间范围过滤",
            tool_type=ToolType.QUERY,
            params_schema={
                "keywords": {"type": "array", "items": {"type": "string"}},
                "time_range": {"type": "string"},
                "limit": {"type": "integer", "default": 100}
            },
            result_type=ResultType.TABLE
        ),
        Tool(
            id="network_flow",
            name="网络流量查询",
            description="查询网络流量数据，包括流量大小、连接数、协议分布等",
            tool_type=ToolType.QUERY,
            params_schema={
                "time_range": {"type": "string", "enum": ["today", "last_week", "last_month"]},
                "limit": {"type": "integer", "default": 10}
            },
            result_type=ResultType.TABLE
        ),
    ]
