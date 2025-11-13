"""
计费系统数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from app.utils.timezone import now_tz


class BillingTier(str, Enum):
    """计费等级"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    """计费周期"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ONE_TIME = "one_time"


class UsageType(str, Enum):
    """使用类型"""
    API_CALL = "api_call"
    STORAGE = "storage"
    USER = "user"
    FEATURE = "feature"


class InvoiceStatus(str, Enum):
    """发票状态"""
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class BillingPlan(BaseModel):
    """计费方案"""
    tier: BillingTier
    name: str
    description: str
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    price_one_time: Optional[float] = None
    
    # 配额限制
    max_users: int = 10
    max_storage_gb: int = 1
    max_api_calls_per_day: int = 1000
    
    # 功能特性
    features: list[str] = Field(default_factory=list)
    
    # 计费规则
    api_call_price: float = 0.0  # 每次API调用价格（超出配额后）
    storage_price_per_gb: float = 0.0  # 每GB存储价格（超出配额后）
    user_price: float = 0.0  # 每个用户价格（超出配额后）


class UsageRecord(BaseModel):
    """使用记录"""
    tenant_id: str
    usage_type: UsageType
    amount: float  # 使用量
    unit: str = "count"  # 单位
    timestamp: datetime = Field(default_factory=now_tz)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BillingRecord(BaseModel):
    """计费记录"""
    tenant_id: str
    billing_cycle: BillingCycle
    start_date: datetime
    end_date: datetime
    tier: BillingTier
    
    # 使用统计
    api_calls: int = 0
    storage_gb: float = 0.0
    users: int = 0
    
    # 费用计算
    base_fee: float = 0.0  # 基础费用
    usage_fee: float = 0.0  # 使用费用（超出配额）
    total_fee: float = 0.0  # 总费用
    
    # 状态
    status: str = "pending"  # pending, paid, overdue
    created_at: datetime = Field(default_factory=now_tz)
    paid_at: Optional[datetime] = None


class Invoice(BaseModel):
    """发票"""
    invoice_id: str
    tenant_id: str
    billing_record_id: str
    
    # 发票信息
    invoice_number: str
    amount: float
    tax_amount: float = 0.0
    total_amount: float
    
    # 状态
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issue_date: datetime = Field(default_factory=now_tz)
    due_date: datetime
    paid_date: Optional[datetime] = None
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)

