"""报表生成API路由"""
from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.report_generation_agent import get_report_generation_agent
from app.agents.debug_agent import get_debug_agent
from app.schemas.report import (
    ReportGenerationRequest,
    ReportGenerationResult,
    DataPartExecutionRequest,
    DebugSession,
    DataPartResult,
)
from app.schemas.block import Block, BlockStore, BlockCategory
from app.schemas.template import Template, get_built_in_templates
from app.tools.vector_store import initialize_vector_store, get_vector_store
from app.schemas.tool import ToolRegistry, get_default_tools

router = APIRouter(prefix="/api/v1", tags=["report"])


@router.post("/report/generate", response_model=ReportGenerationResult)
async def generate_report(request: ReportGenerationRequest) -> ReportGenerationResult:
    """
    生成报表

    - 使用模板ID：加载模板并生成报表
    - 使用自定义prompt：先改写prompt，然后生成报表
    """
    # 确保工具注册表已初始化
    if not ToolRegistry.list_all():
        tools = get_default_tools()
        for tool in tools:
            ToolRegistry.register(tool)
        initialize_vector_store(tools)

    agent = get_report_generation_agent()
    result = await agent.generate(request)
    return result


@router.post("/report/debug/execute", response_model=DataPartResult)
async def debug_execute(request: DataPartExecutionRequest) -> DataPartResult:
    """
    调试模式：执行单个Data Part

    用于用户调试单个prompt，确认结果是否符合预期
    """
    agent = get_debug_agent()
    result = await agent.execute_single(request)
    return result


@router.post("/report/debug/rewrite", response_model=dict[str, Any])
async def debug_rewrite_and_execute(
    prompt: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    调试模式：改写prompt并执行

    输入用户原始prompt，系统自动改写并执行，返回结果
    """
    agent = get_debug_agent()

    if session_id:
        # 使用现有会话
        session = agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        # 创建新会话
        session = agent.create_session()
        session_id = session.id

    data_part, result = await agent.rewrite_and_execute(prompt, session_id)

    return {
        "session_id": session_id,
        "data_part": {
            "id": data_part.id,
            "type": data_part.type,
            "original_prompt": data_part.original_prompt,
            "rewritten_prompt": data_part.rewritten_prompt,
            "tool_id": data_part.tool_id,
            "params": data_part.params,
        },
        "result": result.model_dump(),
    }


@router.post("/report/debug/session", response_model=DebugSession)
async def create_debug_session(user_id: str = "anonymous") -> DebugSession:
    """创建调试会话"""
    agent = get_debug_agent()
    session = agent.create_session(user_id)
    return session


@router.get("/report/debug/session/{session_id}/history")
async def get_debug_history(session_id: str) -> list[dict[str, Any]]:
    """获取调试历史"""
    agent = get_debug_agent()
    history = agent.get_history(session_id)
    return [
        {
            "id": dp.id,
            "type": dp.type,
            "original_prompt": dp.original_prompt,
            "rewritten_prompt": dp.rewritten_prompt,
            "tool_id": dp.tool_id,
            "params": dp.params,
            "state": dp.state,
            "result_type": dp.result_type,
            "error": dp.error,
            "created_at": dp.created_at.isoformat(),
            "completed_at": dp.completed_at.isoformat() if dp.completed_at else None,
        }
        for dp in history
    ]


@router.post("/report/block/save", response_model=Block)
async def save_block(
    original_prompt: str,
    rewritten_prompt: str,
    tool_id: str,
    params: dict[str, Any],
    result_type: str,
    name: str,
    description: str = "",
    category: BlockCategory = BlockCategory.PERSONAL,
    user_id: str = "anonymous",
) -> Block:
    """
    保存预制件

    用户调试满意后，可以将改写后的prompt+工具链保存为预制件
    """
    import uuid

    block = Block(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        original_prompt=original_prompt,
        rewritten_prompt=rewritten_prompt,
        tool_chain=[
            {
                "tool_id": tool_id,
                "params": params,
            }
        ],
        result_type=result_type,
        category=category,
        created_by=user_id,
    )

    BlockStore.save(block)
    return block


@router.get("/report/block", response_model=list[Block])
async def list_blocks(
    category: BlockCategory | None = None,
    keyword: str | None = None,
) -> list[Block]:
    """
    列出预制件

    - 按分类筛选
    - 按关键词搜索
    """
    if category:
        return BlockStore.list_by_category(category)
    elif keyword:
        return BlockStore.search(keyword)
    else:
        return BlockStore.list_all()


@router.get("/report/block/{block_id}", response_model=Block | None)
async def get_block(block_id: str) -> Block | None:
    """获取预制件详情"""
    return BlockStore.get(block_id)


@router.delete("/report/block/{block_id}")
async def delete_block(block_id: str) -> dict[str, bool]:
    """删除预制件"""
    success = BlockStore.delete(block_id)
    return {"success": success}


@router.get("/report/templates")
async def list_templates() -> list[Template]:
    """列出可用模板"""
    return get_built_in_templates()


@router.get("/report/templates/{template_id}")
async def get_template(template_id: str) -> Template | None:
    """获取模板详情"""
    templates = get_built_in_templates()
    return next((t for t in templates if t.id == template_id), None)
