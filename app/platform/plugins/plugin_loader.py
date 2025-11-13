"""
插件加载器
从文件系统加载插件
"""
from typing import List, Optional
from pathlib import Path
import json
import importlib.util

from .plugin_registry import PluginRegistry, PluginMetadata, get_registry


class PluginLoader:
    """插件加载器"""
    
    def __init__(self, plugin_dir: str, registry: Optional[PluginRegistry] = None):
        self.plugin_dir = Path(plugin_dir)
        self.registry = registry or get_registry()
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """发现插件"""
        plugins = []
        
        if not self.plugin_dir.exists():
            return plugins
        
        # 遍历插件目录
        for plugin_path in self.plugin_dir.iterdir():
            if plugin_path.is_dir():
                metadata = self._load_plugin_metadata(plugin_path)
                if metadata:
                    plugins.append(metadata)
        
        return plugins
    
    def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """加载插件元数据"""
        # 查找plugin.json或plugin.yaml
        metadata_file = plugin_path / "plugin.json"
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 确定入口点
            entry_point = data.get("entry_point")
            if not entry_point:
                # 尝试查找main.py
                main_file = plugin_path / "main.py"
                if main_file.exists():
                    entry_point = str(main_file)
                else:
                    return None
            
            metadata = self.registry.register(
                plugin_id=data.get("id", plugin_path.name),
                name=data.get("name", plugin_path.name),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", "unknown"),
                entry_point=entry_point,
                config_schema=data.get("config_schema", {}),
                dependencies=data.get("dependencies", []),
                tags=data.get("tags", []),
                plugin_path=str(plugin_path),
            )
            
            return metadata
        except Exception as e:
            print(f"Failed to load plugin metadata from {plugin_path}: {e}")
            return None
    
    def load_all(self) -> int:
        """加载所有插件"""
        plugins = self.discover_plugins()
        return len(plugins)


# 全局加载器实例
_global_loader: Optional[PluginLoader] = None


def get_loader(plugin_dir: Optional[str] = None) -> PluginLoader:
    """获取全局加载器"""
    global _global_loader
    if _global_loader is None:
        from app.platform.core.platform_config import platform_settings
        plugin_dir = plugin_dir or platform_settings.PLUGIN_DIR
        _global_loader = PluginLoader(plugin_dir)
    return _global_loader

