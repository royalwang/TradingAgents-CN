"""
数据源工厂
用于创建和注册数据源
"""
from typing import Dict, Any, Optional, Callable, List

from .data_source_registry import DataSourceRegistry, DataSourceType, DataSourceMetadata, get_registry
from .data_source_manager import DataSourceManager, get_manager
from app.services.data_sources.base import DataSourceAdapter


class DataSourceFactory:
    """数据源工厂"""
    
    def __init__(
        self,
        registry: Optional[DataSourceRegistry] = None,
        manager: Optional[DataSourceManager] = None,
    ):
        self.registry = registry or get_registry()
        self.manager = manager or get_manager()
    
    def register_adapter(
        self,
        source_id: str,
        name: str,
        display_name: str,
        adapter_class: Callable[[], DataSourceAdapter],
        description: Optional[str] = None,
        source_type: DataSourceType = DataSourceType.STOCK,
        priority: int = 0,
        supported_markets: Optional[List[str]] = None,
        supported_features: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> DataSourceMetadata:
        """注册数据源适配器"""
        return self.registry.register(
            source_id=source_id,
            name=name,
            display_name=display_name,
            adapter_class=adapter_class,
            description=description,
            source_type=source_type,
            priority=priority,
            supported_markets=supported_markets or [],
            supported_features=supported_features or [],
            **kwargs,
        )
    
    def register_from_existing(self):
        """从现有适配器注册数据源"""
        from app.services.data_sources import (
            TushareAdapter,
            AKShareAdapter,
            BaoStockAdapter,
        )
        
        # 注册Tushare
        self.register_adapter(
            source_id="tushare",
            name="tushare",
            display_name="Tushare",
            adapter_class=TushareAdapter,
            description="Tushare是专业的金融数据平台，提供全面的A股数据",
            source_type=DataSourceType.STOCK,
            priority=3,  # 最高优先级
            supported_markets=["A股"],
            supported_features=["stock_list", "daily_basic", "realtime_quotes", "kline", "news"],
            website="https://tushare.pro",
            documentation_url="https://tushare.pro/document/2",
        )
        
        # 注册AKShare
        self.register_adapter(
            source_id="akshare",
            name="akshare",
            display_name="AKShare",
            adapter_class=AKShareAdapter,
            description="AKShare是Python开源金融数据接口库，提供全面的金融数据",
            source_type=DataSourceType.STOCK,
            priority=2,
            supported_markets=["A股", "港股", "美股"],
            supported_features=["stock_list", "daily_basic", "realtime_quotes", "kline", "news"],
            website="https://akshare.akfamily.xyz",
            documentation_url="https://akshare.readthedocs.io",
        )
        
        # 注册BaoStock
        self.register_adapter(
            source_id="baostock",
            name="baostock",
            display_name="BaoStock",
            adapter_class=BaoStockAdapter,
            description="BaoStock是证券宝数据接口，提供免费的A股数据",
            source_type=DataSourceType.STOCK,
            priority=1,
            supported_markets=["A股"],
            supported_features=["stock_list", "daily_basic", "kline"],
            website="http://baostock.com",
            documentation_url="http://baostock.com/baostock/index.php",
        )


# 全局工厂实例
_global_factory: Optional[DataSourceFactory] = None


def get_factory() -> DataSourceFactory:
    """获取全局工厂"""
    global _global_factory
    if _global_factory is None:
        _global_factory = DataSourceFactory()
        # 自动注册现有适配器
        try:
            _global_factory.register_from_existing()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to register existing adapters: {e}")
    return _global_factory

