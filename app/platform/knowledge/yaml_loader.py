"""
知识库YAML加载器
从YAML文件加载知识库配置
"""
from typing import List, Dict, Any
from datetime import datetime

from app.platform.core.declarative_manager import DeclarativeYAMLLoader
from .knowledge_config import KnowledgeBaseMetadata, DocumentMetadata, KnowledgeBaseStatus


class KnowledgeBaseYAMLLoader(DeclarativeYAMLLoader[KnowledgeBaseMetadata]):
    """知识库YAML加载器"""
    
    def __init__(self):
        super().__init__("knowledge_bases")
    
    def _parse_item(self, data: Dict[str, Any]) -> KnowledgeBaseMetadata:
        """解析单个知识库配置"""
        # 必需字段
        kb_id = data.get("kb_id") or data.get("id")
        if not kb_id:
            raise ValueError("Knowledge base 'kb_id' is required")
        
        name = data.get("name") or kb_id
        description = data.get("description", "")
        
        # 可选字段
        metadata = KnowledgeBaseMetadata(
            kb_id=kb_id,
            name=name,
            description=description,
            vector_store_type=data.get("vector_store_type", "chromadb"),
            embedding_model=data.get("embedding_model", "text-embedding-3-small"),
            chunk_size=data.get("chunk_size", 1000),
            chunk_overlap=data.get("chunk_overlap", 200),
            collection_name=data.get("collection_name"),
            persist_directory=data.get("persist_directory"),
            status=KnowledgeBaseStatus(data.get("status", "active")),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        
        # 处理时间字段
        if "created_at" in data:
            metadata.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return metadata
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段"""
        return "kb_id" in data or "id" in data
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段"""
        if "kb_id" not in data:
            data["kb_id"] = value


class DocumentYAMLLoader(DeclarativeYAMLLoader[DocumentMetadata]):
    """文档元数据YAML加载器"""
    
    def __init__(self):
        super().__init__("documents")
    
    def _parse_item(self, data: Dict[str, Any]) -> DocumentMetadata:
        """解析单个文档元数据"""
        # 必需字段
        document_id = data.get("document_id") or data.get("id")
        if not document_id:
            raise ValueError("Document 'document_id' is required")
        
        kb_id = data.get("kb_id")
        if not kb_id:
            raise ValueError("Document 'kb_id' is required")
        
        title = data.get("title", "")
        source = data.get("source", "")
        document_type = data.get("document_type", "txt")
        
        # 可选字段
        metadata = DocumentMetadata(
            document_id=document_id,
            kb_id=kb_id,
            title=title,
            source=source,
            document_type=document_type,
            content_length=data.get("content_length", 0),
            chunk_count=data.get("chunk_count", 0),
            status=data.get("status", "pending"),
            metadata=data.get("metadata", {}),
        )
        
        # 处理时间字段
        if "created_at" in data:
            metadata.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        if "indexed_at" in data:
            metadata.indexed_at = datetime.fromisoformat(data["indexed_at"])
        
        return metadata
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段"""
        return "document_id" in data or "id" in data
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段"""
        if "document_id" not in data:
            data["document_id"] = value


# 示例YAML格式
EXAMPLE_KNOWLEDGE_BASES_YAML = """
# 知识库配置示例
knowledge_bases:
  - kb_id: stock_research
    name: 股票研究知识库
    description: 存储股票研究报告和分析文档
    vector_store_type: chromadb
    embedding_model: text-embedding-3-small
    chunk_size: 1000
    chunk_overlap: 200
    collection_name: kb_stock_research
    persist_directory: data/chromadb
    status: active
    tags:
      - stock
      - research
      - analysis
    metadata:
      category: research
      market: A股
  
  - kb_id: financial_reports
    name: 财务报告知识库
    description: 存储上市公司财务报告
    vector_store_type: chromadb
    embedding_model: text-embedding-3-small
    chunk_size: 1500
    chunk_overlap: 300
    status: active
    tags:
      - financial
      - reports
"""

EXAMPLE_DOCUMENTS_YAML = """
# 文档元数据配置示例
documents:
  - document_id: doc_001
    kb_id: stock_research
    title: 招商银行2024年Q3财报分析
    source: https://example.com/report.pdf
    document_type: pdf
    content_length: 50000
    chunk_count: 50
    status: indexed
    metadata:
      author: 分析师A
      category: 财报分析
      publish_date: 2024-10-15
    created_at: 2024-10-17T10:00:00Z
    indexed_at: 2024-10-17T10:05:00Z
"""

