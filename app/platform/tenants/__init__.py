"""
多租户管理模块
支持平台的多租户架构，实现数据隔离和权限管理
"""

from .tenant_registry import TenantRegistry, TenantMetadata, TenantStatus, TenantTier, get_registry
from .tenant_manager import TenantManager, get_manager
from .tenant_service import TenantService, get_service
from .yaml_loader import TenantYAMLLoader
from .tenant_middleware import TenantMiddleware, TenantContext, get_tenant_context, get_tenant_id, require_tenant

__all__ = [
    "TenantRegistry",
    "TenantMetadata",
    "TenantStatus",
    "TenantTier",
    "get_registry",
    "TenantManager",
    "get_manager",
    "TenantService",
    "get_service",
    "TenantYAMLLoader",
    "TenantMiddleware",
    "TenantContext",
    "get_tenant_context",
    "get_tenant_id",
    "require_tenant",
]

