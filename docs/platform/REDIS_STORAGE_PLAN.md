# Redis 存储规划

## 概述

平台使用 Redis 作为高性能缓存、队列管理和实时数据存储。Redis 主要用于临时数据、会话管理、任务队列和实时状态追踪。

## Redis 配置

- **连接方式**: 异步 (redis.asyncio)
- **连接池配置**:
  - 最大连接数: 20 (可配置)
  - TCP Keepalive: 启用
  - 健康检查间隔: 30秒
  - 重试超时: 启用
- **数据编码**: UTF-8 (decode_responses=True)

## 键命名规范

所有Redis键使用统一的命名规范：
- 使用冒号 `:` 作为分隔符
- 使用前缀区分不同功能模块
- 使用模板变量 `{variable}` 表示动态部分

## 数据结构分类

### 1. 队列管理

#### 用户队列
```
键名: user:{user_id}:pending
类型: LIST
用途: 用户待处理任务队列
值: JSON序列化的任务对象
操作: LPUSH (入队), BRPOP (出队)
TTL: 无（队列数据）
```

#### 用户处理中集合
```
键名: user:{user_id}:processing
类型: SET
用途: 用户正在处理的任务ID集合
值: task_id列表
操作: SADD, SREM, SMEMBERS
TTL: 无（任务完成时删除）
```

#### 全局队列
```
键名: global:pending
类型: LIST
用途: 全局待处理任务队列
值: JSON序列化的任务对象
操作: LPUSH, BRPOP
TTL: 无
```

#### 全局处理中集合
```
键名: global:processing
类型: SET
用途: 全局正在处理的任务ID集合
值: task_id列表
操作: SADD, SREM
TTL: 无
```

#### 队列统计
```
键名: queue:stats
类型: HASH
用途: 队列统计信息
字段:
  - total_pending: 总待处理数
  - total_processing: 总处理中数
  - total_completed: 总完成数
  - total_failed: 总失败数
操作: HSET, HGET, HGETALL
TTL: 无
```

### 2. 任务管理

#### 任务进度
```
键名: task:{task_id}:progress
类型: STRING (JSON)
用途: 任务进度信息
值: {
  "progress": 0-100,
  "message": "当前步骤",
  "current_step": "步骤名称",
  "updated_at": "ISO时间戳"
}
操作: SET, GET
TTL: 3600秒（1小时）
```

#### 任务结果
```
键名: task:{task_id}:result
类型: STRING (JSON)
用途: 任务执行结果
值: {
  "status": "completed|failed",
  "result": {},
  "error": "错误信息",
  "completed_at": "ISO时间戳"
}
操作: SET, GET
TTL: 86400秒（24小时）
```

#### 任务锁
```
键名: task:{task_id}:lock
类型: STRING
用途: 任务分布式锁
值: UUID (锁标识)
操作: SET NX EX (获取锁), DEL (释放锁)
TTL: 30秒（自动过期）
```

### 3. 批次管理

#### 批次进度
```
键名: batch:{batch_id}:progress
类型: STRING (JSON)
用途: 批次整体进度
值: {
  "total": 100,
  "completed": 50,
  "failed": 2,
  "progress": 50,
  "updated_at": "ISO时间戳"
}
操作: SET, GET
TTL: 7200秒（2小时）
```

#### 批次任务列表
```
键名: batch:{batch_id}:tasks
类型: SET
用途: 批次包含的任务ID集合
值: task_id列表
操作: SADD, SMEMBERS, SCARD
TTL: 86400秒（24小时）
```

#### 批次锁
```
键名: batch:{batch_id}:lock
类型: STRING
用途: 批次操作分布式锁
值: UUID
操作: SET NX EX, DEL
TTL: 60秒
```

### 4. 用户会话与认证

#### 用户会话
```
键名: session:{session_id}
类型: STRING (JSON)
用途: 用户会话信息
值: {
  "user_id": "用户ID",
  "username": "用户名",
  "role": "admin|user",
  "created_at": "ISO时间戳",
  "last_activity": "ISO时间戳"
}
操作: SET, GET, DEL
TTL: 86400秒（24小时，可配置）
```

#### 速率限制
```
键名: rate_limit:{user_id}:{endpoint}
类型: STRING (整数)
用途: 用户API调用速率限制计数
值: 调用次数
操作: INCR, EXPIRE
TTL: 60秒（每分钟重置）
```

#### 每日配额
```
键名: quota:{user_id}:{date}
类型: STRING (整数)
用途: 用户每日配额使用量
值: 已使用配额数
操作: INCR, GET
TTL: 86400秒（24小时，每日重置）
```

### 5. 缓存数据

#### 筛选结果缓存
```
键名: screening:{cache_key}
类型: STRING (JSON)
用途: 股票筛选结果缓存
值: {
  "criteria": {},
  "results": ["600036", "000001"],
  "count": 2,
  "created_at": "ISO时间戳"
}
操作: SET, GET
TTL: 3600秒（1小时）
```

#### 分析结果缓存
```
键名: analysis:{cache_key}
类型: STRING (JSON)
用途: 分析结果缓存
值: {
  "symbol": "600036",
  "analysis_type": "comprehensive",
  "result": {},
  "created_at": "ISO时间戳"
}
操作: SET, GET
TTL: 7200秒（2小时）
```

#### 系统配置缓存
```
键名: system:config
类型: STRING (JSON)
用途: 系统配置缓存
值: {
  "max_concurrent_tasks": 3,
  "enable_cache": true,
  "cache_ttl": 3600,
  ...
}
操作: SET, GET
TTL: 无（手动更新）
```

### 6. Worker管理

#### Worker心跳
```
键名: worker:{worker_id}:heartbeat
类型: STRING (JSON)
用途: Worker心跳信息
值: {
  "worker_id": "worker_001",
  "status": "active|idle|busy",
  "current_task": "task_id",
  "last_heartbeat": "ISO时间戳"
}
操作: SET
TTL: 60秒（超时视为离线）
```

### 7. 通知与PubSub

#### 通知频道
```
频道名: notifications:{user_id}
类型: PUBSUB
用途: 用户实时通知推送
消息格式: {
  "type": "task_completed|task_failed|system_notification",
  "data": {},
  "timestamp": "ISO时间戳"
}
操作: PUBLISH, SUBSCRIBE
TTL: 无
```

#### 任务状态频道
```
频道名: task:{task_id}:status
类型: PUBSUB
用途: 任务状态变更通知
消息格式: {
  "task_id": "task_001",
  "status": "processing|completed|failed",
  "progress": 50,
  "message": "当前步骤"
}
操作: PUBLISH, SUBSCRIBE
TTL: 无
```

### 8. 并发控制

#### 用户并发计数
```
键名: qa:user_processing:{user_id}
类型: STRING (整数)
用途: 用户当前并发任务数
值: 并发数
操作: INCR, DECR
TTL: 无（任务完成时删除）
```

#### 全局并发计数
```
键名: qa:global_concurrent
类型: STRING (整数)
用途: 全局当前并发任务数
值: 并发数
操作: INCR, DECR
TTL: 无
```

#### 可见性超时
```
键名: qa:visibility:{task_id}
类型: STRING (时间戳)
用途: 任务可见性超时时间
值: Unix时间戳
操作: SET, GET, DEL
TTL: 300秒（5分钟）
```

## TTL策略

### 短期数据（< 1小时）
- 任务进度: 3600秒
- 速率限制: 60秒
- Worker心跳: 60秒

### 中期数据（1-24小时）
- 任务结果: 86400秒
- 用户会话: 86400秒
- 每日配额: 86400秒
- 批次任务: 86400秒

### 长期数据（无TTL）
- 队列数据: 无（任务完成时删除）
- 系统配置: 无（手动更新）
- 处理中集合: 无（任务完成时删除）

## 数据持久化策略

### RDB快照
- **频率**: 每5分钟或至少1000次写操作
- **用途**: 定期备份Redis数据
- **位置**: 配置的持久化目录

### AOF追加
- **模式**: everysec（每秒同步）
- **用途**: 记录所有写操作
- **优势**: 更好的数据安全性

## 内存管理

### 最大内存
- **配置**: 根据服务器内存设置
- **策略**: allkeys-lru（最近最少使用）
- **监控**: 定期检查内存使用率

### 键过期
- **自动清理**: Redis自动删除过期键
- **清理频率**: 每100ms检查一次
- **内存回收**: 惰性删除 + 定期删除

## 性能优化建议

1. **连接池管理**: 合理配置连接池大小，避免连接泄漏
2. **管道操作**: 使用Pipeline批量操作减少网络往返
3. **键名优化**: 使用短键名减少内存占用
4. **数据结构选择**: 根据场景选择合适的数据结构
5. **TTL设置**: 合理设置TTL避免内存泄漏

## 监控指标

### 关键指标
- **内存使用率**: 应 < 80%
- **连接数**: 应 < 最大连接数的80%
- **命中率**: 缓存命中率应 > 90%
- **队列长度**: 监控队列积压情况

### 告警阈值
- 内存使用率 > 85%
- 连接数 > 最大连接数的90%
- 队列长度 > 1000
- 响应时间 > 100ms

## 备份与恢复

### 备份策略
- **RDB备份**: 每日全量备份
- **AOF备份**: 实时追加
- **备份存储**: 备份文件存储在对象存储或专用备份服务器

### 恢复流程
1. 停止Redis服务
2. 恢复RDB或AOF文件
3. 启动Redis服务
4. 验证数据完整性

## 安全考虑

1. **访问控制**: 使用密码认证
2. **网络隔离**: 限制Redis端口访问
3. **命令重命名**: 禁用危险命令（如FLUSHALL）
4. **TLS加密**: 生产环境使用TLS加密传输

## 总结

Redis存储规划涵盖了平台的所有临时数据和实时状态需求：
- ✅ 队列管理（用户队列、全局队列）
- ✅ 任务管理（进度、结果、锁）
- ✅ 批次管理（进度、任务列表）
- ✅ 用户会话与认证
- ✅ 缓存数据（筛选、分析、配置）
- ✅ Worker管理（心跳、状态）
- ✅ 通知与PubSub（实时推送）
- ✅ 并发控制（用户并发、全局并发）

通过合理的TTL设置和数据结构选择，可以确保Redis的高性能和高可用性。

