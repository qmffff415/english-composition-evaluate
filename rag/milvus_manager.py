from typing import List, Dict, Any, Optional
from pymilvus import MilvusClient, DataType
from rag.config import rag_config

class MilvusManager:
    """Milvus 向量数据库生命周期管理与集合维护"""

    def __init__(self, uri: str = None, db_name: str = None, collection_name: str = None):
        self.uri = uri or rag_config.MILVUS_URI
        self.db_name = db_name or rag_config.MILVUS_DB_NAME
        self.collection_name = collection_name or rag_config.MILVUS_COLLECTION_NAME
        self._ensure_database()
        self.client = MilvusClient(uri=self.uri, db_name=self.db_name)

    def _ensure_database(self):
        """确保目标数据库 EnglishTwoEvaluate 存在，若不存在则创建"""
        root_client = MilvusClient(uri=self.uri)
        existing_dbs = root_client.list_databases()
        if self.db_name not in existing_dbs:
            root_client.create_database(self.db_name)
            print(f"[MilvusManager] 成功创建数据库 '{self.db_name}'")
        else:
            print(f"[MilvusManager] 数据库 '{self.db_name}' 已存在")

    def init_collection(self, recreate: bool = False):
        """初始化知识库集合，支持按需重新创建"""
        if self.client.has_collection(self.collection_name):
            if recreate:
                print(f"[MilvusManager] 正在删除旧集合 '{self.collection_name}'...")
                self.client.drop_collection(self.collection_name)
            else:
                print(f"[MilvusManager] 集合 '{self.collection_name}' 已存在，准备复用")
                return

        # 定义 Schema
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=256, is_primary=True)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=rag_config.VECTOR_DIM)
        schema.add_field(field_name="module", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="essay_type", datatype=DataType.VARCHAR, max_length=32)
        schema.add_field(field_name="category", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=8192)
        schema.add_field(field_name="metadata", datatype=DataType.JSON)

        # 定义索引参数（使用 COSINE 距离度量）
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            metric_type=rag_config.METRIC_TYPE,
            index_type="AUTOINDEX"
        )

        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params
        )
        print(f"[MilvusManager] 成功创建集合 '{self.collection_name}' 并建立 COSINE 索引")

    def insert_entities(self, entities: List[Dict[str, Any]]) -> int:
        """批量插入实体数据并刷新持久化与加载内存"""
        if not entities:
            return 0
        res = self.client.insert(
            collection_name=self.collection_name,
            data=entities
        )
        # 刷新数据持久化并加载到内存中供检索
        self.client.flush(self.collection_name)
        self.client.load_collection(self.collection_name)
        insert_count = res.get("insert_count", len(entities)) if isinstance(res, dict) else len(entities)
        return insert_count

    def count(self) -> int:
        """获取当前集合中的实体总数"""
        if not self.client.has_collection(self.collection_name):
            return 0
        stats = self.client.get_collection_stats(self.collection_name)
        return stats.get("row_count", 0)

    def search(
        self,
        query_vector: List[float],
        filter_expr: Optional[str] = None,
        top_k: int = 5,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """在集合中执行向量相似度检索"""
        if output_fields is None:
            output_fields = ["id", "module", "essay_type", "category", "title", "content", "metadata"]

        search_params = {
            "metric_type": rag_config.METRIC_TYPE,
            "params": {"radius": -1.0}
        }

        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            filter=filter_expr or "",
            limit=top_k,
            output_fields=output_fields,
            search_params=search_params
        )

        flat_results = []
        if results and len(results) > 0:
            for hit in results[0]:
                entity = hit.get("entity", {})
                flat_results.append({
                    "id": hit.get("id"),
                    "score": hit.get("distance"),
                    "module": entity.get("module"),
                    "essay_type": entity.get("essay_type"),
                    "category": entity.get("category"),
                    "title": entity.get("title"),
                    "content": entity.get("content"),
                    "metadata": entity.get("metadata")
                })
        return flat_results
