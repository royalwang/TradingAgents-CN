"""
数据序列化器
支持多种序列化格式
"""
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import yaml
import csv
import io

from .schema import DataSchema, SchemaRegistry, get_registry


class SerializationFormat(str, Enum):
    """序列化格式"""
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    XML = "xml"
    TOML = "toml"


class DataSerializer:
    """数据序列化器"""
    
    def __init__(self, registry: Optional[SchemaRegistry] = None):
        self.registry = registry or get_registry()
    
    def serialize(
        self,
        data: Dict[str, Any],
        format: SerializationFormat = SerializationFormat.JSON,
        schema_id: Optional[str] = None,
        **options: Any,
    ) -> str:
        """序列化数据"""
        if format == SerializationFormat.JSON:
            return self._serialize_json(data, **options)
        elif format == SerializationFormat.YAML:
            return self._serialize_yaml(data, **options)
        elif format == SerializationFormat.CSV:
            return self._serialize_csv(data, schema_id, **options)
        elif format == SerializationFormat.XML:
            return self._serialize_xml(data, **options)
        elif format == SerializationFormat.TOML:
            return self._serialize_toml(data, **options)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def deserialize(
        self,
        data_str: str,
        format: SerializationFormat = SerializationFormat.JSON,
        schema_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """反序列化数据"""
        if format == SerializationFormat.JSON:
            return self._deserialize_json(data_str)
        elif format == SerializationFormat.YAML:
            return self._deserialize_yaml(data_str)
        elif format == SerializationFormat.CSV:
            return self._deserialize_csv(data_str, schema_id)
        elif format == SerializationFormat.XML:
            return self._deserialize_xml(data_str)
        elif format == SerializationFormat.TOML:
            return self._deserialize_toml(data_str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _serialize_json(self, data: Dict[str, Any], **options: Any) -> str:
        """序列化为JSON"""
        indent = options.get("indent", 2)
        ensure_ascii = options.get("ensure_ascii", False)
        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    
    def _deserialize_json(self, data_str: str) -> Dict[str, Any]:
        """从JSON反序列化"""
        return json.loads(data_str)
    
    def _serialize_yaml(self, data: Dict[str, Any], **options: Any) -> str:
        """序列化为YAML"""
        default_flow_style = options.get("default_flow_style", False)
        allow_unicode = options.get("allow_unicode", True)
        return yaml.dump(
            data,
            default_flow_style=default_flow_style,
            allow_unicode=allow_unicode,
        )
    
    def _deserialize_yaml(self, data_str: str) -> Dict[str, Any]:
        """从YAML反序列化"""
        return yaml.safe_load(data_str) or {}
    
    def _serialize_csv(
        self,
        data: Dict[str, Any],
        schema_id: Optional[str],
        **options: Any,
    ) -> str:
        """序列化为CSV"""
        # 如果是单个对象，转换为列表
        if isinstance(data, dict) and not any(isinstance(v, (list, dict)) for v in data.values()):
            data = [data]
        
        if not isinstance(data, list):
            raise ValueError("CSV serialization requires a list of objects")
        
        if not data:
            return ""
        
        # 获取字段顺序
        fieldnames = list(data[0].keys())
        if schema_id:
            schema = self.registry.get(schema_id)
            if schema:
                fieldnames = [field.name for field in schema.fields if field.name in fieldnames]
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    def _deserialize_csv(
        self,
        data_str: str,
        schema_id: Optional[str],
    ) -> Dict[str, Any]:
        """从CSV反序列化"""
        reader = csv.DictReader(io.StringIO(data_str))
        rows = list(reader)
        
        if len(rows) == 1:
            return rows[0]
        elif len(rows) > 1:
            return {"items": rows}
        else:
            return {}
    
    def _serialize_xml(self, data: Dict[str, Any], **options: Any) -> str:
        """序列化为XML"""
        root_name = options.get("root_name", "root")
        
        def dict_to_xml(d: Dict[str, Any], root: str) -> str:
            xml = f"<{root}>"
            for key, value in d.items():
                if isinstance(value, dict):
                    xml += dict_to_xml(value, key)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            xml += dict_to_xml(item, key)
                        else:
                            xml += f"<{key}>{item}</{key}>"
                else:
                    xml += f"<{key}>{value}</{key}>"
            xml += f"</{root}>"
            return xml
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{dict_to_xml(data, root_name)}'
    
    def _deserialize_xml(self, data_str: str) -> Dict[str, Any]:
        """从XML反序列化"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data_str)
            
            def xml_to_dict(element) -> Any:
                if len(element) == 0:
                    return element.text
                result = {}
                for child in element:
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(xml_to_dict(child))
                    else:
                        result[child.tag] = xml_to_dict(child)
                return result
            
            return {root.tag: xml_to_dict(root)}
        except ImportError:
            raise ValueError("XML parsing requires xml.etree.ElementTree")
    
    def _serialize_toml(self, data: Dict[str, Any], **options: Any) -> str:
        """序列化为TOML"""
        try:
            import tomllib
            import tomli_w
        except ImportError:
            try:
                import tomli as tomllib
                import tomli_w
            except ImportError:
                raise ValueError("TOML serialization requires tomli/tomli-w")
        
        return tomli_w.dumps(data)
    
    def _deserialize_toml(self, data_str: str) -> Dict[str, Any]:
        """从TOML反序列化"""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                raise ValueError("TOML parsing requires tomli")
        
        return tomllib.loads(data_str)


# 全局序列化器实例
_global_serializer: Optional[DataSerializer] = None


def get_serializer() -> DataSerializer:
    """获取全局序列化器"""
    global _global_serializer
    if _global_serializer is None:
        _global_serializer = DataSerializer()
    return _global_serializer

