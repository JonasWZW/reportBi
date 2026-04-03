"""报表模板数据模型"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """章节定义"""
    id: str = Field(..., description="章节唯一标识")
    title: str = Field(..., description="章节标题")
    data_parts: list[str] = Field(default_factory=list, description="引用的Data Part ID列表")
    order: int = Field(default=0, description="章节顺序")
    content: str | None = Field(None, description="章节内容（生成后填充）")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ch1",
                "title": "概述",
                "data_parts": ["dp_001"],
                "order": 1
            }
        }


class Template(BaseModel):
    """报表模板"""
    id: str = Field(..., description="模板唯一标识")
    name: str = Field(..., description="模板名称")
    description: str = Field("", description="模板描述")
    owner: str = Field(default="system", description="所有者")
    is_public: bool = Field(default=False, description="是否公开")
    is_built_in: bool = Field(default=False, description="是否内置模板")

    chapters: list[Chapter] = Field(default_factory=list, description="章节列表")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "template_security_weekly",
                "name": "安全周报",
                "description": "标准安全运营周报模板",
                "chapters": [
                    {
                        "id": "ch1",
                        "title": "概述",
                        "data_parts": ["dp_overview"],
                        "order": 1
                    },
                    {
                        "id": "ch2",
                        "title": "威胁事件分析",
                        "data_parts": ["dp_threat_stats", "dp_threat_trend"],
                        "order": 2
                    }
                ]
            }
        }


def get_built_in_templates() -> list[Template]:
    """获取内置模板"""
    return [
        Template(
            id="template_security_weekly",
            name="安全周报",
            description="标准安全运营周报模板，包含概述、威胁事件、漏洞分析等章节",
            owner="system",
            is_public=True,
            is_built_in=True,
            chapters=[
                Chapter(id="ch1", title="概述", data_parts=["dp_overview"], order=1),
                Chapter(id="ch2", title="威胁事件分析", data_parts=["dp_threat_stats", "dp_threat_trend"], order=2),
                Chapter(id="ch3", title="漏洞分析", data_parts=["dp_vul_stats"], order=3),
                Chapter(id="ch4", title="资产风险", data_parts=["dp_asset_risk"], order=4),
                Chapter(id="ch5", title="总结与建议", data_parts=["dp_summary"], order=5),
            ]
        ),
        Template(
            id="template_security_monthly",
            name="安全月报",
            description="月度安全运营报表模板",
            owner="system",
            is_public=True,
            is_built_in=True,
            chapters=[
                Chapter(id="ch1", title="月度概况", data_parts=["dp_month_overview"], order=1),
                Chapter(id="ch2", title="威胁态势", data_parts=["dp_month_threat"], order=2),
                Chapter(id="ch3", title="漏洞管理", data_parts=["dp_month_vul"], order=3),
                Chapter(id="ch4", title="合规检查", data_parts=["dp_month_compliance"], order=4),
                Chapter(id="ch5", title="下月计划", data_parts=["dp_next_month_plan"], order=5),
            ]
        ),
        Template(
            id="template_vulnerability_analysis",
            name="漏洞分析报告",
            description="专项漏洞分析报表模板",
            owner="system",
            is_public=True,
            is_built_in=True,
            chapters=[
                Chapter(id="ch1", title="漏洞概览", data_parts=["dp_vul_overview"], order=1),
                Chapter(id="ch2", title="高危漏洞", data_parts=["dp_high_risk_vul"], order=2),
                Chapter(id="ch3", title="漏洞趋势", data_parts=["dp_vul_trend"], order=3),
                Chapter(id="ch4", title="修复建议", data_parts=["dp_remediation"], order=4),
            ]
        ),
    ]
