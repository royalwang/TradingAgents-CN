"""
数据验证器
基于模式验证数据
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re

from .schema import DataSchema, SchemaType, SchemaRegistry, FieldDefinition, get_registry


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    value: Any = None
    code: str = "validation_error"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
            "code": self.code,
        }


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "valid": self.valid,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": self.warnings,
        }


class DataValidator:
    """数据验证器"""
    
    def __init__(self, registry: Optional[SchemaRegistry] = None):
        self.registry = registry or get_registry()
    
    def validate(
        self,
        data: Dict[str, Any],
        schema: DataSchema,
    ) -> ValidationResult:
        """验证数据"""
        errors = []
        warnings = []
        
        # 检查必需字段
        required_fields = {field.name for field in schema.fields if field.required}
        provided_fields = set(data.keys())
        missing_fields = required_fields - provided_fields
        
        for field_name in missing_fields:
            errors.append(ValidationError(
                field=field_name,
                message=f"Required field '{field_name}' is missing",
                code="missing_required_field",
            ))
        
        # 验证每个字段
        for field_def in schema.fields:
            field_name = field_def.name
            
            if field_name not in data:
                if field_def.default is not None:
                    # 使用默认值
                    continue
                elif not field_def.required:
                    # 可选字段，跳过
                    continue
                else:
                    # 已在上面处理
                    continue
            
            value = data.get(field_name)
            
            # 验证字段
            field_errors = self._validate_field(value, field_def, schema)
            errors.extend(field_errors)
        
        # 检查未知字段
        schema_field_names = {field.name for field in schema.fields}
        unknown_fields = provided_fields - schema_field_names
        if unknown_fields:
            warnings.append(f"Unknown fields: {', '.join(unknown_fields)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def _validate_field(
        self,
        value: Any,
        field_def: FieldDefinition,
        schema: DataSchema,
    ) -> List[ValidationError]:
        """验证单个字段"""
        errors = []
        
        # 类型验证
        type_error = self._validate_type(value, field_def, schema)
        if type_error:
            errors.append(type_error)
            return errors  # 类型错误时不再继续验证
        
        # 枚举验证
        if field_def.enum_values and value not in field_def.enum_values:
            errors.append(ValidationError(
                field=field_def.name,
                message=f"Value must be one of {field_def.enum_values}",
                value=value,
                code="enum_error",
            ))
        
        # 自定义验证规则
        for rule, rule_value in field_def.validation_rules.items():
            rule_error = self._apply_validation_rule(
                value, field_def, rule, rule_value
            )
            if rule_error:
                errors.append(rule_error)
        
        return errors
    
    def _validate_type(
        self,
        value: Any,
        field_def: FieldDefinition,
        schema: DataSchema,
    ) -> Optional[ValidationError]:
        """验证类型"""
        if value is None:
            if field_def.required:
                return ValidationError(
                    field=field_def.name,
                    message="Field cannot be None",
                    value=value,
                    code="null_value",
                )
            return None
        
        field_type = field_def.field_type
        
        if field_type == SchemaType.STRING:
            if not isinstance(value, str):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected string, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
        elif field_type == SchemaType.INTEGER:
            if not isinstance(value, int):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected integer, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
        elif field_type == SchemaType.FLOAT:
            if not isinstance(value, (int, float)):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected number, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
        elif field_type == SchemaType.BOOLEAN:
            if not isinstance(value, bool):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected boolean, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
        elif field_type == SchemaType.DATETIME:
            if not isinstance(value, (str, datetime)):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected datetime or string, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
        elif field_type == SchemaType.ARRAY:
            if not isinstance(value, list):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected array, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
            # 验证数组元素
            if field_def.array_item_schema:
                for i, item in enumerate(value):
                    item_errors = self._validate_field(
                        item,
                        FieldDefinition(
                            name=f"{field_def.name}[{i}]",
                            field_type=SchemaType.OBJECT,
                            nested_schema=field_def.array_item_schema,
                        ),
                        schema,
                    )
                    if item_errors:
                        return item_errors[0]  # 返回第一个错误
        elif field_type == SchemaType.OBJECT:
            if not isinstance(value, dict):
                return ValidationError(
                    field=field_def.name,
                    message=f"Expected object, got {type(value).__name__}",
                    value=value,
                    code="type_error",
                )
            # 验证嵌套对象
            if field_def.nested_schema:
                nested_result = self.validate(value, field_def.nested_schema)
                if not nested_result.valid:
                    # 将嵌套错误添加到当前字段
                    for error in nested_result.errors:
                        error.field = f"{field_def.name}.{error.field}"
                    return nested_result.errors[0] if nested_result.errors else None
        elif field_type == SchemaType.REFERENCE:
            # 验证引用模式
            if field_def.reference_schema:
                ref_schema = self.registry.get(field_def.reference_schema)
                if ref_schema:
                    ref_result = self.validate(value, ref_schema)
                    if not ref_result.valid:
                        return ref_result.errors[0] if ref_result.errors else None
        
        return None
    
    def _apply_validation_rule(
        self,
        value: Any,
        field_def: 'FieldDefinition',
        rule: str,
        rule_value: Any,
    ) -> Optional[ValidationError]:
        """应用验证规则"""
        if rule == "minLength" and isinstance(value, str):
            if len(value) < rule_value:
                return ValidationError(
                    field=field_def.name,
                    message=f"String length must be at least {rule_value}",
                    value=value,
                    code="min_length_error",
                )
        elif rule == "maxLength" and isinstance(value, str):
            if len(value) > rule_value:
                return ValidationError(
                    field=field_def.name,
                    message=f"String length must be at most {rule_value}",
                    value=value,
                    code="max_length_error",
                )
        elif rule == "minimum" and isinstance(value, (int, float)):
            if value < rule_value:
                return ValidationError(
                    field=field_def.name,
                    message=f"Value must be at least {rule_value}",
                    value=value,
                    code="minimum_error",
                )
        elif rule == "maximum" and isinstance(value, (int, float)):
            if value > rule_value:
                return ValidationError(
                    field=field_def.name,
                    message=f"Value must be at most {rule_value}",
                    value=value,
                    code="maximum_error",
                )
        elif rule == "pattern" and isinstance(value, str):
            if not re.match(rule_value, value):
                return ValidationError(
                    field=field_def.name,
                    message=f"Value does not match pattern {rule_value}",
                    value=value,
                    code="pattern_error",
                )
        elif rule == "minItems" and isinstance(value, list):
            if len(value) < rule_value:
                return ValidationError(
                    field=field_def.name,
                    message=f"Array must have at least {rule_value} items",
                    value=value,
                    code="min_items_error",
                )
        elif rule == "maxItems" and isinstance(value, list):
            if len(value) > rule_value:
                return ValidationError(
                    field=field_def.name,
                    message=f"Array must have at most {rule_value} items",
                    value=value,
                    code="max_items_error",
                )
        
        return None


# 全局验证器实例
_global_validator: Optional[DataValidator] = None


def get_validator() -> DataValidator:
    """获取全局验证器"""
    global _global_validator
    if _global_validator is None:
        _global_validator = DataValidator()
    return _global_validator

