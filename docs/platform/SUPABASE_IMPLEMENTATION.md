# Supabase 平台数据存储实施方案

## 概述

本文档描述如何实施方案一：完全迁移平台数据到 Supabase。平台数据（用户、租户、配置、计费等）存储在 Supabase，业务数据保留在 MongoDB。

## 架构设计

```
┌─────────────────────────────────────┐
│      Supabase (Platform Data)        │
├─────────────────────────────────────┤
│ - users (用户认证)                   │
│ - tenants (租户元数据)               │
│ - platform_configs (平台配置)        │
│ - llm_providers (LLM提供商)          │
│ - billing_plans (计费方案)            │
│ - billing_records (计费记录)          │
│ - invoices (发票)                     │
│ - usage_records (使用记录)            │
│ - operation_logs (操作日志)           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   MongoDB (Business Data)            │
├─────────────────────────────────────┤
│ - tenant_company_a_* (租户A数据)     │
│ - tenant_company_b_* (租户B数据)     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   ChromaDB (Vector Data)            │
├─────────────────────────────────────┤
│ - 知识库向量存储                      │
└─────────────────────────────────────┘
```

## 实施步骤

### 步骤1：创建 Supabase 项目

1. 访问 [Supabase](https://supabase.com) 创建新项目
2. 获取项目 URL 和 API Key
3. 配置环境变量：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
USE_SUPABASE_FOR_PLATFORM=true
```

### 步骤2：初始化数据库 Schema

1. 在 Supabase Dashboard 中打开 SQL Editor
2. 执行 `app/platform/supabase/schema.sql` 中的 SQL 脚本
3. 验证表创建成功

### 步骤3：配置应用

更新 `.env` 文件：

```env
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
USE_SUPABASE_FOR_PLATFORM=true

# MongoDB 配置（用于业务数据）
BUSINESS_MONGODB_DATABASE=tradingagents_business
```

### 步骤4：数据迁移

#### 方式1：使用 API 迁移

```bash
POST /api/platform/supabase/migrate
{
  "migrate_users": true,
  "migrate_tenants": true,
  "migrate_configs": true
}
```

#### 方式2：使用迁移脚本

```python
from app.platform.supabase import get_migration

migration = get_migration()
results = await migration.migrate_all()
print(results)
```

### 步骤5：验证和切换

1. **验证数据一致性**：
   - 对比 MongoDB 和 Supabase 中的数据
   - 检查关键字段和关系

2. **性能测试**：
   - 测试查询性能
   - 测试写入性能
   - 测试并发访问

3. **切换应用代码**：
   - 确保 `USE_SUPABASE_FOR_PLATFORM=true`
   - 重启应用
   - 监控日志

## 代码使用

### 使用平台数据适配器（推荐）

```python
from app.platform.supabase.platform_data_adapter import get_platform_data_adapter

adapter = get_platform_data_adapter()

# 获取用户（自动选择 Supabase 或 MongoDB）
user = await adapter.get_user(user_id)

# 获取租户
tenant = await adapter.get_tenant(tenant_id)

# 创建用户
user_data = {
    "username": "user1",
    "email": "user1@example.com",
    "hashed_password": "...",
}
user = await adapter.create_user(user_data)
```

### 直接使用 Supabase 访问层

```python
from app.platform.supabase import get_supabase_access

supabase = get_supabase_access()

# 获取用户
user = await supabase.get_user_async(user_id)

# 列出租户
tenants = await supabase.list_tenants_async(status="active")
```

## 数据访问模式

### 平台数据 → Supabase

所有平台数据通过 `PlatformDataAdapter` 访问，自动根据配置选择 Supabase 或 MongoDB：

- 用户数据
- 租户元数据
- 平台配置
- 计费数据

### 业务数据 → MongoDB

所有业务数据继续使用 MongoDB，通过 `DataAccessLayer` 访问：

- 租户用户数据
- 租户业务资源
- 租户业务数据

## 配置说明

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `SUPABASE_URL` | Supabase 项目 URL | 是 |
| `SUPABASE_KEY` | Supabase Anon Key | 是 |
| `SUPABASE_SERVICE_KEY` | Supabase Service Role Key | 否（用于管理操作） |
| `USE_SUPABASE_FOR_PLATFORM` | 是否启用 Supabase | 否（默认 false） |

### 配置优先级

1. 如果 `USE_SUPABASE_FOR_PLATFORM=true`，使用 Supabase
2. 否则，使用 MongoDB（平台数据库）

## 数据迁移

### 迁移流程

1. **准备阶段**：
   - 创建 Supabase 项目
   - 执行 Schema SQL
   - 配置环境变量

2. **迁移阶段**：
   - 运行迁移脚本
   - 验证数据完整性
   - 处理错误和异常

3. **验证阶段**：
   - 数据一致性检查
   - 功能测试
   - 性能测试

4. **切换阶段**：
   - 启用 Supabase
   - 监控运行状态
   - 逐步切换流量

### 迁移脚本

```python
from app.platform.supabase import get_migration

# 完整迁移
migration = get_migration()
results = await migration.migrate_all()

# 分步迁移
await migration.migrate_users()
await migration.migrate_tenants()
await migration.migrate_configs()
```

## 回滚方案

如果迁移后出现问题，可以快速回滚：

1. 设置 `USE_SUPABASE_FOR_PLATFORM=false`
2. 重启应用
3. 应用将自动使用 MongoDB

## 监控和维护

### 健康检查

```bash
GET /api/platform/supabase/health
```

返回：
```json
{
  "healthy": true,
  "enabled": true
}
```

### 日志监控

- Supabase 操作日志
- 迁移进度日志
- 错误和异常日志

### 性能监控

- 查询响应时间
- 写入性能
- 连接池使用情况

## 常见问题

### Q: 如何切换回 MongoDB？

A: 设置 `USE_SUPABASE_FOR_PLATFORM=false` 并重启应用。

### Q: 数据迁移失败怎么办？

A: 检查 Supabase 连接和权限，查看错误日志，修复后重新迁移。

### Q: 如何验证数据迁移成功？

A: 使用数据对比脚本，检查关键数据的数量和内容。

### Q: Supabase 连接失败怎么办？

A: 检查网络连接、URL 和 Key 配置，确保 Supabase 项目正常运行。

## 总结

通过实施方案一，平台数据完全迁移到 Supabase，获得以下优势：

1. ✅ **关系型数据支持**：PostgreSQL 完美支持平台数据
2. ✅ **认证系统**：利用 Supabase Auth 简化认证
3. ✅ **实时功能**：Supabase Realtime 支持状态更新
4. ✅ **自动备份**：Supabase 自动备份和恢复
5. ✅ **开发效率**：自动生成 API 和类型定义

业务数据保留在 MongoDB，充分利用文档型数据库的优势。

