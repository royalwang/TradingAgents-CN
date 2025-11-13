"""
智能体平台API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.platform.agents import (
    AgentRegistry, AgentManager, AgentFactory, AgentService,
    get_registry, get_manager, get_factory, get_service as get_agent_service,
)
from app.platform.knowledge import (
    KnowledgeBase, create_vector_store, create_embedding_service,
    KnowledgeBaseService, get_service as get_kb_service,
)
from app.platform.parsers import ParserFactory, get_parser_factory
from app.platform.mcp import MCPServer, MCPToolRegistry, get_mcp_server
from app.platform.plugins import (
    PluginRegistry, PluginManager, PluginLoader, PluginService,
    get_registry as get_plugin_registry, get_manager as get_plugin_manager,
    get_service as get_plugin_service,
)
from app.platform.workflow import (
    WorkflowEngine, WorkflowExecutor, WorkflowService,
    get_engine, get_executor, get_service as get_workflow_service,
)
from app.platform.data import (
    SchemaRegistry, DataSchema, FieldDefinition, SchemaType,
    DataValidator, DataFactory, DataBuilder, DataGenerator,
    DataTransformer, DataSerializer, SerializationFormat,
    RelationshipManager, DataRelationship, RelationshipType,
    get_registry, get_validator, get_factory, get_transformer,
    get_serializer, get_relationship_manager,
)
from app.platform.providers import (
    ProviderService, ProviderManager, YAMLProviderLoader,
    get_provider_service, get_provider_manager,
)
from app.platform.business import (
    BusinessPlugin, PluginCapability, PluginStatus,
    BusinessPluginRegistry, BusinessPluginManager, BusinessPluginLoader,
    get_registry as get_business_registry, get_manager as get_business_manager,
    get_loader as get_business_loader,
)
from app.platform.data_sources import (
    DataSourceRegistry, DataSourceMetadata, DataSourceStatus, DataSourceType,
    DataSourceManager, DataSourceFactory, DataSourceService,
    get_registry as get_ds_registry, get_manager as get_ds_manager,
    get_factory as get_ds_factory, get_service as get_ds_service,
)
from app.platform.tenants import (
    TenantRegistry, TenantMetadata, TenantStatus, TenantTier,
    TenantManager, TenantService,
    get_registry as get_tenant_registry, get_manager as get_tenant_manager,
    get_service as get_tenant_service,
    get_tenant_id, require_tenant,
)
from app.core.config import settings

router = APIRouter(prefix="/api/platform", tags=["platform"])


# ==================== 智能体管理API ====================

@router.get("/agents")
async def list_agents(
    agent_type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
):
    """列出所有智能体"""
    registry = get_registry()
    agents = registry.list(
        agent_type=agent_type,
        category=category,
        status=status,
    )
    return {"agents": [agent.to_dict() for agent in agents]}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取智能体详情"""
    registry = get_registry()
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.to_dict()


@router.post("/agents/{agent_id}/instances")
async def create_agent_instance(
    agent_id: str,
    name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
):
    """创建智能体实例"""
    factory = get_factory()
    try:
        instance = await factory.create_agent(
            agent_id=agent_id,
            name=name,
            config=config,
        )
        return instance.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/instances")
async def list_agent_instances(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """列出智能体实例"""
    manager = get_manager()
    instances = manager.list_instances(
        agent_id=agent_id,
        status=status,
    )
    return {"instances": [instance.to_dict() for instance in instances]}


@router.delete("/agents/instances/{instance_id}")
async def delete_agent_instance(instance_id: str):
    """删除智能体实例"""
    manager = get_manager()
    success = await manager.delete_instance(instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Instance not found")
    return {"success": True}


# ==================== 智能体YAML声明式管理API ====================

@router.post("/agents/import/yaml")
async def import_agents_from_yaml_string(
    yaml_str: str,
    update_existing: bool = False,
):
    """从YAML字符串导入智能体配置"""
    service = get_agent_service()
    try:
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/import/yaml-file")
async def import_agents_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入智能体配置"""
    service = get_agent_service()
    try:
        content = await file.read()
        yaml_str = content.decode('utf-8')
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/export/yaml")
async def export_agents_to_yaml(
    status: Optional[str] = None,
    category: Optional[str] = None,
):
    """导出智能体配置为YAML格式"""
    service = get_agent_service()
    try:
        def filter_func(agent):
            if status and agent.status.value != status:
                return False
            if category and agent.category != category:
                return False
            return True
        
        yaml_str = await service.export_to_yaml_string(filter_func)
        return {
            "yaml": yaml_str,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 知识库API ====================

@router.post("/knowledge/{kb_name}/documents")
async def add_document(
    kb_name: str,
    title: str,
    content: str,
    source: str,
    document_type: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """添加文档到知识库"""
    # 这里需要从某个地方获取知识库实例
    # 为了简化，我们创建一个临时的知识库
    from app.platform.core.platform_config import platform_settings
    
    vector_store = create_vector_store(
        store_type="chromadb",
        collection_name=f"{platform_settings.KNOWLEDGE_BASE_COLLECTION_PREFIX}{kb_name}",
    )
    
    embedding_service = create_embedding_service(
        service_type="openai",
        model=platform_settings.KNOWLEDGE_BASE_EMBEDDING_MODEL,
    )
    
    kb = KnowledgeBase(
        name=kb_name,
        vector_store=vector_store,
        embedding_service=embedding_service,
    )
    
    document = await kb.add_document(
        title=title,
        content=content,
        source=source,
        document_type=document_type,
        metadata=metadata,
    )
    
    return document.to_dict()


@router.post("/knowledge/{kb_name}/documents/upload")
async def upload_document(
    kb_name: str,
    file: UploadFile = File(...),
):
    """上传并解析文档"""
    parser_factory = get_parser_factory()
    
    # 保存临时文件
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # 解析文档
        result = await parser_factory.parse(tmp_file_path)
        
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        
        # 添加到知识库
        from app.platform.core.platform_config import platform_settings
        
        vector_store = create_vector_store(
            store_type="chromadb",
            collection_name=f"{platform_settings.KNOWLEDGE_BASE_COLLECTION_PREFIX}{kb_name}",
        )
        
        embedding_service = create_embedding_service(
            service_type="openai",
            model=platform_settings.KNOWLEDGE_BASE_EMBEDDING_MODEL,
        )
        
        kb = KnowledgeBase(
            name=kb_name,
            vector_store=vector_store,
            embedding_service=embedding_service,
        )
        
        document = await kb.add_document(
            title=result.title,
            content=result.content,
            source=file.filename,
            document_type=os.path.splitext(file.filename)[1][1:],
            metadata=result.metadata,
        )
        
        return document.to_dict()
    finally:
        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/knowledge/{kb_name}/search")
async def search_knowledge(
    kb_name: str,
    query: str,
    top_k: int = 5,
):
    """搜索知识库"""
    from app.platform.core.platform_config import platform_settings
    
    vector_store = create_vector_store(
        store_type="chromadb",
        collection_name=f"{platform_settings.KNOWLEDGE_BASE_COLLECTION_PREFIX}{kb_name}",
    )
    
    embedding_service = create_embedding_service(
        service_type="openai",
        model=platform_settings.KNOWLEDGE_BASE_EMBEDDING_MODEL,
    )
    
    kb = KnowledgeBase(
        name=kb_name,
        vector_store=vector_store,
        embedding_service=embedding_service,
    )
    
    results = await kb.search(query=query, top_k=top_k)
    return {"results": results}


# ==================== 知识库YAML声明式管理API ====================

@router.post("/knowledge/import/yaml")
async def import_knowledge_bases_from_yaml_string(
    yaml_str: str,
    update_existing: bool = False,
):
    """从YAML字符串导入知识库配置"""
    service = get_kb_service()
    try:
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge/import/yaml-file")
async def import_knowledge_bases_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入知识库配置"""
    service = get_kb_service()
    try:
        content = await file.read()
        yaml_str = content.decode('utf-8')
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge/export/yaml")
async def export_knowledge_bases_to_yaml(
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """导出知识库配置为YAML格式"""
    service = get_kb_service()
    try:
        def filter_func(kb):
            if status and kb.status.value != status:
                return False
            if tags and not any(tag in kb.tags for tag in tags):
                return False
            return True
        
        yaml_str = await service.export_to_yaml_string(filter_func)
        return {
            "yaml": yaml_str,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== MCP工具API ====================

@router.get("/mcp/tools")
async def list_mcp_tools():
    """列出MCP工具"""
    server = get_mcp_server()
    tools = await server.list_tools()
    return {"tools": tools}


@router.post("/mcp/tools/execute")
async def execute_mcp_tool(
    tool_name: str,
    parameters: Dict[str, Any],
):
    """执行MCP工具"""
    server = get_mcp_server()
    result = await server.execute_tool(tool_name, parameters)
    return result


# ==================== 插件API ====================

@router.get("/plugins")
async def list_plugins(
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """列出插件"""
    registry = get_plugin_registry()
    plugins = registry.list(status=status, tags=tags)
    return {"plugins": [plugin.to_dict() for plugin in plugins]}


@router.post("/plugins/{plugin_id}/load")
async def load_plugin(
    plugin_id: str,
    config: Optional[Dict[str, Any]] = None,
):
    """加载插件"""
    manager = get_plugin_manager()
    try:
        instance = await manager.load_plugin(plugin_id, config)
        return instance.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/discover")
async def discover_plugins():
    """发现插件"""
    from app.platform.core.platform_config import platform_settings
    loader = PluginLoader(platform_settings.PLUGIN_DIR)
    plugins = loader.discover_plugins()
    return {"plugins": [plugin.to_dict() for plugin in plugins], "count": len(plugins)}


# ==================== 插件YAML声明式管理API ====================

@router.post("/plugins/import/yaml")
async def import_plugins_from_yaml_string(
    yaml_str: str,
    update_existing: bool = False,
):
    """从YAML字符串导入插件配置"""
    service = get_plugin_service()
    try:
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/import/yaml-file")
async def import_plugins_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入插件配置"""
    service = get_plugin_service()
    try:
        content = await file.read()
        yaml_str = content.decode('utf-8')
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/export/yaml")
async def export_plugins_to_yaml(
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """导出插件配置为YAML格式"""
    service = get_plugin_service()
    try:
        def filter_func(plugin):
            if status and plugin.status.value != status:
                return False
            if tags and not any(tag in plugin.tags for tag in tags):
                return False
            return True
        
        yaml_str = await service.export_to_yaml_string(filter_func)
        return {
            "yaml": yaml_str,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 工作流API ====================

@router.get("/workflows")
async def list_workflows():
    """列出工作流"""
    engine = get_engine()
    workflows = engine.list_workflows()
    return {"workflows": [workflow.to_dict() for workflow in workflows]}


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    initial_state: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
):
    """执行工作流"""
    executor = get_executor()
    result = await executor.execute(workflow_id, initial_state, config)
    return result


# ==================== 工作流YAML声明式管理API ====================

@router.post("/workflows/import/yaml")
async def import_workflows_from_yaml_string(
    yaml_str: str,
    update_existing: bool = False,
):
    """从YAML字符串导入工作流配置"""
    service = get_workflow_service()
    try:
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/import/yaml-file")
async def import_workflows_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入工作流配置"""
    service = get_workflow_service()
    try:
        content = await file.read()
        yaml_str = content.decode('utf-8')
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/export/yaml")
async def export_workflows_to_yaml(
    status: Optional[str] = None,
):
    """导出工作流配置为YAML格式"""
    service = get_workflow_service()
    try:
        def filter_func(workflow):
            if status and workflow.status != status:
                return False
            return True
        
        yaml_str = await service.export_to_yaml_string(filter_func)
        return {
            "yaml": yaml_str,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 声明式数据API ====================

@router.post("/data/schemas")
async def create_schema(schema_data: Dict[str, Any]):
    """创建数据模式"""
    registry = get_registry()
    schema = DataSchema.from_dict(schema_data)
    registry.register(schema)
    return schema.to_dict()


@router.get("/data/schemas")
async def list_schemas():
    """列出所有数据模式"""
    registry = get_registry()
    schemas = registry.list()
    return {"schemas": [schema.to_dict() for schema in schemas]}


@router.get("/data/schemas/{schema_id}")
async def get_schema(schema_id: str):
    """获取数据模式"""
    registry = get_registry()
    schema = registry.get(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema.to_dict()


@router.get("/data/schemas/{schema_id}/json-schema")
async def get_json_schema(schema_id: str):
    """获取JSON Schema格式"""
    registry = get_registry()
    schema = registry.get(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema.to_json_schema()


@router.post("/data/schemas/{schema_id}/validate")
async def validate_data(
    schema_id: str,
    data: Dict[str, Any],
):
    """验证数据"""
    registry = get_registry()
    validator = get_validator()
    
    schema = registry.get(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    result = validator.validate(data, schema)
    return result.to_dict()


@router.post("/data/schemas/{schema_id}/create")
async def create_data_instance(
    schema_id: str,
    data: Optional[Dict[str, Any]] = None,
    validate: bool = True,
    fill_defaults: bool = True,
):
    """从模式创建数据实例"""
    factory = get_factory()
    try:
        instance = factory.create(
            schema_id=schema_id,
            data=data,
            validate=validate,
            fill_defaults=fill_defaults,
        )
        return instance
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data/schemas/{schema_id}/generate")
async def generate_data(
    schema_id: str,
    count: int = 1,
    overrides: Optional[Dict[str, Any]] = None,
):
    """生成示例数据"""
    generator = DataGenerator()
    try:
        instances = generator.generate(
            schema_id=schema_id,
            count=count,
            **(overrides or {}),
        )
        return {"instances": instances, "count": len(instances)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data/transform")
async def transform_data(
    data: Dict[str, Any],
    transformation_name: str,
    direction: str = "forward",
):
    """转换数据"""
    transformer = get_transformer()
    try:
        from app.platform.data.transformer import TransformDirection
        direction_enum = TransformDirection(direction)
        result = transformer.transform(data, transformation_name, direction_enum)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data/serialize")
async def serialize_data(
    data: Dict[str, Any],
    format: str = "json",
    schema_id: Optional[str] = None,
):
    """序列化数据"""
    serializer = get_serializer()
    try:
        format_enum = SerializationFormat(format)
        result = serializer.serialize(data, format_enum, schema_id)
        return {"format": format, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data/deserialize")
async def deserialize_data(
    data_str: str,
    format: str = "json",
    schema_id: Optional[str] = None,
):
    """反序列化数据"""
    serializer = get_serializer()
    try:
        format_enum = SerializationFormat(format)
        result = serializer.deserialize(data_str, format_enum, schema_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data/relationships")
async def create_relationship(relationship_data: Dict[str, Any]):
    """创建数据关系"""
    manager = get_relationship_manager()
    try:
        relationship = manager.register(
            relationship_id=relationship_data["relationship_id"],
            name=relationship_data["name"],
            source_schema_id=relationship_data["source_schema_id"],
            target_schema_id=relationship_data["target_schema_id"],
            relationship_type=RelationshipType(relationship_data["relationship_type"]),
            source_field=relationship_data["source_field"],
            target_field=relationship_data["target_field"],
            cascade_delete=relationship_data.get("cascade_delete", False),
            cascade_update=relationship_data.get("cascade_update", False),
            metadata=relationship_data.get("metadata"),
        )
        return relationship.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data/relationships")
async def list_relationships():
    """列出所有数据关系"""
    manager = get_relationship_manager()
    relationships = manager.list()
    return {"relationships": [rel.to_dict() for rel in relationships]}


@router.post("/data/schemas/{schema_id}/resolve")
async def resolve_references(
    schema_id: str,
    data: Dict[str, Any],
    depth: int = 1,
):
    """解析数据引用关系"""
    manager = get_relationship_manager()
    result = manager.resolve_references(data, schema_id, depth)
    return result


# ==================== LLM Provider管理API ====================

@router.get("/providers")
async def list_providers(is_active: Optional[bool] = None):
    """列出所有LLM Provider"""
    service = get_provider_service()
    providers = await service.get_all(is_active=is_active)
    return {
        "providers": [provider.model_dump(by_alias=True, exclude={"api_key", "api_secret"}) for provider in providers],
        "count": len(providers),
    }


@router.get("/providers/{name}")
async def get_provider(name: str):
    """获取LLM Provider详情"""
    service = get_provider_service()
    provider = await service.get_by_name(name)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider.model_dump(by_alias=True, exclude={"api_key", "api_secret"})


@router.post("/providers")
async def create_provider(
    provider_data: Dict[str, Any],
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
):
    """创建LLM Provider"""
    service = get_provider_service()
    try:
        provider = await service.create_provider(provider_data, api_key, api_secret)
        return provider.model_dump(by_alias=True, exclude={"api_key", "api_secret"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/providers/{name}")
async def update_provider(
    name: str,
    provider_data: Dict[str, Any],
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
):
    """更新LLM Provider"""
    service = get_provider_service()
    try:
        provider = await service.update_provider(name, provider_data, api_key, api_secret)
        return provider.model_dump(by_alias=True, exclude={"api_key", "api_secret"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/providers/{name}")
async def delete_provider(name: str):
    """删除LLM Provider"""
    service = get_provider_service()
    success = await service.delete_provider(name)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"success": True, "message": f"Provider {name} deleted"}


@router.post("/providers/import/yaml")
async def import_providers_from_yaml(
    yaml_content: str,
    update_existing: bool = False,
):
    """从YAML字符串导入Provider"""
    service = get_provider_service()
    try:
        result = await service.import_from_yaml_string(yaml_content, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/providers/import/yaml-file")
async def import_providers_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入Provider"""
    service = get_provider_service()
    try:
        # 读取文件内容
        content = await file.read()
        yaml_str = content.decode('utf-8')
        
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers/export/yaml")
async def export_providers_to_yaml(
    is_active: Optional[bool] = None,
):
    """导出Provider为YAML格式"""
    service = get_provider_service()
    try:
        providers = await service.get_all(is_active=is_active)
        
        # 转换为ProviderMetadata并导出为YAML字符串
        from app.platform.providers.provider_manager import ProviderMetadata
        from app.platform.providers.yaml_loader import YAMLProviderLoader
        
        metadata_list = []
        for provider in providers:
            metadata = ProviderMetadata(
                name=provider.name,
                display_name=provider.display_name,
                description=provider.description,
                website=provider.website,
                api_doc_url=provider.api_doc_url,
                logo_url=provider.logo_url,
                is_active=provider.is_active,
                supported_features=provider.supported_features,
                default_base_url=provider.default_base_url,
                is_aggregator=provider.is_aggregator,
                aggregator_type=provider.aggregator_type,
                model_name_format=provider.model_name_format,
                extra_config=provider.extra_config or {},
            )
            metadata_list.append(metadata)
        
        import yaml
        data = {"providers": [m.to_dict() for m in metadata_list]}
        yaml_str = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return {
            "yaml": yaml_str,
            "count": len(metadata_list),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 业务插件API ====================

@router.get("/business/plugins")
async def list_business_plugins(
    capability: Optional[str] = None,
    status: Optional[str] = None,
    enabled: Optional[bool] = None,
    tags: Optional[List[str]] = None,
):
    """列出所有业务插件"""
    manager = get_business_manager()
    
    capability_enum = None
    if capability:
        capability_enum = PluginCapability(capability)
    
    status_enum = None
    if status:
        status_enum = PluginStatus(status)
    
    plugins = manager.list_plugins(
        capability=capability_enum,
        status=status_enum,
        enabled=enabled,
    )
    
    return {
        "plugins": [plugin.to_dict() for plugin in plugins],
        "count": len(plugins),
    }


@router.get("/business/plugins/{plugin_id}")
async def get_business_plugin(plugin_id: str):
    """获取业务插件详情"""
    manager = get_business_manager()
    plugin = manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin.to_dict()


@router.post("/business/plugins/{plugin_id}/activate")
async def activate_business_plugin(
    plugin_id: str,
    config: Optional[Dict[str, Any]] = None,
):
    """激活业务插件"""
    manager = get_business_manager()
    success = await manager.activate_plugin(plugin_id, config)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to activate plugin")
    return {"success": True, "message": f"Plugin {plugin_id} activated"}


@router.post("/business/plugins/{plugin_id}/deactivate")
async def deactivate_business_plugin(plugin_id: str):
    """停用业务插件"""
    manager = get_business_manager()
    success = await manager.deactivate_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to deactivate plugin")
    return {"success": True, "message": f"Plugin {plugin_id} deactivated"}


@router.post("/business/plugins/{plugin_id}/execute")
async def execute_business_plugin_capability(
    plugin_id: str,
    capability: str,
    input_data: Dict[str, Any],
):
    """执行业务插件能力"""
    manager = get_business_manager()
    try:
        capability_enum = PluginCapability(capability)
        result = await manager.execute_capability(
            capability=capability_enum,
            input_data=input_data,
            plugin_id=plugin_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/business/plugins/discover")
async def discover_business_plugins():
    """发现业务插件"""
    loader = get_business_loader()
    plugins = loader.discover_plugins()
    return {
        "plugins": [plugin.to_dict() for plugin in plugins],
        "count": len(plugins),
    }


@router.post("/business/plugins/register")
async def register_business_plugin(plugin_data: Dict[str, Any]):
    """注册业务插件"""
    registry = get_business_registry()
    try:
        plugin = BusinessPlugin.from_dict(plugin_data)
        registry.register(plugin)
        return plugin.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 数据源管理API ====================

@router.get("/data-sources")
async def list_data_sources(
    source_type: Optional[str] = None,
    market: Optional[str] = None,
    status: Optional[str] = None,
    enabled: Optional[bool] = None,
    tags: Optional[List[str]] = None,
):
    """列出所有数据源"""
    registry = get_ds_registry()
    
    type_enum = None
    if source_type:
        type_enum = DataSourceType(source_type)
    
    status_enum = None
    if status:
        status_enum = DataSourceStatus(status)
    
    sources = registry.list(
        source_type=type_enum,
        market=market,
        status=status_enum,
        enabled=enabled,
        tags=tags,
    )
    
    return {
        "sources": [source.to_dict() for source in sources],
        "count": len(sources),
    }


@router.get("/data-sources/{source_id}")
async def get_data_source(source_id: str):
    """获取数据源详情"""
    registry = get_ds_registry()
    source = registry.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source.to_dict()


@router.post("/data-sources/{source_id}/check")
async def check_data_source_availability(source_id: str):
    """检查数据源可用性"""
    manager = get_ds_manager()
    is_available = await manager.check_availability(source_id)
    return {
        "source_id": source_id,
        "available": is_available,
    }


@router.post("/data-sources/check-all")
async def check_all_data_sources_availability():
    """检查所有数据源可用性"""
    manager = get_ds_manager()
    await manager.check_all_availability()
    return {"success": True, "message": "All data sources checked"}


@router.post("/data-sources/stock-list")
async def get_stock_list_from_sources(
    market: Optional[str] = None,
    preferred_sources: Optional[List[str]] = None,
):
    """从数据源获取股票列表"""
    manager = get_ds_manager()
    df, source_name = await manager.get_stock_list(market, preferred_sources)
    
    if df is None:
        raise HTTPException(status_code=404, detail="No data source available")
    
    return {
        "data": df.to_dict(orient="records"),
        "source": source_name,
        "count": len(df),
    }


@router.post("/data-sources/daily-basic")
async def get_daily_basic_from_sources(
    trade_date: str,
    market: Optional[str] = None,
    preferred_sources: Optional[List[str]] = None,
):
    """从数据源获取每日基础数据"""
    manager = get_ds_manager()
    df, source_name = await manager.get_daily_basic(trade_date, market, preferred_sources)
    
    if df is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    return {
        "data": df.to_dict(orient="records"),
        "source": source_name,
        "count": len(df),
    }


@router.post("/data-sources/realtime-quotes")
async def get_realtime_quotes_from_sources(
    market: Optional[str] = None,
    preferred_sources: Optional[List[str]] = None,
):
    """从数据源获取实时行情"""
    manager = get_ds_manager()
    quotes, source_name = await manager.get_realtime_quotes(market, preferred_sources)
    
    if quotes is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    return {
        "quotes": quotes,
        "source": source_name,
        "count": len(quotes),
    }


@router.post("/data-sources/kline")
async def get_kline_from_sources(
    code: str,
    period: str = "day",
    limit: int = 120,
    adj: Optional[str] = None,
    market: Optional[str] = None,
    preferred_sources: Optional[List[str]] = None,
):
    """从数据源获取K线数据"""
    manager = get_ds_manager()
    kline, source_name = await manager.get_kline(
        code, period, limit, adj, market, preferred_sources
    )
    
    if kline is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    return {
        "kline": kline,
        "source": source_name,
        "count": len(kline),
    }


@router.post("/data-sources/news")
async def get_news_from_sources(
    code: str,
    days: int = 2,
    limit: int = 50,
    include_announcements: bool = True,
    market: Optional[str] = None,
    preferred_sources: Optional[List[str]] = None,
):
    """从数据源获取新闻数据"""
    manager = get_ds_manager()
    news, source_name = await manager.get_news(
        code, days, limit, include_announcements, market, preferred_sources
    )
    
    if news is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    return {
        "news": news,
        "source": source_name,
        "count": len(news),
    }


@router.post("/data-sources/import/yaml")
async def import_data_sources_from_yaml(
    yaml_content: str,
    update_existing: bool = False,
):
    """从YAML字符串导入数据源配置"""
    service = get_ds_service()
    try:
        result = await service.import_from_yaml_string(yaml_content, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data-sources/import/yaml-file")
async def import_data_sources_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入数据源配置"""
    service = get_ds_service()
    try:
        # 读取文件内容
        content = await file.read()
        yaml_str = content.decode('utf-8')
        
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data-sources/export/yaml")
async def export_data_sources_to_yaml(
    source_type: Optional[str] = None,
    enabled: Optional[bool] = None,
):
    """导出数据源配置为YAML格式"""
    service = get_ds_service()
    try:
        sources = await service.get_all(source_type=source_type, enabled=enabled)
        
        from app.platform.data_sources.yaml_loader import DataSourceYAMLLoader
        import yaml
        
        data = {"data_sources": [s.to_dict() for s in sources]}
        yaml_str = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return {
            "yaml": yaml_str,
            "count": len(sources),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 租户管理API ====================

@router.get("/tenants")
async def list_tenants(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
):
    """列出租户"""
    registry = get_tenant_registry()
    
    # 转换状态和等级
    tenant_status = TenantStatus(status) if status else None
    tenant_tier = TenantTier(tier) if tier else None
    
    if search:
        tenants = registry.search(search)
    else:
        tenants = registry.list(status=tenant_status, tier=tenant_tier)
    
    return {
        "tenants": [tenant.to_dict() for tenant in tenants],
        "count": len(tenants),
    }


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """获取租户详情"""
    registry = get_tenant_registry()
    tenant = registry.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant.to_dict()


@router.get("/tenants/{tenant_id}/statistics")
async def get_tenant_statistics(tenant_id: str):
    """获取租户统计信息"""
    manager = get_tenant_manager()
    stats = await manager.get_tenant_statistics(tenant_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return stats


@router.post("/tenants/{tenant_id}/status")
async def update_tenant_status(
    tenant_id: str,
    status: str,
):
    """更新租户状态"""
    registry = get_tenant_registry()
    try:
        tenant_status = TenantStatus(status)
        success = registry.update_status(tenant_id, tenant_status)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return {"success": True, "status": status}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")


# ==================== 租户YAML声明式管理API ====================

@router.post("/tenants/import/yaml")
async def import_tenants_from_yaml_string(
    yaml_str: str,
    update_existing: bool = False,
):
    """从YAML字符串导入租户配置"""
    service = get_tenant_service()
    try:
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tenants/import/yaml-file")
async def import_tenants_from_yaml_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
):
    """从YAML文件导入租户配置"""
    service = get_tenant_service()
    try:
        content = await file.read()
        yaml_str = content.decode('utf-8')
        result = await service.import_from_yaml_string(yaml_str, update_existing)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants/export/yaml")
async def export_tenants_to_yaml(
    status: Optional[str] = None,
    tier: Optional[str] = None,
):
    """导出租户配置为YAML格式"""
    service = get_tenant_service()
    try:
        # 构建过滤函数
        filter_func = None
        if status or tier:
            def filter_tenant(tenant):
                if status and tenant.status.value != status:
                    return False
                if tier and tenant.tier.value != tier:
                    return False
                return True
            filter_func = filter_tenant
        
        yaml_str = await service.export_to_yaml_string(filter_func)
        return {"yaml": yaml_str}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Supabase 平台数据管理API ====================

@router.get("/supabase/health")
async def check_supabase_health():
    """检查 Supabase 连接健康状态"""
    from app.platform.supabase import get_supabase_client
    
    try:
        client = get_supabase_client()
        is_healthy = client.health_check()
        return {
            "healthy": is_healthy,
            "enabled": settings.USE_SUPABASE_FOR_PLATFORM,
        }
    except Exception as e:
        return {
            "healthy": False,
            "enabled": settings.USE_SUPABASE_FOR_PLATFORM,
            "error": str(e),
        }


@router.post("/supabase/migrate")
async def migrate_to_supabase(
    migrate_users: bool = True,
    migrate_tenants: bool = True,
    migrate_configs: bool = True,
):
    """迁移平台数据到 Supabase"""
    from app.platform.supabase import get_migration
    
    if not settings.USE_SUPABASE_FOR_PLATFORM:
        raise HTTPException(
            status_code=400,
            detail="Supabase is not enabled. Set USE_SUPABASE_FOR_PLATFORM=true"
        )
    
    try:
        migration = get_migration()
        results = {}
        
        if migrate_users:
            results["users"] = await migration.migrate_users()
        
        if migrate_tenants:
            results["tenants"] = await migration.migrate_tenants()
        
        if migrate_configs:
            results["configs"] = await migration.migrate_configs()
        
        return {
            "success": True,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"迁移失败: {str(e)}")

