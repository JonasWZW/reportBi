"""预制件（Block）数据模型"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.data_part import DataPartType


class BlockCategory(str, Enum):
    PERSONAL = "personal"
    SHARED = "shared"


class Block(BaseModel):
    """预制件 - 已验证的prompt+改写prompt+工具链组合"""
    id: str = Field(..., description="唯一标识")
    name: str = Field(..., description="预制件名称")
    description: str = Field("", description="预制件描述")

    # Prompt 相关
    original_prompt: str = Field(..., description="用户原始输入")
    rewritten_prompt: str = Field(..., description="改写后的标准prompt")

    # 工具链
    tool_chain: list[dict[str, Any]] = Field(default_factory=list, description="工具调用链")

    # 元数据
    result_type: str = Field(..., description="结果类型：table, chart, text")
    category: BlockCategory = Field(default=BlockCategory.PERSONAL, description="分类")
    created_by: str = Field(default="system", description="创建者")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")
    last_used_at: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "block_001",
                "name": "资产被攻击Top10分析",
                "description": "查询被攻击资产并按攻击次数排序",
                "original_prompt": "最近一周哪些资产被攻击最严重",
                "rewritten_prompt": "查询被攻击资产，按攻击次数Top10",
                "tool_chain": [
                    {"tool_id": "asset_attacks", "params": {"time_range": "last_week", "limit": 10}}
                ],
                "result_type": "table",
                "category": "personal"
            }
        }


class BlockStore:
    """预制件存储（内存中）"""
    _blocks: dict[str, Block] = {}

    @classmethod
    def save(cls, block: Block) -> None:
        cls._blocks[block.id] = block

    @classmethod
    def get(cls, block_id: str) -> Block | None:
        return cls._blocks.get(block_id)

    @classmethod
    def delete(cls, block_id: str) -> bool:
        return cls._blocks.pop(block_id, None) is not None

    @classmethod
    def list_all(cls) -> list[Block]:
        return list(cls._blocks.values())

    @classmethod
    def list_by_category(cls, category: BlockCategory) -> list[Block]:
        return [b for b in cls._blocks.values() if b.category == category]

    @classmethod
    def search(cls, keyword: str) -> list[Block]:
        keyword_lower = keyword.lower()
        return [
            b for b in cls._blocks.values()
            if keyword_lower in b.name.lower()
            or keyword_lower in b.description.lower()
            or keyword_lower in b.original_prompt.lower()
            or keyword_lower in b.rewritten_prompt.lower()
        ]
