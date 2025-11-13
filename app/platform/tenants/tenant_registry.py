"""
租户注册表
管理租户元数据和配置
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class TenantTier(str, Enum):
    """租户等级"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class TenantMetadata:
    """租户元数据"""
    tenant_id: str
    name: str
    display_name: str
    description: str
    domain: Optional[str] = None  # 租户域名（如：company1.tradingagents.cn）
    tier: TenantTier = TenantTier.FREE
    status: TenantStatus = TenantStatus.TRIAL
    max_users: int = 10
    max_storage_gb: int = 1
    max_api_calls_per_day: int = 1000
    features: List[str] = field(default_factory=list)  # 启用的功能模块
    config: Dict[str, any] = field(default_factory=dict)  # 租户特定配置
    metadata: Dict[str, any] = field(default_factory=dict)  # 扩展元数据
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    owner_id: Optional[str] = None  # 租户所有者用户ID
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典"""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "domain": self.domain,
            "tier": self.tier.value,
            "status": self.status.value,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "max_api_calls_per_day": self.max_api_calls_per_day,
            "features": self.features,
            "config": self.config,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "owner_id": self.owner_id,
        }


class TenantRegistry:
    """租户注册表"""
    
    def __init__(self):
        self._tenants: Dict[str, TenantMetadata] = {}
        self._by_status: Dict[TenantStatus, List[str]] = {
            status: [] for status in TenantStatus
        }
        self._by_tier: Dict[TenantTier, List[str]] = {
            tier: [] for tier in TenantTier
        }
        self._by_domain: Dict[str, str] = {}  # domain -> tenant_id
    
    def register(self, metadata: TenantMetadata) -> TenantMetadata:
        """注册租户"""
        if metadata.tenant_id in self._tenants:
            raise ValueError(f"Tenant {metadata.tenant_id} already registered")
        
        # 检查域名唯一性
        if metadata.domain:
            if metadata.domain in self._by_domain:
                raise ValueError(f"Domain {metadata.domain} already registered")
            self._by_domain[metadata.domain] = metadata.tenant_id
        
        metadata.updated_at = datetime.utcnow()
        self._tenants[metadata.tenant_id] = metadata
        self._by_status[metadata.status].append(metadata.tenant_id)
        self._by_tier[metadata.tier].append(metadata.tenant_id)
        
        return metadata
    
    def get(self, tenant_id: str) -> Optional[TenantMetadata]:
        """获取租户元数据"""
        return self._tenants.get(tenant_id)
    
    def get_by_domain(self, domain: str) -> Optional[TenantMetadata]:
        """通过域名获取租户"""
        tenant_id = self._by_domain.get(domain)
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None
    
    def list(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        features: Optional[List[str]] = None,
    ) -> List[TenantMetadata]:
        """列出租户"""
        result = []
        
        # 按状态过滤
        if status:
            tenant_ids = self._by_status.get(status, [])
        elif tier:
            tenant_ids = self._by_tier.get(tier, [])
        else:
            tenant_ids = list(self._tenants.keys())
        
        # 应用过滤条件
        for tenant_id in tenant_ids:
            metadata = self._tenants.get(tenant_id)
            if not metadata:
                continue
            
            if status and metadata.status != status:
                continue
            
            if tier and metadata.tier != tier:
                continue
            
            if features and not any(feature in metadata.features for feature in features):
                continue
            
            result.append(metadata)
        
        return result
    
    def unregister(self, tenant_id: str) -> bool:
        """注销租户"""
        if tenant_id not in self._tenants:
            return False
        
        metadata = self._tenants[tenant_id]
        del self._tenants[tenant_id]
        
        # 从索引中移除
        if tenant_id in self._by_status[metadata.status]:
            self._by_status[metadata.status].remove(tenant_id)
        
        if tenant_id in self._by_tier[metadata.tier]:
            self._by_tier[metadata.tier].remove(tenant_id)
        
        if metadata.domain and metadata.domain in self._by_domain:
            del self._by_domain[metadata.domain]
        
        return True
    
    def update_status(self, tenant_id: str, status: TenantStatus) -> bool:
        """更新租户状态"""
        if tenant_id not in self._tenants:
            return False
        
        metadata = self._tenants[tenant_id]
        old_status = metadata.status
        metadata.status = status
        metadata.updated_at = datetime.utcnow()
        
        # 更新索引
        if tenant_id in self._by_status[old_status]:
            self._by_status[old_status].remove(tenant_id)
        self._by_status[status].append(tenant_id)
        
        return True
    
    def search(self, query: str) -> List[TenantMetadata]:
        """搜索租户"""
        query_lower = query.lower()
        result = []
        
        for metadata in self._tenants.values():
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.display_name.lower() or
                query_lower in metadata.description.lower()):
                result.append(metadata)
        
        return result


# 全局注册表实例
_global_registry: Optional[TenantRegistry] = None


def get_registry() -> TenantRegistry:
    """获取全局注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = TenantRegistry()
    return _global_registry

