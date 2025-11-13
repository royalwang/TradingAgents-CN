"""
智能体服务层
提供高级智能体管理功能，包括YAML声明式管理
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .agent_registry import AgentRegistry, AgentMetadata, AgentStatus, get_registry
from .yaml_loader import AgentYAMLLoader
from app.platform.core.declarative_manager import DeclarativeService


class AgentService(DeclarativeService[AgentMetadata]):
    """智能体服务"""
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        loader = AgentYAMLLoader()
        super().__init__(loader)
        self.registry = registry or get_registry()
    
    async def _import_items(
        self,
        items: List[AgentMetadata],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入智能体"""
        imported = []
        updated = []
        skipped = []
        errors = []
        
        for metadata in items:
            try:
                existing = self.registry.get(metadata.id)
                
                if existing:
                    if update_existing:
                        # 更新现有智能体
                        # 注意：AgentRegistry没有直接的update方法，需要先注销再注册
                        self.registry.unregister(metadata.id)
                        self.registry.register(
                            agent_id=metadata.id,
                            name=metadata.name,
                            description=metadata.description,
                            version=metadata.version,
                            agent_type=metadata.agent_type,
                            author=metadata.author,
                            category=metadata.category,
                            tags=metadata.tags,
                            capabilities=metadata.capabilities,
                            requirements=metadata.requirements,
                            config_schema=metadata.config_schema,
                            factory_func=metadata.factory_func,
                        )
                        # 恢复状态
                        if metadata.status != AgentStatus.REGISTERED:
                            self.registry.update_status(metadata.id, metadata.status)
                        updated.append(metadata.id)
                    else:
                        skipped.append(metadata.id)
                else:
                    # 注册新智能体
                    self.registry.register(
                        agent_id=metadata.id,
                        name=metadata.name,
                        description=metadata.description,
                        version=metadata.version,
                        agent_type=metadata.agent_type,
                        author=metadata.author,
                        category=metadata.category,
                        tags=metadata.tags,
                        capabilities=metadata.capabilities,
                        requirements=metadata.requirements,
                        config_schema=metadata.config_schema,
                        factory_func=metadata.factory_func,
                    )
                    # 设置状态
                    if metadata.status != AgentStatus.REGISTERED:
                        self.registry.update_status(metadata.id, metadata.status)
                    imported.append(metadata.id)
            except Exception as e:
                errors.append({
                    "id": metadata.id,
                    "error": str(e)
                })
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(items),
        }
    
    async def _get_all_items(self, filter_func: Optional[callable] = None) -> List[AgentMetadata]:
        """获取所有智能体"""
        agents = self.registry.list()
        
        if filter_func:
            agents = [agent for agent in agents if filter_func(agent)]
        
        return agents


# 全局服务实例
_global_service: Optional[AgentService] = None


def get_service() -> AgentService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = AgentService()
    return _global_service

