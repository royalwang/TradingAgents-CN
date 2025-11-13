"""
数据关系管理
管理数据之间的关系和引用
"""
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RelationshipType(str, Enum):
    """关系类型"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    REFERENCE = "reference"  # 简单引用


@dataclass
class DataRelationship:
    """数据关系"""
    relationship_id: str
    name: str
    source_schema_id: str
    target_schema_id: str
    relationship_type: RelationshipType
    source_field: str  # 源字段名
    target_field: str  # 目标字段名
    cascade_delete: bool = False
    cascade_update: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "relationship_id": self.relationship_id,
            "name": self.name,
            "source_schema_id": self.source_schema_id,
            "target_schema_id": self.target_schema_id,
            "relationship_type": self.relationship_type.value,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "cascade_delete": self.cascade_delete,
            "cascade_update": self.cascade_update,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class RelationshipManager:
    """关系管理器"""
    
    def __init__(self):
        self._relationships: Dict[str, DataRelationship] = {}
        self._by_source: Dict[str, List[str]] = {}  # schema_id -> relationship_ids
        self._by_target: Dict[str, List[str]] = {}  # schema_id -> relationship_ids
    
    def register(
        self,
        relationship_id: str,
        name: str,
        source_schema_id: str,
        target_schema_id: str,
        relationship_type: RelationshipType,
        source_field: str,
        target_field: str,
        cascade_delete: bool = False,
        cascade_update: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataRelationship:
        """注册关系"""
        if relationship_id in self._relationships:
            raise ValueError(f"Relationship {relationship_id} already registered")
        
        relationship = DataRelationship(
            relationship_id=relationship_id,
            name=name,
            source_schema_id=source_schema_id,
            target_schema_id=target_schema_id,
            relationship_type=relationship_type,
            source_field=source_field,
            target_field=target_field,
            cascade_delete=cascade_delete,
            cascade_update=cascade_update,
            metadata=metadata or {},
        )
        
        self._relationships[relationship_id] = relationship
        
        # 建立索引
        if source_schema_id not in self._by_source:
            self._by_source[source_schema_id] = []
        self._by_source[source_schema_id].append(relationship_id)
        
        if target_schema_id not in self._by_target:
            self._by_target[target_schema_id] = []
        self._by_target[target_schema_id].append(relationship_id)
        
        return relationship
    
    def get(self, relationship_id: str) -> Optional[DataRelationship]:
        """获取关系"""
        return self._relationships.get(relationship_id)
    
    def get_by_source(self, schema_id: str) -> List[DataRelationship]:
        """获取源模式的所有关系"""
        relationship_ids = self._by_source.get(schema_id, [])
        return [self._relationships[rid] for rid in relationship_ids]
    
    def get_by_target(self, schema_id: str) -> List[DataRelationship]:
        """获取目标模式的所有关系"""
        relationship_ids = self._by_target.get(schema_id, [])
        return [self._relationships[rid] for rid in relationship_ids]
    
    def resolve_references(
        self,
        data: Dict[str, Any],
        schema_id: str,
        resolve_depth: int = 1,
    ) -> Dict[str, Any]:
        """解析数据中的引用关系"""
        if resolve_depth <= 0:
            return data
        
        result = data.copy()
        
        # 获取所有关系
        relationships = self.get_by_source(schema_id)
        
        for relationship in relationships:
            source_field = relationship.source_field
            
            if source_field not in result:
                continue
            
            value = result[source_field]
            
            # 根据关系类型解析
            if relationship.relationship_type == RelationshipType.ONE_TO_ONE:
                # 一对一：直接解析
                if value:
                    # 这里应该从数据存储中获取，简化处理
                    result[f"{source_field}_resolved"] = {"id": value}
            elif relationship.relationship_type == RelationshipType.ONE_TO_MANY:
                # 一对多：解析列表
                if isinstance(value, list):
                    result[f"{source_field}_resolved"] = [
                        {"id": item} for item in value
                    ]
            elif relationship.relationship_type == RelationshipType.MANY_TO_ONE:
                # 多对一：解析单个值
                if value:
                    result[f"{source_field}_resolved"] = {"id": value}
            elif relationship.relationship_type == RelationshipType.REFERENCE:
                # 简单引用
                if value:
                    result[f"{source_field}_resolved"] = {"id": value}
        
        return result
    
    def validate_relationship(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        relationship: DataRelationship,
    ) -> tuple[bool, Optional[str]]:
        """验证关系数据"""
        source_value = source_data.get(relationship.source_field)
        target_value = target_data.get(relationship.target_field)
        
        if relationship.relationship_type == RelationshipType.ONE_TO_ONE:
            # 一对一：源值应该等于目标值
            if source_value != target_value:
                return False, f"One-to-one relationship mismatch: {source_value} != {target_value}"
        elif relationship.relationship_type == RelationshipType.ONE_TO_MANY:
            # 一对多：目标值应该在源值的列表中
            if not isinstance(source_value, list):
                return False, "Source field must be a list for one-to-many relationship"
            if target_value not in source_value:
                return False, f"Target value {target_value} not in source list"
        elif relationship.relationship_type == RelationshipType.MANY_TO_ONE:
            # 多对一：源值应该等于目标值
            if source_value != target_value:
                return False, f"Many-to-one relationship mismatch: {source_value} != {target_value}"
        elif relationship.relationship_type == RelationshipType.REFERENCE:
            # 引用：只需要值存在
            if not source_value or not target_value:
                return False, "Reference values cannot be empty"
        
        return True, None
    
    def list(self) -> List[DataRelationship]:
        """列出所有关系"""
        return list(self._relationships.values())
    
    def unregister(self, relationship_id: str) -> bool:
        """注销关系"""
        if relationship_id not in self._relationships:
            return False
        
        relationship = self._relationships[relationship_id]
        del self._relationships[relationship_id]
        
        # 从索引中移除
        if relationship.source_schema_id in self._by_source:
            if relationship_id in self._by_source[relationship.source_schema_id]:
                self._by_source[relationship.source_schema_id].remove(relationship_id)
        
        if relationship.target_schema_id in self._by_target:
            if relationship_id in self._by_target[relationship.target_schema_id]:
                self._by_target[relationship.target_schema_id].remove(relationship_id)
        
        return True


# 全局关系管理器实例
_global_manager: Optional[RelationshipManager] = None


def get_relationship_manager() -> RelationshipManager:
    """获取全局关系管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = RelationshipManager()
    return _global_manager

