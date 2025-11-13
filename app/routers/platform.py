"""
智能体平台API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.platform.agents import AgentRegistry, AgentManager, AgentFactory, get_registry, get_manager, get_factory
from app.platform.knowledge import KnowledgeBase, create_vector_store, create_embedding_service
from app.platform.parsers import ParserFactory, get_parser_factory
from app.platform.mcp import MCPServer, MCPToolRegistry, get_mcp_server
from app.platform.plugins import PluginRegistry, PluginManager, PluginLoader, get_registry as get_plugin_registry, get_manager as get_plugin_manager
from app.platform.workflow import WorkflowEngine, WorkflowExecutor, get_engine, get_executor
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

