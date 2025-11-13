"""
业务插件管理器
管理插件的加载、激活和运行
"""
from typing import Dict, Any, List, Optional
import importlib
import importlib.util
from pathlib import Path

from .business_plugin import BusinessPlugin, PluginStatus, PluginCapability
from .plugin_registry import BusinessPluginRegistry, get_registry


class BusinessPluginManager:
    """业务插件管理器"""
    
    def __init__(self, registry: Optional[BusinessPluginRegistry] = None):
        self.registry = registry or get_registry()
        self._loaded_plugins: Dict[str, Any] = {}
    
    async def load_plugin(self, plugin_id: str) -> BusinessPlugin:
        """加载插件"""
        plugin = self.registry.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")
        
        # 检查依赖
        for dep_id in plugin.dependencies:
            dep_plugin = self.registry.get(dep_id)
            if not dep_plugin or dep_plugin.status != PluginStatus.ACTIVE:
                raise ValueError(f"Plugin {plugin_id} depends on {dep_id} which is not available")
        
        # 加载插件模块
        if plugin.entry_point:
            try:
                plugin_instance = self._load_plugin_module(plugin)
                plugin.plugin_instance = plugin_instance
                plugin.status = PluginStatus.LOADED
                self._loaded_plugins[plugin_id] = plugin_instance
            except Exception as e:
                plugin.status = PluginStatus.ERROR
                raise ValueError(f"Failed to load plugin {plugin_id}: {str(e)}")
        else:
            plugin.status = PluginStatus.LOADED
        
        return plugin
    
    def _load_plugin_module(self, plugin: BusinessPlugin) -> Any:
        """加载插件模块"""
        entry_point = plugin.entry_point
        
        # 如果是文件路径
        if Path(entry_point).exists():
            spec = importlib.util.spec_from_file_location(
                plugin.plugin_id,
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
    
    async def activate_plugin(self, plugin_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """激活插件"""
        plugin = self.registry.get(plugin_id)
        if not plugin:
            return False
        
        if plugin.status == PluginStatus.ACTIVE:
            return True
        
        try:
            # 确保插件已加载
            if plugin.status != PluginStatus.LOADED:
                await self.load_plugin(plugin_id)
            
            # 激活插件实例
            if plugin.plugin_instance and hasattr(plugin.plugin_instance, 'activate'):
                await plugin.plugin_instance.activate(config or plugin.plugin_config)
            
            plugin.status = PluginStatus.ACTIVE
            plugin.enabled = True
            return True
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            return False
    
    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """停用插件"""
        plugin = self.registry.get(plugin_id)
        if not plugin:
            return False
        
        try:
            if plugin.plugin_instance and hasattr(plugin.plugin_instance, 'deactivate'):
                await plugin.plugin_instance.deactivate()
            
            plugin.status = PluginStatus.INACTIVE
            plugin.enabled = False
            return True
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            return False
    
    async def execute_capability(
        self,
        capability: 'PluginCapability',
        input_data: Dict[str, Any],
        plugin_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行插件能力"""
        # 查找支持该能力的插件
        if plugin_id:
            plugin = self.registry.get(plugin_id)
            if not plugin or capability not in plugin.capabilities:
                raise ValueError(f"Plugin {plugin_id} does not support capability {capability}")
            plugins = [plugin]
        else:
            plugins = self.registry.list(
                capability=capability,
                status=PluginStatus.ACTIVE,
                enabled=True,
            )
        
        if not plugins:
            raise ValueError(f"No active plugin found for capability {capability}")
        
        # 使用第一个可用的插件
        plugin = plugins[0]
        
        # 执行插件能力
        if plugin.plugin_instance and hasattr(plugin.plugin_instance, 'execute'):
            return await plugin.plugin_instance.execute(capability, input_data)
        else:
            raise ValueError(f"Plugin {plugin.plugin_id} does not have execute method")
    
    def get_plugin(self, plugin_id: str) -> Optional[BusinessPlugin]:
        """获取插件"""
        return self.registry.get(plugin_id)
    
    def list_plugins(
        self,
        capability: Optional['PluginCapability'] = None,
        status: Optional[PluginStatus] = None,
        enabled: Optional[bool] = None,
    ) -> List[BusinessPlugin]:
        """列出插件"""
        return self.registry.list(capability=capability, status=status, enabled=enabled)


# 全局管理器实例
_global_manager: Optional[BusinessPluginManager] = None


def get_manager() -> BusinessPluginManager:
    """获取全局管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = BusinessPluginManager()
    return _global_manager

