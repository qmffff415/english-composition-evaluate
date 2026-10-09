import requests
import time
from typing import List
from rag.config import rag_config

class OllamaEmbedder:
    """基于 Ollama 的嵌入向量生成器 (适配 bge-m3 等模型)"""

    def __init__(self, base_url: str = None, model_name: str = None):
        self.base_url = (base_url or rag_config.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or rag_config.EMBEDDING_MODEL_NAME
        self.embed_url = f"{self.base_url}/api/embed"
        self.legacy_embed_url = f"{self.base_url}/api/embeddings"
        self._verify_connection()

    def _verify_connection(self):
        """检查 Ollama 服务连通性及模型可用性"""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if res.status_code == 200:
                models = [m.get("name") for m in res.json().get("models", [])]
                if self.model_name not in models:
                    # 匹配标签如 bge-m3 vs bge-m3:latest
                    prefix_match = any(m.startswith(self.model_name.split(":")[0]) for m in models)
                    if not prefix_match:
                        print(f"[警告] Ollama 服务中未直接找到模型 '{self.model_name}', 当前已加载模型: {models}")
                print(f"[OllamaEmbedder] 成功连接至 Ollama: {self.base_url}, 使用嵌入模型: {self.model_name}")
            else:
                print(f"[OllamaEmbedder] 警告: 获取 Ollama tags 失败: {res.status_code}")
        except Exception as e:
            raise ConnectionError(f"无法连接到 Ollama 服务 ({self.base_url}): {e}")

    def embed_query(self, text: str) -> List[float]:
        """为单条检索查询生成向量"""
        if not text or not text.strip():
            return [0.0] * rag_config.VECTOR_DIM
        embeddings = self.embed_documents([text.strip()], batch_size=1)
        return embeddings[0]

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """批量为文本列表生成向量，支持分批次与重试机制"""
        all_embeddings: List[List[float]] = []
        total = len(texts)

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            # 过滤空文本
            cleaned_batch = [t if (t and t.strip()) else "empty" for t in batch]
            
            embeddings = self._embed_batch_with_retry(cleaned_batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _embed_batch_with_retry(self, batch: List[str], max_retries: int = 3) -> List[List[float]]:
        """尝试使用 /api/embed 批量接口，若不支持则降级为逐条请求"""
        for attempt in range(max_retries):
            try:
                # 尝试 Ollama 0.1.30+ 原生批量 /api/embed 接口
                payload = {
                    "model": self.model_name,
                    "input": batch
                }
                res = requests.post(self.embed_url, json=payload, timeout=60)
                if res.status_code == 200:
                    data = res.json()
                    embs = data.get("embeddings")
                    if embs and len(embs) == len(batch):
                        return embs
                
                # 若 /api/embed 不可用或格式异常，尝试单条 /api/embeddings 接口
                single_embs = []
                for text in batch:
                    single_res = requests.post(
                        self.legacy_embed_url,
                        json={"model": self.model_name, "prompt": text},
                        timeout=30
                    )
                    if single_res.status_code == 200:
                        single_embs.append(single_res.json().get("embedding", []))
                    else:
                        raise RuntimeError(f"Ollama legacy embedding failed: {single_res.status_code} {single_res.text}")
                return single_embs

            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"生成向量失败（已重试 {max_retries} 次）: {e}")
                time.sleep(1.0 * (attempt + 1))

        return []
