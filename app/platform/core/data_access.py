"""
统一数据访问层
提供平台数据和业务数据的统一访问接口
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.database import get_platform_db, get_business_db


class DataAccessLayer:
    """统一数据访问层"""
    
    def __init__(self):
        self.platform_db = get_platform_db()
        self.business_db = get_business_db()
    
    def get_platform_collection(self, collection_name: str):
        """获取平台数据集合"""
        return self.platform_db[collection_name]
    
    def get_tenant_collection(self, tenant_id: str, collection_name: str):
        """获取租户业务数据集合"""
        full_name = f"tenant_{tenant_id}_{collection_name}"
        return self.business_db[full_name]
    
    async def create_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        data: Dict[str, Any]
    ) -> str:
        """创建租户业务数据"""
        coll = self.get_tenant_collection(tenant_id, collection)
        data["tenant_id"] = tenant_id
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        result = await coll.insert_one(data)
        return str(result.inserted_id)
    
    async def get_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
    ) -> list:
        """获取租户业务数据"""
        coll = self.get_tenant_collection(tenant_id, collection)
        query = query or {}
        query["tenant_id"] = tenant_id  # 确保租户隔离
        
        cursor = coll.find(query, projection)
        results = await cursor.to_list(length=None)
        
        # 转换ObjectId为字符串
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        
        return results
    
    async def update_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
    ) -> int:
        """更新租户业务数据"""
        coll = self.get_tenant_collection(tenant_id, collection)
        query["tenant_id"] = tenant_id  # 确保租户隔离
        
        # 添加更新时间
        if "$set" not in update:
            update["$set"] = {}
        update["$set"]["updated_at"] = datetime.utcnow()
        
        result = await coll.update_many(query, update)
        return result.modified_count
    
    async def delete_tenant_data(
        self,
        tenant_id: str,
        collection: str,
        query: Dict[str, Any],
    ) -> int:
        """删除租户业务数据"""
        coll = self.get_tenant_collection(tenant_id, collection)
        query["tenant_id"] = tenant_id  # 确保租户隔离
        
        result = await coll.delete_many(query)
        return result.deleted_count


# 全局数据访问层实例
_global_data_access: Optional[DataAccessLayer] = None


def get_data_access() -> DataAccessLayer:
    """获取全局数据访问层实例"""
    global _global_data_access
    if _global_data_access is None:
        _global_data_access = DataAccessLayer()
    return _global_data_access

