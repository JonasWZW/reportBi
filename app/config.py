"""配置管理"""
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    name: str = "smart-report-bi"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    api_key: str = ""


class EmbeddingConfig(BaseModel):
    provider: str = "sentence-transformers"
    model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"


class VectorStoreConfig(BaseModel):
    type: str = "faiss"
    index_path: str = "./storage/vector_store"
    dimension: int = 384


class DataPlatformConfig(BaseModel):
    base_url: str = ""
    api_key: str = ""
    timeout: int = 30


class CacheConfig(BaseModel):
    type: str = "redis"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    ttl: int = 3600


class BlocksConfig(BaseModel):
    storage_type: str = "file"
    storage_path: str = "./storage/blocks"


class TemplatesConfig(BaseModel):
    storage_type: str = "file"
    storage_path: str = "./storage/templates"
    built_in_path: str = "./templates"


class DatabaseConfig(BaseModel):
    url: str = "sqlite:///./storage/report_bi.db"


class AuthConfig(BaseModel):
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    llm: LLMConfig = LLMConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    vector_store: VectorStoreConfig = VectorStoreConfig()
    data_platform: DataPlatformConfig = DataPlatformConfig()
    cache: CacheConfig = CacheConfig()
    blocks: BlocksConfig = BlocksConfig()
    templates: TemplatesConfig = TemplatesConfig()
    database: DatabaseConfig = DatabaseConfig()
    auth: AuthConfig = AuthConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Settings":
        """从YAML文件加载配置"""
        path = Path(path)
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # 展开环境变量
        data = _expand_env_vars(data)
        return cls(**data)


def _expand_env_vars(data: Any) -> Any:
    """递归展开环境变量"""
    if isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        import os
        env_var = data[2:-1]
        return os.environ.get(env_var, "")
    return data


# 全局配置实例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml("config.yaml")
    return _settings
