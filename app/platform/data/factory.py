"""
数据工厂
从声明式模式创建数据实例
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import random
import string

from .schema import DataSchema, FieldDefinition, SchemaType, SchemaRegistry, get_registry
from .validator import DataValidator, get_validator


class DataFactory:
    """数据工厂"""
    
    def __init__(
        self,
        registry: Optional[SchemaRegistry] = None,
        validator: Optional[DataValidator] = None,
    ):
        self.registry = registry or get_registry()
        self.validator = validator or get_validator()
    
    def create(
        self,
        schema_id: str,
        data: Optional[Dict[str, Any]] = None,
        validate: bool = True,
        fill_defaults: bool = True,
    ) -> Dict[str, Any]:
        """从模式创建数据实例"""
        schema = self.registry.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        instance = {}
        
        # 使用提供的数据或创建新实例
        if data:
            instance.update(data)
        
        # 填充默认值
        if fill_defaults:
            for field_def in schema.fields:
                if field_def.name not in instance:
                    if field_def.default is not None:
                        instance[field_def.name] = self._get_default_value(field_def)
                    elif not field_def.required:
                        # 可选字段，跳过
                        continue
        
        # 验证数据
        if validate:
            result = self.validator.validate(instance, schema)
            if not result.valid:
                raise ValueError(f"Validation failed: {result.errors}")
        
        return instance
    
    def _get_default_value(self, field_def: FieldDefinition) -> Any:
        """获取默认值"""
        if field_def.default is not None:
            return field_def.default
        
        # 根据类型生成默认值
        if field_def.field_type == SchemaType.STRING:
            return ""
        elif field_def.field_type == SchemaType.INTEGER:
            return 0
        elif field_def.field_type == SchemaType.FLOAT:
            return 0.0
        elif field_def.field_type == SchemaType.BOOLEAN:
            return False
        elif field_def.field_type == SchemaType.ARRAY:
            return []
        elif field_def.field_type == SchemaType.OBJECT:
            return {}
        elif field_def.field_type == SchemaType.DATETIME:
            return datetime.utcnow().isoformat()
        elif field_def.field_type == SchemaType.ENUM and field_def.enum_values:
            return field_def.enum_values[0]
        
        return None


class DataBuilder:
    """数据构建器（流式API）"""
    
    def __init__(
        self,
        schema_id: str,
        factory: Optional[DataFactory] = None,
    ):
        self.schema_id = schema_id
        self.factory = factory or DataFactory()
        self._data: Dict[str, Any] = {}
    
    def set(self, field: str, value: Any) -> 'DataBuilder':
        """设置字段值"""
        self._data[field] = value
        return self
    
    def set_many(self, data: Dict[str, Any]) -> 'DataBuilder':
        """批量设置字段值"""
        self._data.update(data)
        return self
    
    def build(self, validate: bool = True, fill_defaults: bool = True) -> Dict[str, Any]:
        """构建数据实例"""
        return self.factory.create(
            schema_id=self.schema_id,
            data=self._data,
            validate=validate,
            fill_defaults=fill_defaults,
        )


class DataGenerator:
    """数据生成器（用于测试和示例）"""
    
    def __init__(self, factory: Optional[DataFactory] = None):
        self.factory = factory or DataFactory()
    
    def generate(
        self,
        schema_id: str,
        count: int = 1,
        **overrides: Any,
    ) -> List[Dict[str, Any]]:
        """生成示例数据"""
        schema = self.factory.registry.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        instances = []
        for _ in range(count):
            instance = {}
            
            for field_def in schema.fields:
                if field_def.name in overrides:
                    instance[field_def.name] = overrides[field_def.name]
                else:
                    instance[field_def.name] = self._generate_value(field_def)
            
            instances.append(instance)
        
        return instances
    
    def _generate_value(self, field_def: FieldDefinition) -> Any:
        """生成字段值"""
        if field_def.default is not None:
            return field_def.default
        
        field_type = field_def.field_type
        
        if field_type == SchemaType.STRING:
            if field_def.enum_values:
                return random.choice(field_def.enum_values)
            min_len = field_def.validation_rules.get("minLength", 5)
            max_len = field_def.validation_rules.get("maxLength", 20)
            length = random.randint(min_len, max_len)
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        elif field_type == SchemaType.INTEGER:
            min_val = field_def.validation_rules.get("minimum", 0)
            max_val = field_def.validation_rules.get("maximum", 100)
            return random.randint(min_val, max_val)
        elif field_type == SchemaType.FLOAT:
            min_val = field_def.validation_rules.get("minimum", 0.0)
            max_val = field_def.validation_rules.get("maximum", 100.0)
            return round(random.uniform(min_val, max_val), 2)
        elif field_type == SchemaType.BOOLEAN:
            return random.choice([True, False])
        elif field_type == SchemaType.DATETIME:
            return datetime.utcnow().isoformat()
        elif field_type == SchemaType.ARRAY:
            min_items = field_def.validation_rules.get("minItems", 0)
            max_items = field_def.validation_rules.get("maxItems", 5)
            count = random.randint(min_items, max_items)
            if field_def.array_item_schema:
                return [
                    self._generate_value_from_schema(field_def.array_item_schema)
                    for _ in range(count)
                ]
            return []
        elif field_type == SchemaType.OBJECT:
            if field_def.nested_schema:
                nested_instance = {}
                for nested_field in field_def.nested_schema.fields:
                    nested_instance[nested_field.name] = self._generate_value(nested_field)
                return nested_instance
            return {}
        elif field_type == SchemaType.ENUM and field_def.enum_values:
            return random.choice(field_def.enum_values)
        
        return None
    
    def _generate_value_from_schema(self, schema: DataSchema) -> Dict[str, Any]:
        """从模式生成值"""
        instance = {}
        for field_def in schema.fields:
            instance[field_def.name] = self._generate_value(field_def)
        return instance


# 全局工厂实例
_global_factory: Optional[DataFactory] = None


def get_factory() -> DataFactory:
    """获取全局数据工厂"""
    global _global_factory
    if _global_factory is None:
        _global_factory = DataFactory()
    return _global_factory

