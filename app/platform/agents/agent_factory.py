"""
智能体工厂
用于创建和配置智能体实例
"""
from typing import Dict, Any, Optional, Callable
from .agent_registry import AgentRegistry, AgentMetadata, get_registry
from .agent_manager import AgentManager, AgentInstance, get_manager


class AgentFactory:
    """智能体工厂"""
    
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        manager: Optional[AgentManager] = None,
    ):
        self.registry = registry or get_registry()
        self.manager = manager or get_manager()
    
    async def create_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        auto_start: bool = True,
    ) -> AgentInstance:
        """创建智能体实例"""
        instance = await self.manager.create_instance(
            agent_id=agent_id,
            name=name,
            config=config or {},
        )
        
        if auto_start:
            await self.manager.start_instance(instance.instance_id)
        
        return instance
    
    def validate_config(
        self,
        agent_id: str,
        config: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """验证配置"""
        metadata = self.registry.get(agent_id)
        if not metadata:
            return False, f"Agent {agent_id} not found"
        
        # 检查必需字段
        if metadata.config_schema:
            required_fields = metadata.config_schema.get("required", [])
            for field in required_fields:
                if field not in config:
                    return False, f"Missing required field: {field}"
        
        return True, None
    
    def get_default_config(self, agent_id: str) -> Dict[str, Any]:
        """获取默认配置"""
        metadata = self.registry.get(agent_id)
        if not metadata:
            return {}
        
        config_schema = metadata.config_schema
        if not config_schema:
            return {}
        
        # 从schema中提取默认值
        default_config = {}
        properties = config_schema.get("properties", {})
        for key, prop in properties.items():
            if "default" in prop:
                default_config[key] = prop["default"]
        
        return default_config


# 全局工厂实例
_global_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    """获取全局工厂"""
    global _global_factory
    if _global_factory is None:
        _global_factory = AgentFactory()
    return _global_factory

