"""
Supabase 数据迁移工具
从 MongoDB 迁移平台数据到 Supabase
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from app.core.database import get_platform_db, get_mongo_db
from app.platform.supabase.supabase_access import get_supabase_access
import logging

logger = logging.getLogger(__name__)


class SupabaseMigration:
    """Supabase 数据迁移工具"""
    
    def __init__(self):
        self.mongo_db = get_mongo_db()
        self.supabase = get_supabase_access()
        self.stats = {
            "users": {"migrated": 0, "errors": 0},
            "tenants": {"migrated": 0, "errors": 0},
            "configs": {"migrated": 0, "errors": 0},
            "billing": {"migrated": 0, "errors": 0},
        }
    
    def _convert_objectid_to_uuid(self, object_id: Any) -> str:
        """将 MongoDB ObjectId 转换为 UUID"""
        if isinstance(object_id, str):
            # 尝试解析为 UUID
            try:
                return str(uuid.UUID(object_id))
            except ValueError:
                # 如果不是有效的 UUID，生成新的
                return str(uuid.uuid4())
        # 如果是 ObjectId，生成新的 UUID
        return str(uuid.uuid4())
    
    def _convert_datetime(self, dt: Any) -> Optional[str]:
        """转换 datetime 为 ISO 格式字符串"""
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt.isoformat()
        if isinstance(dt, str):
            return dt
        return None
    
    async def migrate_users(self, batch_size: int = 100) -> Dict[str, int]:
        """迁移用户数据"""
        logger.info("开始迁移用户数据...")
        
        collection = self.mongo_db["users"]
        total = await collection.count_documents({})
        logger.info(f"找到 {total} 个用户")
        
        offset = 0
        while offset < total:
            users = await collection.find({}).skip(offset).limit(batch_size).to_list(length=batch_size)
            
            for user in users:
                try:
                    # 转换数据格式
                    supabase_user = {
                        "id": self._convert_objectid_to_uuid(user.get("_id")),
                        "username": user.get("username"),
                        "email": user.get("email"),
                        "hashed_password": user.get("hashed_password"),
                        "tenant_id": user.get("tenant_id"),
                        "is_active": user.get("is_active", True),
                        "is_verified": user.get("is_verified", False),
                        "is_admin": user.get("is_admin", False),
                        "is_tenant_admin": user.get("is_tenant_admin", False),
                        "preferences": user.get("preferences", {}),
                        "daily_quota": user.get("daily_quota", 1000),
                        "concurrent_limit": user.get("concurrent_limit", 3),
                        "total_analyses": user.get("total_analyses", 0),
                        "successful_analyses": user.get("successful_analyses", 0),
                        "failed_analyses": user.get("failed_analyses", 0),
                        "created_at": self._convert_datetime(user.get("created_at")),
                        "updated_at": self._convert_datetime(user.get("updated_at")),
                        "last_login": self._convert_datetime(user.get("last_login")),
                    }
                    
                    # 插入 Supabase
                    await self.supabase.create_user(supabase_user)
                    self.stats["users"]["migrated"] += 1
                    
                except Exception as e:
                    logger.error(f"迁移用户失败 {user.get('username')}: {e}")
                    self.stats["users"]["errors"] += 1
            
            offset += batch_size
            logger.info(f"已迁移 {offset}/{total} 个用户")
        
        logger.info(f"用户迁移完成: {self.stats['users']}")
        return self.stats["users"]
    
    async def migrate_tenants(self) -> Dict[str, int]:
        """迁移租户数据"""
        logger.info("开始迁移租户数据...")
        
        from app.platform.tenants import get_registry
        
        registry = get_registry()
        tenants = registry.list()
        logger.info(f"找到 {len(tenants)} 个租户")
        
        for tenant in tenants:
            try:
                # 转换数据格式
                supabase_tenant = {
                    "tenant_id": tenant.tenant_id,
                    "name": tenant.name,
                    "display_name": tenant.display_name,
                    "description": tenant.description,
                    "domain": tenant.domain,
                    "tier": tenant.tier.value,
                    "status": tenant.status.value,
                    "max_users": tenant.max_users,
                    "max_storage_gb": tenant.max_storage_gb,
                    "max_api_calls_per_day": tenant.max_api_calls_per_day,
                    "features": tenant.features,
                    "config": tenant.config,
                    "metadata": tenant.metadata,
                    "owner_id": tenant.owner_id,
                    "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                    "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None,
                    "expires_at": tenant.expires_at.isoformat() if tenant.expires_at else None,
                }
                
                # 插入 Supabase
                await self.supabase.create_tenant(supabase_tenant)
                self.stats["tenants"]["migrated"] += 1
                
            except Exception as e:
                logger.error(f"迁移租户失败 {tenant.tenant_id}: {e}")
                self.stats["tenants"]["errors"] += 1
        
        logger.info(f"租户迁移完成: {self.stats['tenants']}")
        return self.stats["tenants"]
    
    async def migrate_configs(self) -> Dict[str, int]:
        """迁移平台配置数据"""
        logger.info("开始迁移平台配置数据...")
        
        collection = self.mongo_db["system_configs"]
        configs = await collection.find({}).to_list(length=None)
        logger.info(f"找到 {len(configs)} 个配置")
        
        for config in configs:
            try:
                supabase_config = {
                    "config_name": config.get("config_name"),
                    "config_type": config.get("config_type", "system"),
                    "config_data": config.get("config_data", {}),
                    "description": config.get("description"),
                    "created_at": self._convert_datetime(config.get("created_at")),
                    "updated_at": self._convert_datetime(config.get("updated_at")),
                }
                
                await self.supabase.set_platform_config(
                    config.get("config_name"),
                    supabase_config
                )
                self.stats["configs"]["migrated"] += 1
                
            except Exception as e:
                logger.error(f"迁移配置失败 {config.get('config_name')}: {e}")
                self.stats["configs"]["errors"] += 1
        
        logger.info(f"配置迁移完成: {self.stats['configs']}")
        return self.stats["configs"]
    
    async def migrate_all(self) -> Dict[str, Any]:
        """迁移所有平台数据"""
        logger.info("开始完整迁移...")
        
        results = {
            "users": await self.migrate_users(),
            "tenants": await self.migrate_tenants(),
            "configs": await self.migrate_configs(),
        }
        
        total_migrated = sum(r["migrated"] for r in results.values())
        total_errors = sum(r["errors"] for r in results.values())
        
        logger.info(f"迁移完成: 总计 {total_migrated} 条记录，{total_errors} 个错误")
        
        return {
            "results": results,
            "total_migrated": total_migrated,
            "total_errors": total_errors,
        }


# 全局迁移实例
_global_migration: Optional[SupabaseMigration] = None


def get_migration() -> SupabaseMigration:
    """获取全局迁移实例"""
    global _global_migration
    if _global_migration is None:
        _global_migration = SupabaseMigration()
    return _global_migration

