"""
Provider服务层
提供高级Provider管理功能
"""
from typing import List, Dict, Any, Optional
from pathlib import Path

from .provider_manager import ProviderManager, ProviderMetadata, get_provider_manager
from .yaml_loader import YAMLProviderLoader
from app.models.config import LLMProvider


class ProviderService:
    """Provider服务"""
    
    def __init__(self, manager: Optional[ProviderManager] = None):
        self.manager = manager or get_provider_manager()
        self.yaml_loader = YAMLProviderLoader()
    
    async def import_from_yaml_file(
        self,
        file_path: str,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """从YAML文件导入Provider"""
        providers = self.yaml_loader.load_from_file(file_path)
        return await self.manager.import_batch(providers, update_existing)
    
    async def import_from_yaml_string(
        self,
        yaml_str: str,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """从YAML字符串导入Provider"""
        providers = self.yaml_loader.load_from_string(yaml_str)
        return await self.manager.import_batch(providers, update_existing)
    
    async def export_to_yaml_file(
        self,
        file_path: str,
        is_active: Optional[bool] = None,
    ):
        """导出Provider到YAML文件"""
        providers_list = await self.manager.list(is_active=is_active)
        
        # 转换为ProviderMetadata
        providers = []
        for provider in providers_list:
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
            providers.append(metadata)
        
        self.yaml_loader.export_to_yaml(providers, file_path)
    
    async def get_all(self, is_active: Optional[bool] = None) -> List[LLMProvider]:
        """获取所有Provider"""
        return await self.manager.list(is_active=is_active)
    
    async def get_by_name(self, name: str) -> Optional[LLMProvider]:
        """根据名称获取Provider"""
        return await self.manager.get(name)
    
    async def create_provider(
        self,
        provider_data: Dict[str, Any],
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> LLMProvider:
        """创建Provider"""
        provider = ProviderMetadata(
            name=provider_data["name"],
            display_name=provider_data.get("display_name", provider_data["name"]),
            description=provider_data.get("description"),
            website=provider_data.get("website"),
            api_doc_url=provider_data.get("api_doc_url"),
            logo_url=provider_data.get("logo_url"),
            is_active=provider_data.get("is_active", True),
            supported_features=provider_data.get("supported_features", []),
            default_base_url=provider_data.get("default_base_url"),
            is_aggregator=provider_data.get("is_aggregator", False),
            aggregator_type=provider_data.get("aggregator_type"),
            model_name_format=provider_data.get("model_name_format"),
            extra_config=provider_data.get("extra_config", {}),
        )
        
        return await self.manager.create(provider, api_key, api_secret)
    
    async def update_provider(
        self,
        name: str,
        provider_data: Dict[str, Any],
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> LLMProvider:
        """更新Provider"""
        provider = ProviderMetadata(
            name=provider_data.get("name", name),
            display_name=provider_data.get("display_name"),
            description=provider_data.get("description"),
            website=provider_data.get("website"),
            api_doc_url=provider_data.get("api_doc_url"),
            logo_url=provider_data.get("logo_url"),
            is_active=provider_data.get("is_active"),
            supported_features=provider_data.get("supported_features"),
            default_base_url=provider_data.get("default_base_url"),
            is_aggregator=provider_data.get("is_aggregator"),
            aggregator_type=provider_data.get("aggregator_type"),
            model_name_format=provider_data.get("model_name_format"),
            extra_config=provider_data.get("extra_config", {}),
        )
        
        return await self.manager.update(name, provider, api_key, api_secret)
    
    async def delete_provider(self, name: str) -> bool:
        """删除Provider"""
        return await self.manager.delete(name)


# 全局服务实例
_global_service: Optional[ProviderService] = None


def get_provider_service() -> ProviderService:
    """获取全局Provider服务"""
    global _global_service
    if _global_service is None:
        _global_service = ProviderService()
    return _global_service

