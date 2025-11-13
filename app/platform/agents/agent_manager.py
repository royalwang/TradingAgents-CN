"""
智能体管理器
管理智能体实例的生命周期
"""
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid

from .agent_registry import AgentRegistry, AgentMetadata, AgentStatus, get_registry


class InstanceStatus(str, Enum):
    """实例状态"""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentInstance:
    """智能体实例"""
    instance_id: str
    agent_id: str
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    status: InstanceStatus = InstanceStatus.CREATED
    metadata: Optional[AgentMetadata] = None
    agent_obj: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "instance_id": self.instance_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "config": self.config,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "error_message": self.error_message,
            "metrics": self.metrics,
        }


class AgentManager:
    """智能体管理器"""
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or get_registry()
        self._instances: Dict[str, AgentInstance] = {}
        self._heartbeat_interval = 30  # 30秒
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def create_instance(
        self,
        agent_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AgentInstance:
        """创建智能体实例"""
        # 获取智能体元数据
        metadata = self.registry.get(agent_id)
        if not metadata:
            raise ValueError(f"Agent {agent_id} not found in registry")
        
        if metadata.status != AgentStatus.ACTIVE:
            raise ValueError(f"Agent {agent_id} is not active")
        
        # 创建实例
        instance_id = str(uuid.uuid4())
        instance = AgentInstance(
            instance_id=instance_id,
            agent_id=agent_id,
            name=name or f"{metadata.name}_{instance_id[:8]}",
            config=config or {},
            metadata=metadata,
            status=InstanceStatus.CREATED,
        )
        
        self._instances[instance_id] = instance
        
        # 初始化实例
        try:
            await self._initialize_instance(instance)
        except Exception as e:
            instance.status = InstanceStatus.ERROR
            instance.error_message = str(e)
            raise
        
        return instance
    
    async def _initialize_instance(self, instance: AgentInstance):
        """初始化智能体实例"""
        instance.status = InstanceStatus.INITIALIZING
        
        # 如果有工厂函数，使用它创建智能体对象
        if instance.metadata and instance.metadata.factory_func:
            try:
                # 调用工厂函数创建智能体
                agent_obj = instance.metadata.factory_func(instance.config)
                instance.agent_obj = agent_obj
                instance.status = InstanceStatus.RUNNING
            except Exception as e:
                instance.status = InstanceStatus.ERROR
                instance.error_message = f"Failed to create agent: {str(e)}"
                raise
        else:
            # 如果没有工厂函数，标记为运行状态
            instance.status = InstanceStatus.RUNNING
    
    async def start_instance(self, instance_id: str) -> bool:
        """启动智能体实例"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        if instance.status == InstanceStatus.RUNNING:
            return True
        
        try:
            instance.status = InstanceStatus.INITIALIZING
            await self._initialize_instance(instance)
            return True
        except Exception as e:
            instance.status = InstanceStatus.ERROR
            instance.error_message = str(e)
            return False
    
    async def stop_instance(self, instance_id: str) -> bool:
        """停止智能体实例"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        instance.status = InstanceStatus.STOPPED
        
        # 清理资源
        if instance.agent_obj and hasattr(instance.agent_obj, 'cleanup'):
            try:
                await instance.agent_obj.cleanup()
            except Exception:
                pass
        
        return True
    
    async def delete_instance(self, instance_id: str) -> bool:
        """删除智能体实例"""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        # 先停止实例
        await self.stop_instance(instance_id)
        
        # 从字典中移除
        del self._instances[instance_id]
        return True
    
    def get_instance(self, instance_id: str) -> Optional[AgentInstance]:
        """获取智能体实例"""
        return self._instances.get(instance_id)
    
    def list_instances(
        self,
        agent_id: Optional[str] = None,
        status: Optional[InstanceStatus] = None,
    ) -> List[AgentInstance]:
        """列出智能体实例"""
        result = []
        
        for instance in self._instances.values():
            if agent_id and instance.agent_id != agent_id:
                continue
            if status and instance.status != status:
                continue
            result.append(instance)
        
        return result
    
    async def update_heartbeat(self, instance_id: str):
        """更新心跳"""
        instance = self._instances.get(instance_id)
        if instance:
            instance.last_heartbeat = datetime.utcnow()
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                # 检查所有运行中的实例
                for instance in self._instances.values():
                    if instance.status == InstanceStatus.RUNNING:
                        await self.update_heartbeat(instance.instance_id)
                        
                        # 检查是否超时（5分钟无心跳）
                        timeout = (datetime.utcnow() - instance.last_heartbeat).total_seconds()
                        if timeout > 300:
                            instance.status = InstanceStatus.ERROR
                            instance.error_message = "Heartbeat timeout"
            except Exception as e:
                # 记录错误但继续运行
                print(f"Heartbeat loop error: {e}")
    
    def start_heartbeat_monitoring(self):
        """启动心跳监控"""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    def stop_heartbeat_monitoring(self):
        """停止心跳监控"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()


# 全局管理器实例
_global_manager: Optional[AgentManager] = None


def get_manager() -> AgentManager:
    """获取全局管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = AgentManager()
        _global_manager.start_heartbeat_monitoring()
    return _global_manager

