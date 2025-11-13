# 智能体平台文档

## 概述

新一代模块化智能体平台，提供完整的智能体管理、知识库、文档解析、MCP工具、插件系统和工作流编排功能。

## 架构设计

### 核心模块

1. **智能体管理 (Agents)**
   - 智能体注册表
   - 智能体生命周期管理
   - 智能体实例管理

2. **知识库 (Knowledge Base)**
   - 向量数据库集成
   - 文档存储和检索
   - 嵌入服务

3. **文档解析 (Document Parsers)**
   - 支持多种格式：PDF、Word、Excel、Markdown、HTML、JSON等
   - 自动文档分块
   - 元数据提取

4. **MCP工具 (Model Context Protocol)**
   - MCP服务器实现
   - 工具注册和执行
   - 客户端支持

5. **插件系统 (Plugins)**
   - 插件注册和发现
   - 插件加载和管理
   - 插件生命周期管理

6. **工作流编排 (Workflow)**
   - 基于LangGraph的工作流引擎
   - 可视化工作流构建
   - 工作流执行和监控

## 快速开始

### 1. 智能体管理

```python
from app.platform.agents import get_registry, get_factory

# 注册智能体
registry = get_registry()
registry.register(
    agent_id="my_agent",
    name="我的智能体",
    description="一个示例智能体",
    version="1.0.0",
    agent_type=AgentType.CUSTOM,
    author="开发者",
    category="general",
)

# 创建智能体实例
factory = get_factory()
instance = await factory.create_agent(
    agent_id="my_agent",
    name="实例1",
    config={"param1": "value1"},
)
```

### 2. 知识库使用

```python
from app.platform.knowledge import KnowledgeBase, create_vector_store, create_embedding_service

# 创建知识库
vector_store = create_vector_store("chromadb", "my_kb")
embedding_service = create_embedding_service("openai", "text-embedding-3-small")

kb = KnowledgeBase(
    name="my_kb",
    vector_store=vector_store,
    embedding_service=embedding_service,
)

# 添加文档
document = await kb.add_document(
    title="文档标题",
    content="文档内容...",
    source="文件路径",
    document_type="pdf",
)

# 搜索
results = await kb.search("查询内容", top_k=5)
```

### 3. 文档解析

```python
from app.platform.parsers import get_parser_factory

parser_factory = get_parser_factory()

# 解析文档
result = await parser_factory.parse("document.pdf")
print(result.title)
print(result.content)
```

### 4. MCP工具

```python
from app.platform.mcp import get_mcp_server

server = get_mcp_server()

# 注册工具
server.registry.register(
    name="my_tool",
    description="我的工具",
    tool_type=ToolType.FUNCTION,
    handler=my_tool_function,
)

# 执行工具
result = await server.execute_tool("my_tool", {"param": "value"})
```

### 5. 插件系统

```python
from app.platform.plugins import get_registry, get_manager, get_loader

# 发现插件
loader = get_loader()
plugins = loader.discover_plugins()

# 加载插件
manager = get_manager()
instance = await manager.load_plugin("plugin_id", config={})

# 激活插件
await manager.activate_plugin(instance.instance_id)
```

### 6. 工作流编排

```python
from app.platform.workflow import WorkflowBuilder, get_executor

# 构建工作流
builder = WorkflowBuilder()
workflow = (builder
    .create("我的工作流", "描述")
    .add_node("节点1", handler1)
    .add_node("节点2", handler2)
    .connect("节点1", "节点2")
    .build())

# 执行工作流
executor = get_executor()
result = await executor.execute(workflow.workflow_id, initial_state={})
```

## API接口

### 智能体API

- `GET /api/platform/agents` - 列出所有智能体
- `GET /api/platform/agents/{agent_id}` - 获取智能体详情
- `POST /api/platform/agents/{agent_id}/instances` - 创建智能体实例
- `GET /api/platform/agents/instances` - 列出智能体实例
- `DELETE /api/platform/agents/instances/{instance_id}` - 删除智能体实例

### 知识库API

- `POST /api/platform/knowledge/{kb_name}/documents` - 添加文档
- `POST /api/platform/knowledge/{kb_name}/documents/upload` - 上传文档
- `POST /api/platform/knowledge/{kb_name}/search` - 搜索知识库

### MCP工具API

- `GET /api/platform/mcp/tools` - 列出MCP工具
- `POST /api/platform/mcp/tools/execute` - 执行MCP工具

### 插件API

- `GET /api/platform/plugins` - 列出插件
- `POST /api/platform/plugins/{plugin_id}/load` - 加载插件
- `POST /api/platform/plugins/discover` - 发现插件

### 工作流API

- `GET /api/platform/workflows` - 列出工作流
- `POST /api/platform/workflows/{workflow_id}/execute` - 执行工作流

## 配置

平台配置在 `app/platform/core/platform_config.py` 中定义，可以通过环境变量进行配置：

- `KNOWLEDGE_BASE_ENABLED` - 启用知识库
- `KNOWLEDGE_BASE_VECTOR_DB` - 向量数据库类型
- `KNOWLEDGE_BASE_EMBEDDING_MODEL` - 嵌入模型
- `DOCUMENT_PARSER_ENABLED` - 启用文档解析
- `MCP_ENABLED` - 启用MCP工具
- `PLUGIN_ENABLED` - 启用插件系统
- `WORKFLOW_ENABLED` - 启用工作流编排

## 扩展开发

### 创建自定义智能体

```python
from app.platform.agents import get_registry, AgentType

def create_my_agent(config):
    # 创建智能体逻辑
    return MyAgent(config)

registry = get_registry()
registry.register(
    agent_id="my_agent",
    name="我的智能体",
    description="描述",
    version="1.0.0",
    agent_type=AgentType.CUSTOM,
    author="开发者",
    factory_func=create_my_agent,
)
```

### 创建自定义插件

创建插件目录结构：

```
plugins/my_plugin/
  ├── plugin.json
  └── main.py
```

`plugin.json`:
```json
{
  "id": "my_plugin",
  "name": "我的插件",
  "version": "1.0.0",
  "description": "插件描述",
  "author": "开发者",
  "entry_point": "main.py",
  "dependencies": [],
  "tags": ["example"]
}
```

`main.py`:
```python
class Plugin:
    def __init__(self):
        pass
    
    async def activate(self, config):
        # 激活逻辑
        pass
    
    async def deactivate(self):
        # 停用逻辑
        pass
```

## 最佳实践

1. **智能体设计**
   - 保持智能体职责单一
   - 使用配置而非硬编码
   - 实现适当的错误处理

2. **知识库使用**
   - 合理设置文档分块大小
   - 使用有意义的文档元数据
   - 定期清理过期文档

3. **工作流设计**
   - 保持工作流节点简单
   - 使用有意义的节点名称
   - 实现适当的错误处理

4. **插件开发**
   - 遵循插件接口规范
   - 处理依赖关系
   - 提供清晰的文档

## 故障排除

### 常见问题

1. **向量数据库连接失败**
   - 检查ChromaDB是否安装
   - 确认数据目录权限

2. **文档解析失败**
   - 检查文件格式是否支持
   - 确认相关解析库已安装

3. **插件加载失败**
   - 检查插件JSON格式
   - 确认依赖已安装
   - 查看错误日志

## 更多信息

- [智能体架构文档](agents/README.md)
- [知识库文档](knowledge/README.md)
- [工作流文档](workflow/README.md)

