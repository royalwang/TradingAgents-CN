"""
数据源服务层
提供高级数据源管理功能
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .data_source_registry import DataSourceRegistry, DataSourceMetadata, get_registry
from .data_source_manager import DataSourceManager, get_manager
from .data_source_factory import DataSourceFactory, get_factory
from .yaml_loader import DataSourceYAMLLoader


class DataSourceService:
    """数据源服务"""
    
    def __init__(
        self,
        registry: Optional[DataSourceRegistry] = None,
        manager: Optional[DataSourceManager] = None,
        factory: Optional[DataSourceFactory] = None,
    ):
        self.registry = registry or get_registry()
        self.manager = manager or get_manager()
        self.factory = factory or get_factory()
        self.yaml_loader = DataSourceYAMLLoader()
    
    async def import_from_yaml_file(
        self,
        file_path: str,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """从YAML文件导入数据源配置"""
        sources = self.yaml_loader.load_from_file(file_path)
        return await self._import_sources(sources, update_existing)
    
    async def import_from_yaml_string(
        self,
        yaml_str: str,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """从YAML字符串导入数据源配置"""
        sources = self.yaml_loader.load_from_string(yaml_str)
        return await self._import_sources(sources, update_existing)
    
    async def _import_sources(
        self,
        sources: List[DataSourceMetadata],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入数据源"""
        results = {
            "registered": [],
            "updated": [],
            "skipped": [],
            "errors": [],
        }
        
        for source in sources:
            try:
                existing = self.registry.get(source.source_id)
                if existing:
                    if update_existing:
                        # 更新现有数据源
                        # 注意：这里只更新元数据，不更新适配器类
                        existing.display_name = source.display_name
                        existing.description = source.description
                        existing.priority = source.priority
                        existing.enabled = source.enabled
                        existing.config = source.config
                        existing.supported_markets = source.supported_markets
                        existing.supported_features = source.supported_features
                        existing.tags = source.tags
                        existing.website = source.website
                        existing.documentation_url = source.documentation_url
                        existing.updated_at = datetime.utcnow()
                        results["updated"].append(source.source_id)
                    else:
                        results["skipped"].append(source.source_id)
                else:
                    # 注册新数据源
                    # 注意：YAML导入只注册元数据，不包含适配器类
                    # 适配器类需要通过代码注册
                    self.registry.register(source)
                    results["registered"].append(source.source_id)
            except Exception as e:
                results["errors"].append({
                    "source_id": source.source_id,
                    "error": str(e),
                })
        
        return results
    
    async def export_to_yaml_file(
        self,
        file_path: str,
        source_type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        """导出数据源配置到YAML文件"""
        from .data_source_registry import DataSourceType
        
        type_enum = None
        if source_type:
            type_enum = DataSourceType(source_type)
        
        sources = self.registry.list(
            source_type=type_enum,
            enabled=enabled,
        )
        
        self.yaml_loader.export_to_yaml(sources, file_path)
    
    async def get_all(
        self,
        source_type: Optional[str] = None,
        market: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> List[DataSourceMetadata]:
        """获取所有数据源"""
        from .data_source_registry import DataSourceType
        
        type_enum = None
        if source_type:
            type_enum = DataSourceType(source_type)
        
        return self.registry.list(
            source_type=type_enum,
            market=market,
            enabled=enabled,
        )
    
    async def get_by_id(self, source_id: str) -> Optional[DataSourceMetadata]:
        """根据ID获取数据源"""
        return self.registry.get(source_id)
    
    async def register_source(
        self,
        source_data: Dict[str, Any],
        adapter_class: Optional[Any] = None,
    ) -> DataSourceMetadata:
        """注册数据源"""
        from .data_source_registry import DataSourceType
        
        source = DataSourceMetadata(
            source_id=source_data["source_id"],
            name=source_data.get("name", source_data["source_id"]),
            display_name=source_data.get("display_name", source_data["source_id"]),
            description=source_data.get("description"),
            source_type=DataSourceType(source_data.get("source_type", "stock")),
            version=source_data.get("version", "1.0.0"),
            author=source_data.get("author", "unknown"),
            priority=source_data.get("priority", 0),
            enabled=source_data.get("enabled", True),
            config=source_data.get("config", {}),
            supported_markets=source_data.get("supported_markets", []),
            supported_features=source_data.get("supported_features", []),
            adapter_class=adapter_class,
            tags=source_data.get("tags", []),
            website=source_data.get("website"),
            documentation_url=source_data.get("documentation_url"),
        )
        
        self.registry.register(source)
        return source
    
    async def update_source(
        self,
        source_id: str,
        source_data: Dict[str, Any],
    ) -> DataSourceMetadata:
        """更新数据源"""
        source = self.registry.get(source_id)
        if not source:
            raise ValueError(f"Data source {source_id} not found")
        
        # 更新字段
        if "display_name" in source_data:
            source.display_name = source_data["display_name"]
        if "description" in source_data:
            source.description = source_data["description"]
        if "priority" in source_data:
            source.priority = source_data["priority"]
        if "enabled" in source_data:
            source.enabled = source_data["enabled"]
        if "config" in source_data:
            source.config.update(source_data["config"])
        if "supported_markets" in source_data:
            source.supported_markets = source_data["supported_markets"]
        if "supported_features" in source_data:
            source.supported_features = source_data["supported_features"]
        if "tags" in source_data:
            source.tags = source_data["tags"]
        if "website" in source_data:
            source.website = source_data["website"]
        if "documentation_url" in source_data:
            source.documentation_url = source_data["documentation_url"]
        
        source.updated_at = datetime.utcnow()
        return source
    
    async def delete_source(self, source_id: str) -> bool:
        """删除数据源"""
        return self.registry.unregister(source_id)


# 全局服务实例
_global_service: Optional[DataSourceService] = None


def get_service() -> DataSourceService:
    """获取全局数据源服务"""
    global _global_service
    if _global_service is None:
        _global_service = DataSourceService()
    return _global_service

