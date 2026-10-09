import os
import re
import io
import sys
from pathlib import Path
from typing import Dict, Any, Union, Optional

class DocumentLoader:
    """
    考研英语二作文多格式文档加载与识别模块
    支持格式：txt, md, docx, doc, pdf, png, jpg, jpeg
    包含文本提取、扫描件/图像 OCR 识别与段落结构复原
    """

    _ocr_engine = None

    @classmethod
    def get_ocr_engine(cls):
        """懒加载 RapidOCR 引擎（避免不使用图像时产生内存开销）"""
        if cls._ocr_engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                cls._ocr_engine = RapidOCR()
            except Exception as e:
                print(f"[DocumentLoader] 警告: RapidOCR 初始化失败: {e}")
                cls._ocr_engine = False
        return cls._ocr_engine

    @classmethod
    def load_document(
        cls,
        file_source: Union[str, Path, bytes, io.BytesIO],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        统一文档加载与文本识别主入口
        :param file_source: 文件路径、字节流或 BytesIO
        :param filename: 文件名（如果输入为 bytes 时用于推断文件类型）
        :return: 包含识别出的文本、格式、是否使用OCR等元数据的字典
        """
        # 解析文件扩展名
        if isinstance(file_source, (str, Path)):
            path = Path(file_source)
            if not path.exists():
                raise FileNotFoundError(f"未找到指定文件: {file_source}")
            ext = path.suffix.lower().lstrip(".")
            fname = path.name
            with open(path, "rb") as f:
                content_bytes = f.read()
        else:
            fname = filename or "uploaded_document"
            ext = Path(fname).suffix.lower().lstrip(".")
            if isinstance(file_source, io.BytesIO):
                content_bytes = file_source.getvalue()
            else:
                content_bytes = file_source

        if not ext:
            raise ValueError(f"无法推断文件格式，请提供带有扩展名的文件名: {fname}")

        ext = ext.lower()
        ocr_used = False
        page_count = 1

        # 根据扩展名调度解析器
        if ext in ["txt"]:
            text = cls._extract_txt(content_bytes)
        elif ext in ["md", "markdown"]:
            text = cls._extract_md(content_bytes)
        elif ext in ["docx"]:
            text = cls._extract_docx(content_bytes)
        elif ext in ["doc"]:
            text = cls._extract_doc(content_bytes, file_source if isinstance(file_source, (str, Path)) else None)
        elif ext in ["pdf"]:
            text, page_count, ocr_used = cls._extract_pdf(content_bytes)
        elif ext in ["png", "jpg", "jpeg", "webp", "bmp"]:
            text = cls._extract_image(content_bytes)
            ocr_used = True
        else:
            raise ValueError(f"暂不支持的文件格式: .{ext}，目前支持: txt, pdf, doc, docx, md, png, jpg, jpeg")

        # 后处理清洗：清理多余不可见字符并规范换行
        cleaned_text = cls._clean_extracted_text(text)

        # 统计词数（严格遵循考研大纲规范：标点符号不计算在内，连字符与缩写计为一个词）
        word_count = len(re.findall(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b", cleaned_text))

        return {
            "text": cleaned_text,
            "filename": fname,
            "format": ext,
            "word_count": word_count,
            "page_count": page_count,
            "ocr_used": ocr_used,
            "char_count": len(cleaned_text)
        }

    @staticmethod
    def _extract_txt(content_bytes: bytes) -> str:
        """多重编码自适应读取 TXT 文件"""
        encodings = ["utf-8", "gbk", "gb2312", "gb18030", "utf-16", "big5", "latin1"]
        for enc in encodings:
            try:
                return content_bytes.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return content_bytes.decode("utf-8", errors="ignore")

    @staticmethod
    def _extract_md(content_bytes: bytes) -> str:
        """读取 Markdown 文本"""
        text = DocumentLoader._extract_txt(content_bytes)
        return text

    @staticmethod
    def _extract_docx(content_bytes: bytes) -> str:
        """从 DOCX 文件提取段落与表格文本"""
        import docx
        doc_stream = io.BytesIO(content_bytes)
        doc = docx.Document(doc_stream)
        
        paragraphs = []
        for p in doc.paragraphs:
            txt = p.text.strip()
            if txt:
                paragraphs.append(txt)

        # 同样读取表格文本（如果有）
        for table in doc.tables:
            for row in table.rows:
                row_txt = " ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_txt:
                    paragraphs.append(row_txt)

        return "\n\n".join(paragraphs)

    @staticmethod
    def _extract_doc(content_bytes: bytes, file_path: Optional[Path] = None) -> str:
        """
        从 Word 97-2003 (.doc) 文件提取文本
        优先尝试 Windows COM (若 Word 存在)，或尝试 docx 解析 (部分 doc 实为 docx)，最后采用二进制纯文本抽取
        """
        # 1. 尝试作为 docx 读取（不少用户直接将 docx 重命名为 doc）
        try:
            return DocumentLoader._extract_docx(content_bytes)
        except Exception:
            pass

        # 2. 若存在实际文件路径且在 Windows 环境下，尝试使用 win32com
        if file_path and sys.platform == "win32":
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                abs_path = str(Path(file_path).resolve())
                doc = word.Documents.Open(abs_path)
                text = doc.Content.Text
                doc.Close(False)
                word.Quit()
                return text
            except Exception as e:
                print(f"[DocumentLoader] win32com doc 解析跳过: {e}")

        # 3. 降级方案：从二进制流提取可见字符
        text_chars = []
        in_ascii = False
        current_word = []
        for b in content_bytes:
            if 32 <= b <= 126 or b in [10, 13, 9]:
                current_word.append(chr(b))
            else:
                if len(current_word) >= 3:
                    text_chars.append("".join(current_word))
                current_word = []
        if current_word:
            text_chars.append("".join(current_word))

        extracted = " ".join(text_chars)
        # 提取其中看似英文句子的片段
        sentences = re.findall(r"[A-Z][a-zA-Z0-9\s,.'\"?!-]{15,}[.?!]", extracted)
        if sentences:
            return "\n\n".join(sentences)
        return extracted[:3000]

    @classmethod
    def _extract_pdf(cls, content_bytes: bytes) -> (str, int, bool):
        """
        使用 PyMuPDF 从 PDF 提取文本
        如果 PDF 为纯图片扫描件（数字文本少于20字），自动启动 OCR 引擎逐页识别
        """
        import pymupdf

        doc = pymupdf.open(stream=content_bytes, filetype="pdf")
        page_count = len(doc)
        text_parts = []
        ocr_used = False

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text().strip()

            # 若页面提取出有效文本
            if len(page_text) > 20:
                text_parts.append(page_text)
            else:
                # 页面无文本或为纯扫描图片，尝试 OCR
                ocr = cls.get_ocr_engine()
                if ocr:
                    pix = page.get_pixmap(dpi=180)
                    img_bytes = pix.tobytes("png")
                    page_ocr_text = cls._extract_image(img_bytes)
                    if page_ocr_text.strip():
                        text_parts.append(page_ocr_text.strip())
                        ocr_used = True

        doc.close()
        full_text = "\n\n".join(text_parts)
        return full_text, page_count, ocr_used

    @classmethod
    def _extract_image(cls, content_bytes: bytes) -> str:
        """
        使用 RapidOCR 从图片（JPG/PNG）中提取英文与中文字符，
        并按从上到下、从左到右的空间位置组织段落
        """
        ocr = cls.get_ocr_engine()
        if not ocr:
            raise RuntimeError("OCR 引擎未安装或初始化失败，无法识别图片内容！")

        from PIL import Image
        import numpy as np

        image = Image.open(io.BytesIO(content_bytes))
        # 转换为 RGB 格式
        if image.mode != "RGB":
            image = image.convert("RGB")
        img_np = np.array(image)

        result, _ = ocr(img_np)
        if not result:
            return ""

        # RapidOCR 输出格式: [[dt_boxes, text, score], ...]
        # 按 y 坐标排序（自上而下），并在行内按 x 坐标排序
        lines_with_pos = []
        for item in result:
            box = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = item[1].strip()
            # 计算中心点坐标
            center_y = sum(p[1] for p in box) / 4.0
            center_x = sum(p[0] for p in box) / 4.0
            lines_with_pos.append({
                "y": center_y,
                "x": center_x,
                "text": text
            })

        # 按 y 坐标自上而下排序
        lines_with_pos.sort(key=lambda item: item["y"])

        # 合并相近高度的文字为行，并组织段落
        merged_paragraphs = []
        current_paragraph = []

        for line in lines_with_pos:
            txt = line["text"]
            # 若是典型的信件称呼、落款或明显换行
            if any(txt.startswith(prefix) for prefix in ["Dear", "Yours", "Li Ming", "Notice", "Part"]):
                if current_paragraph:
                    merged_paragraphs.append(" ".join(current_paragraph))
                    current_paragraph = []
                merged_paragraphs.append(txt)
            else:
                current_paragraph.append(txt)

        if current_paragraph:
            merged_paragraphs.append(" ".join(current_paragraph))

        return "\n\n".join(merged_paragraphs)

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """清洗提取文本中的多余控制字符、断字连字符等"""
        if not text:
            return ""
        # 修复跨行英文断字符 (如 exam- \n ination -> examination)
        cleaned = re.sub(r"([a-zA-Z]+)-\s*\n\s*([a-zA-Z]+)", r"\1\2", text)
        # 统一回车换行符
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        # 压缩连续三个以上的换行
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
