"""
数据源YAML加载器
从YAML文件加载数据源配置
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from .data_source_registry import DataSourceMetadata, DataSourceType, DataSourceStatus


class DataSourceYAMLLoader:
    """数据源YAML加载器"""
    
    @staticmethod
    def load_from_file(file_path: str) -> List[DataSourceMetadata]:
        """从YAML文件加载数据源配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return DataSourceYAMLLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_string(yaml_str: str) -> List[DataSourceMetadata]:
        """从YAML字符串加载数据源配置"""
        data = yaml.safe_load(yaml_str)
        return DataSourceYAMLLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> List[DataSourceMetadata]:
        """从字典加载数据源配置"""
        sources = []
        
        # 支持两种格式：
        # 1. 列表格式: data_sources: [ {...}, {...} ]
        # 2. 对象格式: data_sources: { id: {...}, id2: {...} }
        
        if isinstance(data, dict):
            if "data_sources" in data:
                sources_data = data["data_sources"]
            else:
                # 整个字典就是data_sources
                sources_data = data
        elif isinstance(data, list):
            sources_data = data
        else:
            raise ValueError("Invalid YAML format: expected dict or list")
        
        # 处理列表格式
        if isinstance(sources_data, list):
            for item in sources_data:
                source = DataSourceYAMLLoader._parse_source(item)
                sources.append(source)
        # 处理对象格式
        elif isinstance(sources_data, dict):
            for source_id, item in sources_data.items():
                if isinstance(item, dict):
                    # 确保source_id字段存在
                    if "source_id" not in item:
                        item["source_id"] = source_id
                    source = DataSourceYAMLLoader._parse_source(item)
                    sources.append(source)
        
        return sources
    
    @staticmethod
    def _parse_source(data: Dict[str, Any]) -> DataSourceMetadata:
        """解析单个数据源配置"""
        # 必需字段
        source_id = data.get("source_id")
        if not source_id:
            raise ValueError("Data source 'source_id' is required")
        
        name = data.get("name") or source_id
        display_name = data.get("display_name") or data.get("displayName") or name
        
        # 可选字段
        source = DataSourceMetadata(
            source_id=source_id,
            name=name,
            display_name=display_name,
            description=data.get("description"),
            source_type=DataSourceType(data.get("source_type", data.get("sourceType", "stock"))),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "unknown"),
            priority=data.get("priority", 0),
            enabled=data.get("is_active", data.get("isActive", True)),
            config=data.get("config", {}),
            supported_markets=data.get("supported_markets") or data.get("supportedMarkets") or [],
            supported_features=data.get("supported_features") or data.get("supportedFeatures") or [],
            tags=data.get("tags", []),
            website=data.get("website"),
            documentation_url=data.get("documentation_url") or data.get("documentationUrl"),
        )
        
        return source
    
    @staticmethod
    def export_to_yaml(sources: List[DataSourceMetadata], file_path: str):
        """导出数据源配置到YAML文件"""
        data = {
            "data_sources": [source.to_dict() for source in sources]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# 示例YAML格式
EXAMPLE_YAML = """
# 数据源配置示例
data_sources:
  - source_id: tushare
    name: tushare
    display_name: Tushare
    description: Tushare是专业的金融数据平台，提供全面的A股数据
    source_type: stock
    version: 1.0.0
    author: Tushare
    priority: 3
    is_active: true
    supported_markets:
      - A股
    supported_features:
      - stock_list
      - daily_basic
      - realtime_quotes
      - kline
      - news
    website: https://tushare.pro
    documentation_url: https://tushare.pro/document/2
    tags:
      - professional
      - a_shares
  
  - source_id: akshare
    name: akshare
    display_name: AKShare
    description: AKShare是Python开源金融数据接口库
    source_type: stock
    priority: 2
    supported_markets:
      - A股
      - 港股
      - 美股
    supported_features:
      - stock_list
      - daily_basic
      - realtime_quotes
      - kline
      - news
"""

