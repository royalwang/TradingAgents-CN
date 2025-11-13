"""
数据转换器
在不同数据格式和结构之间转换
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .schema import DataSchema, SchemaType, SchemaRegistry, get_registry


class TransformDirection(str, Enum):
    """转换方向"""
    FORWARD = "forward"  # 正向转换
    BACKWARD = "backward"  # 反向转换
    BIDIRECTIONAL = "bidirectional"  # 双向转换


@dataclass
class TransformRule:
    """转换规则"""
    source_field: str
    target_field: str
    transform_func: Optional[Callable] = None
    direction: TransformDirection = TransformDirection.FORWARD
    default_value: Any = None
    required: bool = False
    
    def apply(self, data: Dict[str, Any], direction: TransformDirection) -> Dict[str, Any]:
        """应用转换规则"""
        if self.direction not in [direction, TransformDirection.BIDIRECTIONAL]:
            return {}
        
        result = {}
        
        if direction == TransformDirection.FORWARD:
            source = self.source_field
            target = self.target_field
        else:
            source = self.target_field
            target = self.source_field
        
        if source in data:
            value = data[source]
            
            if self.transform_func:
                value = self.transform_func(value)
            
            result[target] = value
        elif self.required and self.default_value is not None:
            result[target] = self.default_value
        
        return result


class DataTransformer:
    """数据转换器"""
    
    def __init__(self, registry: Optional[SchemaRegistry] = None):
        self.registry = registry or get_registry()
        self._rules: Dict[str, List[TransformRule]] = {}
    
    def register_transformation(
        self,
        name: str,
        rules: List[TransformRule],
    ):
        """注册转换规则"""
        self._rules[name] = rules
    
    def transform(
        self,
        data: Dict[str, Any],
        transformation_name: str,
        direction: TransformDirection = TransformDirection.FORWARD,
    ) -> Dict[str, Any]:
        """转换数据"""
        if transformation_name not in self._rules:
            raise ValueError(f"Transformation {transformation_name} not found")
        
        rules = self._rules[transformation_name]
        result = {}
        
        for rule in rules:
            transformed = rule.apply(data, direction)
            result.update(transformed)
        
        return result
    
    def transform_between_schemas(
        self,
        data: Dict[str, Any],
        source_schema_id: str,
        target_schema_id: str,
    ) -> Dict[str, Any]:
        """在模式之间转换数据"""
        source_schema = self.registry.get(source_schema_id)
        target_schema = self.registry.get(target_schema_id)
        
        if not source_schema or not target_schema:
            raise ValueError("Source or target schema not found")
        
        result = {}
        
        # 创建字段映射
        source_fields = {field.name: field for field in source_schema.fields}
        target_fields = {field.name: field for field in target_schema.fields}
        
        # 直接映射相同名称的字段
        for field_name, target_field in target_fields.items():
            if field_name in source_fields:
                source_field = source_fields[field_name]
                if source_field.field_type == target_field.field_type:
                    if field_name in data:
                        result[field_name] = data[field_name]
                else:
                    # 类型转换
                    result[field_name] = self._convert_type(
                        data.get(field_name),
                        source_field.field_type,
                        target_field.field_type,
                    )
        
        return result
    
    def _convert_type(
        self,
        value: Any,
        source_type: SchemaType,
        target_type: SchemaType,
    ) -> Any:
        """类型转换"""
        if value is None:
            return None
        
        # 相同类型，直接返回
        if source_type == target_type:
            return value
        
        # 字符串转换
        if target_type.value == "string":
            return str(value)
        
        # 数字转换
        if target_type.value in ["integer", "float"]:
            try:
                if target_type.value == "integer":
                    return int(value)
                else:
                    return float(value)
            except (ValueError, TypeError):
                return 0
        
        # 布尔转换
        if target_type.value == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ["true", "1", "yes", "on"]
            return bool(value)
        
        # 数组转换
        if target_type.value == "array":
            if isinstance(value, list):
                return value
            return [value]
        
        # 对象转换
        if target_type.value == "object":
            if isinstance(value, dict):
                return value
            return {"value": value}
        
        return value


# 全局转换器实例
_global_transformer: Optional[DataTransformer] = None


def get_transformer() -> DataTransformer:
    """获取全局转换器"""
    global _global_transformer
    if _global_transformer is None:
        _global_transformer = DataTransformer()
    return _global_transformer

