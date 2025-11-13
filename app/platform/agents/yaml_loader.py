"""
智能体YAML加载器
从YAML文件加载智能体配置
"""
from typing import List, Dict, Any
from datetime import datetime

from app.platform.core.declarative_manager import DeclarativeYAMLLoader
from .agent_registry import AgentMetadata, AgentType, AgentStatus


class AgentYAMLLoader(DeclarativeYAMLLoader[AgentMetadata]):
    """智能体YAML加载器"""
    
    def __init__(self):
        super().__init__("agents")
    
    def _parse_item(self, data: Dict[str, Any]) -> AgentMetadata:
        """解析单个智能体配置"""
        # 必需字段
        agent_id = data.get("id") or data.get("agent_id")
        if not agent_id:
            raise ValueError("Agent 'id' is required")
        
        name = data.get("name") or agent_id
        description = data.get("description", "")
        version = data.get("version", "1.0.0")
        
        # 解析agent_type
        agent_type_str = data.get("agent_type") or data.get("agentType") or "custom"
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            agent_type = AgentType.CUSTOM
        
        author = data.get("author", "unknown")
        category = data.get("category", "general")
        
        # 可选字段
        metadata = AgentMetadata(
            id=agent_id,
            name=name,
            description=description,
            version=version,
            agent_type=agent_type,
            author=author,
            category=category,
            tags=data.get("tags", []),
            capabilities=data.get("capabilities", []),
            requirements=data.get("requirements", {}),
            config_schema=data.get("config_schema") or data.get("configSchema", {}),
            status=AgentStatus(data.get("status", "registered")),
        )
        
        # 处理时间字段
        if "created_at" in data:
            metadata.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return metadata
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段"""
        return "id" in data or "agent_id" in data
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段"""
        if "id" not in data:
            data["id"] = value


# 示例YAML格式
EXAMPLE_YAML = """
# 智能体配置示例
agents:
  - id: stock_analyst
    name: 股票分析师
    description: 专业的股票分析智能体，能够进行深度分析和研究
    version: 1.0.0
    agent_type: analyst
    author: Platform Team
    category: trading
    tags:
      - stock
      - analysis
      - trading
    capabilities:
      - market_analysis
      - fundamental_analysis
      - technical_analysis
      - report_generation
    requirements:
      - data_source: tushare
      - llm_provider: dashscope
    config_schema:
      analysis_depth:
        type: string
        enum: [标准, 深度, 极深]
        default: 标准
      include_news:
        type: boolean
        default: true
    status: active
  
  - id: risk_manager
    name: 风险管理智能体
    description: 负责风险评估和管理的智能体
    version: 1.0.0
    agent_type: risk_manager
    author: Platform Team
    category: risk
    tags:
      - risk
      - management
    capabilities:
      - risk_assessment
      - position_monitoring
      - alert_generation
    status: active
"""

