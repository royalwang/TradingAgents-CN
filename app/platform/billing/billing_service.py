"""
计费服务
基于租户等级的计费管理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.utils.timezone import now_tz
from app.core.database import get_mongo_db
from app.platform.tenants import get_manager as get_tenant_manager, TenantTier
from .billing_models import (
    BillingPlan, BillingTier, BillingCycle,
    UsageRecord, UsageType, BillingRecord,
    Invoice, InvoiceStatus,
)


# 默认计费方案
DEFAULT_BILLING_PLANS = {
    BillingTier.FREE: BillingPlan(
        tier=BillingTier.FREE,
        name="免费版",
        description="适合个人用户和小团队",
        price_monthly=0.0,
        price_yearly=0.0,
        max_users=3,
        max_storage_gb=1,
        max_api_calls_per_day=100,
        features=["trading"],
        api_call_price=0.01,
        storage_price_per_gb=0.5,
        user_price=0.0,
    ),
    BillingTier.BASIC: BillingPlan(
        tier=BillingTier.BASIC,
        name="基础版",
        description="适合小型企业",
        price_monthly=99.0,
        price_yearly=990.0,
        max_users=20,
        max_storage_gb=10,
        max_api_calls_per_day=5000,
        features=["trading", "analytics"],
        api_call_price=0.005,
        storage_price_per_gb=0.3,
        user_price=5.0,
    ),
    BillingTier.PROFESSIONAL: BillingPlan(
        tier=BillingTier.PROFESSIONAL,
        name="专业版",
        description="适合中型企业",
        price_monthly=299.0,
        price_yearly=2990.0,
        max_users=50,
        max_storage_gb=100,
        max_api_calls_per_day=10000,
        features=["trading", "analytics", "reporting"],
        api_call_price=0.003,
        storage_price_per_gb=0.2,
        user_price=3.0,
    ),
    BillingTier.ENTERPRISE: BillingPlan(
        tier=BillingTier.ENTERPRISE,
        name="企业版",
        description="适合大型企业，支持定制",
        price_monthly=999.0,
        price_yearly=9990.0,
        max_users=1000,
        max_storage_gb=1000,
        max_api_calls_per_day=100000,
        features=["trading", "analytics", "reporting", "custom"],
        api_call_price=0.001,
        storage_price_per_gb=0.1,
        user_price=1.0,
    ),
}


class BillingService:
    """计费服务"""
    
    def __init__(self):
        self.db = get_mongo_db()
        self.tenant_manager = get_tenant_manager()
        self.billing_plans = DEFAULT_BILLING_PLANS
    
    def get_billing_plan(self, tier: BillingTier) -> BillingPlan:
        """获取计费方案"""
        return self.billing_plans.get(tier, self.billing_plans[BillingTier.FREE])
    
    def get_billing_plan_by_tenant_tier(self, tenant_tier: TenantTier) -> BillingPlan:
        """通过租户等级获取计费方案"""
        tier_map = {
            TenantTier.FREE: BillingTier.FREE,
            TenantTier.BASIC: BillingTier.BASIC,
            TenantTier.PROFESSIONAL: BillingTier.PROFESSIONAL,
            TenantTier.ENTERPRISE: BillingTier.ENTERPRISE,
        }
        billing_tier = tier_map.get(tenant_tier, BillingTier.FREE)
        return self.get_billing_plan(billing_tier)
    
    async def record_usage(
        self,
        tenant_id: str,
        usage_type: UsageType,
        amount: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """记录使用量"""
        usage_record = UsageRecord(
            tenant_id=tenant_id,
            usage_type=usage_type,
            amount=amount,
            metadata=metadata or {},
        )
        
        collection = self.db["usage_records"]
        result = await collection.insert_one(usage_record.model_dump())
        return str(result.inserted_id)
    
    async def calculate_billing(
        self,
        tenant_id: str,
        billing_cycle: BillingCycle,
        start_date: datetime,
        end_date: datetime,
    ) -> BillingRecord:
        """计算账单"""
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        billing_plan = self.get_billing_plan_by_tenant_tier(tenant.tier)
        
        # 获取周期内的使用统计
        usage_stats = await self._get_usage_stats(tenant_id, start_date, end_date)
        
        # 计算基础费用
        if billing_cycle == BillingCycle.MONTHLY:
            base_fee = billing_plan.price_monthly
        elif billing_cycle == BillingCycle.YEARLY:
            base_fee = billing_plan.price_yearly
        else:
            base_fee = billing_plan.price_one_time or 0.0
        
        # 计算超出配额的使用费用
        usage_fee = 0.0
        
        # API调用超出费用
        if usage_stats["api_calls"] > billing_plan.max_api_calls_per_day * 30:  # 假设30天
            excess_api_calls = usage_stats["api_calls"] - billing_plan.max_api_calls_per_day * 30
            usage_fee += excess_api_calls * billing_plan.api_call_price
        
        # 存储超出费用
        if usage_stats["storage_gb"] > billing_plan.max_storage_gb:
            excess_storage = usage_stats["storage_gb"] - billing_plan.max_storage_gb
            usage_fee += excess_storage * billing_plan.storage_price_per_gb
        
        # 用户超出费用
        if usage_stats["users"] > billing_plan.max_users:
            excess_users = usage_stats["users"] - billing_plan.max_users
            usage_fee += excess_users * billing_plan.user_price
        
        total_fee = base_fee + usage_fee
        
        billing_record = BillingRecord(
            tenant_id=tenant_id,
            billing_cycle=billing_cycle,
            start_date=start_date,
            end_date=end_date,
            tier=billing_plan.tier,
            api_calls=usage_stats["api_calls"],
            storage_gb=usage_stats["storage_gb"],
            users=usage_stats["users"],
            base_fee=base_fee,
            usage_fee=usage_fee,
            total_fee=total_fee,
        )
        
        # 保存计费记录
        collection = self.db["billing_records"]
        result = await collection.insert_one(billing_record.model_dump())
        
        return billing_record
    
    async def _get_usage_stats(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """获取使用统计"""
        collection = self.db["usage_records"]
        
        # 统计API调用
        api_calls = await collection.count_documents({
            "tenant_id": tenant_id,
            "usage_type": UsageType.API_CALL.value,
            "timestamp": {"$gte": start_date, "$lte": end_date},
        })
        
        # 统计存储（简化处理，实际应从存储系统获取）
        storage_records = await collection.find({
            "tenant_id": tenant_id,
            "usage_type": UsageType.STORAGE.value,
            "timestamp": {"$gte": start_date, "$lte": end_date},
        }).sort("timestamp", -1).limit(1).to_list(length=1)
        
        storage_gb = storage_records[0]["amount"] if storage_records else 0.0
        
        # 统计用户数（从租户统计获取）
        stats = await self.tenant_manager.get_tenant_statistics(tenant_id)
        users = stats.get("current_users", 0)
        
        return {
            "api_calls": api_calls,
            "storage_gb": storage_gb,
            "users": users,
        }
    
    async def create_invoice(
        self,
        billing_record_id: str,
        tenant_id: str,
        due_date: datetime,
    ) -> Invoice:
        """创建发票"""
        # 获取计费记录
        from bson import ObjectId
        collection = self.db["billing_records"]
        try:
            billing_doc = await collection.find_one({"_id": ObjectId(billing_record_id)})
        except:
            billing_doc = await collection.find_one({"tenant_id": tenant_id})
        
        if not billing_doc:
            raise ValueError(f"Billing record {billing_record_id} not found")
        
        billing_record = BillingRecord(**billing_doc)
        
        # 生成发票号
        invoice_number = f"INV-{tenant_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 计算税费（假设10%）
        tax_rate = 0.1
        tax_amount = billing_record.total_fee * tax_rate
        total_amount = billing_record.total_fee + tax_amount
        
        invoice = Invoice(
            invoice_id=f"invoice_{datetime.now().timestamp()}",
            tenant_id=tenant_id,
            billing_record_id=billing_record_id,
            invoice_number=invoice_number,
            amount=billing_record.total_fee,
            tax_amount=tax_amount,
            total_amount=total_amount,
            due_date=due_date,
        )
        
        # 保存发票
        invoice_collection = self.db["invoices"]
        await invoice_collection.insert_one(invoice.model_dump())
        
        return invoice


# 全局服务实例
_global_billing_service: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    """获取全局计费服务实例"""
    global _global_billing_service
    if _global_billing_service is None:
        _global_billing_service = BillingService()
    return _global_billing_service

