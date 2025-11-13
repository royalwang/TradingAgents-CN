"""
业务插件定义
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PluginStatus(str, Enum):
    """插件状态"""
    REGISTERED = "registered"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


class PluginCapability(str, Enum):
    """插件能力类型"""
    ANALYSIS = "analysis"  # 分析能力
    TRADING = "trading"  # 交易能力
    SCREENING = "screening"  # 筛选能力
    RESEARCH = "research"  # 研究能力
    PREDICTION = "prediction"  # 预测能力
    CUSTOM = "custom"  # 自定义能力


@dataclass
class AgentConfig:
    """智能体配置"""
    agent_id: str
    agent_type: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfig:
    """工具配置"""
    tool_id: str
    tool_type: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    """工作流配置"""
    workflow_id: str
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataModelConfig:
    """数据模型配置"""
    model_id: str
    model_type: str
    schema: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BusinessPlugin:
    """业务插件"""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    capabilities: List[PluginCapability] = field(default_factory=list)
    
    # 插件配置
    agents: List[AgentConfig] = field(default_factory=list)
    tools: List[ToolConfig] = field(default_factory=list)
    workflows: List[WorkflowConfig] = field(default_factory=list)
    data_models: List[DataModelConfig] = field(default_factory=list)
    
    # 插件元数据
    entry_point: Optional[str] = None  # 插件入口点（模块路径）
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
    
    # 插件状态
    status: PluginStatus = PluginStatus.REGISTERED
    enabled: bool = True
    
    # 插件配置
    plugin_config: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # 插件实例（运行时）
    plugin_instance: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "capabilities": [cap.value for cap in self.capabilities],
            "agents": [agent.__dict__ for agent in self.agents],
            "tools": [tool.__dict__ for tool in self.tools],
            "workflows": [workflow.__dict__ for workflow in self.workflows],
            "data_models": [model.__dict__ for model in self.data_models],
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "icon_url": self.icon_url,
            "documentation_url": self.documentation_url,
            "status": self.status.value,
            "enabled": self.enabled,
            "plugin_config": self.plugin_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessPlugin':
        """从字典创建"""
        # 转换能力列表
        capabilities = [
            PluginCapability(cap) if isinstance(cap, str) else cap
            for cap in data.get("capabilities", [])
        ]
        
        # 转换智能体配置
        agents = [
            AgentConfig(**agent_data) if isinstance(agent_data, dict) else agent_data
            for agent_data in data.get("agents", [])
        ]
        
        # 转换工具配置
        tools = [
            ToolConfig(**tool_data) if isinstance(tool_data, dict) else tool_data
            for tool_data in data.get("tools", [])
        ]
        
        # 转换工作流配置
        workflows = [
            WorkflowConfig(**workflow_data) if isinstance(workflow_data, dict) else workflow_data
            for workflow_data in data.get("workflows", [])
        ]
        
        # 转换数据模型配置
        data_models = [
            DataModelConfig(**model_data) if isinstance(model_data, dict) else model_data
            for model_data in data.get("data_models", [])
        ]
        
        return cls(
            plugin_id=data["plugin_id"],
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            capabilities=capabilities,
            agents=agents,
            tools=tools,
            workflows=workflows,
            data_models=data_models,
            entry_point=data.get("entry_point"),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            icon_url=data.get("icon_url"),
            documentation_url=data.get("documentation_url"),
            status=PluginStatus(data.get("status", "registered")),
            enabled=data.get("enabled", True),
            plugin_config=data.get("plugin_config", {}),
        )

