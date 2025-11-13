# 声明式数据抽象文档

## 概述

声明式数据抽象模块提供了完整的数据定义、验证、创建、转换和序列化功能，允许开发者通过声明式的方式定义数据结构，而无需编写命令式代码。

## 核心功能

### 1. 数据模式定义 (Schema)

数据模式是声明式数据抽象的核心，用于定义数据的结构和约束。

#### 基本用法

```python
from app.platform.data import DataSchema, FieldDefinition, SchemaType, get_registry

# 创建模式
schema = DataSchema(
    schema_id="user",
    name="用户",
    description="用户数据模式",
    fields=[
        FieldDefinition(
            name="id",
            field_type=SchemaType.INTEGER,
            description="用户ID",
            required=True,
        ),
        FieldDefinition(
            name="name",
            field_type=SchemaType.STRING,
            description="用户名",
            required=True,
            validation_rules={"minLength": 3, "maxLength": 50},
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

#### 从JSON/YAML创建

```python
# 从JSON创建
schema_json = """
{
  "schema_id": "product",
  "name": "产品",
  "properties": {
    "id": {"type": "integer", "required": true},
    "name": {"type": "string", "required": true, "validation": {"minLength": 1}},
    "price": {"type": "float", "required": true, "validation": {"minimum": 0}}
  }
}
"""
schema = DataSchema.from_json(schema_json)

# 从YAML创建
schema_yaml = """
schema_id: order
name: 订单
properties:
  id:
    type: integer
    required: true
  items:
    type: array
    required: true
"""
schema = DataSchema.from_yaml(schema_yaml)
```

### 2. 数据验证 (Validator)

基于模式验证数据。

```python
from app.platform.data import get_validator, get_registry

validator = get_validator()
registry = get_registry()

schema = registry.get("user")
data = {
    "id": 1,
    "name": "John",
    "email": "john@example.com",
    "age": 25,
}

result = validator.validate(data, schema)
if result.valid:
    print("数据有效")
else:
    for error in result.errors:
        print(f"错误: {error.field} - {error.message}")
```

### 3. 数据工厂 (Factory)

从模式创建数据实例。

```python
from app.platform.data import get_factory, DataBuilder

factory = get_factory()

# 方式1: 直接创建
instance = factory.create(
    schema_id="user",
    data={"name": "John", "email": "john@example.com"},
    validate=True,
    fill_defaults=True,
)

# 方式2: 使用构建器（流式API）
instance = (DataBuilder("user")
    .set("name", "John")
    .set("email", "john@example.com")
    .set("age", 25)
    .build(validate=True))
```

### 4. 数据生成器 (Generator)

生成测试和示例数据。

```python
from app.platform.data import DataGenerator

generator = DataGenerator()

# 生成单个实例
instance = generator.generate("user", count=1)[0]

# 生成多个实例
instances = generator.generate("user", count=10)

# 使用覆盖值
instances = generator.generate(
    "user",
    count=5,
    name="Custom Name",
    age=30,
)
```

### 5. 数据转换器 (Transformer)

在不同数据格式和结构之间转换。

```python
from app.platform.data import get_transformer, TransformRule, TransformDirection

transformer = get_transformer()

# 注册转换规则
transformer.register_transformation(
    "user_to_api",
    [
        TransformRule(
            source_field="name",
            target_field="username",
        ),
        TransformRule(
            source_field="email",
            target_field="email_address",
            transform_func=lambda x: x.lower(),
        ),
    ],
)

# 执行转换
data = {"name": "John", "email": "John@Example.com"}
result = transformer.transform(data, "user_to_api", TransformDirection.FORWARD)
# 结果: {"username": "John", "email_address": "john@example.com"}

# 模式间转换
result = transformer.transform_between_schemas(
    data,
    source_schema_id="user",
    target_schema_id="api_user",
)
```

### 6. 数据序列化器 (Serializer)

支持多种序列化格式。

```python
from app.platform.data import get_serializer, SerializationFormat

serializer = get_serializer()

data = {"id": 1, "name": "John", "email": "john@example.com"}

# JSON序列化
json_str = serializer.serialize(data, SerializationFormat.JSON)
# 反序列化
data = serializer.deserialize(json_str, SerializationFormat.JSON)

# YAML序列化
yaml_str = serializer.serialize(data, SerializationFormat.YAML)

# CSV序列化（需要列表）
csv_str = serializer.serialize([data], SerializationFormat.CSV)

# XML序列化
xml_str = serializer.serialize(data, SerializationFormat.XML)
```

### 7. 数据关系管理 (Relationship)

管理数据之间的关系和引用。

```python
from app.platform.data import (
    get_relationship_manager,
    RelationshipType,
)

manager = get_relationship_manager()

# 注册关系
manager.register(
    relationship_id="user_orders",
    name="用户订单关系",
    source_schema_id="user",
    target_schema_id="order",
    relationship_type=RelationshipType.ONE_TO_MANY,
    source_field="id",
    target_field="user_id",
    cascade_delete=True,
)

# 解析引用
user_data = {"id": 1, "name": "John", "orders": [1, 2, 3]}
resolved = manager.resolve_references(user_data, "user", depth=1)
```

## 高级特性

### 嵌套对象

```python
# 定义嵌套模式
address_schema = DataSchema(
    schema_id="address",
    name="地址",
    fields=[
        FieldDefinition("street", SchemaType.STRING),
        FieldDefinition("city", SchemaType.STRING),
        FieldDefinition("zipcode", SchemaType.STRING),
    ],
)

user_schema = DataSchema(
    schema_id="user",
    name="用户",
    fields=[
        FieldDefinition("id", SchemaType.INTEGER),
        FieldDefinition("name", SchemaType.STRING),
        FieldDefinition(
            "address",
            SchemaType.OBJECT,
            nested_schema=address_schema,
        ),
    ],
)
```

### 数组类型

```python
schema = DataSchema(
    schema_id="order",
    name="订单",
    fields=[
        FieldDefinition("id", SchemaType.INTEGER),
        FieldDefinition(
            "items",
            SchemaType.ARRAY,
            array_item_schema=item_schema,  # 数组元素模式
            validation_rules={"minItems": 1},
        ),
    ],
)
```

### 枚举类型

```python
schema = DataSchema(
    schema_id="status",
    name="状态",
    fields=[
        FieldDefinition(
            "status",
            SchemaType.ENUM,
            enum_values=["pending", "active", "inactive"],
        ),
    ],
)
```

### 引用类型

```python
schema = DataSchema(
    schema_id="order",
    name="订单",
    fields=[
        FieldDefinition("id", SchemaType.INTEGER),
        FieldDefinition(
            "user_id",
            SchemaType.REFERENCE,
            reference_schema="user",  # 引用user模式
        ),
    ],
)
```

## API接口

### 模式管理

- `POST /api/platform/data/schemas` - 创建模式
- `GET /api/platform/data/schemas` - 列出所有模式
- `GET /api/platform/data/schemas/{schema_id}` - 获取模式
- `GET /api/platform/data/schemas/{schema_id}/json-schema` - 获取JSON Schema

### 数据操作

- `POST /api/platform/data/schemas/{schema_id}/validate` - 验证数据
- `POST /api/platform/data/schemas/{schema_id}/create` - 创建数据实例
- `POST /api/platform/data/schemas/{schema_id}/generate` - 生成示例数据

### 数据转换

- `POST /api/platform/data/transform` - 转换数据
- `POST /api/platform/data/serialize` - 序列化数据
- `POST /api/platform/data/deserialize` - 反序列化数据

### 关系管理

- `POST /api/platform/data/relationships` - 创建关系
- `GET /api/platform/data/relationships` - 列出所有关系
- `POST /api/platform/data/schemas/{schema_id}/resolve` - 解析引用

## 使用示例

### 完整示例

```python
from app.platform.data import (
    DataSchema, FieldDefinition, SchemaType,
    get_registry, get_factory, get_validator,
    DataBuilder, DataGenerator,
)

# 1. 定义模式
schema = DataSchema(
    schema_id="product",
    name="产品",
    fields=[
        FieldDefinition("id", SchemaType.INTEGER, required=True),
        FieldDefinition("name", SchemaType.STRING, required=True),
        FieldDefinition("price", SchemaType.FLOAT, required=True),
        FieldDefinition("category", SchemaType.STRING, required=False),
    ],
)

# 2. 注册模式
registry = get_registry()
registry.register(schema)

# 3. 创建数据实例
factory = get_factory()
product = factory.create(
    schema_id="product",
    data={"id": 1, "name": "Laptop", "price": 999.99},
)

# 4. 验证数据
validator = get_validator()
result = validator.validate(product, schema)
assert result.valid

# 5. 生成示例数据
generator = DataGenerator()
examples = generator.generate("product", count=10)
```

## 最佳实践

1. **模式设计**
   - 使用有意义的模式ID和名称
   - 为字段添加描述
   - 合理设置验证规则

2. **数据验证**
   - 始终在生产环境中启用验证
   - 提供清晰的错误消息
   - 处理验证错误

3. **数据创建**
   - 使用构建器模式提高可读性
   - 合理使用默认值
   - 避免硬编码数据

4. **性能优化**
   - 缓存模式定义
   - 批量处理数据
