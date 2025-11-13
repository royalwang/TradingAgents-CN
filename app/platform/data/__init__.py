"""
声明式数据抽象模块
提供声明式数据定义、验证、创建和管理功能
"""

from .schema import DataSchema, FieldDefinition, SchemaRegistry, SchemaType
from .validator import DataValidator, ValidationResult
from .factory import DataFactory, DataBuilder
from .transformer import DataTransformer, TransformRule
from .serializer import DataSerializer, SerializationFormat
from .relationship import DataRelationship, RelationshipManager

__all__ = [
    "DataSchema",
    "FieldDefinition",
    "SchemaRegistry",
    "SchemaType",
    "DataValidator",
    "ValidationResult",
    "DataFactory",
    "DataBuilder",
    "DataTransformer",
    "TransformRule",
    "DataSerializer",
    "SerializationFormat",
    "DataRelationship",
    "RelationshipManager",
]

