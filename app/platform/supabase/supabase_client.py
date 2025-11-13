"""
Supabase 客户端管理
"""
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 全局 Supabase 客户端实例
_global_supabase_client: Optional[Client] = None


class SupabaseClient:
    """Supabase 客户端封装"""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or settings.SUPABASE_URL
        self.key = key or settings.SUPABASE_KEY
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and Key are required")
        
        self.client = create_client(self.url, self.key)
        logger.info("✅ Supabase 客户端初始化成功")
    
    def get_client(self) -> Client:
        """获取 Supabase 客户端"""
        return self.client
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试执行一个简单查询
            result = self.client.table("_health").select("1").limit(1).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase 健康检查失败: {e}")
            # 如果 _health 表不存在，尝试其他方式
            try:
                # 尝试访问 auth 服务
                self.client.auth.get_session()
                return True
            except Exception:
                return False


def get_supabase_client() -> SupabaseClient:
    """获取全局 Supabase 客户端"""
    global _global_supabase_client
    
    if _global_supabase_client is None:
        _global_supabase_client = SupabaseClient()
    
    return _global_supabase_client

