"""
平台数据适配器
提供统一的平台数据访问接口，支持 MongoDB 和 Supabase 切换
"""
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.database import get_platform_db
from app.platform.supabase.supabase_access import get_supabase_access
import logging

logger = logging.getLogger(__name__)


class PlatformDataAdapter:
    """平台数据适配器 - 统一访问接口"""
    
    def __init__(self):
        self.use_supabase = settings.USE_SUPABASE_FOR_PLATFORM
        if self.use_supabase:
            self.supabase = get_supabase_access()
            logger.info("✅ 使用 Supabase 存储平台数据")
        else:
            self.mongo_db = get_platform_db()
            logger.info("✅ 使用 MongoDB 存储平台数据")
    
    # ==================== 用户数据访问 ====================
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        if self.use_supabase:
            return await self.supabase.get_user_async(user_id)
        else:
            from bson import ObjectId
            try:
                user_doc = await self.mongo_db["users"].find_one({"_id": ObjectId(user_id)})
                if user_doc:
                    user_doc["_id"] = str(user_doc["_id"])
                return user_doc
            except:
                return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        if self.use_supabase:
            return await self.supabase.get_user_by_username_async(username)
        else:
            user_doc = await self.mongo_db["users"].find_one({"username": username})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
            return user_doc
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        if self.use_supabase:
            return await self.supabase.create_user_async(user_data)
        else:
            from datetime import datetime
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            result = await self.mongo_db["users"].insert_one(user_data)
            user_data["_id"] = str(result.inserted_id)
            return user_data
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户"""
        if self.use_supabase:
            return await self.supabase.update_user_async(user_id, user_data)
        else:
            from bson import ObjectId
            from datetime import datetime
            user_data["updated_at"] = datetime.utcnow()
            await self.mongo_db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": user_data}
            )
            return await self.get_user(user_id)
    
    # ==================== 租户数据访问 ====================
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户信息"""
        if self.use_supabase:
            return await self.supabase.get_tenant_async(tenant_id)
        else:
            # 从租户注册表获取
            from app.platform.tenants import get_registry
            registry = get_registry()
            tenant = registry.get(tenant_id)
            if tenant:
                return tenant.to_dict()
            return None
    
    async def list_tenants(
        self,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出租户"""
        if self.use_supabase:
            return await self.supabase.list_tenants_async(status, tier, limit, offset)
        else:
            from app.platform.tenants import get_registry, TenantStatus, TenantTier
            registry = get_registry()
            tenant_status = TenantStatus(status) if status else None
            tenant_tier = TenantTier(tier) if tier else None
            tenants = registry.list(status=tenant_status, tier=tenant_tier)
            return [tenant.to_dict() for tenant in tenants[offset:offset+limit]]
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建租户"""
        if self.use_supabase:
            return await self.supabase.create_tenant_async(tenant_data)
        else:
            from app.platform.tenants import get_registry, TenantMetadata, TenantStatus, TenantTier
            registry = get_registry()
            tenant = TenantMetadata(
                tenant_id=tenant_data["tenant_id"],
                name=tenant_data["name"],
                display_name=tenant_data["display_name"],
                description=tenant_data.get("description", ""),
                tier=TenantTier(tenant_data.get("tier", "free")),
                status=TenantStatus(tenant_data.get("status", "trial")),
                max_users=tenant_data.get("max_users", 10),
                max_storage_gb=tenant_data.get("max_storage_gb", 1),
                max_api_calls_per_day=tenant_data.get("max_api_calls_per_day", 1000),
                features=tenant_data.get("features", []),
                config=tenant_data.get("config", {}),
                metadata=tenant_data.get("metadata", {}),
                owner_id=tenant_data.get("owner_id"),
            )
            registry.register(tenant)
            return tenant.to_dict()
    
    async def update_tenant(self, tenant_id: str, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新租户"""
        if self.use_supabase:
            return await self.supabase.update_tenant_async(tenant_id, tenant_data)
        else:
            from app.platform.tenants import get_registry
            registry = get_registry()
            tenant = registry.get(tenant_id)
            if tenant:
                # 更新租户元数据
                for key, value in tenant_data.items():
                    if hasattr(tenant, key):
                        setattr(tenant, key, value)
                return tenant.to_dict()
            return None
    
    # ==================== 配置数据访问 ====================
    
    async def get_platform_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取平台配置"""
        if self.use_supabase:
            return await self.supabase.get_platform_config_async(config_name)
        else:
            config_doc = await self.mongo_db["system_configs"].find_one({"config_name": config_name})
            if config_doc:
                config_doc["_id"] = str(config_doc["_id"])
            return config_doc
    
    async def set_platform_config(self, config_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """设置平台配置"""
        if self.use_supabase:
            return await self.supabase.set_platform_config_async(config_name, config_data)
        else:
            from datetime import datetime
            config_data["config_name"] = config_name
            config_data["updated_at"] = datetime.utcnow()
            await self.mongo_db["system_configs"].update_one(
                {"config_name": config_name},
                {"$set": config_data},
                upsert=True
            )
            return await self.get_platform_config(config_name)
    
    # ==================== 计费数据访问 ====================
    
    async def get_billing_plan(self, tier: str) -> Optional[Dict[str, Any]]:
        """获取计费方案"""
        if self.use_supabase:
            return await self.supabase.get_billing_plan_async(tier)
        else:
            from app.platform.billing import get_billing_service
            billing_service = get_billing_service()
            from app.platform.billing.billing_models import BillingTier
            plan = billing_service.get_billing_plan(BillingTier(tier))
            return plan.model_dump() if plan else None
    
    async def create_billing_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建计费记录"""
        if self.use_supabase:
            return await self.supabase.create_billing_record_async(record_data)
        else:
            from app.core.database import get_platform_db
            from datetime import datetime
            platform_db = get_platform_db()
            record_data["created_at"] = datetime.utcnow()
            result = await platform_db["billing_records"].insert_one(record_data)
            record_data["_id"] = str(result.inserted_id)
            return record_data
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建发票"""
        if self.use_supabase:
            return await self.supabase.create_invoice_async(invoice_data)
        else:
            from app.core.database import get_platform_db
            from datetime import datetime
            platform_db = get_platform_db()
            invoice_data["issue_date"] = datetime.utcnow()
            result = await platform_db["invoices"].insert_one(invoice_data)
            invoice_data["_id"] = str(result.inserted_id)
            return invoice_data


# 全局适配器实例
_global_adapter: Optional[PlatformDataAdapter] = None


def get_platform_data_adapter() -> PlatformDataAdapter:
    """获取全局平台数据适配器实例"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = PlatformDataAdapter()
    return _global_adapter

