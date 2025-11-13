"""
工作流引擎
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGRAPH_AVAILABLE = True
except ImportError:
    LANGRAPH_AVAILABLE = False


class WorkflowStatus(str, Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    name: str
    node_type: str
    handler: Callable
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Workflow:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[tuple[str, str]] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    config: Dict[str, Any] = field(default_factory=dict)
    graph: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._checkpointer = MemorySaver() if LANGRAPH_AVAILABLE else None
    
    def create_workflow(
        self,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            config=config or {},
        )
        
        self._workflows[workflow_id] = workflow
        return workflow
    
    def add_node(
        self,
        workflow_id: str,
        name: str,
        node_type: str,
        handler: Callable,
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """添加节点"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        node_id = f"{workflow_id}_{name}_{len(workflow.nodes)}"
        
        node = WorkflowNode(
            node_id=node_id,
            name=name,
            node_type=node_type,
            handler=handler,
            config=config or {},
            dependencies=dependencies or [],
        )
        
        workflow.nodes.append(node)
        workflow.updated_at = datetime.utcnow()
        
        return node_id
    
    def add_edge(
        self,
        workflow_id: str,
        from_node_id: str,
        to_node_id: str,
    ):
        """添加边"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # 验证节点存在
        node_ids = [node.node_id for node in workflow.nodes]
        if from_node_id not in node_ids or to_node_id not in node_ids:
            raise ValueError("Node not found")
        
        workflow.edges.append((from_node_id, to_node_id))
        workflow.updated_at = datetime.utcnow()
    
    def build_graph(self, workflow_id: str) -> bool:
        """构建图"""
        if not LANGRAPH_AVAILABLE:
            return False
        
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False
        
        try:
            # 创建状态图
            graph = StateGraph(dict)
            
            # 添加节点
            for node in workflow.nodes:
                graph.add_node(node.node_id, node.handler)
            
            # 添加边
            for from_id, to_id in workflow.edges:
                graph.add_edge(from_id, to_id)
            
            # 设置入口点（第一个节点）
            if workflow.nodes:
                graph.set_entry_point(workflow.nodes[0].node_id)
            
            # 编译图
            workflow.graph = graph.compile(checkpointer=self._checkpointer)
            workflow.updated_at = datetime.utcnow()
            
            return True
        except Exception as e:
            print(f"Failed to build graph: {e}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Workflow]:
        """列出工作流"""
        return list(self._workflows.values())
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False


# 全局引擎实例
_global_engine: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """获取全局引擎"""
    global _global_engine
    if _global_engine is None:
        _global_engine = WorkflowEngine()
    return _global_engine

