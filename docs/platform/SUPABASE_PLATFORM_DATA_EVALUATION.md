# 平台数据存储 Supabase 适用性评估

## 概述

本文档评估将平台数据存储迁移到 Supabase 的适用性，基于平台数据与业务数据分离架构，分析平台数据存储的特殊需求和 Supabase 的匹配度。

## 平台数据特点

### 数据规模
- **数据量**：相对较小，主要是元数据和配置
- **增长速率**：缓慢增长
- **访问频率**：中等频率
- **数据关系**：关系型数据为主

### 数据类型
1. **用户与认证数据**
   - 用户账户信息
   - 会话信息
   - 权限配置

2. **租户元数据**
   - 租户基本信息
   - 租户配置
   - 租户状态

3. **系统配置**
   - 平台配置
   - LLM提供商配置
   - 数据源配置

4. **平台资源**
   - 智能体模板
   - 工作流模板
   - 插件定义

5. **计费数据**
   - 计费方案
   - 计费记录
   - 发票

6. **审计日志**
   - 操作日志
   - 系统日志

## Supabase 优势分析

### ✅ 适合平台数据的方面

#### 1. 关系型数据结构
**优势**：
- 平台数据主要是关系型数据（用户-租户-配置）
- Supabase 基于 PostgreSQL，关系型数据支持完善
- 外键约束、事务支持良好

**示例**：
```sql
-- 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  email VARCHAR(255) UNIQUE,
  tenant_id UUID REFERENCES tenants(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 租户表
CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  tenant_id VARCHAR(50) UNIQUE,
  name VARCHAR(255),
  tier VARCHAR(20),
  status VARCHAR(20)
);
```

#### 2. 实时功能
**优势**：
- Supabase Realtime 可以实时推送平台状态变化
- 适合租户状态更新、配置变更通知

**使用场景**：
- 租户状态变更实时通知
- 系统配置更新广播
- 计费状态变化通知

#### 3. 认证和授权
**优势**：
- Supabase Auth 提供完整的认证系统
- Row Level Security (RLS) 支持细粒度权限控制
- 与平台的多租户架构匹配

**示例**：
```sql
-- RLS策略：用户只能访问自己租户的数据
CREATE POLICY tenant_isolation ON users
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

#### 4. 数据备份和恢复
**优势**：
- Supabase 自动备份（每日）
- 时间点恢复（PITR）
- 备份管理简单

#### 5. 开发效率
**优势**：
- 自动生成 REST API
- 自动生成 TypeScript 类型
- 减少后端代码量

### ⚠️ 需要注意的方面

#### 1. 审计日志存储
**挑战**：
- 审计日志数据量大，增长快
- 需要高效的查询和归档
- Supabase 存储成本可能较高

**建议**：
- 使用 Supabase 存储近期日志（如最近3个月）
- 历史日志迁移到对象存储（Supabase Storage 或 S3）
- 或使用专门的日志服务

#### 2. 复杂查询性能
**挑战**：
- 平台数据查询相对简单
- 但如果需要复杂聚合查询，PostgreSQL 性能良好

**建议**：
- 合理设计索引
- 使用物化视图优化复杂查询
- 利用 PostgreSQL 的查询优化器

#### 3. 向量数据存储
**挑战**：
- 如果平台知识库需要向量搜索
- Supabase 支持 pgvector 扩展

**优势**：
- Supabase 支持 pgvector
- 可以存储和查询向量数据

#### 4. 成本考虑
**挑战**：
- Supabase 按使用量计费
- 平台数据量小，成本可控
- 但需要评估长期成本

**成本估算**（基于 Supabase Pro 计划）：
- 数据库：$25/月起（包含 8GB 存储）
- 存储：$0.021/GB/月
- 带宽：$0.09/GB
- 平台数据预计：< 1GB，成本较低

## 架构适配方案

### 方案一：完全迁移到 Supabase（推荐用于平台数据）

```
┌─────────────────────────────────────┐
│      Supabase (Platform Data)        │
├─────────────────────────────────────┤
│ - users (用户)                       │
│ - tenants (租户)                     │
│ - platform_configs (平台配置)        │
│ - platform_agents (智能体模板)       │
│ - platform_workflows (工作流模板)    │
│ - billing_plans (计费方案)            │
│ - billing_records (计费记录)          │
│ - invoices (发票)                     │
│ - operation_logs (操作日志)            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   MongoDB (Business Data)            │
├─────────────────────────────────────┤
│ - tenant_company_a_* (租户A数据)     │
│ - tenant_company_b_* (租户B数据)     │
└─────────────────────────────────────┘
```

**优点**：
- 平台数据关系型，适合 PostgreSQL
- 利用 Supabase 的认证和授权功能
- 实时功能支持平台状态更新
- 业务数据保留在 MongoDB（文档型数据）

**缺点**：
- 需要维护两套数据库系统
- 跨数据库查询需要应用层处理

### 方案二：混合架构（平台核心数据 + 日志分离）

```
┌─────────────────────────────────────┐
│   Supabase (Core Platform Data)     │
├─────────────────────────────────────┤
│ - users                              │
│ - tenants                            │
│ - platform_configs                   │
│ - billing_*                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   MongoDB (Logs & Business Data)     │
├─────────────────────────────────────┤
│ - operation_logs (审计日志)          │
│ - tenant_* (业务数据)                │
└─────────────────────────────────────┘
```

**优点**：
- 核心平台数据使用 Supabase
- 日志数据保留在 MongoDB（更适合大量日志）
- 业务数据保留在 MongoDB

**缺点**：
- 数据分散在多个系统

## 数据迁移评估

### 迁移复杂度：低到中等

#### 简单迁移的数据
1. **用户数据**：直接映射到 Supabase Auth + users 表
2. **租户数据**：关系型数据，迁移简单
3. **配置数据**：JSON 字段，PostgreSQL 支持良好
4. **计费数据**：关系型数据，迁移简单

#### 需要转换的数据
1. **ObjectId → UUID**：MongoDB ObjectId 转换为 PostgreSQL UUID
2. **嵌套文档 → 关系表**：将嵌套文档拆分为关系表
3. **数组字段 → 关联表**：将数组字段转换为关联表

### 迁移脚本示例

```python
async def migrate_users_to_supabase():
    """迁移用户数据到 Supabase"""
    from supabase import create_client
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    mongo_db = get_mongo_db()
    
    # 从 MongoDB 读取用户
    users = mongo_db["users"].find({})
    
    async for user in users:
        # 转换数据格式
        supabase_user = {
            "id": str(user["_id"]),  # 或生成新 UUID
            "username": user["username"],
            "email": user["email"],
            "tenant_id": user.get("tenant_id"),
            "is_admin": user.get("is_admin", False),
            "created_at": user["created_at"].isoformat(),
        }
        
        # 插入 Supabase
        supabase.table("users").insert(supabase_user).execute()
```

## 功能对比

### 认证功能

| 功能 | MongoDB + 自建 | Supabase |
|------|---------------|----------|
| 用户注册/登录 | ✅ 需要自建 | ✅ 内置 |
| JWT Token | ✅ 需要自建 | ✅ 自动生成 |
| 社交登录 | ❌ 需要集成 | ✅ 内置支持 |
| 邮箱验证 | ❌ 需要自建 | ✅ 内置 |
| 密码重置 | ❌ 需要自建 | ✅ 内置 |
| 多因素认证 | ❌ 需要集成 | ✅ 内置 |

**优势**：Supabase Auth 可以显著减少认证相关代码

### 实时功能

| 功能 | MongoDB + 自建 | Supabase |
|------|---------------|----------|
| 实时订阅 | ❌ 需要 WebSocket | ✅ Realtime |
| 变更通知 | ❌ 需要自建 | ✅ 自动推送 |
| 在线状态 | ❌ 需要自建 | ✅ Presence |

**优势**：Supabase Realtime 可以简化实时功能实现

### 数据查询

| 功能 | MongoDB | Supabase (PostgreSQL) |
|------|---------|----------------------|
| 关系查询 | ⚠️ 需要应用层 | ✅ JOIN 支持 |
| 事务支持 | ✅ 支持 | ✅ 支持 |
| 复杂查询 | ⚠️ 有限 | ✅ SQL 强大 |
| 全文搜索 | ✅ 支持 | ✅ 支持 |
| 向量搜索 | ❌ 需要扩展 | ✅ pgvector |

## 性能评估

### 查询性能

**平台数据查询特点**：
- 主要是点查询（根据ID查询）
- 少量范围查询（时间范围、状态筛选）
- 简单聚合查询（统计、计数）

**Supabase 性能**：
- PostgreSQL 对关系型查询性能优秀
- 索引支持完善
- 查询优化器成熟

**预期性能**：✅ 优于或等于 MongoDB

### 写入性能

**平台数据写入特点**：
- 写入频率低
- 主要是配置更新、状态变更

**Supabase 性能**：
- PostgreSQL 写入性能良好
- 事务支持完善

**预期性能**：✅ 满足需求

## 成本分析

### Supabase 成本（平台数据）

**数据量估算**：
- 用户数据：< 100MB（假设10万用户）
- 租户数据：< 10MB（假设1000租户）
- 配置数据：< 50MB
- 计费数据：< 100MB（假设1年数据）
- 日志数据：< 500MB（假设3个月）
- **总计**：< 1GB

**Supabase Pro 计划**：
- 月费：$25
- 包含：8GB 数据库存储
- 带宽：50GB/月
- **平台数据完全在免费额度内**

### 对比：自建 MongoDB

**服务器成本**：
- 小型服务器：$20-50/月
- 备份存储：$5-10/月
- 维护成本：人工时间

**总成本**：$25-60/月 + 维护成本

**结论**：Supabase 成本可控，且包含备份、监控等附加服务

## 风险评估

### 低风险项

1. **数据丢失风险**：低
   - Supabase 自动备份
   - 时间点恢复支持

2. **性能风险**：低
   - 平台数据量小
   - PostgreSQL 性能优秀

3. **功能风险**：低
   - Supabase 功能完善
   - 满足平台数据需求

### 中等风险项

1. **供应商锁定**：中等
   - 使用标准 PostgreSQL
   - 可以导出数据迁移

2. **网络延迟**：中等
   - 如果 Supabase 服务器在国外
   - 国内用户可能有延迟
   - 建议：使用 Supabase 中国区（如果有）或自建

3. **成本增长**：中等
   - 如果数据量快速增长
   - 需要监控使用量

### 高风险项

1. **无**：平台数据存储迁移到 Supabase 风险较低

## 实施建议

### 推荐方案：平台数据迁移到 Supabase

**理由**：
1. ✅ 平台数据关系型，适合 PostgreSQL
2. ✅ Supabase Auth 可以简化认证系统
3. ✅ Supabase Realtime 支持实时功能
4. ✅ 成本可控，功能完善
5. ✅ 减少维护负担

### 实施步骤

#### 阶段1：准备（1周）
1. 创建 Supabase 项目
2. 设计数据库 Schema
3. 准备迁移脚本

#### 阶段2：并行运行（2-3周）
1. 同时写入 MongoDB 和 Supabase
2. 验证数据一致性
3. 性能测试

#### 阶段3：切换（1周）
1. 应用代码切换到 Supabase
2. 监控和优化
3. 停止 MongoDB 写入

#### 阶段4：清理（1周）
1. 数据归档
2. 清理旧代码
3. 文档更新

### 保留 MongoDB 的场景

**建议保留 MongoDB 用于**：
1. **业务数据**：租户的业务数据（文档型，适合 MongoDB）
2. **审计日志**：大量日志数据（MongoDB 更适合）
3. **向量数据**：如果使用 ChromaDB，保留独立向量数据库

## 总结

### ✅ 平台数据存储适合 Supabase

**核心优势**：
1. **数据结构匹配**：平台数据主要是关系型数据，PostgreSQL 非常适合
2. **功能完善**：认证、实时、API 自动生成等功能可以显著减少开发工作
3. **成本可控**：平台数据量小，Supabase Pro 计划完全覆盖
4. **维护简单**：自动备份、监控、更新等减少运维负担
5. **性能优秀**：PostgreSQL 对关系型查询性能优秀

**建议架构**：
- **Supabase**：平台核心数据（用户、租户、配置、计费）
- **MongoDB**：业务数据（租户业务数据、审计日志）
- **ChromaDB**：向量数据（知识库向量存储）

**迁移优先级**：
1. **高优先级**：用户认证数据（利用 Supabase Auth）
2. **中优先级**：租户元数据、配置数据
3. **低优先级**：审计日志（可保留在 MongoDB）

**结论**：平台数据存储迁移到 Supabase 是**推荐方案**，可以显著提升开发效率和系统稳定性，同时保持成本可控。

