-- Supabase 平台数据 Schema
-- 用于初始化 Supabase 数据库表结构

-- ==================== 用户表 ====================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_tenant_admin BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}'::jsonb,
    daily_quota INTEGER DEFAULT 1000,
    concurrent_limit INTEGER DEFAULT 3,
    total_analyses INTEGER DEFAULT 0,
    successful_analyses INTEGER DEFAULT 0,
    failed_analyses INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ==================== 租户表 ====================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    domain VARCHAR(255) UNIQUE,
    tier VARCHAR(20) NOT NULL DEFAULT 'free',
    status VARCHAR(20) NOT NULL DEFAULT 'trial',
    max_users INTEGER DEFAULT 10,
    max_storage_gb INTEGER DEFAULT 1,
    max_api_calls_per_day INTEGER DEFAULT 1000,
    features TEXT[] DEFAULT ARRAY[]::TEXT[],
    config JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    owner_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 租户表索引
CREATE INDEX IF NOT EXISTS idx_tenants_tenant_id ON tenants(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_tier ON tenants(tier);
CREATE INDEX IF NOT EXISTS idx_tenants_owner_id ON tenants(owner_id);

-- ==================== 平台配置表 ====================
CREATE TABLE IF NOT EXISTS platform_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name VARCHAR(255) UNIQUE NOT NULL,
    config_type VARCHAR(50) NOT NULL DEFAULT 'system',
    config_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 平台配置表索引
CREATE INDEX IF NOT EXISTS idx_platform_configs_name ON platform_configs(config_name);
CREATE INDEX IF NOT EXISTS idx_platform_configs_type ON platform_configs(config_type);

-- ==================== LLM提供商表 ====================
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    api_key VARCHAR(255),
    api_base VARCHAR(255),
    config JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LLM提供商表索引
CREATE INDEX IF NOT EXISTS idx_llm_providers_provider_id ON llm_providers(provider_id);
CREATE INDEX IF NOT EXISTS idx_llm_providers_is_active ON llm_providers(is_active);

-- ==================== 计费方案表 ====================
CREATE TABLE IF NOT EXISTS billing_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tier VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10, 2) DEFAULT 0.0,
    price_yearly DECIMAL(10, 2) DEFAULT 0.0,
    price_one_time DECIMAL(10, 2),
    max_users INTEGER DEFAULT 10,
    max_storage_gb INTEGER DEFAULT 1,
    max_api_calls_per_day INTEGER DEFAULT 1000,
    features TEXT[] DEFAULT ARRAY[]::TEXT[],
    api_call_price DECIMAL(10, 4) DEFAULT 0.0,
    storage_price_per_gb DECIMAL(10, 4) DEFAULT 0.0,
    user_price DECIMAL(10, 4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 计费方案表索引
CREATE INDEX IF NOT EXISTS idx_billing_plans_tier ON billing_plans(tier);

-- ==================== 计费记录表 ====================
CREATE TABLE IF NOT EXISTS billing_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    tier VARCHAR(20) NOT NULL,
    api_calls INTEGER DEFAULT 0,
    storage_gb DECIMAL(10, 2) DEFAULT 0.0,
    users INTEGER DEFAULT 0,
    base_fee DECIMAL(10, 2) DEFAULT 0.0,
    usage_fee DECIMAL(10, 2) DEFAULT 0.0,
    total_fee DECIMAL(10, 2) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE
);

-- 计费记录表索引
CREATE INDEX IF NOT EXISTS idx_billing_records_tenant_id ON billing_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_records_status ON billing_records(status);
CREATE INDEX IF NOT EXISTS idx_billing_records_created_at ON billing_records(created_at);

-- ==================== 发票表 ====================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id VARCHAR(100) UNIQUE NOT NULL,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    billing_record_id UUID REFERENCES billing_records(id),
    amount DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0.0,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    issue_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    paid_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 发票表索引
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_id ON invoices(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_tenant_id ON invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

-- ==================== 使用记录表 ====================
CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    usage_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(50) DEFAULT 'count',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 使用记录表索引
CREATE INDEX IF NOT EXISTS idx_usage_records_tenant_id ON usage_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_usage_type ON usage_records(usage_type);
CREATE INDEX IF NOT EXISTS idx_usage_records_timestamp ON usage_records(timestamp);

-- ==================== 操作日志表 ====================
CREATE TABLE IF NOT EXISTS operation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50),
    username VARCHAR(50),
    tenant_id VARCHAR(50),
    action_type VARCHAR(50) NOT NULL,
    action VARCHAR(255) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    duration_ms INTEGER,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 操作日志表索引
CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_tenant_id ON operation_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_action_type ON operation_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_operation_logs_success ON operation_logs(success);

-- ==================== Row Level Security (RLS) ====================
-- 启用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE operation_logs ENABLE ROW LEVEL SECURITY;

-- 用户表策略：用户可以查看和更新自己的数据
CREATE POLICY "Users can view own data" ON users
    FOR SELECT
    USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE
    USING (auth.uid()::text = id::text);

-- 租户表策略：用户可以查看自己租户的数据
CREATE POLICY "Users can view own tenant" ON tenants
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users WHERE id::text = auth.uid()::text
        )
    );

-- 计费记录策略：租户管理员可以查看自己租户的计费记录
CREATE POLICY "Tenant admins can view own billing" ON billing_records
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users 
            WHERE id::text = auth.uid()::text AND is_tenant_admin = TRUE
        )
    );

-- 发票策略：租户管理员可以查看自己租户的发票
CREATE POLICY "Tenant admins can view own invoices" ON invoices
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users 
            WHERE id::text = auth.uid()::text AND is_tenant_admin = TRUE
        )
    );

-- 使用记录策略：租户管理员可以查看自己租户的使用记录
CREATE POLICY "Tenant admins can view own usage" ON usage_records
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users 
            WHERE id::text = auth.uid()::text AND is_tenant_admin = TRUE
        )
    );

-- 操作日志策略：用户可以查看自己的操作日志
CREATE POLICY "Users can view own logs" ON operation_logs
    FOR SELECT
    USING (
        user_id = auth.uid()::text OR
        tenant_id IN (
            SELECT tenant_id FROM users 
            WHERE id::text = auth.uid()::text AND is_tenant_admin = TRUE
        )
    );

-- 平台配置策略：所有认证用户都可以查看
CREATE POLICY "Authenticated users can view configs" ON platform_configs
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- ==================== 更新时间触发器 ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_platform_configs_updated_at BEFORE UPDATE ON platform_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_llm_providers_updated_at BEFORE UPDATE ON llm_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_billing_plans_updated_at BEFORE UPDATE ON billing_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

