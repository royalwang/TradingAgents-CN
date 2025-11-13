"""
数据源注册表
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.services.data_sources.base import DataSourceAdapter


class DataSourceStatus(str, Enum):
    """数据源状态"""
    REGISTERED = "registered"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    DEPRECATED = "deprecated"


class DataSourceType(str, Enum):
    """数据源类型"""
    STOCK = "stock"  # 股票数据
    FUTURES = "futures"  # 期货数据
    FOREX = "forex"  # 外汇数据
    CRYPTO = "crypto"  # 加密货币
    NEWS = "news"  # 新闻数据
    SOCIAL = "social"  # 社交媒体
    CUSTOM = "custom"  # 自定义


@dataclass
class DataSourceMetadata:
    """数据源元数据"""
    source_id: str
    name: str
    display_name: str
    description: Optional[str] = None
    source_type: DataSourceType = DataSourceType.STOCK
    version: str = "1.0.0"
    author: str = "unknown"
    
    # 数据源配置
    priority: int = 0  # 优先级（数字越大优先级越高）
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 支持的功能
    supported_markets: List[str] = field(default_factory=list)  # 支持的市场（A股、港股、美股等）
    supported_features: List[str] = field(default_factory=list)  # 支持的功能
    
    # 数据源实例
    adapter_class: Optional[Callable] = None
    adapter_instance: Optional[DataSourceAdapter] = None
    
    # 状态
    status: DataSourceStatus = DataSourceStatus.REGISTERED
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    website: Optional[str] = None
    documentation_url: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "source_id": self.source_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "source_type": self.source_type.value,
            "version": self.version,
            "author": self.author,
            "priority": self.priority,
            "enabled": self.enabled,
            "config": self.config,
            "supported_markets": self.supported_markets,
            "supported_features": self.supported_features,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error_message": self.error_message,
            "tags": self.tags,
            "website": self.website,
            "documentation_url": self.documentation_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DataSourceRegistry:
    """数据源注册表"""
    
    def __init__(self):
        self._sources: Dict[str, DataSourceMetadata] = {}
        self._by_type: Dict[DataSourceType, List[str]] = {
            source_type: [] for source_type in DataSourceType
        }
        self._by_market: Dict[str, List[str]] = {}
    
    def register(
        self,
        source_id: str,
        name: str,
        display_name: str,
        adapter_class: Optional[Callable] = None,
        description: Optional[str] = None,
        source_type: DataSourceType = DataSourceType.STOCK,
        version: str = "1.0.0",
        author: str = "unknown",
        priority: int = 0,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
        supported_markets: Optional[List[str]] = None,
        supported_features: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        website: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ) -> DataSourceMetadata:
        """注册数据源"""
        if source_id in self._sources:
            raise ValueError(f"Data source {source_id} already registered")
        
        metadata = DataSourceMetadata(
            source_id=source_id,
            name=name,
            display_name=display_name,
            description=description,
            source_type=source_type,
            version=version,
            author=author,
            priority=priority,
            enabled=enabled,
            config=config or {},
            supported_markets=supported_markets or [],
            supported_features=supported_features or [],
            adapter_class=adapter_class,
            tags=tags or [],
            website=website,
            documentation_url=documentation_url,
        )
        
        self._sources[source_id] = metadata
        self._by_type[source_type].append(source_id)
        
        # 按市场索引
        for market in metadata.supported_markets:
            if market not in self._by_market:
                self._by_market[market] = []
            self._by_market[market].append(source_id)
        
        return metadata
    
    def get(self, source_id: str) -> Optional[DataSourceMetadata]:
        """获取数据源元数据"""
        return self._sources.get(source_id)
    
    def list(
        self,
        source_type: Optional[DataSourceType] = None,
        market: Optional[str] = None,
        status: Optional[DataSourceStatus] = None,
        enabled: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> List[DataSourceMetadata]:
        """列出数据源"""
        result = []
        
        # 按类型过滤
        if source_type:
            source_ids = self._by_type.get(source_type, [])
        elif market:
            source_ids = self._by_market.get(market, [])
        else:
            source_ids = list(self._sources.keys())
        
        # 应用过滤条件
        for source_id in source_ids:
            metadata = self._sources.get(source_id)
            if not metadata:
                continue
            
            if status and metadata.status != status:
                continue
            
            if enabled is not None and metadata.enabled != enabled:
                continue
            
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            result.append(metadata)
        
        # 按优先级排序
        result.sort(key=lambda x: x.priority, reverse=True)
        
        return result
    
    def unregister(self, source_id: str) -> bool:
        """注销数据源"""
        if source_id not in self._sources:
            return False
        
        metadata = self._sources[source_id]
        del self._sources[source_id]
        
        # 从索引中移除
        if source_id in self._by_type[metadata.source_type]:
            self._by_type[metadata.source_type].remove(source_id)
        
        for market in metadata.supported_markets:
            if market in self._by_market and source_id in self._by_market[market]:
                self._by_market[market].remove(source_id)
        
        return True
    
    def update_status(self, source_id: str, status: DataSourceStatus, error_message: Optional[str] = None):
        """更新数据源状态"""
        if source_id in self._sources:
            metadata = self._sources[source_id]
            metadata.status = status
            metadata.last_check = datetime.utcnow()
            metadata.error_message = error_message
            metadata.updated_at = datetime.utcnow()
            return True
        return False
    
    def search(self, query: str) -> List[DataSourceMetadata]:
        """搜索数据源"""
        query_lower = query.lower()
        result = []
        
        for metadata in self._sources.values():
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.display_name.lower() or
                (metadata.description and query_lower in metadata.description.lower()) or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                result.append(metadata)
        
        return result


# 全局注册表实例
_global_registry = DataSourceRegistry()


def get_registry() -> DataSourceRegistry:
    """获取全局注册表"""
    return _global_registry

