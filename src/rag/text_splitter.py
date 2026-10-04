from src.config.settings import settings


def chunk_text(text, chunk_size=settings.CHUNK_SIZE, overlap=settings.OVERLAP):
    chunks = []
    start = 0
    text_length = len(text)
    
    # 循环直到指针走到文本末尾
    while start < text_length:
        # 1. 计算这一块的结束位置（不能超过总长度）
        end = start + chunk_size
        if end > text_length:
            end = text_length
            
        # 2. 切片并存入 chunks 列表
        chunk = text[start:end]
        chunks.append(chunk)
        
        # 3. 关键：更新 start 指针。
        # 正常应该是 start += chunk_size，但因为有重叠，必须减去 overlap
        start += (chunk_size - overlap)
        
        # 4. 防御机制：如果已经切到末尾，就退出循环
        if end == text_length:
            break
            
    return chunks