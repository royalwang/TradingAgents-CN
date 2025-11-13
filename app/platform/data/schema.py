"""
数据模式定义
声明式数据模式定义和管理
"""
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import yaml


class SchemaType(str, Enum):
    """模式类型"""
    OBJECT = "object"
    ARRAY = "array"
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    ENUM = "enum"
    REFERENCE = "reference"  # 引用其他模式
    UNION = "union"  # 联合类型
    ANY = "any"


@dataclass
class FieldDefinition:
    """字段定义"""
    name: str
    field_type: SchemaType
    description: Optional[str] = None
    required: bool = True
    default: Any = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    enum_values: Optional[List[Any]] = None
    reference_schema: Optional[str] = None  # 引用的模式ID
    union_types: Optional[List[SchemaType]] = None
    nested_schema: Optional['DataSchema'] = None  # 嵌套对象模式
    array_item_schema: Optional['DataSchema'] = None  # 数组元素模式
    transform: Optional[Callable] = None  # 数据转换函数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
        }
        
        if self.description:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        if self.validation_rules:
            result["validation"] = self.validation_rules
        if self.enum_values:
            result["enum"] = self.enum_values
        if self.reference_schema:
            result["$ref"] = self.reference_schema
        if self.union_types:
            result["union"] = [t.value for t in self.union_types]
        if self.nested_schema:
            result["properties"] = self.nested_schema.to_dict()
        if self.array_item_schema:
            result["items"] = self.array_item_schema.to_dict()
        
        return result


@dataclass
class DataSchema:
    """数据模式"""
    schema_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    fields: List[FieldDefinition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "schema_id": self.schema_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "object",
            "properties": {field.name: field.to_dict() for field in self.fields},
            "required": [field.name for field in self.fields if field.required],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def to_json_schema(self) -> Dict[str, Any]:
        """转换为JSON Schema格式"""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": self.name,
            "description": self.description,
            "properties": {},
            "required": [],
        }
        
        for field_def in self.fields:
            prop = self._field_to_json_schema_property(field_def)
            schema["properties"][field_def.name] = prop
            
            if field_def.required:
                schema["required"].append(field_def.name)
        
        return schema
    
    def _field_to_json_schema_property(self, field_def: FieldDefinition) -> Dict[str, Any]:
        """将字段定义转换为JSON Schema属性"""
        prop = {}
        
        # 处理类型
        if field_def.field_type == SchemaType.OBJECT:
            if field_def.nested_schema:
                prop = field_def.nested_schema.to_json_schema()
            else:
                prop["type"] = "object"
        elif field_def.field_type == SchemaType.ARRAY:
            prop["type"] = "array"
            if field_def.array_item_schema:
                prop["items"] = field_def.array_item_schema.to_json_schema()
            else:
                prop["items"] = {"type": "string"}
        elif field_def.field_type == SchemaType.STRING:
            prop["type"] = "string"
        elif field_def.field_type == SchemaType.INTEGER:
            prop["type"] = "integer"
        elif field_def.field_type == SchemaType.FLOAT:
            prop["type"] = "number"
        elif field_def.field_type == SchemaType.BOOLEAN:
            prop["type"] = "boolean"
        elif field_def.field_type == SchemaType.DATETIME:
            prop["type"] = "string"
            prop["format"] = "date-time"
        elif field_def.field_type == SchemaType.ENUM:
            prop["type"] = "string"
            prop["enum"] = field_def.enum_values
        elif field_def.field_type == SchemaType.REFERENCE:
            prop["$ref"] = f"#/definitions/{field_def.reference_schema}"
        elif field_def.field_type == SchemaType.UNION:
            prop["oneOf"] = [
                self._field_to_json_schema_property(
                    FieldDefinition(name="", field_type=t)
                ) for t in field_def.union_types
            ]
        elif field_def.field_type == SchemaType.ANY:
            prop = {}
        
        # 添加验证规则
        if field_def.validation_rules:
            for rule, value in field_def.validation_rules.items():
                if rule == "minLength" and "type" in prop and prop["type"] == "string":
                    prop["minLength"] = value
                elif rule == "maxLength" and "type" in prop and prop["type"] == "string":
                    prop["maxLength"] = value
                elif rule == "minimum" and "type" in prop and prop["type"] in ["integer", "number"]:
                    prop["minimum"] = value
                elif rule == "maximum" and "type" in prop and prop["type"] in ["integer", "number"]:
                    prop["maximum"] = value
                elif rule == "pattern" and "type" in prop and prop["type"] == "string":
                    prop["pattern"] = value
                else:
                    prop[rule] = value
        
        # 添加默认值
        if field_def.default is not None:
            prop["default"] = field_def.default
        
        # 添加描述
        if field_def.description:
            prop["description"] = field_def.description
        
        return prop
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSchema':
        """从字典创建模式"""
        fields = []
        for field_name, field_data in data.get("properties", {}).items():
            field_def = cls._field_from_dict(field_name, field_data)
            fields.append(field_def)
        
        return cls(
            schema_id=data.get("schema_id", data.get("$id", "")),
            name=data.get("name", data.get("title", "")),
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            fields=fields,
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def _field_from_dict(cls, name: str, field_data: Dict[str, Any]) -> FieldDefinition:
        """从字典创建字段定义"""
        field_type_str = field_data.get("type", "string")
        field_type = SchemaType(field_type_str)
        
        return FieldDefinition(
            name=name,
            field_type=field_type,
            description=field_data.get("description"),
            required=field_data.get("required", True),
            default=field_data.get("default"),
            validation_rules=field_data.get("validation", {}),
            enum_values=field_data.get("enum"),
            reference_schema=field_data.get("$ref"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DataSchema':
        """从JSON字符串创建模式"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'DataSchema':
        """从YAML字符串创建模式"""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class SchemaRegistry:
    """模式注册表"""
    
    def __init__(self):
        self._schemas: Dict[str, DataSchema] = {}
    
    def register(self, schema: DataSchema) -> DataSchema:
        """注册模式"""
        if schema.schema_id in self._schemas:
            raise ValueError(f"Schema {schema.schema_id} already registered")
        
        self._schemas[schema.schema_id] = schema
        return schema
    
    def get(self, schema_id: str) -> Optional[DataSchema]:
        """获取模式"""
        return self._schemas.get(schema_id)
    
    def list(self) -> List[DataSchema]:
        """列出所有模式"""
        return list(self._schemas.values())
    
    def unregister(self, schema_id: str) -> bool:
        """注销模式"""
        if schema_id in self._schemas:
            del self._schemas[schema_id]
            return True
        return False
    
    def search(self, query: str) -> List[DataSchema]:
        """搜索模式"""
        query_lower = query.lower()
        result = []
        
        for schema in self._schemas.values():
            if (query_lower in schema.name.lower() or
                (schema.description and query_lower in schema.description.lower())):
                result.append(schema)
        
        return result


# 全局注册表实例
_global_registry = SchemaRegistry()


def get_registry() -> SchemaRegistry:
    """获取全局模式注册表"""
    return _global_registry

