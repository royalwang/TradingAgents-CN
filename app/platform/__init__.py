"""
智能体平台核心模块
新一代模块化智能体平台，支持Agents、知识库、文档解析、MCP工具、插件、工作流编排、声明式数据、LLM Provider管理等
所有模块都支持YAML声明式管理
"""

from . import data, providers, business, data_sources, agents, workflow, plugins

__version__ = "2.0.0"
__all__ = [
    "data",
    "providers",
    "business",
    "data_sources",
    "agents",
    "workflow",
    "plugins",
]

