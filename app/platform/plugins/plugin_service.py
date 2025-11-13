"""
插件服务层
提供高级插件管理功能，包括YAML声明式管理
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .plugin_registry import PluginRegistry, PluginMetadata, PluginStatus, get_registry
from .yaml_loader import PluginYAMLLoader
from app.platform.core.declarative_manager import DeclarativeService


class PluginService(DeclarativeService[PluginMetadata]):
    """插件服务"""
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        loader = PluginYAMLLoader()
        super().__init__(loader)
        self.registry = registry or get_registry()
    
    async def _import_items(
        self,
        items: List[PluginMetadata],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入插件"""
        imported = []
        updated = []
        skipped = []
        errors = []
        
        for metadata in items:
            try:
                existing = self.registry.get(metadata.plugin_id)
                
                if existing:
                    if update_existing:
                        # 更新现有插件
                        self.registry.unregister(metadata.plugin_id)
                        self.registry.register(
                            plugin_id=metadata.plugin_id,
                            name=metadata.name,
                            version=metadata.version,
                            description=metadata.description,
                            author=metadata.author,
                            entry_point=metadata.entry_point,
                            config_schema=metadata.config_schema,
                            dependencies=metadata.dependencies,
                            tags=metadata.tags,
                            plugin_path=metadata.plugin_path,
                        )
                        # 恢复状态
                        if metadata.status != PluginStatus.REGISTERED:
                            self.registry.update_status(metadata.plugin_id, metadata.status)
                        updated.append(metadata.plugin_id)
                    else:
                        skipped.append(metadata.plugin_id)
                else:
                    # 注册新插件
                    self.registry.register(
                        plugin_id=metadata.plugin_id,
                        name=metadata.name,
                        version=metadata.version,
                        description=metadata.description,
                        author=metadata.author,
                        entry_point=metadata.entry_point,
                        config_schema=metadata.config_schema,
                        dependencies=metadata.dependencies,
                        tags=metadata.tags,
                        plugin_path=metadata.plugin_path,
                    )
                    # 设置状态
                    if metadata.status != PluginStatus.REGISTERED:
                        self.registry.update_status(metadata.plugin_id, metadata.status)
                    imported.append(metadata.plugin_id)
            except Exception as e:
                errors.append({
                    "plugin_id": metadata.plugin_id,
                    "error": str(e)
                })
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(items),
        }
    
    async def _get_all_items(self, filter_func: Optional[callable] = None) -> List[PluginMetadata]:
        """获取所有插件"""
        plugins = self.registry.list()
        
        if filter_func:
            plugins = [plugin for plugin in plugins if filter_func(plugin)]
        
        return plugins


# 全局服务实例
_global_service: Optional[PluginService] = None


def get_service() -> PluginService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = PluginService()
    return _global_service

