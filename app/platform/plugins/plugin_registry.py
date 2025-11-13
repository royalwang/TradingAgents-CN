"""
插件注册表
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class PluginStatus(str, Enum):
    """插件状态"""
    REGISTERED = "registered"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass
class PluginMetadata:
    """插件元数据"""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    entry_point: str  # 插件入口点（模块路径或文件路径）
    config_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.REGISTERED
    plugin_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "entry_point": self.entry_point,
            "config_schema": self.config_schema,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "status": self.status.value,
            "plugin_path": self.plugin_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error_message": self.error_message,
        }


class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self._plugins: Dict[str, PluginMetadata] = {}
        self._by_tag: Dict[str, List[str]] = {}
    
    def register(
        self,
        plugin_id: str,
        name: str,
        version: str,
        description: str,
        author: str,
        entry_point: str,
        config_schema: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        plugin_path: Optional[str] = None,
    ) -> PluginMetadata:
        """注册插件"""
        if plugin_id in self._plugins:
            raise ValueError(f"Plugin {plugin_id} already registered")
        
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name=name,
            version=version,
            description=description,
            author=author,
            entry_point=entry_point,
            config_schema=config_schema or {},
            dependencies=dependencies or [],
            tags=tags or [],
            plugin_path=plugin_path,
        )
        
        self._plugins[plugin_id] = metadata
        
        # 按标签索引
        for tag in metadata.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(plugin_id)
        
        return metadata
    
    def get(self, plugin_id: str) -> Optional[PluginMetadata]:
        """获取插件元数据"""
        return self._plugins.get(plugin_id)
    
    def list(
        self,
        status: Optional[PluginStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[PluginMetadata]:
        """列出插件"""
        result = []
        
        for metadata in self._plugins.values():
            if status and metadata.status != status:
                continue
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            result.append(metadata)
        
        return result
    
    def unregister(self, plugin_id: str) -> bool:
        """注销插件"""
        if plugin_id not in self._plugins:
            return False
        
        metadata = self._plugins[plugin_id]
        del self._plugins[plugin_id]
        
        # 从标签索引中移除
        for tag in metadata.tags:
            if tag in self._by_tag and plugin_id in self._by_tag[tag]:
                self._by_tag[tag].remove(plugin_id)
        
        return True
    
    def update_status(self, plugin_id: str, status: PluginStatus, error_message: Optional[str] = None):
        """更新插件状态"""
        if plugin_id not in self._plugins:
            return False
        
        metadata = self._plugins[plugin_id]
        metadata.status = status
        metadata.updated_at = datetime.utcnow()
        if error_message:
            metadata.error_message = error_message
        return True


# 全局注册表实例
_global_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """获取全局注册表"""
    return _global_registry

