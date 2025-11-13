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

