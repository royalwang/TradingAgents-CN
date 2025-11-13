"""
业务插件模块
将业务能力抽象为插件，平台通过集成业务插件获得业务能力
"""

from .business_plugin import BusinessPlugin, PluginCapability, PluginStatus
from .plugin_registry import BusinessPluginRegistry
from .plugin_manager import BusinessPluginManager
from .plugin_loader import BusinessPluginLoader

__all__ = [
    "BusinessPlugin",
    "PluginCapability",
    "PluginStatus",
    "BusinessPluginRegistry",
    "BusinessPluginManager",
    "BusinessPluginLoader",
]

