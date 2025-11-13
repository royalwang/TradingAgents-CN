"""
解析器工厂
"""
from typing import List, Optional
from enum import Enum
from pathlib import Path

from .document_parser import DocumentParser, ParseResult
from .document_parser import (
    PDFParser,
    DOCXParser,
    TXTParser,
    ExcelParser,
    HTMLParser,
    JSONParser,
)


class ParserType(str, Enum):
    """解析器类型"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    EXCEL = "excel"
    HTML = "html"
    JSON = "json"


class ParserFactory:
    """解析器工厂"""
    
    def __init__(self):
        self._parsers: List[DocumentParser] = [
            PDFParser(),
            DOCXParser(),
            TXTParser(),
            ExcelParser(),
            HTMLParser(),
            JSONParser(),
        ]
    
    def get_parser(self, file_path: str) -> Optional[DocumentParser]:
        """获取适合的解析器"""
        for parser in self._parsers:
            if parser.supports(file_path):
                return parser
        return None
    
    def register_parser(self, parser: DocumentParser):
        """注册解析器"""
        self._parsers.append(parser)
    
    async def parse(self, file_path: str) -> ParseResult:
        """解析文件"""
        parser = self.get_parser(file_path)
        if not parser:
            return ParseResult(
                title=Path(file_path).stem,
                content="",
                metadata={"file_path": file_path},
                error=f"Unsupported file type: {Path(file_path).suffix}",
            )
        
        return await parser.parse(file_path)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        formats = set()
        for parser in self._parsers:
            if isinstance(parser, PDFParser):
                formats.add(".pdf")
            elif isinstance(parser, DOCXParser):
                formats.update([".docx", ".doc"])
            elif isinstance(parser, TXTParser):
                formats.update([".txt", ".md", ".markdown"])
            elif isinstance(parser, ExcelParser):
                formats.update([".xlsx", ".xls"])
            elif isinstance(parser, HTMLParser):
                formats.update([".html", ".htm"])
            elif isinstance(parser, JSONParser):
                formats.add(".json")
        return sorted(list(formats))


# 全局工厂实例
_global_factory: Optional[ParserFactory] = None


def get_parser_factory() -> ParserFactory:
    """获取全局解析器工厂"""
    global _global_factory
    if _global_factory is None:
        _global_factory = ParserFactory()
    return _global_factory

