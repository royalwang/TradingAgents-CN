"""
知识库注册表
管理知识库配置元数据
"""
from typing import Dict, List, Optional
from datetime import datetime

from .knowledge_config import KnowledgeBaseMetadata, KnowledgeBaseStatus

# 全局注册表实例
_global_registry: Optional[KnowledgeBaseRegistry] = None


class KnowledgeBaseRegistry:
    """知识库注册表"""
    
    def __init__(self):
        self._knowledge_bases: Dict[str, KnowledgeBaseMetadata] = {}
        self._by_status: Dict[KnowledgeBaseStatus, List[str]] = {
            status: [] for status in KnowledgeBaseStatus
        }
        self._by_tag: Dict[str, List[str]] = {}
    
    def register(self, metadata: KnowledgeBaseMetadata) -> KnowledgeBaseMetadata:
        """注册知识库"""
        if metadata.kb_id in self._knowledge_bases:
            raise ValueError(f"Knowledge base {metadata.kb_id} already registered")
        
        # 设置默认值
        if not metadata.collection_name:
            metadata.collection_name = f"kb_{metadata.name}"
        if not metadata.created_at:
            metadata.created_at = datetime.utcnow()
        if not metadata.updated_at:
            metadata.updated_at = datetime.utcnow()
        
        self._knowledge_bases[metadata.kb_id] = metadata
        self._by_status[metadata.status].append(metadata.kb_id)
        
        # 按标签索引
        for tag in metadata.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(metadata.kb_id)
        
        return metadata
    
    def get(self, kb_id: str) -> Optional[KnowledgeBaseMetadata]:
        """获取知识库元数据"""
        return self._knowledge_bases.get(kb_id)
    
    def list(
        self,
        status: Optional[KnowledgeBaseStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[KnowledgeBaseMetadata]:
        """列出知识库"""
        result = []
        
        # 按状态过滤
        if status:
            kb_ids = self._by_status.get(status, [])
        elif tags:
            # 按标签过滤
            kb_ids = []
            for tag in tags:
                if tag in self._by_tag:
                    kb_ids.extend(self._by_tag[tag])
            kb_ids = list(set(kb_ids))  # 去重
        else:
            kb_ids = list(self._knowledge_bases.keys())
        
        # 应用过滤条件
        for kb_id in kb_ids:
            metadata = self._knowledge_bases.get(kb_id)
            if not metadata:
                continue
            
            if status and metadata.status != status:
                continue
            
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            result.append(metadata)
        
        return result
    
    def unregister(self, kb_id: str) -> bool:
        """注销知识库"""
        if kb_id not in self._knowledge_bases:
            return False
        
        metadata = self._knowledge_bases[kb_id]
        del self._knowledge_bases[kb_id]
        
        # 从索引中移除
        if kb_id in self._by_status[metadata.status]:
            self._by_status[metadata.status].remove(kb_id)
        
        for tag in metadata.tags:
            if tag in self._by_tag and kb_id in self._by_tag[tag]:
                self._by_tag[tag].remove(kb_id)
        
        return True
    
    def update_status(self, kb_id: str, status: KnowledgeBaseStatus) -> bool:
        """更新知识库状态"""
        if kb_id not in self._knowledge_bases:
            return False
        
        metadata = self._knowledge_bases[kb_id]
        old_status = metadata.status
        metadata.status = status
        metadata.updated_at = datetime.utcnow()
        
        # 更新索引
        if kb_id in self._by_status[old_status]:
            self._by_status[old_status].remove(kb_id)
        self._by_status[status].append(kb_id)
        
        return True
    
    def search(self, query: str) -> List[KnowledgeBaseMetadata]:
        """搜索知识库"""
        query_lower = query.lower()
        result = []
        
        for metadata in self._knowledge_bases.values():
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                result.append(metadata)
        
        return result


def get_registry() -> KnowledgeBaseRegistry:
    """获取全局注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = KnowledgeBaseRegistry()
    return _global_registry

