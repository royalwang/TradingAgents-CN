"""
向量存储接口和实现
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod

try:
    import chromadb
    try:
        from chromadb.config import Settings as ChromaSettings
    except ImportError:
        # 新版本chromadb的导入方式
        from chromadb import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorStoreType(str, Enum):
    """向量存储类型"""
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ):
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索"""
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]):
        """删除"""
        pass
    
    @abstractmethod
    async def clear(self):
        """清空"""
        pass


class ChromaDBVectorStore(VectorStore):
    """ChromaDB向量存储实现"""
    
    def __init__(self, collection_name: str, persist_directory: Optional[str] = None):
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb is not installed")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # 初始化客户端
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            self.collection = self.client.create_collection(name=collection_name)
    
    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ):
        """添加文档"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        if metadatas is None:
            metadatas = [{}] * len(documents)
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索"""
        where = filters if filters else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        
        # 格式化结果
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "score": results["distances"][0][i] if results["distances"] else 0.0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
        
        return formatted_results
    
    async def delete(self, ids: List[str]):
        """删除"""
        self.collection.delete(ids=ids)
    
    async def clear(self):
        """清空"""
        # 删除集合并重新创建
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name)


def create_vector_store(
    store_type: VectorStoreType,
    collection_name: str,
    **kwargs,
) -> VectorStore:
    """创建向量存储"""
    if store_type == VectorStoreType.CHROMADB:
        persist_directory = kwargs.get("persist_directory")
        return ChromaDBVectorStore(collection_name, persist_directory)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")

