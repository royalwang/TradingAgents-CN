"""
Supabase 数据访问层
提供平台数据的 Supabase 访问接口
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.platform.supabase.supabase_client import get_supabase_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseDataAccess:
    """Supabase 数据访问层"""
    
    def __init__(self):
        self.client = get_supabase_client().get_client()
        self.use_supabase = settings.USE_SUPABASE_FOR_PLATFORM
    
    def _ensure_supabase_enabled(self):
        """确保 Supabase 已启用"""
        if not self.use_supabase:
            raise RuntimeError("Supabase is not enabled. Set USE_SUPABASE_FOR_PLATFORM=true")
    
    # ==================== 用户数据访问 ====================
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            raise
    
    async def get_user_async(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_user, user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            result = self.client.table("users").select("*").eq("username", username).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            raise
    
    async def get_user_by_username_async(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_user_by_username, username)
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            user_data["created_at"] = datetime.utcnow().isoformat()
            user_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("users").insert(user_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    async def create_user_async(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_user, user_data)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            user_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("users").update(user_data).eq("id", user_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            raise
    
    async def update_user_async(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_user, user_id, user_data)
    
    # ==================== 租户数据访问 ====================
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户信息（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            result = self.client.table("tenants").select("*").eq("tenant_id", tenant_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"获取租户失败: {e}")
            raise
    
    async def get_tenant_async(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户信息（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_tenant, tenant_id)
    
    def list_tenants(
        self,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出租户（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            query = self.client.table("tenants").select("*")
            
            if status:
                query = query.eq("status", status)
            if tier:
                query = query.eq("tier", tier)
            
            result = query.limit(limit).offset(offset).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"列出租户失败: {e}")
            raise
    
    async def list_tenants_async(
        self,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出租户（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.list_tenants, status, tier, limit, offset)
    
    def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建租户（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            tenant_data["created_at"] = datetime.utcnow().isoformat()
            tenant_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("tenants").insert(tenant_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"创建租户失败: {e}")
            raise
    
    async def create_tenant_async(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建租户（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_tenant, tenant_data)
    
    def update_tenant(self, tenant_id: str, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新租户（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            tenant_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("tenants").update(tenant_data).eq("tenant_id", tenant_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"更新租户失败: {e}")
            raise
    
    async def update_tenant_async(self, tenant_id: str, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新租户（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_tenant, tenant_id, tenant_data)
    
    # ==================== 配置数据访问 ====================
    
    def get_platform_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取平台配置（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            result = self.client.table("platform_configs").select("*").eq("config_name", config_name).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"获取平台配置失败: {e}")
            raise
    
    async def get_platform_config_async(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取平台配置（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_platform_config, config_name)
    
    def set_platform_config(self, config_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """设置平台配置（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            config_data["config_name"] = config_name
            config_data["updated_at"] = datetime.utcnow().isoformat()
            
            # 使用 upsert（如果存在则更新，不存在则插入）
            result = self.client.table("platform_configs").upsert(config_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"设置平台配置失败: {e}")
            raise
    
    async def set_platform_config_async(self, config_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """设置平台配置（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.set_platform_config, config_name, config_data)
    
    # ==================== 计费数据访问 ====================
    
    def get_billing_plan(self, tier: str) -> Optional[Dict[str, Any]]:
        """获取计费方案（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            result = self.client.table("billing_plans").select("*").eq("tier", tier).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"获取计费方案失败: {e}")
            raise
    
    async def get_billing_plan_async(self, tier: str) -> Optional[Dict[str, Any]]:
        """获取计费方案（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_billing_plan, tier)
    
    def create_billing_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建计费记录（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            record_data["created_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("billing_records").insert(record_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"创建计费记录失败: {e}")
            raise
    
    async def create_billing_record_async(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建计费记录（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_billing_record, record_data)
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建发票（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            invoice_data["issue_date"] = datetime.utcnow().isoformat()
            
            result = self.client.table("invoices").insert(invoice_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"创建发票失败: {e}")
            raise
    
    async def create_invoice_async(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建发票（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create_invoice, invoice_data)
    
    # ==================== 通用查询方法 ====================
    
    def query(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """通用查询方法（同步方法）"""
        self._ensure_supabase_enabled()
        try:
            query = self.client.table(table).select("*")
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict):
                        # 支持操作符：{"$eq": value}, {"$gt": value}, etc.
                        for op, op_value in value.items():
                            if op == "$eq":
                                query = query.eq(key, op_value)
                            elif op == "$gt":
                                query = query.gt(key, op_value)
                            elif op == "$gte":
                                query = query.gte(key, op_value)
                            elif op == "$lt":
                                query = query.lt(key, op_value)
                            elif op == "$lte":
                                query = query.lte(key, op_value)
                            elif op == "$neq":
                                query = query.neq(key, op_value)
                            elif op == "$in":
                                query = query.in_(key, op_value)
                    else:
                        query = query.eq(key, value)
            
            if order_by:
                # 支持 "field:asc" 或 "field:desc"
                parts = order_by.split(":")
                field = parts[0]
                direction = parts[1] if len(parts) > 1 else "asc"
                query = query.order(field, desc=(direction == "desc"))
            
            result = query.limit(limit).offset(offset).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"查询失败: {e}")
            raise
    
    async def query_async(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """通用查询方法（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, table, filters, order_by, limit, offset)


# 全局数据访问实例
_global_supabase_access: Optional[SupabaseDataAccess] = None


def get_supabase_access() -> SupabaseDataAccess:
    """获取全局 Supabase 数据访问实例"""
    global _global_supabase_access
    if _global_supabase_access is None:
        _global_supabase_access = SupabaseDataAccess()
    return _global_supabase_access

