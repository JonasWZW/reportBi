"""数据模型测试"""
import pytest
from datetime import datetime

from app.schemas.tool import Tool, ToolType, ResultType, ToolRegistry, get_default_tools
from app.schemas.data_part import DataPart, DataPartType, DataPartState
from app.schemas.block import Block, BlockCategory, BlockStore
from app.schemas.template import Template, Chapter, get_built_in_templates


class TestTool:
    """工具模型测试"""

    def test_tool_creation(self):
        """测试工具创建"""
        tool = Tool(
            id="test_tool",
            name="测试工具",
            description="这是一个测试工具",
            tool_type=ToolType.QUERY,
            result_type=ResultType.TABLE,
        )
        assert tool.id == "test_tool"
        assert tool.name == "测试工具"
        assert tool.enabled is True

    def test_tool_registry_register(self):
        """测试工具注册"""
        ToolRegistry._tools.clear()
        tool = Tool(
            id="test_tool",
            name="测试工具",
            description="测试",
            tool_type=ToolType.QUERY,
            result_type=ResultType.TABLE,
        )
        ToolRegistry.register(tool)
        assert ToolRegistry.get("test_tool") is not None

    def test_tool_registry_list_by_type(self):
        """测试按类型筛选"""
        ToolRegistry._tools.clear()
        tools = get_default_tools()
        for t in tools:
            ToolRegistry.register(t)

        query_tools = ToolRegistry.search_by_type(ToolType.QUERY)
        assert len(query_tools) > 0
        assert all(t.tool_type == ToolType.QUERY for t in query_tools)


class TestDataPart:
    """DataPart模型测试"""

    def test_data_part_creation(self):
        """测试DataPart创建"""
        dp = DataPart(
            id="dp_001",
            type=DataPartType.QUERY,
            original_prompt="最近一周哪些资产被攻击",
            rewritten_prompt="查询被攻击资产Top10",
            tool_id="asset_attacks",
            params={"time_range": "last_week", "limit": 10},
        )
        assert dp.id == "dp_001"
        assert dp.type == DataPartType.QUERY
        assert dp.state == DataPartState.PENDING

    def test_data_part_with_dependencies(self):
        """测试带依赖的DataPart"""
        dp = DataPart(
            id="dp_002",
            type=DataPartType.ANALYZE,
            original_prompt="分析一下",
            depends_on=["dp_001"],
        )
        assert "dp_001" in dp.depends_on


class TestBlock:
    """预制件模型测试"""

    def test_block_creation(self):
        """测试预制件创建"""
        block = Block(
            id="block_001",
            name="资产被攻击分析",
            original_prompt="哪些资产被攻击最严重",
            rewritten_prompt="查询被攻击资产Top10",
            tool_chain=[{"tool_id": "asset_attacks", "params": {"limit": 10}}],
            result_type="table",
        )
        assert block.id == "block_001"
        assert block.category == BlockCategory.PERSONAL

    def test_block_store(self):
        """测试预制件存储"""
        BlockStore._blocks.clear()
        block = Block(
            id="block_001",
            name="测试",
            original_prompt="test",
            rewritten_prompt="test rewritten",
            tool_chain=[],
            result_type="table",
        )
        BlockStore.save(block)
        assert BlockStore.get("block_001") is not None

    def test_block_search(self):
        """测试预制件搜索"""
        BlockStore._blocks.clear()
        block = Block(
            id="block_001",
            name="资产分析",
            original_prompt="哪些资产被攻击",
            rewritten_prompt="查询资产",
            tool_chain=[],
            result_type="table",
        )
        BlockStore.save(block)

        results = BlockStore.search("资产")
        assert len(results) > 0


class TestTemplate:
    """模板模型测试"""

    def test_chapter_creation(self):
        """测试章节创建"""
        chapter = Chapter(
            id="ch1",
            title="概述",
            data_parts=["dp_001"],
            order=1,
        )
        assert chapter.id == "ch1"
        assert len(chapter.data_parts) == 1

    def test_template_creation(self):
        """测试模板创建"""
        template = Template(
            id="tpl_001",
            name="测试模板",
            description="这是一个测试模板",
            chapters=[
                Chapter(id="ch1", title="第一章", order=1),
                Chapter(id="ch2", title="第二章", order=2),
            ],
        )
        assert len(template.chapters) == 2

    def test_built_in_templates(self):
        """测试内置模板"""
        templates = get_built_in_templates()
        assert len(templates) >= 3
        assert any(t.id == "template_security_weekly" for t in templates)
