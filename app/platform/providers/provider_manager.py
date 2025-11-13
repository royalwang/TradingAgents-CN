"""
LLM Provider管理器
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.models.config import LLMProvider
from app.core.database import get_mongo_db
from app.utils.timezone import now_tz


class ProviderStatus(str, Enum):
    """Provider状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


@dataclass
class ProviderMetadata:
    """Provider元数据"""
    name: str
    display_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    api_doc_url: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True
    supported_features: List[str] = field(default_factory=list)
    default_base_url: Optional[str] = None
    is_aggregator: bool = False
    aggregator_type: Optional[str] = None
    model_name_format: Optional[str] = None
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "website": self.website,
            "api_doc_url": self.api_doc_url,
            "logo_url": self.logo_url,
            "is_active": self.is_active,
            "supported_features": self.supported_features,
            "default_base_url": self.default_base_url,
            "is_aggregator": self.is_aggregator,
            "aggregator_type": self.aggregator_type,
            "model_name_format": self.model_name_format,
            "extra_config": self.extra_config,
        }
    
    def to_llm_provider(self) -> LLMProvider:
        """转换为LLMProvider模型"""
        return LLMProvider(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            website=self.website,
            api_doc_url=self.api_doc_url,
            logo_url=self.logo_url,
            is_active=self.is_active,
            supported_features=self.supported_features,
            default_base_url=self.default_base_url,
            is_aggregator=self.is_aggregator,
            aggregator_type=self.aggregator_type,
            model_name_format=self.model_name_format,
            extra_config=self.extra_config,
        )


class ProviderRegistry:
    """Provider注册表（内存）"""
    
    def __init__(self):
        self._providers: Dict[str, ProviderMetadata] = {}
    
    def register(self, provider: ProviderMetadata) -> ProviderMetadata:
        """注册Provider"""
        if provider.name in self._providers:
            raise ValueError(f"Provider {provider.name} already registered")
        
        self._providers[provider.name] = provider
        return provider
    
    def get(self, name: str) -> Optional[ProviderMetadata]:
        """获取Provider"""
        return self._providers.get(name)
    
    def list(self, is_active: Optional[bool] = None) -> List[ProviderMetadata]:
        """列出Provider"""
        result = []
        for provider in self._providers.values():
            if is_active is None or provider.is_active == is_active:
                result.append(provider)
        return result
    
    def unregister(self, name: str) -> bool:
        """注销Provider"""
        if name in self._providers:
            del self._providers[name]
            return True
        return False


class ProviderManager:
    """Provider管理器（数据库）"""
    
    def __init__(self):
        self._registry = ProviderRegistry()
    
    async def load_from_database(self) -> List[LLMProvider]:
        """从数据库加载所有Provider"""
        db = get_mongo_db()
        providers_collection = db.llm_providers
        
        providers_data = await providers_collection.find().to_list(length=None)
        providers = []
        
        for provider_data in providers_data:
            provider = LLMProvider(**provider_data)
            providers.append(provider)
            
            # 同步到注册表
            metadata = ProviderMetadata(
                name=provider.name,
                display_name=provider.display_name,
                description=provider.description,
                website=provider.website,
                api_doc_url=provider.api_doc_url,
                logo_url=provider.logo_url,
                is_active=provider.is_active,
                supported_features=provider.supported_features,
                default_base_url=provider.default_base_url,
                is_aggregator=provider.is_aggregator,
                aggregator_type=provider.aggregator_type,
                model_name_format=provider.model_name_format,
                extra_config=provider.extra_config or {},
            )
            self._registry.register(metadata)
        
        return providers
    
    async def create(
        self,
        provider: ProviderMetadata,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> LLMProvider:
        """创建Provider"""
        db = get_mongo_db()
        providers_collection = db.llm_providers
        
        # 检查是否已存在
        existing = await providers_collection.find_one({"name": provider.name})
        if existing:
            raise ValueError(f"Provider {provider.name} already exists")
        
        # 创建LLMProvider对象
        llm_provider = provider.to_llm_provider()
        llm_provider.api_key = api_key
        llm_provider.api_secret = api_secret
        llm_provider.created_at = now_tz()
        llm_provider.updated_at = now_tz()
        
        # 插入数据库
        provider_dict = llm_provider.model_dump(by_alias=True, exclude={"id"})
        result = await providers_collection.insert_one(provider_dict)
        llm_provider.id = result.inserted_id
        
        # 注册到内存
        self._registry.register(provider)
        
        return llm_provider
    
    async def update(
        self,
        name: str,
        provider: ProviderMetadata,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> LLMProvider:
        """更新Provider"""
        db = get_mongo_db()
        providers_collection = db.llm_providers
        
        # 查找现有Provider
        existing = await providers_collection.find_one({"name": name})
        if not existing:
            raise ValueError(f"Provider {name} not found")
        
        # 更新数据
        update_data = provider.to_dict()
        update_data["updated_at"] = now_tz()
        
        if api_key is not None:
            update_data["api_key"] = api_key
        if api_secret is not None:
            update_data["api_secret"] = api_secret
        
        # 更新数据库
        await providers_collection.update_one(
            {"name": name},
            {"$set": update_data}
        )
        
        # 更新注册表
        self._registry.unregister(name)
        self._registry.register(provider)
        
        # 返回更新后的Provider
        updated = await providers_collection.find_one({"name": name})
        return LLMProvider(**updated)
    
    async def delete(self, name: str) -> bool:
        """删除Provider"""
        db = get_mongo_db()
        providers_collection = db.llm_providers
        
        result = await providers_collection.delete_one({"name": name})
        
        if result.deleted_count > 0:
            self._registry.unregister(name)
            return True
        
        return False
    
    async def get(self, name: str) -> Optional[LLMProvider]:
        """获取Provider"""
        db = get_mongo_db()
        providers_collection = db.llm_providers
        
        provider_data = await providers_collection.find_one({"name": name})
        if provider_data:
            return LLMProvider(**provider_data)
        return None
    
    async def list(self, is_active: Optional[bool] = None) -> List[LLMProvider]:
        """列出所有Provider"""
        db = get_mongo_db()
        providers_collection = db.llm_providers
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        
        providers_data = await providers_collection.find(query).to_list(length=None)
        return [LLMProvider(**data) for data in providers_data]
    
    async def import_batch(
        self,
        providers: List[ProviderMetadata],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """批量导入Provider"""
        results = {
            "created": [],
            "updated": [],
            "skipped": [],
            "errors": [],
        }
        
        for provider in providers:
            try:
                existing = await self.get(provider.name)
                if existing:
                    if update_existing:
                        await self.update(provider.name, provider)
                        results["updated"].append(provider.name)
                    else:
                        results["skipped"].append(provider.name)
                else:
                    await self.create(provider)
                    results["created"].append(provider.name)
            except Exception as e:
                results["errors"].append({
                    "name": provider.name,
                    "error": str(e),
                })
        
        return results


# 全局管理器实例
_global_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """获取全局Provider管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = ProviderManager()
    return _global_manager

