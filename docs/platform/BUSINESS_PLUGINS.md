# 业务插件系统文档

## 概述

业务插件系统将业务能力抽象为插件，平台通过集成业务插件获得业务能力，实现"一人公司平台"的理念。每个业务插件封装了完整的业务逻辑、智能体配置、工具和工作流。

## 核心概念

### 业务插件（Business Plugin）

业务插件是一个自包含的业务能力单元，包含：

- **能力定义**：插件提供的能力类型（分析、交易、筛选等）
- **智能体配置**：使用的智能体及其配置
- **工具配置**：使用的工具及其配置
- **工作流配置**：业务工作流定义
- **数据模型**：输入输出数据模型
- **插件实现**：实际的业务逻辑代码

### 插件能力类型

- `ANALYSIS` - 分析能力
- `TRADING` - 交易能力
- `SCREENING` - 筛选能力
- `RESEARCH` - 研究能力
- `PREDICTION` - 预测能力
- `CUSTOM` - 自定义能力

## 股票分析业务插件

股票分析功能已封装为业务插件，位于 `app/platform/business/plugins/stock_analysis/`。

### 插件配置

```json
{
  "plugin_id": "stock_analysis",
  "name": "股票分析业务插件",
  "version": "1.0.0",
  "description": "提供股票分析业务能力",
  "capabilities": ["analysis"],
  "agents": [
    {
      "agent_id": "market_analyst",
      "agent_type": "analyst",
      "enabled": true
    },
    {
      "agent_id": "fundamentals_analyst",
      "agent_type": "analyst",
      "enabled": true
    }
  ]
}
```

### 插件实现

插件主模块实现了标准的插件接口：

```python
class StockAnalysisPlugin:
    async def activate(self, config):
        """激活插件"""
        pass
    
    async def deactivate(self):
        """停用插件"""
        pass
    
    async def execute(self, capability, input_data):
        """执行插件能力"""
        pass
```

## 使用方式

### 1. 发现和加载插件

```python
from app.platform.business import get_business_loader, get_business_manager

# 发现插件
loader = get_business_loader()
plugins = loader.discover_plugins()

# 加载插件
manager = get_business_manager()
for plugin in plugins:
    await manager.load_plugin(plugin.plugin_id)
```

### 2. 激活插件

```python
# 激活插件
await manager.activate_plugin("stock_analysis", config={})
```

### 3. 执行插件能力

```python
# 执行分析能力
result = await manager.execute_capability(
    capability=PluginCapability.ANALYSIS,
    input_data={
        "symbol": "AAPL",
        "analysis_date": "2025-01-01",
        "analysts": ["market", "fundamentals"],
    },
    plugin_id="stock_analysis",
)
```

## API接口

### 插件管理

- `GET /api/platform/business/plugins` - 列出所有业务插件
- `GET /api/platform/business/plugins/{plugin_id}` - 获取插件详情
- `POST /api/platform/business/plugins/{plugin_id}/activate` - 激活插件
- `POST /api/platform/business/plugins/{plugin_id}/deactivate` - 停用插件
- `POST /api/platform/business/plugins/{plugin_id}/execute` - 执行插件能力
- `POST /api/platform/business/plugins/discover` - 发现插件
- `POST /api/platform/business/plugins/register` - 注册插件

## 创建自定义业务插件

### 1. 创建插件目录结构

```
app/platform/business/plugins/my_plugin/
├── plugin.json          # 插件配置
└── main.py             # 插件实现
```

### 2. 定义插件配置

`plugin.json`:
```json
{
  "plugin_id": "my_plugin",
  "name": "我的业务插件",
  "version": "1.0.0",
  "description": "插件描述",
  "capabilities": ["custom"],
  "entry_point": "app.platform.business.plugins.my_plugin.main",
  "agents": [],
  "tools": [],
  "workflows": [],
  "data_models": []
}
```

### 3. 实现插件

`main.py`:
```python
from app.platform.business.business_plugin import PluginCapability

class MyPlugin:
    async def activate(self, config):
        """激活插件"""
        pass
    
    async def deactivate(self):
        """停用插件"""
        pass
    
    async def execute(self, capability, input_data):
        """执行插件能力"""
        if capability == PluginCapability.CUSTOM:
            # 实现业务逻辑
            return {"result": "success"}
        raise ValueError(f"Unsupported capability: {capability}")

def create_plugin():
    return MyPlugin()
```

## 平台架构

```
┌─────────────────────────────────────┐
│        智能体平台 (Platform)         │
│  - Agents管理                        │
│  - 知识库                            │
│  - 工作流编排                        │
│  - 插件系统                          │
└─────────────────────────────────────┘
              ↓ 集成
┌─────────────────────────────────────┐
│      业务插件系统 (Business)         │
│  - 股票分析插件                      │
│  - 其他业务插件...                   │
└─────────────────────────────────────┘
```

## 优势

1. **业务隔离**：业务能力与平台核心功能分离
2. **易于扩展**：新增业务只需创建新插件
3. **灵活配置**：每个插件独立配置和管理
4. **可复用性**：插件可在不同场景复用
5. **模块化**：插件包含完整的业务逻辑

## 总结

业务插件系统实现了"一人公司平台"的理念，将业务能力抽象为插件，平台通过集成插件获得业务能力。股票分析功能已成功封装为业务插件，可以作为其他业务插件的参考实现。

