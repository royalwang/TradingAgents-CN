"""
MCP服务器实现
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from typing import Optional as Opt


class ToolType(str, Enum):
    """工具类型"""
    FUNCTION = "function"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    CUSTOM = "custom"


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    tool_type: ToolType
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }


class MCPToolRegistry:
    """MCP工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
    
    def register(
        self,
        name: str,
        description: str,
        tool_type: ToolType,
        parameters: Optional[Dict[str, Any]] = None,
        handler: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MCPTool:
        """注册工具"""
        if name in self._tools:
            raise ValueError(f"Tool {name} already registered")
        
        tool = MCPTool(
            name=name,
            description=description,
            tool_type=tool_type,
            parameters=parameters or {},
            handler=handler,
            metadata=metadata or {},
        )
        
        self._tools[name] = tool
        return tool
    
    def get(self, name: str) -> Optional[MCPTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list(self) -> List[MCPTool]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False


class MCPServer:
    """MCP服务器"""
    
    def __init__(self, registry: Optional[MCPToolRegistry] = None):
        self.registry = registry or MCPToolRegistry()
        self._running = False
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行工具"""
        tool = self.registry.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found",
            }
        
        if not tool.handler:
            return {
                "success": False,
                "error": f"Tool {tool_name} has no handler",
            }
        
        try:
            # 验证参数
            if not self._validate_parameters(tool, parameters):
                return {
                    "success": False,
                    "error": "Invalid parameters",
                }
            
            # 执行工具
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**parameters)
            else:
                result = tool.handler(**parameters)
            
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _validate_parameters(self, tool: MCPTool, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        # 简单的参数验证
        required_params = tool.parameters.get("required", [])
        for param in required_params:
            if param not in parameters:
                return False
        return True
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [tool.to_dict() for tool in self.registry.list()]
    
    def start(self):
        """启动服务器"""
        self._running = True
    
    def stop(self):
        """停止服务器"""
        self._running = False
    
    @property
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running


# 全局服务器实例
_global_server: Opt[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """获取全局MCP服务器"""
    global _global_server
    if _global_server is None:
        _global_server = MCPServer()
    return _global_server

