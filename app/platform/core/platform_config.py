"""
智能体平台配置
"""
from pydantic import Field
from typing import Optional, List, Dict, Any
from app.core.config import Settings


class PlatformSettings(Settings):
    """平台扩展配置"""
    
    # 知识库配置
    KNOWLEDGE_BASE_ENABLED: bool = Field(default=True)
    KNOWLEDGE_BASE_VECTOR_DB: str = Field(default="chromadb")  # chromadb, pinecone, weaviate
    KNOWLEDGE_BASE_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    KNOWLEDGE_BASE_CHUNK_SIZE: int = Field(default=1000)
    KNOWLEDGE_BASE_CHUNK_OVERLAP: int = Field(default=200)
    KNOWLEDGE_BASE_COLLECTION_PREFIX: str = Field(default="kb_")
    
    # 文档解析配置
    DOCUMENT_PARSER_ENABLED: bool = Field(default=True)
    DOCUMENT_MAX_SIZE_MB: int = Field(default=50)
    DOCUMENT_SUPPORTED_FORMATS: List[str] = Field(default_factory=lambda: [
        "pdf", "docx", "doc", "txt", "md", "xlsx", "xls", "csv", "html", "json"
    ])
    DOCUMENT_PARSER_TIMEOUT: int = Field(default=300)  # 5分钟
    
    # MCP工具配置
    MCP_ENABLED: bool = Field(default=True)
    MCP_SERVER_PORT: int = Field(default=8001)
    MCP_TOOLS_DIR: str = Field(default="app/platform/mcp/tools")
    MCP_MAX_CONCURRENT_REQUESTS: int = Field(default=10)
    
    # 插件系统配置
    PLUGIN_ENABLED: bool = Field(default=True)
    PLUGIN_DIR: str = Field(default="app/platform/plugins")
    PLUGIN_AUTO_LOAD: bool = Field(default=False)
    PLUGIN_SANDBOX_ENABLED: bool = Field(default=True)
    
    # 工作流编排配置
    WORKFLOW_ENABLED: bool = Field(default=True)
    WORKFLOW_ENGINE: str = Field(default="langgraph")  # langgraph, airflow, prefect
    WORKFLOW_MAX_CONCURRENT: int = Field(default=20)
    WORKFLOW_TIMEOUT: int = Field(default=3600)  # 1小时
    WORKFLOW_STORAGE_BACKEND: str = Field(default="mongodb")  # mongodb, redis
    
    # 智能体管理配置
    AGENT_MANAGEMENT_ENABLED: bool = Field(default=True)
    AGENT_REGISTRY_ENABLED: bool = Field(default=True)
    AGENT_MAX_INSTANCES: int = Field(default=100)
    AGENT_HEARTBEAT_INTERVAL: int = Field(default=30)  # 30秒
    
    # 平台存储配置
    PLATFORM_DATA_DIR: str = Field(default="data/platform")
    PLATFORM_LOGS_DIR: str = Field(default="logs/platform")
    PLATFORM_CACHE_DIR: str = Field(default="data/platform/cache")


# 全局平台配置实例
platform_settings = PlatformSettings()

