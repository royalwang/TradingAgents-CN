# 数据源管理文档

## 概述

数据源管理模块提供了统一的数据源注册、管理和查询能力，支持多数据源的优先级管理和自动fallback机制。

## 核心功能

### 1. 数据源注册

数据源通过工厂模式自动注册：

```python
from app.platform.data_sources import get_factory

factory = get_factory()
# 自动注册现有适配器（Tushare、AKShare、BaoStock）
```

### 2. 数据源查询

支持多种查询方式：

```python
from app.platform.data_sources import get_manager

manager = get_manager()

# 获取股票列表
df, source = await manager.get_stock_list(market="A股")

# 获取每日基础数据
df, source = await manager.get_daily_basic("20250101", market="A股")

# 获取实时行情
quotes, source = await manager.get_realtime_quotes()

# 获取K线数据
kline, source = await manager.get_kline("000001", period="day", limit=120)

# 获取新闻数据
news, source = await manager.get_news("000001", days=2, limit=50)
```

### 3. 优先级管理

支持指定优先数据源：

```python
# 指定优先使用AKShare，如果失败则fallback到其他数据源
df, source = await manager.get_stock_list(
    market="A股",
    preferred_sources=["akshare", "tushare"]
)
```

## 支持的数据源

### Tushare
- **优先级**: 3（最高）
- **支持市场**: A股
- **支持功能**: 股票列表、每日基础数据、实时行情、K线、新闻

### AKShare
- **优先级**: 2
- **支持市场**: A股、港股、美股
- **支持功能**: 股票列表、每日基础数据、实时行情、K线、新闻

### BaoStock
- **优先级**: 1
- **支持市场**: A股
- **支持功能**: 股票列表、每日基础数据、K线

## API接口

### 数据源管理

- `GET /api/platform/data-sources` - 列出所有数据源
- `GET /api/platform/data-sources/{source_id}` - 获取数据源详情
- `POST /api/platform/data-sources/{source_id}/check` - 检查数据源可用性
- `POST /api/platform/data-sources/check-all` - 检查所有数据源可用性

### 数据查询

- `POST /api/platform/data-sources/stock-list` - 获取股票列表
- `POST /api/platform/data-sources/daily-basic` - 获取每日基础数据
- `POST /api/platform/data-sources/realtime-quotes` - 获取实时行情
- `POST /api/platform/data-sources/kline` - 获取K线数据
- `POST /api/platform/data-sources/news` - 获取新闻数据

## 使用示例

### Python代码示例

```python
from app.platform.data_sources import get_manager, get_factory

# 初始化（自动注册现有适配器）
factory = get_factory()

# 获取管理器
manager = get_manager()

# 获取股票列表
df, source = await manager.get_stock_list(market="A股")
print(f"从 {source} 获取到 {len(df)} 只股票")

# 获取每日基础数据
df, source = await manager.get_daily_basic(
    trade_date="20250101",
    preferred_sources=["tushare", "akshare"]
)

# 获取实时行情
quotes, source = await manager.get_realtime_quotes()
print(f"从 {source} 获取到 {len(quotes)} 只股票的实时行情")
```

### API调用示例

```bash
# 列出所有数据源
curl -X GET "http://localhost:8000/api/platform/data-sources"

# 获取股票列表
curl -X POST "http://localhost:8000/api/platform/data-sources/stock-list" \
  -H "Content-Type: application/json" \
  -d '{"market": "A股", "preferred_sources": ["akshare"]}'

# 获取每日基础数据
curl -X POST "http://localhost:8000/api/platform/data-sources/daily-basic" \
  -H "Content-Type: application/json" \
  -d '{"trade_date": "20250101", "market": "A股"}'

# 获取K线数据
curl -X POST "http://localhost:8000/api/platform/data-sources/kline" \
  -H "Content-Type: application/json" \
  -d '{"code": "000001", "period": "day", "limit": 120}'
```

## 注册自定义数据源

```python
from app.platform.data_sources import get_factory
from app.services.data_sources.base import DataSourceAdapter

class MyDataSourceAdapter(DataSourceAdapter):
    @property
    def name(self) -> str:
        return "my_source"
    
    def is_available(self) -> bool:
        return True
    
    # 实现其他必需方法...

# 注册数据源
factory = get_factory()
factory.register_adapter(
    source_id="my_source",
    name="my_source",
    display_name="我的数据源",
    adapter_class=MyDataSourceAdapter,
    description="自定义数据源",
    priority=2,
    supported_markets=["A股"],
    supported_features=["stock_list", "daily_basic"],
)
```

## Fallback机制

数据源管理器实现了智能fallback机制：

1. **按优先级尝试**：按配置的优先级顺序尝试各个数据源
2. **自动切换**：如果某个数据源失败，自动切换到下一个
3. **优先数据源**：支持指定优先使用的数据源列表
4. **可用性检查**：自动检查数据源可用性并更新状态

## 与现有系统集成

数据源管理模块与现有的`DataSourceManager`完全兼容：

- 使用相同的数据源适配器接口
- 支持相同的查询方法
- 保持向后兼容

## 总结

数据源管理模块提供了统一、灵活的数据源管理能力，支持多数据源的优先级管理和自动fallback，为平台提供了强大的数据获取能力。

