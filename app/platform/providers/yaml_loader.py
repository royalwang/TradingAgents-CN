"""
YAML Provider加载器
从YAML文件加载Provider配置
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from .provider_manager import ProviderMetadata


class YAMLProviderLoader:
    """YAML Provider加载器"""
    
    @staticmethod
    def load_from_file(file_path: str) -> List[ProviderMetadata]:
        """从YAML文件加载Provider"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return YAMLProviderLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_string(yaml_str: str) -> List[ProviderMetadata]:
        """从YAML字符串加载Provider"""
        data = yaml.safe_load(yaml_str)
        return YAMLProviderLoader.load_from_dict(data)
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> List[ProviderMetadata]:
        """从字典加载Provider"""
        providers = []
        
        # 支持两种格式：
        # 1. 列表格式: providers: [ {...}, {...} ]
        # 2. 对象格式: providers: { name: {...}, name2: {...} }
        
        if isinstance(data, dict):
            if "providers" in data:
                providers_data = data["providers"]
            else:
                # 整个字典就是providers
                providers_data = data
        elif isinstance(data, list):
            providers_data = data
        else:
            raise ValueError("Invalid YAML format: expected dict or list")
        
        # 处理列表格式
        if isinstance(providers_data, list):
            for item in providers_data:
                provider = YAMLProviderLoader._parse_provider(item)
                providers.append(provider)
        # 处理对象格式
        elif isinstance(providers_data, dict):
            for name, item in providers_data.items():
                if isinstance(item, dict):
                    # 确保name字段存在
                    if "name" not in item:
                        item["name"] = name
                    provider = YAMLProviderLoader._parse_provider(item)
                    providers.append(provider)
        
        return providers
    
    @staticmethod
    def _parse_provider(data: Dict[str, Any]) -> ProviderMetadata:
        """解析单个Provider"""
        # 必需字段
        name = data.get("name")
        if not name:
            raise ValueError("Provider 'name' is required")
        
        display_name = data.get("display_name") or data.get("displayName") or name
        
        # 可选字段
        provider = ProviderMetadata(
            name=name,
            display_name=display_name,
            description=data.get("description"),
            website=data.get("website"),
            api_doc_url=data.get("api_doc_url") or data.get("apiDocUrl"),
            logo_url=data.get("logo_url") or data.get("logoUrl"),
            is_active=data.get("is_active", data.get("isActive", True)),
            supported_features=data.get("supported_features") or data.get("supportedFeatures") or [],
            default_base_url=data.get("default_base_url") or data.get("defaultBaseUrl"),
            is_aggregator=data.get("is_aggregator", data.get("isAggregator", False)),
            aggregator_type=data.get("aggregator_type") or data.get("aggregatorType"),
            model_name_format=data.get("model_name_format") or data.get("modelNameFormat"),
            extra_config=data.get("extra_config") or data.get("extraConfig") or {},
        )
        
        return provider
    
    @staticmethod
    def export_to_yaml(providers: List[ProviderMetadata], file_path: str):
        """导出Provider到YAML文件"""
        data = {
            "providers": [provider.to_dict() for provider in providers]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# 示例YAML格式
EXAMPLE_YAML = """
# LLM Provider配置示例
providers:
  - name: openai
    display_name: OpenAI
    description: OpenAI是人工智能领域的领先公司，提供GPT系列模型
    website: https://openai.com
    api_doc_url: https://platform.openai.com/docs
    default_base_url: https://api.openai.com/v1
    is_active: true
    supported_features:
      - chat
      - completion
      - embedding
      - image
      - vision
      - function_calling
      - streaming
    extra_config:
      has_api_key: true
  
  - name: anthropic
    display_name: Anthropic
    description: Anthropic专注于AI安全研究，提供Claude系列模型
    website: https://anthropic.com
    api_doc_url: https://docs.anthropic.com
    default_base_url: https://api.anthropic.com
    is_active: true
    supported_features:
      - chat
      - completion
      - function_calling
      - streaming
"""

