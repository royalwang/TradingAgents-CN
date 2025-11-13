"""
插件管理器
管理插件的加载、运行和生命周期
"""
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import importlib
import importlib.util
import sys
from pathlib import Path

from .plugin_registry import PluginRegistry, PluginMetadata, PluginStatus, get_registry


class InstanceStatus(str, Enum):
    """实例状态"""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class PluginInstance:
    """插件实例"""
    instance_id: str
    plugin_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    status: InstanceStatus = InstanceStatus.LOADED
    plugin_obj: Optional[Any] = None
    metadata: Optional[PluginMetadata] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class PluginManager:
    """插件管理器"""
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or get_registry()
        self._instances: Dict[str, PluginInstance] = {}
    
    async def load_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> PluginInstance:
        """加载插件"""
        metadata = self.registry.get(plugin_id)
        if not metadata:
            raise ValueError(f"Plugin {plugin_id} not found")
        
        # 检查依赖
        for dep in metadata.dependencies:
            dep_metadata = self.registry.get(dep)
            if not dep_metadata or dep_metadata.status != PluginStatus.ACTIVE:
                raise ValueError(f"Plugin {plugin_id} depends on {dep} which is not available")
        
        # 加载插件模块
        try:
            plugin_obj = self._load_plugin_module(metadata)
            
            instance = PluginInstance(
                instance_id=f"{plugin_id}_{datetime.utcnow().timestamp()}",
                plugin_id=plugin_id,
                config=config or {},
                plugin_obj=plugin_obj,
                metadata=metadata,
                status=InstanceStatus.LOADED,
            )
            
            self._instances[instance.instance_id] = instance
            
            # 更新注册表状态
            self.registry.update_status(plugin_id, PluginStatus.LOADED)
            
            return instance
        except Exception as e:
            self.registry.update_status(
                plugin_id,
                PluginStatus.ERROR,
                error_message=str(e),
            )
            raise
    
    def _load_plugin_module(self, metadata: PluginMetadata) -> Any:
        """加载插件模块"""
        entry_point = metadata.entry_point
        
        # 如果是文件路径
        if Path(entry_point).exists():
            spec = importlib.util.spec_from_file_location(
                metadata.plugin_id,
                entry_point,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            # 如果是模块路径
            module = importlib.import_module(entry_point)
        
        # 尝试获取插件类或函数
        if hasattr(module, 'Plugin'):
            return module.Plugin()
        elif hasattr(module, 'plugin'):
            return module.plugin
        elif hasattr(module, 'create_plugin'):
            return module.create_plugin()
        else:
            return module
    
    async def activate_plugin(self, instance_id: str) -> bool:
        """激活插件"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        try:
            if instance.plugin_obj and hasattr(instance.plugin_obj, 'activate'):
                await instance.plugin_obj.activate(instance.config)
            
            instance.status = InstanceStatus.ACTIVE
            self.registry.update_status(instance.plugin_id, PluginStatus.ACTIVE)
            return True
        except Exception as e:
            instance.status = InstanceStatus.ERROR
            instance.error_message = str(e)
            return False
    
    async def deactivate_plugin(self, instance_id: str) -> bool:
        """停用插件"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        try:
            if instance.plugin_obj and hasattr(instance.plugin_obj, 'deactivate'):
                await instance.plugin_obj.deactivate()
            
            instance.status = InstanceStatus.INACTIVE
            self.registry.update_status(instance.plugin_id, PluginStatus.INACTIVE)
            return True
        except Exception as e:
            instance.status = InstanceStatus.ERROR
            instance.error_message = str(e)
            return False
    
    def get_instance(self, instance_id: str) -> Optional[PluginInstance]:
        """获取插件实例"""
        return self._instances.get(instance_id)
    
    def list_instances(
        self,
        plugin_id: Optional[str] = None,
        status: Optional[InstanceStatus] = None,
    ) -> List[PluginInstance]:
        """列出插件实例"""
        result = []
        
        for instance in self._instances.values():
            if plugin_id and instance.plugin_id != plugin_id:
                continue
            if status and instance.status != status:
                continue
            result.append(instance)
        
        return result


# 全局管理器实例
_global_manager: Optional[PluginManager] = None


def get_manager() -> PluginManager:
    """获取全局管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = PluginManager()
    return _global_manager

