"""工具管理API路由"""
from typing import Any

from fastapi import APIRouter

from app.schemas.tool import Tool, ToolType, ToolRegistry, get_default_tools
from app.tools.vector_store import initialize_vector_store, get_vector_store

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("/", response_model=list[Tool])
async def list_tools() -> list[Tool]:
    """列出所有注册的工具"""
    return ToolRegistry.list_all()


@router.get("/types")
async def list_tool_types() -> dict[str, list[Tool]]:
    """按类型列出工具"""
    return {
        "query": ToolRegistry.search_by_type(ToolType.QUERY),
        "chart": ToolRegistry.search_by_type(ToolType.CHART),
        "analyze": ToolRegistry.search_by_type(ToolType.ANALYZE),
        "document": ToolRegistry.search_by_type(ToolType.DOCUMENT),
    }


@router.get("/search")
async def search_tools(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    语义搜索工具

    根据用户描述搜索匹配的工具
    """
    store = get_vector_store()
    matches = store.search(query, top_k=top_k)

    return [
        {
            "tool_id": m.tool.id,
            "name": m.tool.name,
            "description": m.tool.description,
            "similarity": m.similarity,
            "rank": m.rank,
        }
        for m in matches
    ]


@router.post("/register", response_model=Tool)
async def register_tool(tool: Tool) -> Tool:
    """注册新工具"""
    ToolRegistry.register(tool)

    # 同时添加到向量存储
    store = get_vector_store()
    store.add_tool(tool)

    return tool


@router.delete("/{tool_id}")
async def unregister_tool(tool_id: str) -> dict[str, bool]:
    """注销工具"""
    success = ToolRegistry.unregister(tool_id)
    return {"success": success}


@router.post("/init")
async def initialize_tools() -> dict[str, Any]:
    """初始化工具注册表"""
    tools = get_default_tools()
    for tool in tools:
        ToolRegistry.register(tool)

    # 初始化向量存储
    store = initialize_vector_store(tools)

    return {
        "message": "Tools initialized",
        "count": len(tools),
        "tool_ids": [t.id for t in tools],
    }
