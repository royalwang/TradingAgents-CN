# MongoDB 存储规划

## 概述

平台使用 MongoDB 作为主要的数据存储，数据库名称为 `tradingagents`。本文档详细说明了所有集合的用途、数据结构和索引规划。

## 数据库配置

- **数据库名称**: `tradingagents`
- **连接方式**: 异步 (Motor) + 同步 (PyMongo)
- **连接池配置**:
  - 最小连接数: 10
  - 最大连接数: 100
  - 连接超时: 30秒
  - 套接字超时: 60秒
  - 服务器选择超时: 5秒

## 集合分类

### 1. 用户与权限管理

#### `users`
**用途**: 存储用户基本信息

**数据结构**:
```json
{
  "_id": ObjectId,
  "username": "string (unique)",
  "email": "string (unique)",
  "password_hash": "string",
  "role": "admin|user",
  "preferences": {
    "default_market": "A股",
    "default_llm_provider": "dashscope",
    "default_llm_model": "qwen-max"
  },
  "created_at": ISODate,
  "updated_at": ISODate,
  "last_login": ISODate
}
```

**索引**:
- `username`: 唯一索引
- `email`: 唯一索引

#### `user_sessions`
**用途**: 存储用户会话信息

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "session_token": "string",
  "expires_at": ISODate,
  "created_at": ISODate
}
```

**索引**:
- `user_id`: 普通索引
- `session_token`: 唯一索引

#### `user_activities`
**用途**: 记录用户活动日志

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "action": "string",
  "resource": "string",
  "details": {},
  "created_at": ISODate
}
```

**索引**:
- `(user_id, created_at)`: 复合索引（降序）

---

### 2. 股票数据

#### `stock_basic_info`
**用途**: 存储股票基础信息（支持多数据源）

**数据结构**:
```json
{
  "_id": ObjectId,
  "code": "600036",
  "name": "招商银行",
  "market": "A股",
  "source": "tushare|akshare|baostock",
  "industry": "银行",
  "area": "深圳",
  "list_date": "2002-04-09",
  "status": "L|D|P",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `(code, source)`: 联合唯一索引
- `code`: 普通索引（查询所有数据源）
- `source`: 普通索引
- `market`: 普通索引

#### `market_quotes`
**用途**: 存储实时/准实时行情快照（全市场最新行情）

**数据结构**:
```json
{
  "_id": ObjectId,
  "code": "600036 (unique)",
  "close": 46.50,
  "open": 45.23,
  "high": 46.78,
  "low": 45.01,
  "pre_close": 45.42,
  "pct_chg": 2.38,
  "amount": 567890123.45,
  "volume": 12345678,
  "trade_date": "20251017",
  "updated_at": ISODate
}
```

**索引**:
- `code`: 唯一索引
- `updated_at`: 普通索引

**更新频率**: 每30秒（交易时段）

#### `stock_daily_quotes`
**用途**: 存储历史K线数据（日/周/月/分钟线）

**数据结构**:
```json
{
  "_id": ObjectId,
  "symbol": "600036",
  "trade_date": "20251017",
  "data_source": "tushare|akshare|baostock",
  "period": "day|week|month|1min|5min|15min|30min|60min",
  "open": 45.23,
  "high": 46.78,
  "low": 45.01,
  "close": 46.50,
  "volume": 12345678,
  "amount": 567890123.45,
  "created_at": ISODate
}
```

**索引**:
- `(symbol, trade_date, data_source, period)`: 联合唯一索引
- `symbol`: 普通索引
- `trade_date`: 普通索引
- `(symbol, trade_date)`: 复合索引

**数据量**: 数百万条（每只股票数百条历史记录）

#### `stock_financial_data`
**用途**: 存储财务数据

**数据结构**:
```json
{
  "_id": ObjectId,
  "code": "600036",
  "report_date": "20250930",
  "data_source": "tushare",
  "financial_metrics": {
    "revenue": 1234567890.12,
    "net_profit": 123456789.01,
    "total_assets": 9876543210.98
  },
  "created_at": ISODate
}
```

**索引**:
- `(code, report_date, data_source)`: 联合唯一索引
- `code`: 普通索引
- `report_date`: 普通索引

---

### 3. 分析任务与报告

#### `analysis_tasks`
**用途**: 存储分析任务状态和进度

**数据结构**:
```json
{
  "_id": ObjectId,
  "task_id": "string (unique)",
  "user_id": "string",
  "symbol": "600036",
  "status": "pending|processing|completed|failed",
  "progress": 0-100,
  "message": "string",
  "current_step": "string",
  "parameters": {
    "analysts": ["market", "fundamentals"],
    "research_depth": "标准|深度|极深",
    "llm_provider": "dashscope",
    "llm_model": "qwen-max"
  },
  "created_at": ISODate,
  "updated_at": ISODate,
  "completed_at": ISODate
}
```

**索引**:
- `task_id`: 唯一索引
- `(user_id, created_at)`: 复合索引（降序）
- `status`: 普通索引
- `symbol`: 普通索引

#### `analysis_reports`
**用途**: 存储分析报告内容

**数据结构**:
```json
{
  "_id": ObjectId,
  "analysis_id": "string (unique)",
  "task_id": "string",
  "user_id": "string",
  "symbol": "600036",
  "title": "string",
  "content": "string (markdown)",
  "summary": "string",
  "sections": [
    {
      "title": "市场分析",
      "content": "string"
    }
  ],
  "metadata": {
    "analysts": ["market", "fundamentals"],
    "research_depth": "标准",
    "llm_provider": "dashscope",
    "llm_model": "qwen-max"
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `analysis_id`: 唯一索引
- `task_id`: 普通索引
- `user_id`: 普通索引
- `symbol`: 普通索引
- `created_at`: 普通索引（降序）

#### `analysis_progress`
**用途**: 存储分析进度详情（可选，用于详细进度追踪）

**数据结构**:
```json
{
  "_id": ObjectId,
  "task_id": "string",
  "step": "string",
  "progress": 0-100,
  "message": "string",
  "timestamp": ISODate
}
```

**索引**:
- `task_id`: 普通索引
- `timestamp`: 普通索引

---

### 4. 平台配置

#### `system_configs`
**用途**: 存储系统配置（新格式，包含LLM配置）

**数据结构**:
```json
{
  "_id": ObjectId,
  "config_name": "默认配置",
  "config_type": "system|user",
  "llm_configs": [
    {
      "provider": "OPENAI",
      "model_name": "gpt-3.5-turbo",
      "api_key": "sk-xxx",
      "api_base": "https://api.openai.com/v1",
      "max_tokens": 4000,
      "temperature": 0.7,
      "enabled": true
    }
  ],
  "data_source_configs": [],
  "database_configs": [],
  "system_settings": {
    "max_concurrent_tasks": 3,
    "enable_cache": true,
    "cache_ttl": 3600
  },
  "created_at": ISODate,
  "updated_at": ISODate,
  "version": 1,
  "is_active": true
}
```

**索引**:
- `config_name`: 普通索引
- `is_active`: 普通索引

#### `llm_providers`
**用途**: 存储LLM提供商信息（平台模块管理）

**数据结构**:
```json
{
  "_id": ObjectId,
  "name": "dashscope",
  "display_name": "阿里云通义千问",
  "description": "string",
  "website": "https://dashscope.aliyun.com",
  "api_doc_url": "string",
  "logo_url": "string",
  "is_active": true,
  "supported_features": ["chat", "completion", "embedding"],
  "default_base_url": "https://dashscope.aliyuncs.com/api/v1",
  "is_aggregator": false,
  "aggregator_type": null,
  "model_name_format": "{model}",
  "extra_config": {},
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `name`: 唯一索引
- `is_active`: 普通索引

#### `model_config`
**用途**: 存储模型配置

**数据结构**:
```json
{
  "_id": ObjectId,
  "provider": "dashscope",
  "model_name": "qwen-plus-latest",
  "display_name": "通义千问 Plus",
  "enabled": true,
  "is_default": true,
  "config": {
    "max_tokens": 8000,
    "temperature": 0.7
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `(provider, model_name)`: 联合唯一索引
- `enabled`: 普通索引
- `is_default`: 普通索引

#### `platform_configs`
**用途**: 存储平台配置（平台模块相关配置）

**数据结构**:
```json
{
  "_id": ObjectId,
  "config_key": "string",
  "config_value": {},
  "config_type": "string",
  "description": "string",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `config_key`: 唯一索引

#### `user_configs`
**用途**: 存储用户个性化配置

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "config_key": "string",
  "config_value": {},
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `(user_id, config_key)`: 联合唯一索引
- `user_id`: 普通索引

---

### 5. 数据源与同步

#### `sync_status`
**用途**: 记录数据同步状态

**数据结构**:
```json
{
  "_id": ObjectId,
  "data_source": "tushare|akshare|baostock",
  "data_type": "stock_basic|daily_quotes|financial",
  "last_sync_time": ISODate,
  "sync_status": "success|failed|running",
  "error_message": "string",
  "records_count": 12345,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `(data_source, data_type)`: 联合唯一索引
- `last_sync_time`: 普通索引
- `sync_status`: 普通索引

---

### 6. 筛选与标签

#### `screening_results`
**用途**: 存储筛选结果

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "screening_id": "string",
  "criteria": {},
  "results": ["600036", "000001"],
  "created_at": ISODate
}
```

**索引**:
- `screening_id`: 唯一索引
- `user_id`: 普通索引
- `created_at`: 普通索引

#### `favorites`
**用途**: 存储用户自选股

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "symbol": "600036",
  "category": "自选|关注",
  "created_at": ISODate
}
```

**索引**:
- `(user_id, symbol)`: 联合唯一索引
- `user_id`: 普通索引
- `symbol`: 普通索引

#### `tags`
**用途**: 存储标签信息

**数据结构**:
```json
{
  "_id": ObjectId,
  "tag_name": "string",
  "tag_type": "stock|user|analysis",
  "color": "string",
  "created_at": ISODate
}
```

**索引**:
- `tag_name`: 唯一索引
- `tag_type`: 普通索引

---

### 7. 新闻与消息

#### `stock_news`
**用途**: 存储股票新闻

**数据结构**:
```json
{
  "_id": ObjectId,
  "code": "600036",
  "title": "string",
  "content": "string",
  "source": "string",
  "url": "string",
  "published_at": ISODate,
  "created_at": ISODate
}
```

**索引**:
- `(code, published_at)`: 复合索引（降序）
- `code`: 普通索引
- `published_at`: 普通索引

#### `social_media_messages`
**用途**: 存储社媒消息

**数据结构**:
```json
{
  "_id": ObjectId,
  "message_id": "string",
  "platform": "weibo|twitter|xueqiu",
  "symbol": "600036",
  "content": "string",
  "author": "string",
  "publish_time": ISODate,
  "message_type": "post|comment|retweet",
  "sentiment": "positive|neutral|negative",
  "importance": "high|medium|low",
  "created_at": ISODate
}
```

**索引**:
- `(message_id, platform)`: 联合唯一索引
- `symbol`: 普通索引
- `publish_time`: 普通索引（降序）
- `platform`: 普通索引
- `message_type`: 普通索引
- `(platform, message_type)`: 复合索引

---

### 8. 使用统计

#### `usage_statistics`
**用途**: 存储使用统计信息

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "date": "2025-10-17",
  "statistics": {
    "analysis_count": 10,
    "api_calls": 100,
    "tokens_used": 50000
  },
  "created_at": ISODate
}
```

**索引**:
- `(user_id, date)`: 联合唯一索引
- `user_id`: 普通索引
- `date`: 普通索引

#### `token_usage`
**用途**: 存储Token使用记录（如果使用MongoDB存储）

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "provider": "dashscope",
  "model": "qwen-max",
  "tokens": 1000,
  "cost": 0.01,
  "timestamp": ISODate
}
```

**索引**:
- `(user_id, timestamp)`: 复合索引（降序）
- `timestamp`: 普通索引
- `provider`: 普通索引

---

### 9. 操作日志

#### `operation_logs`
**用途**: 存储操作日志

**数据结构**:
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "action": "string",
  "resource": "string",
  "details": {},
  "ip_address": "string",
  "user_agent": "string",
  "created_at": ISODate
}
```

**索引**:
- `created_at`: 普通索引（降序）
- `user_id`: 普通索引
- `action`: 普通索引

---

### 10. 市场分类

#### `market_categories`
**用途**: 存储市场分类配置

**数据结构**:
```json
{
  "_id": ObjectId,
  "category_name": "A股",
  "category_code": "A",
  "description": "string",
  "markets": ["上海", "深圳"],
  "created_at": ISODate
}
```

**索引**:
- `category_code`: 唯一索引
- `category_name`: 普通索引

#### `datasource_groupings`
**用途**: 存储数据源分组配置

**数据结构**:
```json
{
  "_id": ObjectId,
  "group_name": "string",
  "data_sources": ["tushare", "akshare"],
  "priority": 1,
  "created_at": ISODate
}
```

**索引**:
- `group_name`: 唯一索引

---

### 11. 模型目录

#### `model_catalog`
**用途**: 存储模型目录信息

**数据结构**:
```json
{
  "_id": ObjectId,
  "provider": "dashscope",
  "model_id": "string",
  "model_name": "qwen-max",
  "display_name": "通义千问 Max",
  "capabilities": ["chat", "completion"],
  "max_tokens": 8000,
  "pricing": {
    "input": 0.001,
    "output": 0.002
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:
- `(provider, model_id)`: 联合唯一索引
- `provider`: 普通索引

---

## 数据存储策略

### 1. 数据分片策略

- **按市场分片**: 不同市场的股票数据可以分片存储
- **按时间分片**: 历史数据可以按年份/月份分片
- **按数据源分片**: 不同数据源的数据可以分片存储

### 2. 数据归档策略

- **热数据**: 最近3个月的数据，存储在主要集合中
- **温数据**: 3-12个月的数据，可以存储在归档集合中
- **冷数据**: 12个月以上的数据，可以压缩存储或迁移到对象存储

### 3. 数据清理策略

- **任务数据**: 完成的分析任务保留30天，失败任务保留7天
- **日志数据**: 操作日志保留90天
- **临时数据**: 临时计算结果保留24小时

### 4. 索引优化策略

- **唯一索引**: 用于防止重复数据
- **复合索引**: 用于多字段查询优化
- **TTL索引**: 用于自动清理过期数据
- **文本索引**: 用于全文搜索（如新闻、报告内容）

## 性能优化建议

1. **连接池管理**: 合理配置连接池大小，避免连接泄漏
2. **查询优化**: 使用投影减少数据传输，使用索引优化查询
3. **批量操作**: 使用批量插入/更新减少网络往返
4. **读写分离**: 对于读多写少的场景，考虑使用副本集
5. **分片集群**: 当数据量超过单机容量时，考虑使用分片集群

## 备份与恢复

1. **定期备份**: 每日全量备份 + 每小时增量备份
2. **备份存储**: 备份文件存储在对象存储或专用备份服务器
3. **恢复测试**: 定期测试备份恢复流程
4. **监控告警**: 监控数据库健康状态，异常时及时告警

## 安全考虑

1. **访问控制**: 使用MongoDB的RBAC进行权限控制
2. **数据加密**: 敏感数据（如API密钥）加密存储
3. **审计日志**: 记录所有数据库操作日志
4. **网络安全**: 使用TLS加密传输，限制网络访问

## 总结

MongoDB存储规划涵盖了平台的所有数据需求，包括：
- ✅ 用户与权限管理
- ✅ 股票数据（基础信息、行情、财务）
- ✅ 分析任务与报告
- ✅ 平台配置
- ✅ 数据源同步
- ✅ 筛选与标签
- ✅ 新闻与消息
- ✅ 使用统计
- ✅ 操作日志

通过合理的索引设计和数据分片策略，可以确保系统的高性能和高可用性。

