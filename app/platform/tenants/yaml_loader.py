"""
租户YAML加载器
从YAML文件加载租户配置
"""
from typing import List, Dict, Any
from datetime import datetime

from app.platform.core.declarative_manager import DeclarativeYAMLLoader
from .tenant_registry import TenantMetadata, TenantStatus, TenantTier


class TenantYAMLLoader(DeclarativeYAMLLoader[TenantMetadata]):
    """租户YAML加载器"""
    
    def __init__(self):
        super().__init__("tenants")
    
    def _parse_item(self, data: Dict[str, Any]) -> TenantMetadata:
        """解析单个租户配置"""
        # 必需字段
        tenant_id = data.get("tenant_id") or data.get("id")
        if not tenant_id:
            raise ValueError("Tenant 'tenant_id' is required")
        
        name = data.get("name") or tenant_id
        display_name = data.get("display_name") or data.get("displayName") or name
        description = data.get("description", "")
        
        # 可选字段
        metadata = TenantMetadata(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            domain=data.get("domain"),
            tier=TenantTier(data.get("tier", "free")),
            status=TenantStatus(data.get("status", "trial")),
            max_users=data.get("max_users", data.get("maxUsers", 10)),
            max_storage_gb=data.get("max_storage_gb", data.get("maxStorageGb", 1)),
            max_api_calls_per_day=data.get("max_api_calls_per_day", data.get("maxApiCallsPerDay", 1000)),
            features=data.get("features", []),
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            owner_id=data.get("owner_id") or data.get("ownerId"),
        )
        
        # 处理时间字段
        if "created_at" in data:
            metadata.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        if "expires_at" in data:
            metadata.expires_at = datetime.fromisoformat(data["expires_at"])
        
        return metadata
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段"""
        return "tenant_id" in data or "id" in data
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段"""
        if "tenant_id" not in data:
            data["tenant_id"] = value


# 示例YAML格式
EXAMPLE_YAML = """
# 租户配置示例
tenants:
  - tenant_id: company_a
    name: company_a
    display_name: 公司A
    description: 公司A的租户实例
    domain: company-a.tradingagents.cn
    tier: professional
    status: active
    max_users: 50
    max_storage_gb: 100
    max_api_calls_per_day: 10000
    features:
      - trading
      - rental_management
      - analytics
    config:
      theme: "dark"
      language: "zh-CN"
    metadata:
      industry: "金融"
      region: "中国"
    owner_id: "user_001"
    expires_at: "2026-12-31T23:59:59Z"
  
  - tenant_id: company_b
    name: company_b
    display_name: 公司B
    description: 公司B的租户实例
    tier: basic
    status: active
    max_users: 20
    max_storage_gb: 10
    max_api_calls_per_day: 5000
    features:
      - trading
    owner_id: "user_002"
"""

