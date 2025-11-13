"""
工作流构建器
提供便捷的工作流构建接口
"""
from typing import Dict, Any, Optional, Callable, List
from .workflow_engine import WorkflowEngine, Workflow, WorkflowNode, get_engine


class WorkflowBuilder:
    """工作流构建器"""
    
    def __init__(self, engine: Optional[WorkflowEngine] = None):
        self.engine = engine or get_engine()
        self._current_workflow: Optional[Workflow] = None
    
    def create(
        self,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowBuilder':
        """创建新工作流"""
        self._current_workflow = self.engine.create_workflow(
            name=name,
            description=description,
            config=config,
        )
        return self
    
    def add_node(
        self,
        name: str,
        handler: Callable,
        node_type: str = "function",
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> 'WorkflowBuilder':
        """添加节点"""
        if not self._current_workflow:
            raise ValueError("No workflow created. Call create() first.")
        
        self.engine.add_node(
            workflow_id=self._current_workflow.workflow_id,
            name=name,
            node_type=node_type,
            handler=handler,
            config=config,
            dependencies=dependencies,
        )
        return self
    
    def connect(
        self,
        from_node_name: str,
        to_node_name: str,
    ) -> 'WorkflowBuilder':
        """连接节点"""
        if not self._current_workflow:
            raise ValueError("No workflow created. Call create() first.")
        
        # 查找节点ID
        from_node = self._find_node_by_name(from_node_name)
        to_node = self._find_node_by_name(to_node_name)
        
        if not from_node or not to_node:
            raise ValueError("Node not found")
        
        self.engine.add_edge(
            workflow_id=self._current_workflow.workflow_id,
            from_node_id=from_node.node_id,
            to_node_id=to_node.node_id,
        )
        return self
    
    def _find_node_by_name(self, name: str) -> Optional[WorkflowNode]:
        """按名称查找节点"""
        if not self._current_workflow:
            return None
        
        for node in self._current_workflow.nodes:
            if node.name == name:
                return node
        return None
    
    def build(self) -> Workflow:
        """构建工作流"""
        if not self._current_workflow:
            raise ValueError("No workflow created. Call create() first.")
        
        # 构建图
        self.engine.build_graph(self._current_workflow.workflow_id)
        
        workflow = self._current_workflow
        self._current_workflow = None
        
        return workflow

