"""
插件系统模块
提供插件的注册、加载、管理等功能
"""

from .plugin_registry import PluginRegistry, PluginMetadata, PluginStatus
from .plugin_manager import PluginManager, PluginInstance
from .plugin_loader import PluginLoader

__all__ = [
    "PluginRegistry",
    "PluginMetadata",
    "PluginStatus",
    "PluginManager",
    "PluginInstance",
    "PluginLoader",
]

