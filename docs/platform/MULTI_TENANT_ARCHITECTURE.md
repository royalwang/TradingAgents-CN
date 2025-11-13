# 多租户架构设计文档

## 概述

平台支持多租户架构，允许不同组织（租户）在同一平台上独立使用，实现数据隔离、资源管理和权限控制。每个租户拥有独立的数据空间、用户管理和功能配置。

## 核心概念

### 租户（Tenant）

租户是平台上的一个独立组织单元，具有以下特征：

- **数据隔离**：每个租户的数据完全隔离，互不干扰
- **资源限制**：每个租户有独立的资源配额（用户数、存储空间、API调用次数等）
- **功能配置**：每个租户可以启用不同的功能模块
- **独立域名**：支持为每个租户配置独立的子域名

### 租户等级（Tenant Tier）

平台提供多个租户等级，不同等级有不同的资源配额：

- **FREE（免费版）**：基础功能，有限资源
- **BASIC（基础版）**：标准功能，中等资源
- **PROFESSIONAL（专业版）**：完整功能，高资源配额
- **ENTERPRISE（企业版）**：定制化功能，无限制资源

### 租户状态（Tenant Status）

- **ACTIVE（活跃）**：正常使用中
- **INACTIVE（非活跃）**：已停用
- **SUSPENDED（暂停）**：因违规等原因暂停
- **TRIAL（试用）**：试用期
- **EXPIRED（过期）**：已过期

## 架构设计

### 模块结构

```
app/platform/tenants/
├── __init__.py              # 模块导出
├── tenant_registry.py       # 租户注册表
├── tenant_manager.py        # 租户管理器
├── tenant_service.py        # 租户服务层
├── tenant_middleware.py     # 租户中间件
├── yaml_loader.py           # YAML加载器
└── example_tenants.yaml     # 示例配置
```

### 数据隔离方案

#### 方案1：集合前缀（当前实现）

每个租户的数据存储在独立的集合中，集合名称格式：`tenant_{tenant_id}_{collection_name}`

**优点**：
- 实现简单
- 数据完全隔离
- 易于备份和迁移

**缺点**：
- 集合数量可能较多
- 跨租户查询需要特殊处理

#### 方案2：数据库分离（可选）

每个租户使用独立的数据库，数据库名称格式：`tenant_{tenant_id}`

**优点**：
- 更强的数据隔离
- 易于独立备份和恢复

**缺点**：
- 数据库连接管理复杂
- 跨租户操作困难

### 租户识别方式

平台支持多种方式识别租户：

1. **请求头**：`X-Tenant-ID: company_a`
2. **子域名**：`company-a.tradingagents.cn`
3. **查询参数**：`?tenant_id=company_a`（仅开发/测试用）

## 功能特性

### 1. 租户注册和管理

```python
from app.platform.tenants import get_registry, TenantMetadata, TenantStatus, TenantTier

registry = get_registry()

# 注册新租户
tenant = TenantMetadata(
    tenant_id="company_a",
    name="company_a",
    display_name="公司A",
    description="公司A的租户实例",
    domain="company-a.tradingagents.cn",
    tier=TenantTier.PROFESSIONAL,
    status=TenantStatus.ACTIVE,
    max_users=50,
    max_storage_gb=100,
    max_api_calls_per_day=10000,
    features=["trading", "rental_management", "analytics"],
)

registry.register(tenant)
```

### 2. 数据隔离访问

```python
from app.platform.tenants import get_manager

manager = get_manager()

# 获取租户数据（自动添加租户过滤）
data = await manager.get_tenant_data(
    tenant_id="company_a",
    collection="users",
    query={"status": "active"}
)

# 创建租户数据（自动添加租户ID）
user_id = await manager.create_tenant_data(
    tenant_id="company_a",
    collection="users",
    data={"username": "user1", "email": "user1@example.com"}
)
```

### 3. 资源限制检查

```python
# 检查用户数量限制
can_add_user = await manager.check_user_limit("company_a", current_user_count=45)

# 检查存储空间限制
can_add_storage = await manager.check_storage_limit("company_a", current_storage_gb=95)

# 检查API调用配额
can_make_api_call = await manager.check_api_quota("company_a", today_api_calls=9999)
```

### 4. 功能模块检查

```python
# 检查租户是否启用特定功能
has_trading = manager.has_feature("company_a", "trading")
has_rental = manager.has_feature("company_a", "rental_management")
```

### 5. 租户中间件

```python
from fastapi import FastAPI
from app.platform.tenants import TenantMiddleware

app = FastAPI()

# 添加租户中间件
app.add_middleware(TenantMiddleware)

# 在路由中使用租户上下文
from app.platform.tenants import get_tenant_id, require_tenant

@router.get("/api/data")
async def get_data(request: Request):
    tenant_id = get_tenant_id(request)  # 从请求中获取租户ID
    # 使用tenant_id进行数据查询
    ...
```

## YAML声明式管理

### 配置格式

```yaml
tenants:
  - tenant_id: company_a
    name: company_a
    display_name: 公司A
    description: 公司A的租户实例
    domain: company-a.tradingagents.cn
    tier: professional
    status: active
    max_users: 50
    max_storage_gb: 100
    max_api_calls_per_day: 10000
    features:
      - trading
      - rental_management
      - analytics
    config:
      theme: "dark"
      language: "zh-CN"
    metadata:
      industry: "金融"
      region: "中国"
    owner_id: "user_001"
    expires_at: "2026-12-31T23:59:59Z"
```

### 导入/导出

```python
from app.platform.tenants import get_service

service = get_service()

# 从YAML文件导入
result = await service.import_from_yaml_file("tenants.yaml", update_existing=True)

# 导出为YAML字符串
yaml_str = await service.export_to_yaml_string()
```

## API接口

### 租户管理

- `GET /api/platform/tenants` - 列出租户
- `GET /api/platform/tenants/{tenant_id}` - 获取租户详情
- `GET /api/platform/tenants/{tenant_id}/statistics` - 获取租户统计信息
- `POST /api/platform/tenants/{tenant_id}/status` - 更新租户状态

### YAML声明式管理

- `POST /api/platform/tenants/import/yaml` - 从YAML字符串导入
- `POST /api/platform/tenants/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/tenants/export/yaml` - 导出为YAML格式

## 用户与租户关联

### 用户模型扩展

用户模型已扩展支持租户：

```python
class User(BaseModel):
    # ... 其他字段
    tenant_id: Optional[str] = None  # 所属租户ID
    is_tenant_admin: bool = False    # 是否为租户管理员
```

### 登录流程

1. 用户登录时，系统识别租户（通过域名或请求头）
2. 验证用户是否属于该租户
3. 验证租户状态是否允许访问
4. 生成包含租户信息的JWT Token

## 业务模块支持

### 功能模块列表

平台支持以下业务模块：

- **trading**：交易分析
- **rental_management**：租房管理
- **analytics**：数据分析
- **reporting**：报表生成
- **payment**：支付处理
- **custom**：自定义模块

### 模块启用

每个租户可以启用不同的功能模块，通过`features`字段配置：

```yaml
features:
  - trading
  - rental_management
```

在代码中检查功能是否启用：

```python
if manager.has_feature(tenant_id, "rental_management"):
    # 执行租房管理相关逻辑
    ...
```

## 存储规划

### MongoDB集合

租户相关的集合：

- `tenants`：租户元数据
- `tenant_{tenant_id}_users`：租户用户
- `tenant_{tenant_id}_agents`：租户智能体
- `tenant_{tenant_id}_workflows`：租户工作流
- `tenant_{tenant_id}_knowledge_bases`：租户知识库
- `tenant_{tenant_id}_plugins`：租户插件
- `tenant_{tenant_id}_data_sources`：租户数据源
- `tenant_{tenant_id}_rental_properties`：租户房产（租房管理）
- `tenant_{tenant_id}_rental_contracts`：租户合同（租房管理）
- `tenant_{tenant_id}_rental_payments`：租户支付（租房管理）

### 索引策略

- `tenants`集合：`tenant_id`（唯一索引）、`domain`（唯一索引）、`status`、`tier`
- 租户数据集合：`tenant_id`（复合索引）、`created_at`、`updated_at`

## 安全考虑

### 数据隔离

- 所有数据操作必须包含租户ID过滤
- 中间件自动验证租户访问权限
- 跨租户数据访问被严格禁止

### 权限控制

- 系统管理员：可以管理所有租户
- 租户管理员：只能管理本租户的用户和数据
- 普通用户：只能访问本租户的数据

### 审计日志

所有租户操作都记录审计日志，包括：
- 租户创建/更新/删除
- 用户操作
- 数据访问
- 资源使用

## 使用示例

### 创建租户

```python
from app.platform.tenants import get_registry, TenantMetadata, TenantStatus, TenantTier

registry = get_registry()

tenant = TenantMetadata(
    tenant_id="rental_company",
    name="rental_company",
    display_name="租房管理公司",
    description="专注于租房管理的租户",
    domain="rental.tradingagents.cn",
    tier=TenantTier.PROFESSIONAL,
    status=TenantStatus.ACTIVE,
    max_users=100,
    max_storage_gb=200,
    max_api_calls_per_day=20000,
    features=["rental_management", "analytics", "payment"],
)

registry.register(tenant)
```

### 在业务代码中使用租户

```python
from fastapi import Request
from app.platform.tenants import get_tenant_id, get_manager

@router.post("/api/rental/properties")
async def create_property(request: Request, property_data: dict):
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID required")
    
    manager = get_manager()
    
    # 检查功能是否启用
    if not manager.has_feature(tenant_id, "rental_management"):
        raise HTTPException(status_code=403, detail="Feature not enabled")
    
    # 创建房产数据（自动添加租户ID）
    property_id = await manager.create_tenant_data(
        tenant_id=tenant_id,
        collection="rental_properties",
        data=property_data
    )
    
    return {"property_id": property_id}
```

## 未来扩展

### 多租户管理控制台

- 租户创建和管理界面
- 资源使用监控
- 账单和计费管理
- 功能模块配置

### 租户间数据共享

- 支持租户间数据共享（可选）
- 数据市场功能
- 跨租户协作

### 租户迁移工具

- 租户数据导出
- 租户数据导入
- 租户合并功能

## 总结

多租户架构为平台提供了强大的扩展能力，支持：

1. **数据隔离**：每个租户的数据完全独立
2. **资源管理**：灵活的配额和限制管理
3. **功能配置**：按需启用功能模块
4. **扩展性**：支持未来添加新的业务模块（如租房管理）
5. **声明式管理**：通过YAML配置文件管理租户

通过多租户架构，平台可以支持多种业务场景，从交易分析到租房管理，都能在同一平台上实现。

