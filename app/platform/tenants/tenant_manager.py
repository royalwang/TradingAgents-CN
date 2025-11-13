"""
租户管理器
管理租户的数据隔离、资源限制和访问控制
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from .tenant_registry import TenantRegistry, TenantMetadata, TenantStatus, TenantTier, get_registry
from app.core.database import get_mongo_db


class TenantManager:
    """租户管理器"""
    
    def __init__(self, registry: Optional[TenantRegistry] = None):
        self.registry = registry or get_registry()
        self.db = get_mongo_db()
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantMetadata]:
        """获取租户信息"""
        return self.registry.get(tenant_id)
    
    def get_tenant_by_domain(self, domain: str) -> Optional[TenantMetadata]:
        """通过域名获取租户"""
        return self.registry.get_by_domain(domain)
    
    async def check_tenant_access(self, tenant_id: str) -> bool:
        """检查租户访问权限"""
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return False
        
        # 检查状态
        if tenant.status not in [TenantStatus.ACTIVE, TenantStatus.TRIAL]:
            return False
        
        # 检查过期时间
        if tenant.expires_at and tenant.expires_at < datetime.utcnow():
            self.registry.update_status(tenant_id, TenantStatus.EXPIRED)
            return False
        
        return True
    
    async def check_user_limit(self, tenant_id: str, current_user_count: int) -> bool:
        """检查用户数量限制"""
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return False
        
        return current_user_count < tenant.max_users
    
    async def check_storage_limit(self, tenant_id: str, current_storage_gb: float) -> bool:
        """检查存储空间限制"""
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return False
        
        return current_storage_gb < tenant.max_storage_gb
    
    async def check_api_quota(self, tenant_id: str, today_api_calls: int) -> bool:
        """检查API调用配额"""
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return False
        
        return today_api_calls < tenant.max_api_calls_per_day
    
    def has_feature(self, tenant_id: str, feature: str) -> bool:
        """检查租户是否启用特定功能"""
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return False
        
        return feature in tenant.features
    
    def get_tenant_collection_name(self, tenant_id: str, base_collection: str) -> str:
        """获取租户特定的集合名称"""
        # 方案1: 前缀方式
        return f"tenant_{tenant_id}_{base_collection}"
        
        # 方案2: 使用租户ID作为数据库名（可选）
        # return base_collection  # 在租户特定的数据库中
    
    async def get_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """获取租户数据（自动添加租户过滤）"""
        # 确保查询包含租户ID
        query["tenant_id"] = tenant_id
        
        collection_name = self.get_tenant_collection_name(tenant_id, collection)
        coll = self.db[collection_name]
        
        cursor = coll.find(query, projection)
        results = await cursor.to_list(length=None)
        
        # 转换ObjectId为字符串
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        
        return results
    
    async def create_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        data: Dict[str, Any],
    ) -> str:
        """创建租户数据（自动添加租户ID）"""
        # 确保数据包含租户ID
        data["tenant_id"] = tenant_id
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        
        collection_name = self.get_tenant_collection_name(tenant_id, collection)
        coll = self.db[collection_name]
        
        result = await coll.insert_one(data)
        return str(result.inserted_id)
    
    async def update_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
    ) -> int:
        """更新租户数据（自动添加租户过滤）"""
        # 确保查询包含租户ID
        query["tenant_id"] = tenant_id
        
        # 添加更新时间
        if "$set" not in update:
            update["$set"] = {}
        update["$set"]["updated_at"] = datetime.utcnow()
        
        collection_name = self.get_tenant_collection_name(tenant_id, collection)
        coll = self.db[collection_name]
        
        result = await coll.update_many(query, update)
        return result.modified_count
    
    async def delete_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        query: Dict[str, Any],
    ) -> int:
        """删除租户数据（自动添加租户过滤）"""
        # 确保查询包含租户ID
        query["tenant_id"] = tenant_id
        
        collection_name = self.get_tenant_collection_name(tenant_id, collection)
        coll = self.db[collection_name]
        
        result = await coll.delete_many(query)
        return result.deleted_count
    
    async def get_tenant_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息"""
        tenant = self.registry.get(tenant_id)
        if not tenant:
            return {}
        
        # 统计用户数量
        users_collection = self.get_tenant_collection_name(tenant_id, "users")
        users_count = await self.db[users_collection].count_documents({"tenant_id": tenant_id})
        
        # 统计存储使用（示例）
        # 这里需要根据实际存储计算
        
        # 统计今日API调用（示例）
        # 这里需要从使用统计中获取
        
        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "tier": tenant.tier.value,
            "status": tenant.status.value,
            "current_users": users_count,
            "max_users": tenant.max_users,
            "user_usage_percent": (users_count / tenant.max_users * 100) if tenant.max_users > 0 else 0,
            "features": tenant.features,
        }


# 全局管理器实例
_global_manager: Optional[TenantManager] = None


def get_manager() -> TenantManager:
    """获取全局管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = TenantManager()
    return _global_manager

