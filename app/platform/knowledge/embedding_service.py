"""
嵌入服务
提供文本嵌入功能
"""
from typing import List, Optional
from abc import ABC, abstractmethod

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingService(ABC):
    """嵌入服务抽象基类"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """生成嵌入"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入"""
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI嵌入服务"""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is not installed")
        
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
    
    async def embed(self, text: str) -> List[float]:
        """生成嵌入"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        
        return [item.embedding for item in response.data]


def create_embedding_service(
    service_type: str = "openai",
    model: str = "text-embedding-3-small",
    **kwargs,
) -> EmbeddingService:
    """创建嵌入服务"""
    if service_type == "openai":
        api_key = kwargs.get("api_key")
        return OpenAIEmbeddingService(model=model, api_key=api_key)
    else:
        raise ValueError(f"Unsupported embedding service type: {service_type}")

