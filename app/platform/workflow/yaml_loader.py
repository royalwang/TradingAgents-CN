"""
工作流YAML加载器
从YAML文件加载工作流配置
"""
from typing import List, Dict, Any
from datetime import datetime

from app.platform.core.declarative_manager import DeclarativeYAMLLoader
from .workflow_engine import Workflow, WorkflowNode, WorkflowStatus


class WorkflowDefinition:
    """工作流定义（用于YAML序列化）"""
    
    def __init__(self, data: Dict[str, Any]):
        self.workflow_id = data.get("workflow_id") or data.get("id")
        self.name = data.get("name")
        self.description = data.get("description", "")
        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])
        self.status = data.get("status", "created")
        self.config = data.get("config", {})
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": self.nodes,
            "edges": self.edges,
            "status": self.status,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WorkflowYAMLLoader(DeclarativeYAMLLoader[WorkflowDefinition]):
    """工作流YAML加载器"""
    
    def __init__(self):
        super().__init__("workflows")
    
    def _parse_item(self, data: Dict[str, Any]) -> WorkflowDefinition:
        """解析单个工作流配置"""
        return WorkflowDefinition(data)
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段"""
        return "workflow_id" in data or "id" in data
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段"""
        if "workflow_id" not in data:
            data["workflow_id"] = value


# 示例YAML格式
EXAMPLE_YAML = """
# 工作流配置示例
workflows:
  - workflow_id: stock_analysis_workflow
    name: 股票分析工作流
    description: 完整的股票分析流程，包括数据获取、分析和报告生成
    status: created
    config:
      timeout: 3600
      retry_count: 3
    nodes:
      - node_id: fetch_data
        name: 获取数据
        node_type: data_source
        handler_type: tushare_adapter
        config:
          symbol: ${symbol}
          start_date: ${start_date}
        dependencies: []
      
      - node_id: analyze
        name: 分析数据
        node_type: agent
        handler_type: stock_analyst
        config:
          analysis_type: comprehensive
        dependencies:
          - fetch_data
      
      - node_id: generate_report
        name: 生成报告
        node_type: agent
        handler_type: report_generator
        config:
          format: markdown
        dependencies:
          - analyze
    
    edges:
      - [fetch_data, analyze]
      - [analyze, generate_report]
  
  - workflow_id: risk_assessment_workflow
    name: 风险评估工作流
    description: 评估投资组合的风险
    status: created
    nodes:
      - node_id: collect_positions
        name: 收集持仓
        node_type: data_source
        dependencies: []
      
      - node_id: calculate_risk
        name: 计算风险
        node_type: agent
        handler_type: risk_manager
        dependencies:
          - collect_positions
"""

