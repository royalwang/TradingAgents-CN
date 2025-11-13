"""
知识库服务层
提供高级知识库管理功能，包括YAML声明式管理
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .knowledge_registry import KnowledgeBaseRegistry, get_registry
from .knowledge_config import KnowledgeBaseMetadata, KnowledgeBaseStatus
from .yaml_loader import KnowledgeBaseYAMLLoader
from app.platform.core.declarative_manager import DeclarativeService


class KnowledgeBaseService(DeclarativeService[KnowledgeBaseMetadata]):
    """知识库服务"""
    
    def __init__(self, registry: Optional[KnowledgeBaseRegistry] = None):
        loader = KnowledgeBaseYAMLLoader()
        super().__init__(loader)
        self.registry = registry or get_registry()
    
    async def _import_items(
        self,
        items: List[KnowledgeBaseMetadata],
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """导入知识库配置"""
        imported = []
        updated = []
        skipped = []
        errors = []
        
        for metadata in items:
            try:
                existing = self.registry.get(metadata.kb_id)
                
                if existing:
                    if update_existing:
                        # 更新现有知识库
                        self.registry.unregister(metadata.kb_id)
                        self.registry.register(metadata)
                        # 恢复状态
                        if metadata.status != existing.status:
                            self.registry.update_status(metadata.kb_id, metadata.status)
                        updated.append(metadata.kb_id)
                    else:
                        skipped.append(metadata.kb_id)
                else:
                    # 注册新知识库
                    self.registry.register(metadata)
                    imported.append(metadata.kb_id)
            except Exception as e:
                errors.append({
                    "kb_id": metadata.kb_id,
                    "error": str(e)
                })
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(items),
        }
    
    async def _get_all_items(self, filter_func: Optional[Any] = None) -> List[KnowledgeBaseMetadata]:
        """获取所有知识库"""
        knowledge_bases = self.registry.list()
        
        if filter_func:
            knowledge_bases = [kb for kb in knowledge_bases if filter_func(kb)]
        
        return knowledge_bases


# 全局服务实例
_global_service: Optional[KnowledgeBaseService] = None


def get_service() -> KnowledgeBaseService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = KnowledgeBaseService()
    return _global_service

