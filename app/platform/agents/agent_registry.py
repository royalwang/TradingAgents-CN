"""
智能体注册表
管理所有可用的智能体类型和元数据
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class AgentType(str, Enum):
    """智能体类型"""
    ANALYST = "analyst"  # 分析师
    RESEARCHER = "researcher"  # 研究员
    TRADER = "trader"  # 交易员
    RISK_MANAGER = "risk_manager"  # 风险管理
    MANAGER = "manager"  # 管理者
    CUSTOM = "custom"  # 自定义


class AgentStatus(str, Enum):
    """智能体状态"""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


@dataclass
class AgentMetadata:
    """智能体元数据"""
    id: str
    name: str
    description: str
    version: str
    agent_type: AgentType
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.REGISTERED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    factory_func: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "agent_type": self.agent_type.value,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "capabilities": self.capabilities,
            "requirements": self.requirements,
            "config_schema": self.config_schema,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._by_type: Dict[AgentType, List[str]] = {agent_type: [] for agent_type in AgentType}
        self._by_category: Dict[str, List[str]] = {}
    
    def register(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str,
        agent_type: AgentType,
        author: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        requirements: Optional[Dict[str, Any]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        factory_func: Optional[Callable] = None,
    ) -> AgentMetadata:
        """注册智能体"""
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        metadata = AgentMetadata(
            id=agent_id,
            name=name,
            description=description,
            version=version,
            agent_type=agent_type,
            author=author,
            category=category,
            tags=tags or [],
            capabilities=capabilities or [],
            requirements=requirements or {},
            config_schema=config_schema or {},
            factory_func=factory_func,
        )
        
        self._agents[agent_id] = metadata
        self._by_type[agent_type].append(agent_id)
        
        if category not in self._by_category:
            self._by_category[category] = []
        self._by_category[category].append(agent_id)
        
        return metadata
    
    def get(self, agent_id: str) -> Optional[AgentMetadata]:
        """获取智能体元数据"""
        return self._agents.get(agent_id)
    
    def list(
        self,
        agent_type: Optional[AgentType] = None,
        category: Optional[str] = None,
        status: Optional[AgentStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AgentMetadata]:
        """列出智能体"""
        result = []
        
        # 按类型过滤
        if agent_type:
            agent_ids = self._by_type.get(agent_type, [])
        elif category:
            agent_ids = self._by_category.get(category, [])
        else:
            agent_ids = list(self._agents.keys())
        
        # 应用过滤条件
        for agent_id in agent_ids:
            metadata = self._agents.get(agent_id)
            if not metadata:
                continue
            
            if status and metadata.status != status:
                continue
            
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            result.append(metadata)
        
        return result
    
    def unregister(self, agent_id: str) -> bool:
        """注销智能体"""
        if agent_id not in self._agents:
            return False
        
        metadata = self._agents[agent_id]
        del self._agents[agent_id]
        
        # 从索引中移除
        if agent_id in self._by_type[metadata.agent_type]:
            self._by_type[metadata.agent_type].remove(agent_id)
        
        if metadata.category in self._by_category:
            if agent_id in self._by_category[metadata.category]:
                self._by_category[metadata.category].remove(agent_id)
        
        return True
    
    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """更新智能体状态"""
        if agent_id not in self._agents:
            return False
        
        self._agents[agent_id].status = status
        self._agents[agent_id].updated_at = datetime.utcnow()
        return True
    
    def search(self, query: str) -> List[AgentMetadata]:
        """搜索智能体"""
        query_lower = query.lower()
        result = []
        
        for metadata in self._agents.values():
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                result.append(metadata)
        
        return result


# 全局注册表实例
_global_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """获取全局注册表"""
    return _global_registry

