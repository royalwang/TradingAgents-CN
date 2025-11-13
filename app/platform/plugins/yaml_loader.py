"""
插件YAML加载器
从YAML文件加载插件配置
"""
from typing import List, Dict, Any
from datetime import datetime

from app.platform.core.declarative_manager import DeclarativeYAMLLoader
from .plugin_registry import PluginMetadata, PluginStatus


class PluginYAMLLoader(DeclarativeYAMLLoader[PluginMetadata]):
    """插件YAML加载器"""
    
    def __init__(self):
        super().__init__("plugins")
    
    def _parse_item(self, data: Dict[str, Any]) -> PluginMetadata:
        """解析单个插件配置"""
        # 必需字段
        plugin_id = data.get("plugin_id") or data.get("id")
        if not plugin_id:
            raise ValueError("Plugin 'plugin_id' is required")
        
        name = data.get("name") or plugin_id
        version = data.get("version", "1.0.0")
        description = data.get("description", "")
        author = data.get("author", "unknown")
        entry_point = data.get("entry_point") or data.get("entryPoint")
        if not entry_point:
            raise ValueError("Plugin 'entry_point' is required")
        
        # 可选字段
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name=name,
            version=version,
            description=description,
            author=author,
            entry_point=entry_point,
            config_schema=data.get("config_schema") or data.get("configSchema", {}),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            status=PluginStatus(data.get("status", "registered")),
            plugin_path=data.get("plugin_path") or data.get("pluginPath"),
        )
        
        # 处理时间字段
        if "created_at" in data:
            metadata.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "error_message" in data:
            metadata.error_message = data["error_message"]
        
        return metadata
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段"""
        return "plugin_id" in data or "id" in data
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段"""
        if "plugin_id" not in data:
            data["plugin_id"] = value


# 示例YAML格式
EXAMPLE_YAML = """
# 插件配置示例
plugins:
  - plugin_id: data_processor
    name: 数据处理器
    version: 1.0.0
    description: 处理各种数据格式的插件
    author: Platform Team
    entry_point: app.plugins.data_processor.main
    config_schema:
      batch_size:
        type: integer
        default: 100
      timeout:
        type: integer
        default: 300
    dependencies:
      - pandas
      - numpy
    tags:
      - data
      - processing
    status: registered
  
  - plugin_id: notification_sender
    name: 通知发送器
    version: 1.0.0
    description: 发送各种通知的插件
    author: Platform Team
    entry_point: app.plugins.notification.main
    config_schema:
      channels:
        type: array
        items:
          type: string
        default: [email]
    tags:
      - notification
      - communication
    status: active
"""

