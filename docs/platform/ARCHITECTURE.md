# 智能体平台架构文档

## 平台概述

新一代模块化智能体平台已成功构建，提供了完整的智能体管理、知识库、文档解析、MCP工具、插件系统和工作流编排功能。

## 已实现的模块

### 1. 智能体管理模块 (`app/platform/agents/`)

**功能特性：**
- ✅ 智能体注册表（AgentRegistry）
- ✅ 智能体元数据管理
- ✅ 智能体生命周期管理（AgentManager）
- ✅ 智能体实例管理
- ✅ 智能体工厂模式（AgentFactory）
- ✅ 智能体类型分类（分析师、研究员、交易员等）
- ✅ 智能体状态管理（注册、激活、停用等）

**核心文件：**
- `agent_registry.py` - 智能体注册表
- `agent_manager.py` - 智能体管理器
- `agent_factory.py` - 智能体工厂

### 2. 知识库模块 (`app/platform/knowledge/`)

**功能特性：**
- ✅ 向量数据库集成（支持ChromaDB）
- ✅ 文档存储和管理
- ✅ 文档分块处理
- ✅ 向量嵌入服务（支持OpenAI）
- ✅ 语义搜索功能
- ✅ 文档元数据管理

**核心文件：**
- `knowledge_base.py` - 知识库核心
- `vector_store.py` - 向量存储接口
- `embedding_service.py` - 嵌入服务

### 3. 文档解析模块 (`app/platform/parsers/`)

**功能特性：**
- ✅ 多格式文档解析
  - PDF文档解析
  - Word文档解析（.docx, .doc）
  - 文本文件解析（.txt, .md）
  - Excel文件解析（.xlsx, .xls）
  - HTML文件解析
  - JSON文件解析
- ✅ 文档元数据提取
- ✅ 解析器工厂模式
- ✅ 自动格式识别

**核心文件：**
- `document_parser.py` - 文档解析器基类和实现
- `parser_factory.py` - 解析器工厂

### 4. MCP工具模块 (`app/platform/mcp/`)

**功能特性：**
- ✅ MCP服务器实现
- ✅ 工具注册表（MCPToolRegistry）
- ✅ 工具执行引擎
- ✅ MCP客户端支持
- ✅ 工具类型分类（函数、API、数据库等）
- ✅ 参数验证

**核心文件：**
- `mcp_server.py` - MCP服务器
- `mcp_client.py` - MCP客户端

### 5. 插件系统 (`app/platform/plugins/`)

**功能特性：**
- ✅ 插件注册表（PluginRegistry）
- ✅ 插件发现和加载（PluginLoader）
- ✅ 插件生命周期管理（PluginManager）
- ✅ 插件依赖管理
- ✅ 插件配置管理
- ✅ 插件元数据管理

**核心文件：**
- `plugin_registry.py` - 插件注册表
- `plugin_manager.py` - 插件管理器
- `plugin_loader.py` - 插件加载器

### 6. 工作流编排模块 (`app/platform/workflow/`)

**功能特性：**
- ✅ 基于LangGraph的工作流引擎
- ✅ 工作流构建器（WorkflowBuilder）
- ✅ 工作流执行器（WorkflowExecutor）
- ✅ 节点和边的管理
- ✅ 工作流状态管理
- ✅ 工作流可视化支持

**核心文件：**
- `workflow_engine.py` - 工作流引擎
- `workflow_builder.py` - 工作流构建器
- `workflow_executor.py` - 工作流执行器

### 7. API路由 (`app/routers/platform.py`)

**已实现的API端点：**

#### 智能体API
- `GET /api/platform/agents` - 列出所有智能体
- `GET /api/platform/agents/{agent_id}` - 获取智能体详情
- `POST /api/platform/agents/{agent_id}/instances` - 创建智能体实例
- `GET /api/platform/agents/instances` - 列出智能体实例
- `DELETE /api/platform/agents/instances/{instance_id}` - 删除智能体实例

#### 知识库API
- `POST /api/platform/knowledge/{kb_name}/documents` - 添加文档
- `POST /api/platform/knowledge/{kb_name}/documents/upload` - 上传文档
- `POST /api/platform/knowledge/{kb_name}/search` - 搜索知识库

#### MCP工具API
- `GET /api/platform/mcp/tools` - 列出MCP工具
- `POST /api/platform/mcp/tools/execute` - 执行MCP工具

#### 插件API
- `GET /api/platform/plugins` - 列出插件
- `POST /api/platform/plugins/{plugin_id}/load` - 加载插件
- `POST /api/platform/plugins/discover` - 发现插件

#### 工作流API
- `GET /api/platform/workflows` - 列出工作流
- `POST /api/platform/workflows/{workflow_id}/execute` - 执行工作流

## 目录结构

```
app/platform/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── platform_config.py          # 平台配置
├── agents/
│   ├── __init__.py
│   ├── agent_registry.py           # 智能体注册表
│   ├── agent_manager.py            # 智能体管理器
│   └── agent_factory.py            # 智能体工厂
├── knowledge/
│   ├── __init__.py
│   ├── knowledge_base.py           # 知识库核心
│   ├── vector_store.py             # 向量存储
│   └── embedding_service.py        # 嵌入服务
├── parsers/
│   ├── __init__.py
│   ├── document_parser.py          # 文档解析器
│   ├── parser_factory.py           # 解析器工厂
│   └── parsers.py                  # 解析器实现
├── mcp/
│   ├── __init__.py
│   ├── mcp_server.py               # MCP服务器
│   └── mcp_client.py               # MCP客户端
├── plugins/
│   ├── __init__.py
│   ├── plugin_registry.py          # 插件注册表
│   ├── plugin_manager.py           # 插件管理器
│   └── plugin_loader.py            # 插件加载器
└── workflow/
    ├── __init__.py
    ├── workflow_engine.py          # 工作流引擎
    ├── workflow_builder.py         # 工作流构建器
    └── workflow_executor.py        # 工作流执行器
```

## 配置说明

平台配置通过 `app/platform/core/platform_config.py` 管理，主要配置项包括：

- **知识库配置**
  - `KNOWLEDGE_BASE_ENABLED` - 是否启用知识库
  - `KNOWLEDGE_BASE_VECTOR_DB` - 向量数据库类型
  - `KNOWLEDGE_BASE_EMBEDDING_MODEL` - 嵌入模型名称
  - `KNOWLEDGE_BASE_CHUNK_SIZE` - 文档分块大小
  - `KNOWLEDGE_BASE_CHUNK_OVERLAP` - 分块重叠大小

- **文档解析配置**
  - `DOCUMENT_PARSER_ENABLED` - 是否启用文档解析
  - `DOCUMENT_MAX_SIZE_MB` - 最大文档大小
  - `DOCUMENT_SUPPORTED_FORMATS` - 支持的文件格式

- **MCP工具配置**
  - `MCP_ENABLED` - 是否启用MCP
  - `MCP_SERVER_PORT` - MCP服务器端口
  - `MCP_TOOLS_DIR` - MCP工具目录

- **插件系统配置**
  - `PLUGIN_ENABLED` - 是否启用插件系统
  - `PLUGIN_DIR` - 插件目录
  - `PLUGIN_AUTO_LOAD` - 是否自动加载插件

- **工作流配置**
  - `WORKFLOW_ENABLED` - 是否启用工作流
  - `WORKFLOW_ENGINE` - 工作流引擎类型
  - `WORKFLOW_MAX_CONCURRENT` - 最大并发数

## 使用示例

### 1. 注册和使用智能体

```python
from app.platform.agents import get_registry, get_factory, AgentType

# 注册智能体
registry = get_registry()
registry.register(
    agent_id="stock_analyst",
    name="股票分析师",
    description="分析股票数据",
    version="1.0.0",
    agent_type=AgentType.ANALYST,
    author="开发者",
)

# 创建实例
factory = get_factory()
instance = await factory.create_agent(
    agent_id="stock_analyst",
    config={"symbol": "AAPL"},
)
```

### 2. 使用知识库

```python
from app.platform.knowledge import KnowledgeBase, create_vector_store, create_embedding_service

# 创建知识库
kb = KnowledgeBase(
    name="financial_kb",
    vector_store=create_vector_store("chromadb", "financial_kb"),
    embedding_service=create_embedding_service("openai"),
)

# 添加文档
doc = await kb.add_document(
    title="财务报告",
    content="...",
    source="report.pdf",
    document_type="pdf",
)

# 搜索
results = await kb.search("股票分析", top_k=5)
```

### 3. 解析文档

```python
from app.platform.parsers import get_parser_factory

parser = get_parser_factory()
result = await parser.parse("document.pdf")
print(result.title, result.content)
```

### 4. 使用工作流

```python
from app.platform.workflow import WorkflowBuilder, get_executor

# 构建工作流
builder = WorkflowBuilder()
workflow = (builder
    .create("分析工作流", "股票分析流程")
    .add_node("数据获取", get_data_handler)
    .add_node("数据分析", analyze_data_handler)
    .connect("数据获取", "数据分析")
    .build())

# 执行
executor = get_executor()
result = await executor.execute(workflow.workflow_id)
```

## 扩展性

平台设计遵循以下原则：

1. **模块化设计** - 每个模块独立，可单独使用
2. **接口抽象** - 使用抽象基类定义接口
3. **工厂模式** - 使用工厂模式创建实例
4. **注册表模式** - 使用注册表管理组件
5. **配置驱动** - 通过配置控制行为

## 后续改进方向

1. **性能优化**
   - 向量数据库查询优化
   - 文档解析性能提升
   - 工作流执行并发优化

2. **功能增强**
   - 支持更多向量数据库（Pinecone、Weaviate等）
   - 支持更多文档格式
   - 工作流可视化界面
   - 插件市场

3. **监控和日志**
   - 平台运行监控
   - 性能指标收集
   - 错误追踪和报告

4. **安全性**
   - 插件沙箱隔离
   - API认证和授权
   - 数据加密

## 总结

新一代智能体平台已成功构建，提供了完整的模块化架构，支持智能体管理、知识库、文档解析、MCP工具、插件系统和工作流编排等核心功能。平台设计遵循模块化、可扩展的原则，为后续功能扩展奠定了良好基础。

