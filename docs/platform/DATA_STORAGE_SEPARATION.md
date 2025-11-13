# 平台数据与业务数据分离架构规划

## 概述

本文档描述了平台数据存储与业务数据存储的分离架构设计，实现平台核心功能数据与业务应用数据的物理隔离，提高系统的可扩展性、安全性和维护性。

## 架构原则

### 1. 数据分类

#### 平台数据（Platform Data）
平台核心功能所需的数据，包括：
- **用户与认证**：用户账户、会话、权限
- **租户管理**：租户元数据、配置、状态
- **系统配置**：平台配置、LLM提供商、数据源配置
- **平台资源**：智能体、工作流、插件、知识库（平台级）
- **计费系统**：计费方案、账单、发票
- **审计日志**：操作日志、系统日志
- **平台统计**：平台级使用统计

#### 业务数据（Business Data）
租户业务应用产生的数据，包括：
- **租户用户**：租户内的用户数据
- **业务资源**：租户的智能体、工作流、插件、知识库
- **业务数据**：交易数据、分析报告、业务记录
- **业务配置**：租户特定的配置
- **业务统计**：租户内的使用统计

### 2. 分离策略

#### 物理分离
- **平台数据库**：存储所有平台数据
- **业务数据库**：每个租户独立的业务数据库（可选）
- **共享业务数据库**：所有租户共享一个业务数据库，通过租户ID隔离

#### 逻辑分离
- 在同一数据库中，通过集合命名和索引实现逻辑分离
- 平台数据集合：`platform_*` 前缀
- 业务数据集合：`tenant_{tenant_id}_*` 前缀

## 架构设计

### 方案一：完全物理分离（推荐用于大型部署）

```
┌─────────────────────────────────────┐
│        平台数据库 (Platform DB)      │
├─────────────────────────────────────┤
│ - users (平台用户)                   │
│ - tenants (租户元数据)               │
│ - platform_configs (平台配置)        │
│ - platform_agents (平台智能体)       │
│ - platform_workflows (平台工作流)     │
│ - platform_plugins (平台插件)        │
│ - billing_plans (计费方案)            │
│ - billing_records (计费记录)          │
│ - invoices (发票)                     │
│ - operation_logs (操作日志)            │
│ - platform_statistics (平台统计)      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    业务数据库 1 (Tenant A DB)        │
├─────────────────────────────────────┤
│ - tenant_a_users (租户用户)          │
│ - tenant_a_agents (业务智能体)       │
│ - tenant_a_workflows (业务工作流)    │
│ - tenant_a_data (业务数据)           │
│ - tenant_a_reports (业务报告)        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    业务数据库 2 (Tenant B DB)        │
├─────────────────────────────────────┤
│ - tenant_b_users                    │
│ - tenant_b_agents                   │
│ - tenant_b_workflows                │
│ - tenant_b_data                     │
└─────────────────────────────────────┘
```

**优点**：
- 完全的数据隔离
- 易于独立备份和恢复
- 支持租户数据迁移
- 性能隔离

**缺点**：
- 数据库连接管理复杂
- 跨租户查询困难
- 资源消耗较大

### 方案二：混合分离（推荐用于中小型部署）

```
┌─────────────────────────────────────┐
│        平台数据库 (Platform DB)      │
├─────────────────────────────────────┤
│ 平台数据集合：                        │
│ - users                              │
│ - tenants                            │
│ - platform_configs                   │
│ - platform_agents                    │
│ - platform_workflows                 │
│ - platform_plugins                   │
│ - billing_*                          │
│ - operation_logs                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│     业务数据库 (Business DB)        │
├─────────────────────────────────────┤
│ 业务数据集合（租户隔离）：            │
│ - tenant_company_a_users             │
│ - tenant_company_a_agents            │
│ - tenant_company_a_workflows         │
│ - tenant_company_a_data              │
│ - tenant_company_b_users             │
│ - tenant_company_b_agents            │
│ - tenant_company_b_workflows         │
│ - tenant_company_b_data              │
└─────────────────────────────────────┘
```

**优点**：
- 平台和业务数据物理分离
- 业务数据逻辑隔离（通过集合前缀）
- 实现相对简单
- 资源消耗适中

**缺点**：
- 业务数据库可能较大
- 需要良好的索引策略

### 方案三：逻辑分离（当前实现，适合小型部署）

```
┌─────────────────────────────────────┐
│      统一数据库 (Unified DB)         │
├─────────────────────────────────────┤
│ 平台数据集合：                        │
│ - users                              │
│ - tenants                            │
│ - platform_configs                   │
│ - platform_agents                    │
│ - billing_*                          │
│                                      │
│ 业务数据集合（租户隔离）：            │
│ - tenant_company_a_*                 │
│ - tenant_company_b_*                 │
└─────────────────────────────────────┘
```

**优点**：
- 实现最简单
- 资源消耗最小
- 易于管理

**缺点**：
- 平台和业务数据混合
- 备份和恢复需要区分
- 扩展性有限

## 推荐方案：混合分离架构

基于当前平台规模和未来扩展需求，推荐采用**方案二：混合分离架构**。

### 数据库配置

#### 平台数据库（platform_db）

**用途**：存储所有平台核心数据

**集合列表**：
```
platform_db/
├── users                    # 平台用户（系统管理员、租户管理员）
├── tenants                  # 租户元数据
├── platform_configs         # 平台配置
├── platform_agents          # 平台级智能体模板
├── platform_workflows       # 平台级工作流模板
├── platform_plugins         # 平台级插件
├── platform_knowledge_bases  # 平台级知识库
├── llm_providers            # LLM提供商配置
├── data_sources            # 数据源配置
├── billing_plans           # 计费方案
├── billing_records         # 计费记录
├── invoices                # 发票
├── usage_records           # 使用记录（平台级）
├── operation_logs          # 操作日志
└── platform_statistics     # 平台统计
```

#### 业务数据库（business_db）

**用途**：存储所有租户的业务数据

**集合命名规则**：`tenant_{tenant_id}_{collection_name}`

**集合列表**：
```
business_db/
├── tenant_company_a_users              # 租户A的用户
├── tenant_company_a_agents             # 租户A的智能体
├── tenant_company_a_workflows          # 租户A的工作流
├── tenant_company_a_plugins            # 租户A的插件
├── tenant_company_a_knowledge_bases    # 租户A的知识库
├── tenant_company_a_data_sources       # 租户A的数据源
├── tenant_company_a_analysis_reports    # 租户A的分析报告
├── tenant_company_a_business_data      # 租户A的业务数据
├── tenant_company_a_statistics         # 租户A的统计
│
├── tenant_company_b_users              # 租户B的用户
├── tenant_company_b_agents             # 租户B的智能体
└── ...
```

## 数据访问层设计

### 平台数据访问

```python
from app.core.database import get_platform_db

# 平台数据库连接
platform_db = get_platform_db()

# 访问平台数据
users = platform_db["users"]
tenants = platform_db["tenants"]
platform_configs = platform_db["platform_configs"]
```

### 业务数据访问

```python
from app.core.database import get_business_db
from app.platform.tenants import get_tenant_id

# 业务数据库连接
business_db = get_business_db()

# 获取租户ID
tenant_id = get_tenant_id(request)

# 访问租户业务数据
tenant_users = business_db[f"tenant_{tenant_id}_users"]
tenant_agents = business_db[f"tenant_{tenant_id}_agents"]
```

### 统一数据访问接口

```python
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
        data: dict
    ):
        """创建租户业务数据"""
        coll = self.get_tenant_collection(tenant_id, collection)
        data["tenant_id"] = tenant_id
        data["created_at"] = datetime.utcnow()
        return await coll.insert_one(data)
```

## 数据库连接配置

### 配置示例

```python
# app/core/config.py

class Settings:
    # 平台数据库
    PLATFORM_MONGO_URI: str = "mongodb://localhost:27017/"
    PLATFORM_MONGO_DB: str = "tradingagents_platform"
    
    # 业务数据库
    BUSINESS_MONGO_URI: str = "mongodb://localhost:27017/"
    BUSINESS_MONGO_DB: str = "tradingagents_business"
    
    # 可选：Redis分离
    PLATFORM_REDIS_URI: str = "redis://localhost:6379/0"
    BUSINESS_REDIS_URI: str = "redis://localhost:6379/1"
```

### 连接管理

```python
# app/core/database.py

# 平台数据库连接
platform_mongo_client: Optional[AsyncIOMotorClient] = None
platform_mongo_db: Optional[AsyncIOMotorDatabase] = None

# 业务数据库连接
business_mongo_client: Optional[AsyncIOMotorClient] = None
business_mongo_db: Optional[AsyncIOMotorDatabase] = None

def get_platform_db() -> AsyncIOMotorDatabase:
    """获取平台数据库"""
    global platform_mongo_db
    if platform_mongo_db is None:
        # 初始化平台数据库连接
        ...
    return platform_mongo_db

def get_business_db() -> AsyncIOMotorDatabase:
    """获取业务数据库"""
    global business_mongo_db
    if business_mongo_db is None:
        # 初始化业务数据库连接
        ...
    return business_mongo_db
```

## 数据迁移策略

### 从统一数据库迁移到分离架构

#### 步骤1：识别数据分类

```python
# 平台数据集合
PLATFORM_COLLECTIONS = [
    "users",
    "tenants",
    "platform_configs",
    "platform_agents",
    "billing_plans",
    "billing_records",
    "invoices",
    "operation_logs",
]

# 业务数据集合（通过前缀识别）
BUSINESS_COLLECTION_PREFIX = "tenant_"
```

#### 步骤2：数据迁移脚本

```python
async def migrate_to_separated_storage():
    """迁移到分离存储架构"""
    old_db = get_mongo_db()  # 旧数据库
    platform_db = get_platform_db()  # 新平台数据库
    business_db = get_business_db()  # 新业务数据库
    
    # 迁移平台数据
    for collection_name in PLATFORM_COLLECTIONS:
        if collection_name in old_db.list_collection_names():
            old_coll = old_db[collection_name]
            new_coll = platform_db[collection_name]
            
            async for doc in old_coll.find():
                await new_coll.insert_one(doc)
    
    # 迁移业务数据
    for collection_name in old_db.list_collection_names():
        if collection_name.startswith(BUSINESS_COLLECTION_PREFIX):
            old_coll = old_db[collection_name]
            new_coll = business_db[collection_name]
            
            async for doc in old_coll.find():
                await new_coll.insert_one(doc)
```

#### 步骤3：验证和切换

1. 数据验证：确保所有数据正确迁移
2. 应用更新：更新代码使用新的数据库连接
3. 逐步切换：先读新库，再写新库，最后停用旧库

## 索引策略

### 平台数据库索引

```python
# users集合
platform_db["users"].create_index("username", unique=True)
platform_db["users"].create_index("email", unique=True)
platform_db["users"].create_index("tenant_id")

# tenants集合
platform_db["tenants"].create_index("tenant_id", unique=True)
platform_db["tenants"].create_index("domain", unique=True, sparse=True)
platform_db["tenants"].create_index("status")
platform_db["tenants"].create_index("tier")
```

### 业务数据库索引

```python
# 为每个租户集合创建索引
def create_tenant_indexes(tenant_id: str):
    """为租户创建索引"""
    business_db = get_business_db()
    
    # 用户集合索引
    users_coll = business_db[f"tenant_{tenant_id}_users"]
    users_coll.create_index("username", unique=True)
    users_coll.create_index("email", unique=True)
    users_coll.create_index("tenant_id")
    users_coll.create_index("created_at")
    
    # 智能体集合索引
    agents_coll = business_db[f"tenant_{tenant_id}_agents"]
    agents_coll.create_index("agent_id", unique=True)
    agents_coll.create_index("tenant_id")
    agents_coll.create_index("status")
    agents_coll.create_index("created_at")
```

## 备份和恢复策略

### 平台数据库备份

```bash
# 平台数据库备份
mongodump --uri="mongodb://localhost:27017/" \
  --db=tradingagents_platform \
  --out=/backup/platform/$(date +%Y%m%d)
```

### 业务数据库备份

#### 全量备份
```bash
# 所有租户业务数据备份
mongodump --uri="mongodb://localhost:27017/" \
  --db=tradingagents_business \
  --out=/backup/business/$(date +%Y%m%d)
```

#### 租户级备份
```bash
# 单个租户数据备份
mongodump --uri="mongodb://localhost:27017/" \
  --db=tradingagents_business \
  --collection=tenant_company_a_* \
  --out=/backup/tenants/company_a/$(date +%Y%m%d)
```

### 恢复策略

```bash
# 平台数据库恢复
mongorestore --uri="mongodb://localhost:27017/" \
  --db=tradingagents_platform \
  /backup/platform/20250114

# 业务数据库恢复
mongorestore --uri="mongodb://localhost:27017/" \
  --db=tradingagents_business \
  /backup/business/20250114

# 租户数据恢复
mongorestore --uri="mongodb://localhost:27017/" \
  --db=tradingagents_business \
  /backup/tenants/company_a/20250114
```

## 性能优化

### 1. 连接池配置

```python
# 平台数据库连接池
platform_client = AsyncIOMotorClient(
    settings.PLATFORM_MONGO_URI,
    maxPoolSize=50,  # 平台数据库连接池较小
    minPoolSize=10,
)

# 业务数据库连接池
business_client = AsyncIOMotorClient(
    settings.BUSINESS_MONGO_URI,
    maxPoolSize=200,  # 业务数据库连接池较大
    minPoolSize=50,
)
```

### 2. 读写分离

```python
# 主从复制配置
PLATFORM_MONGO_URI_READ = "mongodb://read-replica:27017/"
BUSINESS_MONGO_URI_READ = "mongodb://read-replica:27017/"

def get_platform_db_read() -> AsyncIOMotorDatabase:
    """获取平台数据库只读连接"""
    ...

def get_business_db_read() -> AsyncIOMotorDatabase:
    """获取业务数据库只读连接"""
    ...
```

### 3. 分片策略

对于大型业务数据库，可以考虑分片：

```python
# 按租户ID分片
shard_key = {"tenant_id": 1}

# 或按时间分片
shard_key = {"created_at": 1}
```

## 安全考虑

### 1. 访问控制

```python
# 平台数据库用户（只读平台数据）
platform_readonly_user = {
    "user": "platform_readonly",
    "pwd": "...",
    "roles": [{"role": "read", "db": "tradingagents_platform"}]
}

# 业务数据库用户（只能访问特定租户）
tenant_user = {
    "user": "tenant_company_a",
    "pwd": "...",
    "roles": [{
        "role": "readWrite",
        "db": "tradingagents_business",
        "collection": "tenant_company_a_*"
    }]
}
```

### 2. 数据加密

- 敏感数据加密存储
- 传输加密（TLS）
- 备份加密

### 3. 审计日志

所有数据访问都记录审计日志：

```python
async def log_data_access(
    user_id: str,
    tenant_id: Optional[str],
    collection: str,
    operation: str,
    details: dict
):
    """记录数据访问日志"""
    log_entry = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "collection": collection,
        "operation": operation,
        "details": details,
        "timestamp": datetime.utcnow(),
    }
    await platform_db["data_access_logs"].insert_one(log_entry)
```

## 监控和告警

### 1. 数据库监控指标

- 连接数
- 查询性能
- 存储使用
- 复制延迟

### 2. 告警规则

- 连接池耗尽
- 查询超时
- 存储空间不足
- 备份失败

## 实施计划

### 阶段1：准备阶段（1-2周）
1. 数据库环境准备
2. 配置更新
3. 连接管理代码实现

### 阶段2：迁移阶段（2-3周）
1. 数据迁移脚本开发
2. 数据迁移执行
3. 数据验证

### 阶段3：切换阶段（1周）
1. 应用代码更新
2. 逐步切换
3. 监控和优化

### 阶段4：优化阶段（持续）
1. 性能优化
2. 索引优化
3. 备份策略优化

## 总结

通过平台数据与业务数据的分离架构：

1. **提高安全性**：平台数据和业务数据物理隔离
2. **增强可扩展性**：业务数据库可以独立扩展
3. **简化维护**：平台和业务数据可以独立备份和恢复
4. **支持多租户**：租户数据完全隔离
5. **优化性能**：可以针对不同数据库优化配置

推荐采用**混合分离架构**（方案二），在保证数据隔离的同时，保持实现的相对简单性。

