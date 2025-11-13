# 平台声明式数据管理

## 概述

平台提供了统一的声明式数据管理框架，支持所有模块通过YAML格式进行配置的导入和导出。这使得平台配置可以版本化、可移植、易于管理。

## 架构设计

### 通用框架

平台提供了两个核心基类：

1. **`DeclarativeYAMLLoader`**: 通用YAML加载器基类
   - 支持从YAML文件、字符串、字典加载配置
   - 支持列表和对象两种YAML格式
   - 提供统一的导出功能

2. **`DeclarativeService`**: 通用声明式服务基类
   - 提供导入/导出功能
   - 支持批量操作
   - 支持更新现有配置

### 模块实现

以下模块已实现YAML声明式管理：

- **Agents (智能体)**: `app/platform/agents/yaml_loader.py`, `agent_service.py`
- **Workflows (工作流)**: `app/platform/workflow/yaml_loader.py`, `workflow_service.py`
- **Plugins (插件)**: `app/platform/plugins/yaml_loader.py`, `plugin_service.py`
- **Providers (LLM提供商)**: `app/platform/providers/yaml_loader.py`, `provider_service.py`
- **Data Sources (数据源)**: `app/platform/data_sources/yaml_loader.py`, `data_source_service.py`

## 使用方式

### 1. Agents (智能体)

#### 导入智能体配置

```bash
# 从YAML字符串导入
curl -X POST "http://localhost:8000/api/platform/agents/import/yaml" \
  -H "Content-Type: application/json" \
  -d '{
    "yaml_str": "agents:\n  - id: stock_analyst\n    name: 股票分析师\n    ...",
    "update_existing": true
  }'

# 从YAML文件导入
curl -X POST "http://localhost:8000/api/platform/agents/import/yaml-file" \
  -F "file=@agents.yaml" \
  -F "update_existing=true"
```

#### 导出智能体配置

```bash
# 导出所有智能体
curl -X GET "http://localhost:8000/api/platform/agents/export/yaml"

# 导出特定状态的智能体
curl -X GET "http://localhost:8000/api/platform/agents/export/yaml?status=active&category=trading"
```

#### YAML格式示例

```yaml
agents:
  - id: stock_analyst
    name: 股票分析师
    description: 专业的股票分析智能体
    version: 1.0.0
    agent_type: analyst
    author: Platform Team
    category: trading
    tags:
      - stock
      - analysis
    capabilities:
      - market_analysis
      - fundamental_analysis
    requirements:
      - data_source: tushare
      - llm_provider: dashscope
    config_schema:
      analysis_depth:
        type: string
        enum: [标准, 深度, 极深]
        default: 标准
    status: active
```

### 2. Workflows (工作流)

#### 导入工作流配置

```bash
curl -X POST "http://localhost:8000/api/platform/workflows/import/yaml-file" \
  -F "file=@workflows.yaml" \
  -F "update_existing=true"
```

#### 导出工作流配置

```bash
curl -X GET "http://localhost:8000/api/platform/workflows/export/yaml?status=created"
```

#### YAML格式示例

```yaml
workflows:
  - workflow_id: stock_analysis_workflow
    name: 股票分析工作流
    description: 完整的股票分析流程
    status: created
    config:
      timeout: 3600
      retry_count: 3
    nodes:
      - node_id: fetch_data
        name: 获取数据
        node_type: data_source
        handler_type: tushare_adapter
        config:
          symbol: ${symbol}
        dependencies: []
      - node_id: analyze
        name: 分析数据
        node_type: agent
        handler_type: stock_analyst
        dependencies:
          - fetch_data
    edges:
      - [fetch_data, analyze]
```

### 3. Plugins (插件)

#### 导入插件配置

```bash
curl -X POST "http://localhost:8000/api/platform/plugins/import/yaml-file" \
  -F "file=@plugins.yaml" \
  -F "update_existing=true"
```

#### 导出插件配置

```bash
curl -X GET "http://localhost:8000/api/platform/plugins/export/yaml?status=active"
```

#### YAML格式示例

```yaml
plugins:
  - plugin_id: data_processor
    name: 数据处理器
    version: 1.0.0
    description: 处理各种数据格式的插件
    author: Platform Team
    entry_point: app.plugins.data_processor.main
    config_schema:
      batch_size:
        type: integer
        default: 100
    dependencies:
      - pandas
      - numpy
    tags:
      - data
      - processing
    status: registered
```

### 4. Providers (LLM提供商)

参考 [PROVIDER_MANAGEMENT.md](./PROVIDER_MANAGEMENT.md)

### 5. Data Sources (数据源)

参考 [DATA_SOURCES.md](./DATA_SOURCES.md)

## Python代码使用

### Agents

```python
from app.platform.agents import get_service

service = get_service()

# 从YAML文件导入
result = await service.import_from_yaml_file("agents.yaml", update_existing=True)

# 导出为YAML字符串
yaml_str = await service.export_to_yaml_string()

# 导出为YAML文件
await service.export_to_yaml_file("exported_agents.yaml")
```

### Workflows

```python
from app.platform.workflow import get_service

service = get_service()

# 从YAML文件导入
result = await service.import_from_yaml_file("workflows.yaml")

# 导出为YAML
yaml_str = await service.export_to_yaml_string()
```

### Plugins

```python
from app.platform.plugins import get_service

service = get_service()

# 从YAML文件导入
result = await service.import_from_yaml_file("plugins.yaml")

# 导出为YAML
yaml_str = await service.export_to_yaml_string()
```

## API端点汇总

### Agents
- `POST /api/platform/agents/import/yaml` - 从YAML字符串导入
- `POST /api/platform/agents/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/agents/export/yaml` - 导出为YAML

### Workflows
- `POST /api/platform/workflows/import/yaml` - 从YAML字符串导入
- `POST /api/platform/workflows/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/workflows/export/yaml` - 导出为YAML

### Plugins
- `POST /api/platform/plugins/import/yaml` - 从YAML字符串导入
- `POST /api/platform/plugins/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/plugins/export/yaml` - 导出为YAML

### Providers
- `POST /api/platform/providers/import/yaml` - 从YAML字符串导入
- `POST /api/platform/providers/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/providers/export/yaml` - 导出为YAML

### Data Sources
- `POST /api/platform/data-sources/import/yaml` - 从YAML字符串导入
- `POST /api/platform/data-sources/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/data-sources/export/yaml` - 导出为YAML

## 最佳实践

1. **版本控制**: 将YAML配置文件纳入版本控制系统
2. **环境分离**: 为不同环境（开发、测试、生产）维护不同的配置文件
3. **批量导入**: 使用批量导入功能一次性配置多个资源
4. **定期导出**: 定期导出配置作为备份
5. **更新策略**: 使用`update_existing=true`时注意可能覆盖现有配置

## 扩展新模块

要为新模块添加YAML声明式管理，需要：

1. 创建YAML加载器类，继承`DeclarativeYAMLLoader`
2. 创建服务类，继承`DeclarativeService`
3. 实现必要的抽象方法
4. 在API路由中添加导入/导出端点

示例：

```python
from app.platform.core.declarative_manager import DeclarativeYAMLLoader, DeclarativeService

class MyModuleYAMLLoader(DeclarativeYAMLLoader[MyMetadata]):
    def __init__(self):
        super().__init__("my_module")
    
    def _parse_item(self, data: Dict[str, Any]) -> MyMetadata:
        # 实现解析逻辑
        pass
    
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        # 检查ID字段
        pass
    
    def _set_id_field(self, data: Dict[str, Any], value: str):
        # 设置ID字段
        pass

class MyModuleService(DeclarativeService[MyMetadata]):
    def __init__(self, registry: Optional[MyRegistry] = None):
        loader = MyModuleYAMLLoader()
        super().__init__(loader)
        self.registry = registry or get_registry()
    
    async def _import_items(self, items: List[MyMetadata], update_existing: bool = False):
        # 实现导入逻辑
        pass
    
    async def _get_all_items(self, filter_func: Optional[Any] = None) -> List[MyMetadata]:
        # 实现获取所有项目逻辑
        pass
```

## 总结

声明式数据管理框架为平台提供了统一的配置管理方式，使得：

- ✅ 配置可版本化
- ✅ 配置可移植
- ✅ 配置易于管理
- ✅ 支持批量操作
- ✅ 统一的API接口
- ✅ 易于扩展新模块

所有模块的配置都可以通过YAML进行声明式管理，大大提升了平台的可维护性和可扩展性。

