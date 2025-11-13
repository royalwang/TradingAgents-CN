"""
MCP客户端实现
用于连接到MCP服务器
"""
from typing import Dict, Any, List, Optional
import httpx
import asyncio


class MCPClient:
    """MCP客户端"""
    
    def __init__(self, server_url: str, timeout: int = 30):
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def connect(self):
        """连接服务器"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.server_url,
                timeout=self.timeout,
            )
    
    async def disconnect(self):
        """断开连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        await self.connect()
        
        try:
            response = await self._client.get("/mcp/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to list tools: {str(e)}")
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行工具"""
        await self.connect()
        
        try:
            response = await self._client.post(
                "/mcp/execute",
                json={
                    "tool_name": tool_name,
                    "parameters": parameters,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to execute tool: {str(e)}")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

