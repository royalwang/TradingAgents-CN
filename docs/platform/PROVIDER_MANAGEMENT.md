# LLM Provider管理文档

## 概述

LLM Provider管理模块提供了完整的Provider配置管理功能，支持通过YAML声明式导入和RESTful API进行维护。

## 核心功能

### 1. YAML声明式导入

通过YAML文件定义Provider配置，支持批量导入：

```yaml
providers:
  - name: openai
    display_name: OpenAI
    description: OpenAI是人工智能领域的领先公司
    website: https://openai.com
    api_doc_url: https://platform.openai.com/docs
    default_base_url: https://api.openai.com/v1
    is_active: true
    supported_features:
      - chat
      - completion
      - embedding
      - vision
      - function_calling
      - streaming
    extra_config:
      has_api_key: true
      model_family: gpt
```

### 2. API接口维护

提供完整的CRUD API接口进行Provider管理。

## API接口

### Provider管理

- `GET /api/platform/providers` - 列出所有Provider
- `GET /api/platform/providers/{name}` - 获取Provider详情
- `POST /api/platform/providers` - 创建Provider
- `PUT /api/platform/providers/{name}` - 更新Provider
- `DELETE /api/platform/providers/{name}` - 删除Provider

### YAML导入/导出

- `POST /api/platform/providers/import/yaml` - 从YAML字符串导入
- `POST /api/platform/providers/import/yaml-file` - 从YAML文件导入
- `GET /api/platform/providers/export/yaml` - 导出为YAML格式

## 使用示例

### Python代码示例

```python
from app.platform.providers import get_provider_service

service = get_provider_service()

# 1. 从YAML文件导入
result = await service.import_from_yaml_file(
    "providers.yaml",
    update_existing=True
)
print(f"创建: {result['created']}")
print(f"更新: {result['updated']}")

# 2. 创建Provider
provider = await service.create_provider(
    {
        "name": "custom_provider",
        "display_name": "自定义Provider",
        "description": "自定义Provider描述",
        "default_base_url": "https://api.example.com/v1",
        "supported_features": ["chat", "completion"],
    },
    api_key="your-api-key",
)

# 3. 更新Provider
updated = await service.update_provider(
    "custom_provider",
    {
        "display_name": "更新的名称",
        "is_active": False,
    },
)

# 4. 列出所有Provider
providers = await service.get_all(is_active=True)
for provider in providers:
    print(f"{provider.display_name}: {provider.name}")

# 5. 导出为YAML
await service.export_to_yaml_file("exported_providers.yaml")
```

### API调用示例

#### 1. 列出所有Provider

```bash
curl -X GET "http://localhost:8000/api/platform/providers"
```

#### 2. 创建Provider

```bash
curl -X POST "http://localhost:8000/api/platform/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_provider",
    "display_name": "自定义Provider",
    "description": "描述",
    "default_base_url": "https://api.example.com/v1",
    "supported_features": ["chat", "completion"]
  }'
```

#### 3. 从YAML文件导入

```bash
curl -X POST "http://localhost:8000/api/platform/providers/import/yaml-file" \
  -F "file=@providers.yaml" \
  -F "update_existing=true"
```

#### 4. 导出为YAML

```bash
curl -X GET "http://localhost:8000/api/platform/providers/export/yaml?is_active=true"
```

## YAML格式说明

### 必需字段

- `name` - Provider唯一标识
- `display_name` - 显示名称（可选，默认使用name）

### 可选字段

- `description` - 描述
- `website` - 官网地址
- `api_doc_url` - API文档地址
- `logo_url` - Logo地址
- `default_base_url` - 默认API地址
- `is_active` - 是否启用（默认true）
- `supported_features` - 支持的功能列表
- `is_aggregator` - 是否为聚合渠道（默认false）
- `aggregator_type` - 聚合渠道类型
- `model_name_format` - 模型名称格式
- `extra_config` - 额外配置（字典）

### 支持的功能类型

- `chat` - 聊天对话
- `completion` - 文本补全
- `embedding` - 向量嵌入
- `image` - 图像生成
- `vision` - 视觉理解
- `function_calling` - 函数调用
- `streaming` - 流式输出

## 批量导入脚本

可以使用现有的初始化脚本，或通过API导入：

```python
# 使用初始化脚本
python app/scripts/init_providers.py

# 或通过API导入YAML
import requests

with open('providers.yaml', 'r') as f:
    yaml_content = f.read()

response = requests.post(
    'http://localhost:8000/api/platform/providers/import/yaml',
    json={'yaml_content': yaml_content, 'update_existing': True}
)
```

## 最佳实践

1. **使用YAML管理配置**
   - 将Provider配置保存在YAML文件中
   - 使用版本控制管理配置变更
   - 定期导出配置作为备份

2. **API密钥管理**
   - 通过API接口单独设置API密钥
   - 不要在YAML文件中包含敏感信息
   - 使用环境变量或密钥管理服务

3. **配置验证**
   - 导入前验证YAML格式
   - 检查必需字段
   - 验证URL格式

4. **批量操作**
   - 使用批量导入功能
   - 设置`update_existing`参数控制更新行为
   - 检查导入结果

## 与现有系统集成

Provider管理模块与现有的配置系统完全兼容：

- 使用相同的`LLMProvider`模型
- 数据存储在相同的MongoDB集合中
- 与`ConfigService`共享数据

## 总结

LLM Provider管理模块提供了灵活、强大的Provider配置管理功能，支持声明式配置和API维护两种方式，满足不同场景的需求。

