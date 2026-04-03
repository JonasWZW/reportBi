"""语义向量化模块"""
from typing import Protocol

import numpy as np
from app.config import get_settings


class EmbeddingFunction(Protocol):
    """Embedding函数协议"""

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """将文本列表转换为向量列表"""
        ...


class SentenceTransformerEmbedding:
    """基于 sentence-transformers 的Embedding实现"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name, device=device)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """将文本列表转换为向量列表"""
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [emb for emb in embeddings]

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        return self._model.get_sentence_embedding_dimension()


class OpenAIEmbedding:
    """基于 OpenAI API 的Embedding实现"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self._api_key = api_key
        self._model = model

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """将文本列表转换为向量列表"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai not installed. Install with: pip install openai")

        client = OpenAI(api_key=self._api_key)
        response = client.embeddings.create(model=self._model, input=texts)
        return [np.array(item.embedding) for item in response.data]


def create_embedding_function() -> EmbeddingFunction:
    """创建Embedding函数实例"""
    settings = get_settings()

    if settings.embedding.provider == "sentence-transformers":
        return SentenceTransformerEmbedding(
            model_name=settings.embedding.model,
            device=settings.embedding.device
        )
    elif settings.embedding.provider == "openai":
        return OpenAIEmbedding(
            api_key=settings.llm.api_key,
            model="text-embedding-3-small"
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {settings.embedding.provider}")
