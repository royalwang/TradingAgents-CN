"""
Supabase 平台数据存储模块
实现平台数据到 Supabase 的迁移和访问
"""

from .supabase_client import SupabaseClient, get_supabase_client
from .supabase_access import SupabaseDataAccess, get_supabase_access
from .migration import SupabaseMigration, get_migration
from .platform_data_adapter import PlatformDataAdapter, get_platform_data_adapter

__all__ = [
    "SupabaseClient",
    "get_supabase_client",
    "SupabaseDataAccess",
    "get_supabase_access",
    "SupabaseMigration",
    "get_migration",
    "PlatformDataAdapter",
    "get_platform_data_adapter",
]

