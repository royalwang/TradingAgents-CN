"""
股票分析业务插件主模块
"""
from typing import Dict, Any, Optional
import asyncio
import logging

from app.platform.business.business_plugin import PluginCapability
from app.services.analysis_service import AnalysisService
from app.services.simple_analysis_service import SimpleAnalysisService
from app.models.analysis import SingleAnalysisRequest, AnalysisParameters

logger = logging.getLogger(__name__)


class StockAnalysisPlugin:
    """股票分析业务插件"""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.simple_analysis_service = SimpleAnalysisService()
        self._initialized = False
    
    async def activate(self, config: Optional[Dict[str, Any]] = None):
        """激活插件"""
        logger.info("激活股票分析业务插件")
        self._initialized = True
    
    async def deactivate(self):
        """停用插件"""
        logger.info("停用股票分析业务插件")
        self._initialized = False
    
    async def execute(
        self,
        capability: PluginCapability,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行插件能力"""
        if not self._initialized:
            raise RuntimeError("Plugin not activated")
        
        if capability == PluginCapability.ANALYSIS:
            return await self._execute_analysis(input_data)
        else:
            raise ValueError(f"Unsupported capability: {capability}")
    
    async def _execute_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行股票分析"""
        try:
            # 提取参数
            symbol = input_data.get("symbol")
            if not symbol:
                raise ValueError("Stock symbol is required")
            
            analysis_date = input_data.get("analysis_date")
            analysts = input_data.get("analysts", ["market", "fundamentals"])
            research_depth = input_data.get("research_depth", "标准")
            market_type = input_data.get("market_type", "A股")
            llm_provider = input_data.get("llm_provider")
            llm_model = input_data.get("llm_model")
            
            # 创建分析请求
            parameters = AnalysisParameters(
                analysis_date=analysis_date,
                selected_analysts=analysts,
                research_depth=research_depth,
                market_type=market_type,
                llm_provider=llm_provider,
                llm_model=llm_model,
            )
            
            request = SingleAnalysisRequest(
                symbol=symbol,
                parameters=parameters,
            )
            
            # 执行分析
            import time
            task_id = f"plugin_{symbol}_{int(time.time())}"
            result = await self.simple_analysis_service.execute_analysis_background(
                task_id=task_id,
                user_id="plugin_user",
                request=request,
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "result": result,
            }
        except Exception as e:
            logger.error(f"股票分析执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


def create_plugin():
    """创建插件实例"""
    return StockAnalysisPlugin()


# 兼容性：支持不同的导入方式
Plugin = StockAnalysisPlugin
plugin = StockAnalysisPlugin()

