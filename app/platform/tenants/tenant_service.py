"""
租户服务层
提供高级租户管理功能，包括YAML声明式管理
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from .tenant_registry import TenantRegistry, TenantMetadata, get_registry
from .tenant_manager import TenantManager, get_manager
from .yaml_loader import TenantYAMLLoader
from app.platform.core.declarative_manager import DeclarativeService


class TenantService(DeclarativeService[TenantMetadata]):
    """租户服务"""
    
    def __init__(
        self,
        registry: Optional[TenantRegistry] = None,
        manager: Optional[TenantManager] = None,
    ):
        loader = TenantYAMLLoader()
        super().__init__(loader)
        self.registry = registry or get_registry()
        self.manager = manager or get_manager()
    
    async def _import_items(
        self,
        items: List[TenantMetadata],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入租户配置"""
        imported = []
        updated = []
        skipped = []
        errors = []
        
        for metadata in items:
            try:
                existing = self.registry.get(metadata.tenant_id)
                
                if existing:
                    if update_existing:
                        # 更新现有租户
                        self.registry.unregister(metadata.tenant_id)
                        self.registry.register(metadata)
                        # 恢复状态
                        if metadata.status != existing.status:
                            self.registry.update_status(metadata.tenant_id, metadata.status)
                        updated.append(metadata.tenant_id)
                    else:
                        skipped.append(metadata.tenant_id)
                else:
                    # 注册新租户
                    self.registry.register(metadata)
                    imported.append(metadata.tenant_id)
            except Exception as e:
                errors.append({
                    "tenant_id": metadata.tenant_id,
                    "error": str(e)
                })
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(items),
        }
    
    async def _get_all_items(self, filter_func: Optional[Any] = None) -> List[TenantMetadata]:
        """获取所有租户"""
        tenants = self.registry.list()
        
        if filter_func:
            tenants = [tenant for tenant in tenants if filter_func(tenant)]
        
        return tenants


# 全局服务实例
_global_service: Optional[TenantService] = None


def get_service() -> TenantService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = TenantService()
    return _global_service

