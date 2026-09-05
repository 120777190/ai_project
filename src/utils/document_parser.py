# src/utils/document_parser.py
# ====== 通用文档解析工具 ======
# 职责：解析 .txt / .pdf / .docx 文档，提取文本内容
# 适用范围：所有需要从文档中提取文本的场景（上传、RAG、批量处理等）

import os
import tempfile
from typing import Union

# 导入底层的文档解析实现（原 read_doc.py 的功能）
try:
    from .read_doc import read_file
except ImportError:
    # 如果 read_doc.py 还在项目根目录，兼容处理
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from read_doc import read_file


def parse_document(source: Union[str, bytes], filename: str = None) -> str:
    """
    解析文档，提取文本内容
    
    参数：
        source: str | bytes - 文件路径（str）或文件字节流（bytes）
        filename: str - 当 source 是 bytes 时，需要提供文件名以判断格式
    
    返回：
        str - 提取的文本内容
    
    示例：
        # 从文件路径解析
        content = parse_document("/path/to/file.pdf")
        
        # 从字节流解析（如用户上传）
        content = parse_document(file_bytes, filename="report.docx")
    """
    # 情况1：source 是文件路径
    if isinstance(source, str):
        return read_file(source)
    
    # 情况2：source 是字节流
    if isinstance(source, bytes):
        if not filename:
            raise ValueError("从字节流解析时，必须提供 filename 参数")
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(source)
            tmp_path = tmp.name
        try:
            return read_file(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    raise TypeError(f"不支持的 source 类型: {type(source)}")