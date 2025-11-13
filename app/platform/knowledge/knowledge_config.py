"""
知识库配置元数据
用于YAML声明式管理
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class KnowledgeBaseStatus(str, Enum):
    """知识库状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class KnowledgeBaseMetadata:
    """知识库元数据"""
    kb_id: str
    name: str
    description: str
    vector_store_type: str = "chromadb"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: Optional[str] = None
    persist_directory: Optional[str] = None
    status: KnowledgeBaseStatus = KnowledgeBaseStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "kb_id": self.kb_id,
            "name": self.name,
            "description": self.description,
            "vector_store_type": self.vector_store_type,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "status": self.status.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class DocumentMetadata:
    """文档元数据（用于YAML管理，不包含完整内容）"""
    document_id: str
    kb_id: str
    title: str
    source: str
    document_type: str
    content_length: int = 0
    chunk_count: int = 0
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "kb_id": self.kb_id,
            "title": self.title,
            "source": self.source,
            "document_type": self.document_type,
            "content_length": self.content_length,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }

