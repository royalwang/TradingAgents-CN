"""
工作流执行器
"""
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from .workflow_engine import WorkflowEngine, Workflow, WorkflowStatus, get_engine


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, engine: Optional[WorkflowEngine] = None):
        self.engine = engine or get_engine()
        self._running_workflows: Dict[str, Any] = {}
    
    async def execute(
        self,
        workflow_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行工作流"""
        workflow = self.engine.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if not workflow.graph:
            raise ValueError(f"Workflow {workflow_id} graph not built")
        
        try:
            workflow.status = WorkflowStatus.RUNNING
            
            # 执行图
            if asyncio.iscoroutinefunction(workflow.graph.ainvoke):
                result = await workflow.graph.ainvoke(
                    initial_state or {},
                    config=config or {},
                )
            else:
                result = workflow.graph.invoke(
                    initial_state or {},
                    config=config or {},
                )
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.updated_at = datetime.utcnow()
            
            return {
                "success": True,
                "result": result,
                "workflow_id": workflow_id,
            }
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.updated_at = datetime.utcnow()
            
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id,
            }
    
    async def cancel(self, workflow_id: str) -> bool:
        """取消工作流"""
        workflow = self.engine.get_workflow(workflow_id)
        if not workflow:
            return False
        
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.updated_at = datetime.utcnow()
            return True
        
        return False


# 全局执行器实例
_global_executor: Optional[WorkflowExecutor] = None


def get_executor() -> WorkflowExecutor:
    """获取全局执行器"""
    global _global_executor
    if _global_executor is None:
        _global_executor = WorkflowExecutor()
    return _global_executor

