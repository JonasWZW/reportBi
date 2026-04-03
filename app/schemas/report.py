"""报表生成相关数据模型"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.data_part import DataPart, DataPartResult
from app.schemas.template import Template, Chapter


class ReportGenerationRequest(BaseModel):
    """报表生成请求"""
    template_id: str | None = Field(None, description="模板ID（可选）")
    custom_prompt: str | None = Field(None, description="自定义prompt（不使用模板时）")
    user_id: str = Field(default="anonymous", description="用户ID")
    time_range: str | None = Field(None, description="时间范围覆盖")


class DataPartExecutionRequest(BaseModel):
    """单个Data Part执行请求（用于调试）"""
    prompt: str = Field(..., description="用户prompt")
    tool_id: str | None = Field(None, description="指定工具ID（可选）")
    params: dict[str, Any] = Field(default_factory=dict, description="工具参数")


class DebugSession(BaseModel):
    """调试会话"""
    id: str = Field(..., description="会话ID")
    user_id: str = Field(default="anonymous")
    history: list[DataPart] = Field(default_factory=list)
    current_data_part: DataPart | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ReportChapterResult(BaseModel):
    """报表章节结果"""
    chapter: Chapter
    data_part_results: list[DataPartResult]
    content: str | None = None


class ReportGenerationResult(BaseModel):
    """报表生成结果"""
    template_id: str | None
    template_name: str | None
    chapters: list[ReportChapterResult]
    generated_at: datetime = Field(default_factory=datetime.now)
    total_execution_time_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
