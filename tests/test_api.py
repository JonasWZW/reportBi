"""API测试"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthEndpoint:
    """健康检查端点测试"""

    async def test_health_check(self, client):
        """测试健康检查"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
class TestToolsAPI:
    """工具API测试"""

    async def test_list_tools(self, client):
        """测试列出工具"""
        response = await client.get("/api/v1/tools/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_init_tools(self, client):
        """测试初始化工具"""
        response = await client.post("/api/v1/tools/init")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0


@pytest.mark.asyncio
class TestReportAPI:
    """报表API测试"""

    async def test_generate_report_custom_prompt(self, client):
        """测试自定义prompt生成报表"""
        # 先初始化工具
        await client.post("/api/v1/tools/init")

        response = await client.post(
            "/api/v1/report/generate",
            json={
                "custom_prompt": "最近一周哪些资产被攻击最严重",
                "user_id": "test_user"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "template_id" in data or "chapters" in data

    async def test_debug_execute(self, client):
        """测试调试执行"""
        await client.post("/api/v1/tools/init")

        response = await client.post(
            "/api/v1/report/debug/execute",
            json={
                "prompt": "最近一周哪些资产被攻击",
                "tool_id": "asset_attacks",
                "params": {"time_range": "last_week", "limit": 10}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data_part_id" in data
        assert "state" in data

    async def test_create_debug_session(self, client):
        """测试创建调试会话"""
        response = await client.post(
            "/api/v1/report/debug/session",
            params={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data


@pytest.mark.asyncio
class TestBlockAPI:
    """预制件API测试"""

    async def test_save_block(self, client):
        """测试保存预制件"""
        response = await client.post(
            "/api/v1/report/block/save",
            params={
                "original_prompt": "哪些资产被攻击",
                "rewritten_prompt": "查询被攻击资产",
                "tool_id": "asset_attacks",
                "result_type": "table",
                "name": "资产攻击查询",
                "description": "测试预制件",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "资产攻击查询"

    async def test_list_blocks(self, client):
        """测试列出预制件"""
        response = await client.get("/api/v1/report/block")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestTemplateAPI:
    """模板API测试"""

    async def test_list_templates(self, client):
        """测试列出模板"""
        response = await client.get("/api/v1/report/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_get_template(self, client):
        """测试获取单个模板"""
        response = await client.get("/api/v1/report/templates/template_security_weekly")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "template_security_weekly"
