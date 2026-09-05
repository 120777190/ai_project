import PyPDF2
import docx
import os
import zipfile

def detect_file_type(file_path):
    """通过文件头检测文件的真实格式（中文友好版）"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(100)
            
            # 检测 PDF
            if header.startswith(b'%PDF'):
                return 'pdf'
            
            # 检测 DOCX
            if header.startswith(b'PK\x03\x04'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        if 'word/document.xml' in zf.namelist():
                            return 'docx'
                except:
                    pass
                return 'zip'
            
            # 尝试解码为文本（优先于二进制判断）
            try:
                f.seek(0)
                text_sample = f.read(200).decode('utf-8')
                # 如果成功解码，就认为是文本文件
                return 'txt'
            except UnicodeDecodeError:
                try:
                    f.seek(0)
                    f.read(200).decode('gbk')
                    return 'txt'
                except:
                    pass
            
            # 最后才判断二进制
            printable = sum(1 for b in header[:50] if 32 <= b < 127 or b in (9, 10, 13))
            if printable / len(header[:50]) < 0.5:
                return 'binary'
            
            return 'txt'
    except Exception:
        return 'unknown'

def read_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='gbk') as f:
            return f.read()

def read_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text if text.strip() else "PDF 中未提取到文字（可能是扫描件）"
    except Exception as e:
        return f"读取 PDF 出错：{e}"

def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
        return text if text.strip() else "Word 文档中未找到文字"
    except Exception as e:
        return f"读取 Word 出错：{e}"

def read_file(file_path):
    """自动检测文件格式并读取内容"""
    # 先检测真实格式
    real_type = detect_file_type(file_path)
    
    print(f"📂 文件: {os.path.basename(file_path)}")
    print(f"📌 检测结果: {real_type}")
    
    if real_type == 'not_found':
        return f"❌ 文件不存在：{file_path}"
    elif real_type == 'pdf':
        return read_pdf(file_path)
    elif real_type == 'docx':
        return read_docx(file_path)
    elif real_type == 'txt':
        return read_txt(file_path)
    elif real_type == 'binary':
        return "⚠️ 这是二进制文件，暂不支持解析"
    else:
        return f"⚠️ 无法识别的格式：{real_type}"

# 测试入口
if __name__ == "__main__":
    test_file = r"G:\ai_project\test.docx"  # 改成你的文件路径
    print(f"🚀 开始读取文件: {test_file}")
    print("=" * 50)
    content = read_file(test_file)
    print("=" * 50)
    print("📝 最终内容：")
    print(content)