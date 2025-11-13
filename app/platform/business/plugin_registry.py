"""
业务插件注册表
"""
from typing import Dict, List, Optional
from datetime import datetime
from .business_plugin import BusinessPlugin, PluginStatus, PluginCapability


class BusinessPluginRegistry:
    """业务插件注册表"""
    
    def __init__(self):
        self._plugins: Dict[str, BusinessPlugin] = {}
        self._by_capability: Dict[PluginCapability, List[str]] = {
            cap: [] for cap in PluginCapability
        }
        self._by_tag: Dict[str, List[str]] = {}
    
    def register(self, plugin: BusinessPlugin) -> BusinessPlugin:
        """注册插件"""
        if plugin.plugin_id in self._plugins:
            raise ValueError(f"Plugin {plugin.plugin_id} already registered")
        
        self._plugins[plugin.plugin_id] = plugin
        
        # 按能力索引
        for capability in plugin.capabilities:
            self._by_capability[capability].append(plugin.plugin_id)
        
        # 按标签索引
        for tag in plugin.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(plugin.plugin_id)
        
        return plugin
    
    def get(self, plugin_id: str) -> Optional[BusinessPlugin]:
        """获取插件"""
        return self._plugins.get(plugin_id)
    
    def list(
        self,
        capability: Optional[PluginCapability] = None,
        status: Optional[PluginStatus] = None,
        enabled: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> List[BusinessPlugin]:
        """列出插件"""
        result = []
        
        # 按能力过滤
        if capability:
            plugin_ids = self._by_capability.get(capability, [])
        elif tags:
            # 按标签过滤
            plugin_ids = set()
            for tag in tags:
                if tag in self._by_tag:
                    plugin_ids.update(self._by_tag[tag])
            plugin_ids = list(plugin_ids)
        else:
            plugin_ids = list(self._plugins.keys())
        
        # 应用过滤条件
        for plugin_id in plugin_ids:
            plugin = self._plugins.get(plugin_id)
            if not plugin:
                continue
            
            if status and plugin.status != status:
                continue
            
            if enabled is not None and plugin.enabled != enabled:
                continue
            
            result.append(plugin)
        
        return result
    
    def unregister(self, plugin_id: str) -> bool:
        """注销插件"""
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        del self._plugins[plugin_id]
        
        # 从索引中移除
        for capability in plugin.capabilities:
            if plugin_id in self._by_capability[capability]:
                self._by_capability[capability].remove(plugin_id)
        
        for tag in plugin.tags:
            if tag in self._by_tag and plugin_id in self._by_tag[tag]:
                self._by_tag[tag].remove(plugin_id)
        
        return True
    
    def update_status(self, plugin_id: str, status: PluginStatus):
        """更新插件状态"""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].status = status
            self._plugins[plugin_id].updated_at = datetime.utcnow()
            return True
        return False
    
    def search(self, query: str) -> List[BusinessPlugin]:
        """搜索插件"""
        query_lower = query.lower()
        result = []
        
        for plugin in self._plugins.values():
            if (query_lower in plugin.name.lower() or
                query_lower in plugin.description.lower() or
                any(query_lower in tag.lower() for tag in plugin.tags)):
                result.append(plugin)
        
        return result


# 全局注册表实例
_global_registry = BusinessPluginRegistry()


def get_registry() -> BusinessPluginRegistry:
    """获取全局注册表"""
    return _global_registry

