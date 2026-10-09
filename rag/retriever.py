import re
import json
import socket
from pathlib import Path
from typing import List, Dict, Any, Optional
from rag.config import rag_config
from rag.embedder import OllamaEmbedder
from rag.milvus_manager import MilvusManager

KB_INDEX_PATH = Path(__file__).parent.parent / "knowledge_base" / "index.json"

class KnowledgeRetriever:
    """考研英语一 & 英语二作文评分多场景 RAG 语义检索器（支持向量检索 + 智能内存备用降级）"""

    def __init__(self, embedder: OllamaEmbedder = None, milvus_mgr: MilvusManager = None):
        self._embedder = embedder
        self._milvus_mgr = milvus_mgr
        self._initialized = False
        self._is_available = False
        self._local_chunks = None

    @staticmethod
    def _probe_milvus_alive() -> bool:
        """极速探活 Milvus 端口（超时 0.08 秒），杜绝沉重 gRPC 握手阻塞 30 秒"""
        try:
            uri = rag_config.MILVUS_URI.replace("http://", "").replace("https://", "").strip("/")
            if ":" in uri:
                host, port_str = uri.split(":", 1)
                port = int(port_str.split("/")[0])
            else:
                host, port = uri, 19530
            if host in ("localhost", "127.0.0.1"):
                host = "127.0.0.1"
            sock = socket.create_connection((host, port), timeout=0.08)
            sock.close()
            return True
        except Exception:
            return False

    def _ensure_services(self) -> bool:
        if self._initialized:
            return self._is_available
        self._initialized = True
        try:
            if not self._probe_milvus_alive():
                print("[KnowledgeRetriever] 提示: Milvus 服务端口未启动，系统秒级启用轻量级语义知识库高速检索引擎")
                self._is_available = False
                return False

            if self._embedder is None:
                self._embedder = OllamaEmbedder()
            if self._milvus_mgr is None:
                self._milvus_mgr = MilvusManager()
            self._is_available = True
            return True
        except Exception as e:
            print(f"[KnowledgeRetriever] 提示: Milvus 或向量模型服务未就绪 ({e})，系统已平滑启用轻量级语义知识库高速检索引擎")
            self._is_available = False
            return False

    def _load_local_chunks(self) -> List[Dict[str, Any]]:
        """从 index.json 懒加载知识分块作为高可靠检索底座"""
        if self._local_chunks is not None:
            return self._local_chunks
        if KB_INDEX_PATH.exists():
            try:
                with open(KB_INDEX_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._local_chunks = data.get("chunks", [])
            except Exception as e:
                print(f"[KnowledgeRetriever] 读取 index.json 失败: {e}")
                self._local_chunks = []
        else:
            self._local_chunks = []
        return self._local_chunks

    def _fallback_local_search(
        self,
        query: str,
        exam_category: Optional[str] = None,
        essay_type: Optional[str] = None,
        module: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """当 Milvus 未就绪时，基于内存分块与关键词相关性执行高可靠降级检索"""
        chunks = self._load_local_chunks()
        if not chunks:
            return []

        # 候选过滤
        filtered = []
        for c in chunks:
            c_exam = c.get("exam_category", "通用")
            c_type = c.get("essay_type", "通用")
            c_mod = c.get("module", "")
            c_cat = c.get("category", "")

            # 考研类别过滤（英语一 / 英语二 / 通用）
            if exam_category and c_exam not in [exam_category, "通用"]:
                continue
            # 题型过滤（小作文 / 大作文 / 通用）
            if essay_type and c_type not in [essay_type, "通用"]:
                continue
            # 模块过滤
            if module and c_mod != module:
                continue
            # 子类别过滤
            if category and c_cat != category:
                continue

            filtered.append(c)

        if not filtered:
            # 放宽 category 限制
            for c in chunks:
                c_exam = c.get("exam_category", "通用")
                c_type = c.get("essay_type", "通用")
                if exam_category and c_exam not in [exam_category, "通用"]:
                    continue
                if essay_type and c_type not in [essay_type, "通用"]:
                    continue
                if module and c.get("module") != module:
                    continue
                filtered.append(c)

        # 多粒度关键词与语义特征匹配评分（支持中英文混合与分词）
        raw_words = [w for w in query.lower().split() if len(w) > 1]
        chinese_tokens = re.findall(r"[\u4e00-\u9fa5]{2,4}", query)
        english_tokens = re.findall(r"\b[a-zA-Z0-9]{3,}\b", query.lower())
        query_words = set(raw_words + chinese_tokens + english_tokens)

        scored = []
        for c in filtered:
            text = (c.get("title", "") + " " + c.get("content", "")).lower()
            score = 0.0
            # 关键词与分词加权
            for w in query_words:
                if w in text:
                    score += 1.5 if len(w) >= 3 else 1.0
            # 精确短语权重
            if len(query.strip()) > 2 and query.lower() in text:
                score += 4.0
            # 基础分保证保底结果
            score += 0.1
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def search(
        self,
        query: str,
        exam_category: Optional[str] = None,
        essay_type: Optional[str] = None,
        module: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        通用语义检索，支持考试类别（英语一/英语二）、大小作文、模块混合过滤
        """
        if not self._ensure_services():
            return self._fallback_local_search(
                query=query,
                exam_category=exam_category,
                essay_type=essay_type,
                module=module,
                category=category,
                top_k=top_k
            )

        try:
            query_vector = self._embedder.embed_query(query)

            # 构建 Milvus 标量过滤表达式
            filter_parts = []
            if exam_category:
                filter_parts.append(f'(exam_category == "{exam_category}" or exam_category == "通用")')
            if essay_type:
                filter_parts.append(f'(essay_type == "{essay_type}" or essay_type == "通用")')
            if module:
                filter_parts.append(f'module == "{module}"')
            if category:
                filter_parts.append(f'category == "{category}"')

            filter_expr = " and ".join(filter_parts) if filter_parts else None

            results = self._milvus_mgr.search(
                query_vector=query_vector,
                filter_expr=filter_expr,
                top_k=top_k
            )

            filtered = [r for r in results if r.get("score") is not None and r["score"] >= min_score]
            if filtered:
                return filtered
            # 若 Milvus 未命中足够结果，降级为本地规则结果补充
            return self._fallback_local_search(
                query=query,
                exam_category=exam_category,
                essay_type=essay_type,
                module=module,
                category=category,
                top_k=top_k
            )
        except Exception as e:
            print(f"[KnowledgeRetriever] Milvus 检索异常，平滑降级为本地检索: {e}")
            return self._fallback_local_search(
                query=query,
                exam_category=exam_category,
                essay_type=essay_type,
                module=module,
                category=category,
                top_k=top_k
            )

    def retrieve_scoring_criteria(
        self,
        essay_type: str,
        exam_category: str = "英语二",
        query: str = "",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索评分标准、大纲档次描述及扣分规则"""
        search_query = query if query.strip() else f"{exam_category} {essay_type} 官方评分标准 大纲档次划分 扣分规则"
        return self.search(
            query=search_query,
            exam_category=exam_category,
            essay_type=essay_type,
            module="scoring_criteria",
            top_k=top_k
        )

    def retrieve_sample_essays(
        self,
        essay_type: str,
        exam_category: str = "英语二",
        sub_type: Optional[str] = None,
        band: Optional[str] = None,
        topic: str = "",
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """检索与当前题目或题型最相关的标杆范文（含高分亮点与低分错误分析）"""
        query_terms = [exam_category, essay_type]
        if sub_type:
            query_terms.append(sub_type)
        if band:
            query_terms.append(band)
        if topic:
            query_terms.append(topic)
        query = " ".join(query_terms)

        return self.search(
            query=query,
            exam_category=exam_category,
            essay_type=essay_type,
            module="sample_essays",
            top_k=top_k
        )

    def retrieve_writing_knowledge(
        self,
        query: str,
        essay_type: Optional[str] = None,
        exam_category: str = "英语二",
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """检索高分写作知识（高级词汇替换、图画/图表/书信表达、连接词、高级句型）"""
        return self.search(
            query=query,
            exam_category=exam_category,
            essay_type=essay_type,
            module="writing_knowledge",
            top_k=top_k
        )

    def retrieve_common_errors(self, student_text_or_issue: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """针对学生作文中的疑似错误进行常见病句模式检索"""
        return self.search(
            query=student_text_or_issue,
            exam_category=None,
            essay_type=None,
            module="common_errors",
            top_k=top_k
        )

    def retrieve_evaluation_context(
        self,
        essay_type: str,
        essay_topic: str,
        essay_text: str,
        exam_category: str = "英语二"
    ) -> Dict[str, Any]:
        """
        【Agent 综合评分上下文打包】
        一次性完成指定考试类别（英语一/英语二）的官方评分标准、同类范文锚点、写作语料及常见病句辨析匹配。
        """
        # 1. 评分标准
        criteria = self.retrieve_scoring_criteria(
            essay_type=essay_type,
            exam_category=exam_category,
            query=f"{exam_category} {essay_type} 评分大纲 各档次描述 扣分细则",
            top_k=5
        )

        # 2. 相似标杆范文
        samples = self.retrieve_sample_essays(
            essay_type=essay_type,
            exam_category=exam_category,
            topic=essay_topic,
            top_k=3
        )

        # 3. 写作语料推荐
        knowledge_query = f"{essay_topic} {essay_type} 图画描述 哲理思辨 高级表达 连接词 高分句型" if exam_category == "英语一" else f"{essay_topic} {essay_type} 图表数据分析 高级表达 连接词 高分句型"
        knowledge = self.retrieve_writing_knowledge(
            query=knowledge_query,
            essay_type=essay_type,
            exam_category=exam_category,
            top_k=3
        )

        # 4. 常见错误比对
        diag_query = essay_text[:300] if len(essay_text) > 300 else essay_text
        errors = self.retrieve_common_errors(
            student_text_or_issue=diag_query,
            top_k=4
        )

        return {
            "exam_category": exam_category,
            "essay_type": essay_type,
            "topic": essay_topic,
            "scoring_criteria": criteria,
            "sample_essays": samples,
            "writing_knowledge": knowledge,
            "common_errors": errors
        }
