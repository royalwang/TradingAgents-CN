# 声明式数据抽象文档

## 概述

声明式数据抽象模块提供了完整的数据定义、验证、创建、转换和关系管理功能。通过声明式的方式定义数据结构，可以自动生成、验证和转换数据。

## 核心功能

### 1. 数据模式定义 (Schema)

通过声明式方式定义数据结构：

```python
from app.platform.data import DataSchema, FieldDefinition, SchemaType, get_registry

# 创建模式
schema = DataSchema(
    schema_id="user",
    name="用户",
    description="用户数据模式",
    version="1.0.0",
    fields=[
        FieldDefinition(
            name="id",
            field_type=SchemaType.STRING,
            description="用户ID",
            required=True,
            validation_rules={"minLength": 1, "maxLength": 50},
        ),
        FieldDefinition(
            name="name",
            field_type=SchemaType.STRING,
            description="用户名",
            required=True,
            validation_rules={"minLength": 2, "maxLength": 100},
        ),
        FieldDefinition(
            name="email",
            field_type=SchemaType.STRING,
            description="邮箱",
            required=True,
            validation_rules={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
        ),
        FieldDefinition(
            name="age",
            field_type=SchemaType.INTEGER,
            description="年龄",
            required=False,
            default=0,
            validation_rules={"minimum": 0, "maximum": 150},
        ),
    ],
)

# 注册模式
registry = get_registry()
registry.register(schema)
```

### 2. 数据验证 (Validator)

基于模式验证数据：

```python
from app.platform.data import get_validator, get_registry

validator = get_validator()
schema = get_registry().get("user")

# 验证数据
data = {
    "id": "user123",
    "name": "张三",
    "email": "zhangsan@example.com",
    "age": 25,
}

result = validator.validate(data, schema)
if result.valid:
    print("数据验证通过")
else:
    print(f"验证失败: {result.errors}")
```

### 3. 数据工厂 (Factory)

从模式创建数据实例：

```python
from app.platform.data import get_factory

factory = get_factory()

# 创建数据实例（自动填充默认值）
instance = factory.create(
    schema_id="user",
    data={"id": "user123", "name": "张三", "email": "zhangsan@example.com"},
    validate=True,
    fill_defaults=True,
)

# 使用构建器（流式API）
from app.platform.data import DataBuilder

builder = DataBuilder("user")
instance = (builder
    .set("id", "user123")
    .set("name", "张三")
    .set("email", "zhangsan@example.com")
    .set("age", 25)
    .build())
```

### 4. 数据生成器 (Generator)

生成测试和示例数据：

```python
from app.platform.data import DataGenerator

generator = DataGenerator()

# 生成示例数据
instances = generator.generate(
    schema_id="user",
    count=10,
    overrides={"age": 30},  # 覆盖特定字段
)
```

### 5. 数据转换 (Transformer)

在不同格式和结构之间转换数据：

```python
from app.platform.data import DataTransformer, TransformRule, TransformDirection

transformer = get_transformer()

# 定义转换规则
rules = [
    TransformRule(
        source_field="user_id",
        target_field="id",
        transform_func=lambda x: f"user_{x}",
    ),
    TransformRule(
        source_field="full_name",
        target_field="name",
    ),
]

# 注册转换
transformer.register_transformation("user_mapping", rules)

# 执行转换
data = {"user_id": "123", "full_name": "张三"}
result = transformer.transform(data, "user_mapping", TransformDirection.FORWARD)
```

### 6. 数据序列化 (Serializer)

支持多种序列化格式：

```python
from app.platform.data import get_serializer, SerializationFormat

serializer = get_serializer()

# 序列化
data = {"id": "user123", "name": "张三"}
json_str = serializer.serialize(data, SerializationFormat.JSON)
yaml_str = serializer.serialize(data, SerializationFormat.YAML)
csv_str = serializer.serialize([data], SerializationFormat.CSV, schema_id="user")

# 反序列化
data = serializer.deserialize(json_str, SerializationFormat.JSON)
```

### 7. 数据关系管理 (Relationship)

管理数据之间的关系：

```python
from app.platform.data import get_relationship_manager, RelationshipType

manager = get_relationship_manager()

# 创建关系
relationship = manager.register(
    relationship_id="user_posts",
    name="用户-文章关系",
    source_schema_id="user",
    target_schema_id="post",
    relationship_type=RelationshipType.ONE_TO_MANY,
    source_field="id",
    target_field="user_id",
    cascade_delete=True,
)

# 解析引用
data = {"id": "user123", "name": "张三"}
resolved = manager.resolve_references(data, "user", depth=1)
```

## 支持的字段类型

- `STRING` - 字符串
- `INTEGER` - 整数
- `FLOAT` - 浮点数
- `BOOLEAN` - 布尔值
- `DATETIME` - 日期时间
- `ARRAY` - 数组
- `OBJECT` - 对象
- `ENUM` - 枚举
- `REFERENCE` - 引用其他模式
- `UNION` - 联合类型
- `ANY` - 任意类型

## 验证规则

支持的验证规则：

- `minLength` / `maxLength` - 字符串长度
- `minimum` / `maximum` - 数值范围
- `pattern` - 正则表达式
- `minItems` / `maxItems` - 数组长度
- `enum` - 枚举值

## 序列化格式

支持的序列化格式：

- `JSON` - JSON格式
- `YAML` - YAML格式
- `CSV` - CSV格式
- `XML` - XML格式
- `TOML` - TOML格式

## API接口

### 模式管理

- `POST /api/platform/data/schemas` - 创建数据模式
- `GET /api/platform/data/schemas` - 列出所有模式
- `GET /api/platform/data/schemas/{schema_id}` - 获取模式详情
- `GET /api/platform/data/schemas/{schema_id}/json-schema` - 获取JSON Schema格式

### 数据操作

- `POST /api/platform/data/schemas/{schema_id}/validate` - 验证数据
- `POST /api/platform/data/schemas/{schema_id}/create` - 创建数据实例
- `POST /api/platform/data/schemas/{schema_id}/generate` - 生成示例数据

### 数据转换

- `POST /api/platform/data/transform` - 转换数据
- `POST /api/platform/data/serialize` - 序列化数据
- `POST /api/platform/data/deserialize` - 反序列化数据

### 关系管理

- `POST /api/platform/data/relationships` - 创建数据关系
- `GET /api/platform/data/relationships` - 列出所有关系
- `POST /api/platform/data/schemas/{schema_id}/resolve` - 解析引用关系

## 使用示例

### 完整示例：用户管理系统

```python
from app.platform.data import (
    DataSchema, FieldDefinition, SchemaType,
    get_registry, get_factory, get_validator,
    get_relationship_manager, RelationshipType,
)

# 1. 定义用户模式
user_schema = DataSchema(
    schema_id="user",
    name="用户",
    fields=[
        FieldDefinition("id", SchemaType.STRING, required=True),
        FieldDefinition("name", SchemaType.STRING, required=True),
        FieldDefinition("email", SchemaType.STRING, required=True),
    ],
)

# 2. 定义文章模式
post_schema = DataSchema(
    schema_id="post",
    name="文章",
    fields=[
        FieldDefinition("id", SchemaType.STRING, required=True),
        FieldDefinition("title", SchemaType.STRING, required=True),
        FieldDefinition("content", SchemaType.STRING, required=True),
        FieldDefinition("user_id", SchemaType.STRING, required=True),
    ],
)

# 3. 注册模式
registry = get_registry()
registry.register(user_schema)
registry.register(post_schema)

# 4. 创建数据
factory = get_factory()
user = factory.create("user", {
    "id": "user1",
    "name": "张三",
    "email": "zhangsan@example.com",
})

post = factory.create("post", {
    "id": "post1",
    "title": "我的第一篇文章",
    "content": "这是文章内容...",
    "user_id": "user1",
})

# 5. 验证数据
validator = get_validator()
user_result = validator.validate(user, user_schema)
post_result = validator.validate(post, post_schema)

# 6. 建立关系
manager = get_relationship_manager()
manager.register(
    relationship_id="user_posts",
    name="用户-文章",
    source_schema_id="user",
    target_schema_id="post",
    relationship_type=RelationshipType.ONE_TO_MANY,
    source_field="id",
    target_field="user_id",
)

# 7. 解析引用
resolved = manager.resolve_references(user, "user", depth=1)
```

## 最佳实践

1. **模式设计**
   - 使用有意义的模式ID和名称
   - 为字段添加描述
   - 合理设置必需字段和默认值
   - 使用验证规则确保数据质量

2. **数据创建**
   - 始终验证数据
   - 使用工厂模式创建数据
   - 利用默认值简化数据创建

3. **关系管理**
   - 明确定义关系类型
   - 使用级联操作简化数据管理
   - 合理设置解析深度避免循环引用

4. **序列化**
   - 根据使用场景选择合适的格式
   - 使用模式ID确保序列化一致性

## 总结

声明式数据抽象模块提供了完整的数据管理解决方案，通过声明式的方式定义数据结构，可以自动完成数据验证、创建、转换和关系管理，大大简化了数据处理的复杂性。
