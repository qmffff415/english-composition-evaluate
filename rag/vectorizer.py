import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.config import rag_config
from rag.embedder import OllamaEmbedder
from rag.milvus_manager import MilvusManager
from knowledge_base.kb_loader import build_knowledge_chunks

class KnowledgeVectorizer:
    """考研英语二写作知识库向量化流水线"""

    def __init__(self, embedder: OllamaEmbedder = None, milvus_mgr: MilvusManager = None):
        self.embedder = embedder or OllamaEmbedder()
        self.milvus_mgr = milvus_mgr or MilvusManager()

    def load_chunks(self) -> List[Dict[str, Any]]:
        """从 index.json 或直接构建获取知识库所有分块"""
        if rag_config.KB_INDEX_FILE.exists():
            print(f"[KnowledgeVectorizer] 正在从 {rag_config.KB_INDEX_FILE} 读取分块数据...")
            with open(rag_config.KB_INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                chunks = data.get("chunks", [])
        else:
            print("[KnowledgeVectorizer] 未找到 index.json，动态从原始知识库构建分块...")
            chunks = build_knowledge_chunks()

        print(f"[KnowledgeVectorizer] 共加载 {len(chunks)} 个知识分块")
        return chunks

    def vectorize_and_store(self, recreate_collection: bool = True, batch_size: int = 16) -> int:
        """执行知识库向量化并批量写入 Milvus"""
        chunks = self.load_chunks()
        if not chunks:
            print("[KnowledgeVectorizer] 警告: 没有需要向量化的分块数据！")
            return 0

        # 初始化 Milvus 集合
        self.milvus_mgr.init_collection(recreate=recreate_collection)

        # 准备分块文本进行向量生成（使用 title + content 提升语义匹配度）
        texts_to_embed = [
            f"{c.get('title', '')}\n{c.get('content', '')}"
            for c in chunks
        ]

        print(f"[KnowledgeVectorizer] 开始通过 Ollama ({self.embedder.model_name}) 批量生成嵌入向量...")
        start_time = time.time()
        embeddings = self.embedder.embed_documents(texts_to_embed, batch_size=batch_size)
        elapsed = time.time() - start_time
        print(f"[KnowledgeVectorizer] 向量生成完毕，共 {len(embeddings)} 条向量，耗时 {elapsed:.2f} 秒")

        # 组装 Milvus 实体
        entities = []
        for chunk, emb in zip(chunks, embeddings):
            entities.append({
                "id": str(chunk.get("id"))[:200],
                "vector": emb,
                "exam_category": str(chunk.get("exam_category", "通用")),
                "module": str(chunk.get("module", "")),
                "essay_type": str(chunk.get("essay_type", "")),
                "category": str(chunk.get("category", "")),
                "title": str(chunk.get("title", "")),
                "content": str(chunk.get("content", "")),
                "metadata": chunk.get("metadata", {})
            })

        print(f"[KnowledgeVectorizer] 正在向 Milvus 集合 '{self.milvus_mgr.collection_name}' 批量插入数据...")
        inserted = self.milvus_mgr.insert_entities(entities)
        print(f"[KnowledgeVectorizer] 数据写入完成，实际写入实体数: {inserted}")

        # 校验数量
        total_in_db = self.milvus_mgr.count()
        print(f"[KnowledgeVectorizer] Milvus 集合当前总实体数: {total_in_db}")

        return total_in_db

if __name__ == "__main__":
    vectorizer = KnowledgeVectorizer()
    vectorizer.vectorize_and_store(recreate_collection=True)
