"""
工作流服务层
提供高级工作流管理功能，包括YAML声明式管理
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import uuid

from .workflow_engine import WorkflowEngine, Workflow, WorkflowNode, WorkflowStatus, get_engine
from .yaml_loader import WorkflowYAMLLoader, WorkflowDefinition
from app.platform.core.declarative_manager import DeclarativeService


class WorkflowService(DeclarativeService[WorkflowDefinition]):
    """工作流服务"""
    
    def __init__(self, engine: Optional[WorkflowEngine] = None):
        loader = WorkflowYAMLLoader()
        super().__init__(loader)
        self.engine = engine or get_engine()
    
    async def _import_items(
        self,
        items: List[WorkflowDefinition],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入工作流"""
        imported = []
        updated = []
        skipped = []
        errors = []
        
        for definition in items:
            try:
                workflow_id = definition.workflow_id
                existing = self.engine.get_workflow(workflow_id)
                
                if existing:
                    if update_existing:
                        # 更新现有工作流
                        # 删除旧工作流
                        self.engine.delete_workflow(workflow_id)
                        # 创建新工作流
                        workflow = self._create_workflow_from_definition(definition)
                        updated.append(workflow_id)
                    else:
                        skipped.append(workflow_id)
                else:
                    # 创建新工作流
                    workflow = self._create_workflow_from_definition(definition)
                    imported.append(workflow_id)
            except Exception as e:
                errors.append({
                    "workflow_id": definition.workflow_id,
                    "error": str(e)
                })
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(items),
        }
    
    def _create_workflow_from_definition(self, definition: WorkflowDefinition) -> Workflow:
        """从定义创建工作流"""
        workflow = self.engine.create_workflow(
            name=definition.name,
            description=definition.description,
            config=definition.config,
        )
        
        # 如果定义中有workflow_id，使用它
        if definition.workflow_id:
            # 需要替换workflow_id
            old_id = workflow.workflow_id
            workflow.workflow_id = definition.workflow_id
            # 更新引擎中的映射
            if old_id in self.engine._workflows:
                self.engine._workflows[definition.workflow_id] = workflow
                if old_id != definition.workflow_id:
                    del self.engine._workflows[old_id]
        
        # 添加节点（注意：handler需要在实际使用时动态加载）
        for node_data in definition.nodes:
            node_id = node_data.get("node_id")
            name = node_data.get("name", node_id)
            node_type = node_data.get("node_type", "custom")
            handler_type = node_data.get("handler_type")
            config = node_data.get("config", {})
            dependencies = node_data.get("dependencies", [])
            
            # 创建占位符handler（实际使用时需要根据handler_type加载）
            def placeholder_handler(state: Dict[str, Any]) -> Dict[str, Any]:
                return state
            
            # 添加节点
            added_node_id = self.engine.add_node(
                workflow_id=workflow.workflow_id,
                name=name,
                node_type=node_type,
                handler=placeholder_handler,
                config=config,
                dependencies=dependencies,
            )
            
            # 如果指定了node_id，更新它
            if node_id and added_node_id != node_id:
                # 更新节点ID
                for node in workflow.nodes:
                    if node.node_id == added_node_id:
                        node.node_id = node_id
                        break
        
        # 添加边
        for edge in definition.edges:
            if isinstance(edge, list) and len(edge) == 2:
                from_id, to_id = edge
            elif isinstance(edge, dict):
                from_id = edge.get("from") or edge.get("from_node")
                to_id = edge.get("to") or edge.get("to_node")
            else:
                continue
            
            self.engine.add_edge(
                workflow_id=workflow.workflow_id,
                from_node_id=from_id,
                to_node_id=to_id,
            )
        
        # 设置状态
        if definition.status:
            workflow.status = WorkflowStatus(definition.status)
        
        return workflow
    
    async def _get_all_items(self, filter_func: Optional[callable] = None) -> List[WorkflowDefinition]:
        """获取所有工作流"""
        workflows = self.engine.list_workflows()
        
        definitions = []
        for workflow in workflows:
            # 转换为定义
            definition = WorkflowDefinition({
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "nodes": [
                    {
                        "node_id": node.node_id,
                        "name": node.name,
                        "node_type": node.node_type,
                        "config": node.config,
                        "dependencies": node.dependencies,
                    }
                    for node in workflow.nodes
                ],
                "edges": workflow.edges,
                "status": workflow.status.value,
                "config": workflow.config,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            })
            
            if filter_func is None or filter_func(definition):
                definitions.append(definition)
        
        return definitions


# 全局服务实例
_global_service: Optional[WorkflowService] = None


def get_service() -> WorkflowService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = WorkflowService()
    return _global_service

