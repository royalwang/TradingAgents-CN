"""
租户中间件
处理请求中的租户上下文和权限验证
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, Header
from starlette.middleware.base import BaseHTTPMiddleware

from .tenant_manager import TenantManager, get_manager
from .tenant_registry import TenantStatus


class TenantContext:
    """租户上下文"""
    def __init__(self, tenant_id: str, tenant_metadata: Optional[any] = None):
        self.tenant_id = tenant_id
        self.tenant_metadata = tenant_metadata


class TenantMiddleware(BaseHTTPMiddleware):
    """租户中间件"""
    
    def __init__(self, app, tenant_manager: Optional[TenantManager] = None):
        super().__init__(app)
        self.tenant_manager = tenant_manager or get_manager()
    
    async def dispatch(self, request: Request, call_next: Callable):
        """处理请求，提取租户信息"""
        # 从请求头或域名提取租户ID
        tenant_id = self._extract_tenant_id(request)
        
        if tenant_id:
            # 验证租户访问权限
            has_access = await self.tenant_manager.check_tenant_access(tenant_id)
            if not has_access:
                raise HTTPException(
                    status_code=403,
                    detail=f"Tenant {tenant_id} is not active or has expired"
                )
            
            # 将租户上下文添加到请求状态
            request.state.tenant_id = tenant_id
            request.state.tenant_context = TenantContext(
                tenant_id=tenant_id,
                tenant_metadata=self.tenant_manager.get_tenant(tenant_id)
            )
        else:
            # 没有租户ID，可能是系统管理员或全局操作
            request.state.tenant_id = None
            request.state.tenant_context = None
        
        response = await call_next(request)
        return response
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """从请求中提取租户ID"""
        # 方案1: 从请求头提取
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # 方案2: 从域名提取
        host = request.headers.get("host", "")
        if host:
            # 解析子域名: company-a.tradingagents.cn -> company-a
            parts = host.split(".")
            if len(parts) >= 3:
                subdomain = parts[0]
                # 通过子域名查找租户
                tenant = self.tenant_manager.get_tenant_by_domain(host)
                if tenant:
                    return tenant.tenant_id
        
        # 方案3: 从查询参数提取（开发/测试用）
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id
        
        return None


def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """从请求中获取租户上下文"""
    return getattr(request.state, "tenant_context", None)


def get_tenant_id(request: Request) -> Optional[str]:
    """从请求中获取租户ID"""
    return getattr(request.state, "tenant_id", None)


async def require_tenant(request: Request) -> str:
    """要求请求必须包含租户ID"""
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant ID is required"
        )
    return tenant_id

