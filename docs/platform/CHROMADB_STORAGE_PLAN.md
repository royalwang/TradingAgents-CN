# ChromaDB 存储规划

## 概述

平台使用 ChromaDB 作为向量数据库，用于知识库的文档存储和语义搜索。ChromaDB 支持文档嵌入、相似度搜索和元数据过滤。

## ChromaDB 配置

- **存储类型**: 持久化存储 (PersistentClient)
- **存储位置**: `data/chromadb/` (可配置)
- **集合命名**: 使用前缀 `kb_` + 知识库名称
- **嵌入模型**: 默认使用 OpenAI text-embedding-3-small
- **向量维度**: 1536 (OpenAI) 或根据模型配置

## 集合结构

### 知识库集合

每个知识库对应一个ChromaDB集合，集合命名规则：
```
集合名: kb_{knowledge_base_name}
例如: kb_stock_research, kb_financial_reports
```

### 文档存储结构

#### 文档ID
```
格式: doc_{document_id}_{chunk_index}
示例: doc_abc123_0, doc_abc123_1
说明: 
  - document_id: 文档唯一标识
  - chunk_index: 文档分块索引（从0开始）
```

#### 文档内容
```
字段: documents (List[str])
类型: 字符串列表
内容: 文档分块后的文本内容
示例: ["这是第一段内容...", "这是第二段内容..."]
```

#### 向量嵌入
```
字段: embeddings (List[List[float]])
类型: 浮点数二维列表
维度: 1536 (OpenAI) 或根据模型配置
示例: [[0.1, 0.2, ..., 0.9], [0.2, 0.3, ..., 0.8]]
```

#### 元数据
```
字段: metadatas (List[Dict[str, Any]])
类型: 字典列表
结构: {
  "document_id": "abc123",
  "chunk_index": 0,
  "title": "文档标题",
  "source": "文档来源",
  "document_type": "pdf|docx|txt|md",
  "created_at": "2025-10-17T10:00:00Z",
  "updated_at": "2025-10-17T10:00:00Z",
  "author": "作者",
  "category": "分类",
  "tags": ["标签1", "标签2"],
  "page_number": 1,  // 如果是PDF
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

## 数据操作

### 1. 添加文档

```python
await vector_store.add_documents(
    documents=["文档内容1", "文档内容2"],
    embeddings=[[0.1, 0.2, ...], [0.2, 0.3, ...]],
    metadatas=[
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "title": "文档标题",
            "source": "来源"
        },
        {
            "document_id": "doc1",
            "chunk_index": 1,
            "title": "文档标题",
            "source": "来源"
        }
    ],
    ids=["doc_doc1_0", "doc_doc1_1"]
)
```

### 2. 搜索文档

```python
results = await vector_store.search(
    query_embedding=[0.1, 0.2, ...],
    top_k=5,
    filters={
        "document_type": "pdf",
        "category": "财务报告"
    }
)
```

### 3. 删除文档

```python
await vector_store.delete(
    ids=["doc_doc1_0", "doc_doc1_1"]
)
```

### 4. 清空集合

```python
await vector_store.clear()
```

## 文档分块策略

### 分块参数

- **chunk_size**: 1000字符（默认）
- **chunk_overlap**: 200字符（默认）
- **分块方法**: 按字符数或句子边界

### 分块示例

```
原始文档: "这是一个很长的文档内容..." (5000字符)

分块结果:
- Chunk 0: 字符 0-1000
- Chunk 1: 字符 800-1800 (重叠200字符)
- Chunk 2: 字符 1600-2600 (重叠200字符)
- Chunk 3: 字符 2400-3400 (重叠200字符)
- Chunk 4: 字符 3200-4200 (重叠200字符)
- Chunk 5: 字符 4000-5000 (重叠200字符)
```

## 元数据索引

### 可索引字段

ChromaDB支持对元数据字段建立索引，用于快速过滤：

```python
# 常用索引字段
indexed_fields = [
    "document_id",
    "title",
    "source",
    "document_type",
    "category",
    "tags",
    "created_at"
]
```

### 查询优化

- **向量搜索**: 使用余弦相似度或欧氏距离
- **元数据过滤**: 在向量搜索前应用过滤条件
- **混合搜索**: 结合向量相似度和元数据过滤

## 存储位置

### 默认路径
```
data/chromadb/
├── kb_stock_research/
│   ├── chroma.sqlite3
│   └── ...
├── kb_financial_reports/
│   ├── chroma.sqlite3
│   └── ...
└── ...
```

### 配置路径
可以通过环境变量或配置文件自定义：
```python
CHROMADB_PERSIST_DIR = "data/chromadb"
```

## 性能优化

### 1. 批量操作
- 使用批量添加减少网络往返
- 建议批量大小: 100-500个文档

### 2. 索引优化
- 为常用查询字段建立元数据索引
- 定期重建索引优化查询性能

### 3. 向量维度
- 选择合适的嵌入模型维度
- 平衡精度和性能

### 4. 集合管理
- 按知识库类型分离集合
- 定期清理无用集合

## 数据备份

### 备份策略
- **备份频率**: 每日全量备份
- **备份内容**: 整个 `data/chromadb/` 目录
- **备份存储**: 对象存储或专用备份服务器

### 恢复流程
1. 停止应用服务
2. 恢复 `data/chromadb/` 目录
3. 验证集合完整性
4. 重启应用服务

## 容量规划

### 存储估算

假设：
- 平均文档大小: 10KB
- 平均分块数: 5块/文档
- 向量维度: 1536
- 向量大小: 1536 * 4 bytes = 6KB

单个文档存储：
- 文本内容: 10KB
- 向量数据: 5 * 6KB = 30KB
- 元数据: 1KB
- **总计**: ~41KB/文档

### 容量示例

- 1万文档: ~410MB
- 10万文档: ~4.1GB
- 100万文档: ~41GB

## 监控指标

### 关键指标
- **集合数量**: 监控知识库数量
- **文档数量**: 监控每个集合的文档数
- **存储大小**: 监控磁盘使用情况
- **查询性能**: 监控搜索响应时间

### 告警阈值
- 存储使用率 > 80%
- 查询响应时间 > 1秒
- 集合数量 > 100

## 安全考虑

1. **访问控制**: 限制ChromaDB数据目录访问权限
2. **数据加密**: 敏感文档内容加密存储
3. **备份加密**: 备份文件加密存储
4. **审计日志**: 记录文档添加、删除操作

## 扩展性

### 水平扩展
- ChromaDB支持分布式部署
- 可以按知识库分片存储

### 垂直扩展
- 增加服务器内存和CPU
- 使用SSD提升I/O性能

## 总结

ChromaDB存储规划涵盖了知识库的所有需求：
- ✅ 文档存储（文本、向量、元数据）
- ✅ 语义搜索（向量相似度搜索）
- ✅ 元数据过滤（按类型、分类、标签等）
- ✅ 文档分块（支持大文档分块存储）
- ✅ 集合管理（按知识库分离）
- ✅ 性能优化（批量操作、索引优化）
- ✅ 数据备份（定期备份和恢复）

通过合理的分块策略和元数据设计，可以确保知识库的高效查询和管理。

