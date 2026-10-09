import os
import sys
import time
from pathlib import Path

# 将项目根目录添加到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 设置 Windows 控制台 UTF-8 输出编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rag.config import rag_config
from rag.embedder import OllamaEmbedder
from rag.milvus_manager import MilvusManager
from rag.vectorizer import KnowledgeVectorizer
from rag.retriever import KnowledgeRetriever


def run_tests():
    print("=" * 60)
    print("【考研英语二写作评分 RAG 模块集成测试】")
    print(f"嵌入模型: {rag_config.EMBEDDING_MODEL_NAME}")
    print(f"Ollama 地址: {rag_config.OLLAMA_BASE_URL}")
    print(f"Milvus 地址: {rag_config.MILVUS_URI}")
    print(f"Milvus 数据库: {rag_config.MILVUS_DB_NAME}")
    print(f"Milvus 集合: {rag_config.MILVUS_COLLECTION_NAME}")
    print("=" * 60)

    # 1. 向量化并写入 Milvus
    print("\n>>> 步骤 1: 执行知识库全量向量化与入库...")
    vectorizer = KnowledgeVectorizer()
    total_stored = vectorizer.vectorize_and_store(recreate_collection=True, batch_size=16)
    print(f"入库校验: 知识库共 {total_stored} 条数据已成功向量化并加载至 Milvus！")

    assert total_stored > 0, "知识库入库数量不能为0！"

    # 2. 初始化检索器
    print("\n>>> 步骤 2: 初始化检索器并执行多场景检索测试...")
    retriever = KnowledgeRetriever()

    # 测试场景 A：小作文建议信范文与标准检索
    print("\n--- [测试 A] 检索小作文建议信范文及高分要求 ---")
    query_a = "小作文 建议信 第一档 高分范文及语言亮点"
    results_a = retriever.retrieve_sample_essays(essay_type="小作文", sub_type="建议信", topic="中国传统节日", top_k=2)
    for i, r in enumerate(results_a, 1):
        print(f"  [{i}] 相似度得分: {r['score']:.4f} | 标题: {r['title']}")
        print(f"      模块: {r['module']} | 分类: {r['category']}")
        print(f"      内容摘要: {r['content'][:120]}...\n")

    # 测试场景 B：大作文图表写作词汇与句型检索
    print("--- [测试 B] 检索大作文柱状图数据变化与趋势描述表达 ---")
    query_b = "柱状图 呈现上升趋势 占比 显著增长 描述词汇"
    results_b = retriever.retrieve_writing_knowledge(query=query_b, essay_type="大作文", top_k=2)
    for i, r in enumerate(results_b, 1):
        print(f"  [{i}] 相似度得分: {r['score']:.4f} | 标题: {r['title']}")
        print(f"      内容摘要: {r['content'][:120]}...\n")

    # 测试场景 C：中式英语与语法错误模式检索
    print("--- [测试 C] 检索常见错误（针对学生写出 'more and more' 和 'China have'）---")
    query_c = "more and more people China have many festival"
    results_c = retriever.retrieve_common_errors(student_text_or_issue=query_c, top_k=2)
    for i, r in enumerate(results_c, 1):
        print(f"  [{i}] 相似度得分: {r['score']:.4f} | 标题: {r['title']}")
        print(f"      内容摘要: {r['content'][:120]}...\n")

    # 测试场景 D：评分上下文综合打包（给 Agent 评分调用的整体 Context）
    print("--- [测试 D] 模拟评分 Agent 获取学生作文全套 RAG 上下文 ---")
    student_essay = (
        "Dear Tom, I know you want to learn Chinese festival. I want to tell you about Spring Festival. "
        "Spring Festival is very important in China. We eat dumplings and watch TV show. "
        "Many people go home to see their parents. We also get red money from old people."
    )
    context_pack = retriever.retrieve_evaluation_context(
        essay_type="小作文",
        essay_topic="向外国朋友推荐一个中国传统节日",
        essay_text=student_essay
    )
    print("  [上下文打包结果验证]:")
    print(f"  - 评分标准 chunks: {len(context_pack['scoring_criteria'])} 条")
    print(f"  - 参考范文 chunks: {len(context_pack['sample_essays'])} 条")
    print(f"  - 推荐写作语料 chunks: {len(context_pack['writing_knowledge'])} 条")
    print(f"  - 命中错误诊断 chunks: {len(context_pack['common_errors'])} 条")

    print("\n" + "=" * 60)
    print("【全部 RAG 测试通过！Milvus 向量数据库与检索模块运行正常！】")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
