"""
数据源管理器
管理数据源的实例化和查询
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from datetime import datetime

from .data_source_registry import DataSourceRegistry, DataSourceMetadata, DataSourceStatus, get_registry
from app.services.data_sources.base import DataSourceAdapter


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self, registry: Optional[DataSourceRegistry] = None):
        self.registry = registry or get_registry()
        self._instances: Dict[str, DataSourceAdapter] = {}
    
    def get_adapter(self, source_id: str) -> Optional[DataSourceAdapter]:
        """获取数据源适配器实例"""
        metadata = self.registry.get(source_id)
        if not metadata:
            return None
        
        # 如果已有实例，直接返回
        if source_id in self._instances:
            return self._instances[source_id]
        
        # 创建新实例
        if metadata.adapter_class:
            try:
                adapter = metadata.adapter_class()
                self._instances[source_id] = adapter
                metadata.adapter_instance = adapter
                
                # 检查可用性
                if adapter.is_available():
                    self.registry.update_status(source_id, DataSourceStatus.AVAILABLE)
                else:
                    self.registry.update_status(source_id, DataSourceStatus.UNAVAILABLE, "Adapter not available")
                
                return adapter
            except Exception as e:
                self.registry.update_status(source_id, DataSourceStatus.ERROR, str(e))
                return None
        
        return None
    
    def get_available_adapters(
        self,
        market: Optional[str] = None,
        preferred_sources: Optional[List[str]] = None,
    ) -> List[DataSourceAdapter]:
        """获取可用的数据源适配器列表"""
        # 获取数据源元数据
        sources = self.registry.list(
            market=market,
            status=DataSourceStatus.AVAILABLE,
            enabled=True,
        )
        
        # 如果指定了优先数据源，重新排序
        if preferred_sources:
            priority_map = {name: idx for idx, name in enumerate(preferred_sources)}
            preferred = [s for s in sources if s.name in priority_map]
            others = [s for s in sources if s.name not in priority_map]
            preferred.sort(key=lambda s: priority_map.get(s.name, 999))
            sources = preferred + others
        
        # 获取适配器实例
        adapters = []
        for source in sources:
            adapter = self.get_adapter(source.source_id)
            if adapter and adapter.is_available():
                adapters.append(adapter)
        
        return adapters
    
    async def get_stock_list(
        self,
        market: Optional[str] = None,
        preferred_sources: Optional[List[str]] = None,
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """获取股票列表（带fallback）"""
        adapters = self.get_available_adapters(market, preferred_sources)
        
        for adapter in adapters:
            try:
                df = adapter.get_stock_list()
                if df is not None and not df.empty:
                    return df, adapter.name
            except Exception as e:
                continue
        
        return None, None
    
    async def get_daily_basic(
        self,
        trade_date: str,
        market: Optional[str] = None,
        preferred_sources: Optional[List[str]] = None,
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """获取每日基础数据（带fallback）"""
        adapters = self.get_available_adapters(market, preferred_sources)
        
        for adapter in adapters:
            try:
                df = adapter.get_daily_basic(trade_date)
                if df is not None and not df.empty:
                    return df, adapter.name
            except Exception as e:
                continue
        
        return None, None
    
    async def get_realtime_quotes(
        self,
        market: Optional[str] = None,
        preferred_sources: Optional[List[str]] = None,
    ) -> Tuple[Optional[Dict[str, Dict[str, Optional[float]]]], Optional[str]]:
        """获取实时行情（带fallback）"""
        adapters = self.get_available_adapters(market, preferred_sources)
        
        for adapter in adapters:
            try:
                quotes = adapter.get_realtime_quotes()
                if quotes:
                    return quotes, adapter.name
            except Exception as e:
                continue
        
        return None, None
    
    async def get_kline(
        self,
        code: str,
        period: str = "day",
        limit: int = 120,
        adj: Optional[str] = None,
        market: Optional[str] = None,
        preferred_sources: Optional[List[str]] = None,
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """获取K线数据（带fallback）"""
        adapters = self.get_available_adapters(market, preferred_sources)
        
        for adapter in adapters:
            try:
                kline = adapter.get_kline(code, period, limit, adj)
                if kline:
                    return kline, adapter.name
            except Exception as e:
                continue
        
        return None, None
    
    async def get_news(
        self,
        code: str,
        days: int = 2,
        limit: int = 50,
        include_announcements: bool = True,
        market: Optional[str] = None,
        preferred_sources: Optional[List[str]] = None,
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """获取新闻数据（带fallback）"""
        adapters = self.get_available_adapters(market, preferred_sources)
        
        for adapter in adapters:
            try:
                news = adapter.get_news(code, days, limit, include_announcements)
                if news:
                    return news, adapter.name
            except Exception as e:
                continue
        
        return None, None
    
    async def check_availability(self, source_id: str) -> bool:
        """检查数据源可用性"""
        adapter = self.get_adapter(source_id)
        if adapter:
            is_available = adapter.is_available()
            status = DataSourceStatus.AVAILABLE if is_available else DataSourceStatus.UNAVAILABLE
            self.registry.update_status(source_id, status)
            return is_available
        return False
    
    async def check_all_availability(self):
        """检查所有数据源可用性"""
        sources = self.registry.list(enabled=True)
        for source in sources:
            await self.check_availability(source.source_id)


# 全局管理器实例
_global_manager: Optional[DataSourceManager] = None


def get_manager() -> DataSourceManager:
    """获取全局管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = DataSourceManager()
    return _global_manager

