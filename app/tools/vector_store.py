"""向量存储和检索模块"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings
from app.schemas.tool import Tool
from app.tools.embedding import EmbeddingFunction, create_embedding_function


@dataclass
class ToolMatch:
    """工具匹配结果"""
    tool: Tool
    similarity: float
    rank: int


class VectorStore:
    """向量存储 - 基于FAISS实现"""

    def __init__(self, embedding_fn: EmbeddingFunction, dimension: int):
        self._embedding_fn = embedding_fn
        self._dimension = dimension
        self._index: Any | None = None
        self._tools: list[Tool] = []
        self._id_to_index: dict[str, int] = {}

    def initialize(self) -> None:
        """初始化向量索引"""
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu not installed. Install with: pip install faiss-cpu")

        self._index = faiss.IndexFlatIP(self._dimension)  # Inner Product for cosine similarity
        self._tools = []
        self._id_to_index = {}

    def add_tool(self, tool: Tool) -> None:
        """添加工具到向量索引"""
        if self._index is None:
            self.initialize()

        import faiss
        embedding = self._embedding_fn.embed([tool.description])[0]

        # L2 normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)

        self._index.add(np.array([embedding]).astype(np.float32))
        self._tools.append(tool)
        self._id_to_index[tool.id] = len(self._tools) - 1

    def add_tools(self, tools: list[Tool]) -> None:
        """批量添加工具"""
        for tool in tools:
            self.add_tool(tool)

    def search(self, query: str, top_k: int = 5) -> list[ToolMatch]:
        """语义搜索工具"""
        if self._index is None or self._index.ntotal == 0:
            return []

        import faiss

        query_embedding = self._embedding_fn.embed([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Search
        distances, indices = self._index.search(
            np.array([query_embedding]).astype(np.float32),
            min(top_k, self._index.ntotal)
        )

        results = []
        for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx >= 0 and idx < len(self._tools):
                # Convert L2 distance to similarity score (approximate)
                similarity = float(dist)
                results.append(ToolMatch(
                    tool=self._tools[idx],
                    similarity=similarity,
                    rank=rank + 1
                ))

        return results

    def save(self, path: str | Path) -> None:
        """保存索引到磁盘"""
        if self._index is None:
            return

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        import faiss
        faiss.write_index(self._index, str(path / "index.faiss"))

        import json
        with open(path / "tools.json", "w", encoding="utf-8") as f:
            json.dump([tool.model_dump() for tool in self._tools], f, ensure_ascii=False, indent=2)

    def load(self, path: str | Path) -> None:
        """从磁盘加载索引"""
        path = Path(path)
        if not path.exists():
            return

        try:
            import faiss
        except ImportError:
            return

        index_file = path / "index.faiss"
        tools_file = path / "tools.json"

        if index_file.exists() and tools_file.exists():
            self._index = faiss.read_index(str(index_file))

            import json
            with open(tools_file, encoding="utf-8") as f:
                tools_data = json.load(f)
                self._tools = [Tool(**t) for t in tools_data]
                self._id_to_index = {t.id: i for i, t in enumerate(self._tools)}


# 全局向量存储实例
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        embedding_fn = create_embedding_function()
        _vector_store = VectorStore(
            embedding_fn=embedding_fn,
            dimension=settings.vector_store.dimension
        )
        _vector_store.initialize()
    return _vector_store


def initialize_vector_store(tools: list[Tool] | None = None) -> VectorStore:
    """初始化向量存储并添加工具"""
    store = get_vector_store()
    if tools:
        store.add_tools(tools)
    return store
