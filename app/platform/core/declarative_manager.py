"""
通用声明式数据管理框架
为平台各模块提供统一的YAML声明式管理能力
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
from pathlib import Path
import yaml
from datetime import datetime

T = TypeVar('T')


class DeclarativeYAMLLoader(ABC, Generic[T]):
    """通用YAML加载器基类"""
    
    def __init__(self, root_key: str):
        """
        初始化加载器
        
        Args:
            root_key: YAML根键名，如 "agents", "workflows" 等
        """
        self.root_key = root_key
    
    def load_from_file(self, file_path: str) -> List[T]:
        """从YAML文件加载"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return self.load_from_dict(data)
    
    def load_from_string(self, yaml_str: str) -> List[T]:
        """从YAML字符串加载"""
        data = yaml.safe_load(yaml_str)
        return self.load_from_dict(data)
    
    def load_from_dict(self, data: Dict[str, Any]) -> List[T]:
        """从字典加载"""
        items = []
        
        # 支持两种格式：
        # 1. 列表格式: {root_key: [ {...}, {...} ]}
        # 2. 对象格式: {root_key: { id: {...}, id2: {...} }}
        
        if isinstance(data, dict):
            if self.root_key in data:
                items_data = data[self.root_key]
            else:
                # 整个字典就是items
                items_data = data
        elif isinstance(data, list):
            items_data = data
        else:
            raise ValueError(f"Invalid YAML format: expected dict or list")
        
        # 处理列表格式
        if isinstance(items_data, list):
            for item in items_data:
                parsed_item = self._parse_item(item)
                items.append(parsed_item)
        # 处理对象格式
        elif isinstance(items_data, dict):
            for key, item in items_data.items():
                if isinstance(item, dict):
                    # 确保id字段存在
                    if not self._has_id_field(item):
                        self._set_id_field(item, key)
                    parsed_item = self._parse_item(item)
                    items.append(parsed_item)
        
        return items
    
    @abstractmethod
    def _parse_item(self, data: Dict[str, Any]) -> T:
        """解析单个项目，子类必须实现"""
        pass
    
    @abstractmethod
    def _has_id_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有ID字段，子类必须实现"""
        pass
    
    @abstractmethod
    def _set_id_field(self, data: Dict[str, Any], value: str):
        """设置ID字段，子类必须实现"""
        pass
    
    def export_to_yaml(self, items: List[T], file_path: str, to_dict_func: Optional[Any] = None):
        """导出到YAML文件"""
        if to_dict_func:
            items_data = [to_dict_func(item) for item in items]
        else:
            # 尝试调用to_dict方法
            items_data = []
            for item in items:
                if hasattr(item, 'to_dict'):
                    items_data.append(item.to_dict())
                elif isinstance(item, dict):
                    items_data.append(item)
                else:
                    # 尝试转换为字典
                    items_data.append(self._item_to_dict(item))
        
        data = {
            self.root_key: items_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def _item_to_dict(self, item: T) -> Dict[str, Any]:
        """将项目转换为字典，子类可以重写"""
        if hasattr(item, '__dict__'):
            return item.__dict__
        return str(item)


class DeclarativeService(ABC, Generic[T]):
    """通用声明式服务基类"""
    
    def __init__(self, loader: DeclarativeYAMLLoader[T]):
        """
        初始化服务
        
        Args:
            loader: YAML加载器实例
        """
        self.loader = loader
    
    async def import_from_yaml_file(
        self,
        file_path: str,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """从YAML文件导入"""
        items = self.loader.load_from_file(file_path)
        return await self._import_items(items, update_existing)
    
    async def import_from_yaml_string(
        self,
        yaml_str: str,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """从YAML字符串导入"""
        items = self.loader.load_from_string(yaml_str)
        return await self._import_items(items, update_existing)
    
    @abstractmethod
    async def _import_items(
        self,
        items: List[T],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入项目，子类必须实现"""
        pass
    
    async def export_to_yaml_file(
        self,
        file_path: str,
        filter_func: Optional[Any] = None,
    ):
        """导出到YAML文件"""
        items = await self._get_all_items(filter_func)
        self.loader.export_to_yaml(items, file_path)
    
    async def export_to_yaml_string(
        self,
        filter_func: Optional[Any] = None,
    ) -> str:
        """导出为YAML字符串"""
        items = await self._get_all_items(filter_func)
        
        # 构建字典
        items_data = []
        for item in items:
            if hasattr(item, 'to_dict'):
                items_data.append(item.to_dict())
            elif isinstance(item, dict):
                items_data.append(item)
            else:
                items_data.append(self._item_to_dict(item))
        
        data = {
            self.loader.root_key: items_data
        }
        
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    @abstractmethod
    async def _get_all_items(self, filter_func: Optional[Any] = None) -> List[T]:
        """获取所有项目，子类必须实现"""
        pass
    
    def _item_to_dict(self, item: T) -> Dict[str, Any]:
        """将项目转换为字典"""
        if hasattr(item, '__dict__'):
            return item.__dict__
        return str(item)

