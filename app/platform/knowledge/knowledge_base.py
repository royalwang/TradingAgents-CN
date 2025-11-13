"""
知识库核心模块
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .vector_store import VectorStore, VectorStoreType
from .embedding_service import EmbeddingService


class DocumentStatus(str, Enum):
    """文档状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


@dataclass
class DocumentChunk:
    """文档块"""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


@dataclass
class Document:
    """文档"""
    document_id: str
    title: str
    content: str
    source: str
    document_type: str
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[DocumentChunk] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "source": self.source,
            "document_type": self.document_type,
            "status": self.status.value,
            "metadata": self.metadata,
            "chunk_count": len(self.chunks),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }


class KnowledgeBase:
    """知识库"""
    
    def __init__(
        self,
        name: str,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.name = name
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._documents: Dict[str, Document] = {}
    
    async def add_document(
        self,
        title: str,
        content: str,
        source: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        auto_index: bool = True,
    ) -> Document:
        """添加文档"""
        document_id = str(uuid.uuid4())
        
        document = Document(
            document_id=document_id,
            title=title,
            content=content,
            source=source,
            document_type=document_type,
            metadata=metadata or {},
            status=DocumentStatus.PENDING,
        )
        
        self._documents[document_id] = document
        
        if auto_index:
            await self.index_document(document_id)
        
        return document
    
    async def index_document(self, document_id: str) -> bool:
        """索引文档"""
        document = self._documents.get(document_id)
        if not document:
            return False
        
        try:
            document.status = DocumentStatus.PROCESSING
            
            # 分块
            chunks = self._chunk_document(document)
            document.chunks = chunks
            
            # 生成嵌入
            for chunk in chunks:
                chunk.embedding = await self.embedding_service.embed(chunk.content)
            
            # 存储到向量数据库
            await self.vector_store.add_documents(
                documents=[chunk.content for chunk in chunks],
                embeddings=[chunk.embedding for chunk in chunks],
                metadatas=[{
                    **chunk.metadata,
                    "document_id": document_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                } for chunk in chunks],
                ids=[chunk.chunk_id for chunk in chunks],
            )
            
            document.status = DocumentStatus.INDEXED
            document.indexed_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            
            return True
        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.metadata["error"] = str(e)
            return False
    
    def _chunk_document(self, document: Document) -> List[DocumentChunk]:
        """文档分块"""
        chunks = []
        content = document.content
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk_content = content[start:end]
            
            chunk_id = f"{document.document_id}_chunk_{chunk_index}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                content=chunk_content,
                metadata={
                    **document.metadata,
                    "title": document.title,
                    "source": document.source,
                    "document_type": document.document_type,
                },
                chunk_index=chunk_index,
                start_char=start,
                end_char=end,
            )
            
            chunks.append(chunk)
            
            # 移动到下一个块（考虑重叠）
            start = end - self.chunk_overlap
            chunk_index += 1
        
        return chunks
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索文档"""
        # 生成查询嵌入
        query_embedding = await self.embedding_service.embed(query)
        
        # 在向量数据库中搜索
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
        
        # 格式化结果
        formatted_results = []
        for result in results:
            chunk_id = result.get("id")
            if chunk_id:
                # 查找对应的文档
                document_id = result.get("metadata", {}).get("document_id")
                if document_id and document_id in self._documents:
                    document = self._documents[document_id]
                    formatted_results.append({
                        "document": document.to_dict(),
                        "chunk": result.get("document", ""),
                        "score": result.get("score", 0.0),
                        "metadata": result.get("metadata", {}),
                    })
        
        return formatted_results
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        return self._documents.get(document_id)
    
    def list_documents(
        self,
        document_type: Optional[str] = None,
        status: Optional[DocumentStatus] = None,
    ) -> List[Document]:
        """列出文档"""
        result = []
        
        for document in self._documents.values():
            if document_type and document.document_type != document_type:
                continue
            if status and document.status != status:
                continue
            result.append(document)
        
        return result
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        document = self._documents.get(document_id)
        if not document:
            return False
        
        # 从向量数据库中删除
        chunk_ids = [chunk.chunk_id for chunk in document.chunks]
        if chunk_ids:
            await self.vector_store.delete(ids=chunk_ids)
        
        # 从内存中删除
        del self._documents[document_id]
        
        return True
    
    async def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reindex: bool = True,
    ) -> bool:
        """更新文档"""
        document = self._documents.get(document_id)
        if not document:
            return False
        
        if title:
            document.title = title
        if content:
            document.content = content
        if metadata:
            document.metadata.update(metadata)
        
        document.updated_at = datetime.utcnow()
        
        if reindex:
            # 先删除旧的索引
            chunk_ids = [chunk.chunk_id for chunk in document.chunks]
            if chunk_ids:
                await self.vector_store.delete(ids=chunk_ids)
            
            # 重新索引
            await self.index_document(document_id)
        
        return True

