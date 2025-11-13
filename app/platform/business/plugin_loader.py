"""
业务插件加载器
从文件系统加载插件配置
"""
from typing import List, Optional
from pathlib import Path
import json
import yaml

from .business_plugin import BusinessPlugin, PluginCapability, PluginStatus
from .plugin_registry import BusinessPluginRegistry, get_registry


class BusinessPluginLoader:
    """业务插件加载器"""
    
    def __init__(self, plugin_dir: str, registry: Optional[BusinessPluginRegistry] = None):
        self.plugin_dir = Path(plugin_dir)
        self.registry = registry or get_registry()
    
    def discover_plugins(self) -> List[BusinessPlugin]:
        """发现插件"""
        plugins = []
        
        if not self.plugin_dir.exists():
            return plugins
        
        # 遍历插件目录
        for plugin_path in self.plugin_dir.iterdir():
            if plugin_path.is_dir():
                plugin = self._load_plugin_from_directory(plugin_path)
                if plugin:
                    plugins.append(plugin)
        
        return plugins
    
    def _load_plugin_from_directory(self, plugin_path: Path) -> Optional[BusinessPlugin]:
        """从目录加载插件"""
        # 查找plugin.json或plugin.yaml
        config_file = None
        for ext in ['.json', '.yaml', '.yml']:
            candidate = plugin_path / f"plugin{ext}"
            if candidate.exists():
                config_file = candidate
                break
        
        if not config_file:
            return None
        
        try:
            # 读取配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            # 确定入口点
            entry_point = data.get("entry_point")
            if not entry_point:
                # 尝试查找main.py
                main_file = plugin_path / "main.py"
                if main_file.exists():
                    entry_point = str(main_file)
                else:
                    entry_point = None
            
            # 转换能力列表
            capabilities = [
                PluginCapability(cap) if isinstance(cap, str) else cap
                for cap in data.get("capabilities", [])
            ]
            
            # 创建插件对象
            plugin = BusinessPlugin(
                plugin_id=data.get("plugin_id", plugin_path.name),
                name=data.get("name", plugin_path.name),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", "unknown"),
                capabilities=capabilities,
                entry_point=entry_point,
                dependencies=data.get("dependencies", []),
                tags=data.get("tags", []),
                icon_url=data.get("icon_url"),
                documentation_url=data.get("documentation_url"),
                enabled=data.get("enabled", True),
                plugin_config=data.get("config", {}),
            )
            
            # 加载智能体配置
            if "agents" in data:
                from .business_plugin import AgentConfig
                plugin.agents = [
                    AgentConfig(**agent_data) if isinstance(agent_data, dict) else agent_data
                    for agent_data in data["agents"]
                ]
            
            # 加载工具配置
            if "tools" in data:
                from .business_plugin import ToolConfig
                plugin.tools = [
                    ToolConfig(**tool_data) if isinstance(tool_data, dict) else tool_data
                    for tool_data in data["tools"]
                ]
            
            # 加载工作流配置
            if "workflows" in data:
                from .business_plugin import WorkflowConfig
                plugin.workflows = [
                    WorkflowConfig(**workflow_data) if isinstance(workflow_data, dict) else workflow_data
                    for workflow_data in data["workflows"]
                ]
            
            # 注册插件
            self.registry.register(plugin)
            
            return plugin
        except Exception as e:
            print(f"Failed to load plugin from {plugin_path}: {e}")
            return None
    
    def load_all(self) -> int:
        """加载所有插件"""
        plugins = self.discover_plugins()
        return len(plugins)


# 全局加载器实例
_global_loader: Optional[BusinessPluginLoader] = None


def get_loader(plugin_dir: Optional[str] = None) -> BusinessPluginLoader:
    """获取全局加载器"""
    global _global_loader
    if _global_loader is None:
        from app.platform.core.platform_config import platform_settings
        plugin_dir = plugin_dir or f"{platform_settings.PLATFORM_DATA_DIR}/business_plugins"
        _global_loader = BusinessPluginLoader(plugin_dir)
    return _global_loader

