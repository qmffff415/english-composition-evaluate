import os
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录下的 .env 文件
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)

class RAGConfig:
    # 嵌入向量模型配置（Ollama）
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "bge-m3:latest")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Milvus 向量数据库配置
    MILVUS_URI: str = os.getenv("MILVUS_URI", "http://localhost:19530")
    MILVUS_DB_NAME: str = os.getenv("MILVUS_DB_NAME", "EnglishTwoEvaluate")
    MILVUS_COLLECTION_NAME: str = os.getenv("MILVUS_COLLECTION_NAME", "kaoyan_english_kb")

    # 向量维度与相似度度量（bge-m3 dense 维度为 1024）
    VECTOR_DIM: int = 1024
    METRIC_TYPE: str = "COSINE"

    # 路径配置
    KB_DIR: Path = PROJECT_ROOT / "knowledge_base"
    KB_INDEX_FILE: Path = KB_DIR / "index.json"

rag_config = RAGConfig()
