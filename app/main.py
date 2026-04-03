"""FastAPI应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as report_router
from app.api.tools import router as tools_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    settings = get_settings()
    print(f"Starting {settings.app.name} v{settings.app.version}")

    # 初始化工具注册表
    from app.schemas.tool import ToolRegistry, get_default_tools
    from app.tools.vector_store import initialize_vector_store

    tools = get_default_tools()
    for tool in tools:
        ToolRegistry.register(tool)
    initialize_vector_store(tools)

    yield

    # 关闭时
    print("Shutting down...")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="智能报表BI系统 - 基于LangChain/LangGraph的报表生成平台",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(report_router)
    app.include_router(tools_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app.version}

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
