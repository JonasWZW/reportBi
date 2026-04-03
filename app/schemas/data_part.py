"""Data Part 数据模型"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DataPartType(str, Enum):
    QUERY = "query"
    ANALYZE = "analyze"


class DataPartState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DataPart(BaseModel):
    """数据部分 - 报表的原子组成单元"""
    id: str = Field(..., description="唯一标识")
    type: DataPartType = Field(..., description="类型：query 或 analyze")
    original_prompt: str = Field(..., description="用户原始输入")
    rewritten_prompt: str = Field(..., description="改写后的标准prompt")
    tool_id: str | None = Field(None, description="关联的工具ID（query类型必须有）")
    params: dict[str, Any] = Field(default_factory=dict, description="工具调用参数")
    depends_on: list[str] = Field(default_factory=list, description="依赖的其他Data Part ID列表")
    result: Any | None = Field(None, description="执行结果")
    result_type: str | None = Field(None, description="结果类型：table, chart, text")
    state: DataPartState = Field(default=DataPartState.PENDING, description="执行状态")
    error: str | None = Field(None, description="错误信息")
    execution_time_ms: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "dp_001",
                "type": "query",
                "original_prompt": "最近一周哪些资产被攻击最严重",
                "rewritten_prompt": "查询被攻击资产，按攻击次数Top10",
                "tool_id": "asset_attacks",
                "params": {"time_range": "last_week", "limit": 10},
                "depends_on": [],
                "result_type": "table"
            }
        }


class DataPartResult(BaseModel):
    """Data Part 执行结果"""
    data_part_id: str
    state: DataPartState
    result: Any | None = None
    result_type: str | None = None
    error: str | None = None
    execution_time_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
