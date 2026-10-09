import os
import sys
import json
import time
from pathlib import Path

# 设置 Windows 控制台 UTF-8 输出编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

from agent.evaluator import EssayEvaluator
from agent.report_generator import ReportGenerator
from agent.document_loader import DocumentLoader
from agent.llm_provider import LLM_PRESETS, test_llm_connection
from agent.config import agent_config
from rag.config import rag_config
from rag.milvus_manager import MilvusManager

app = Flask(__name__, static_folder=str(DIST_DIR), static_url_path="")
CORS(app)

# 初始化评估器实例（延迟或全局复用）
evaluator = None

def get_evaluator():
    global evaluator
    if evaluator is None:
        evaluator = EssayEvaluator()
    return evaluator

_status_cache = {
    "last_time": 0,
    "data": None
}

def probe_milvus_online() -> bool:
    """使用轻量 Socket 快速探活（超时 0.04 秒），杜绝沉重的 pymilvus 握手阻塞 2.5 秒"""
    import socket
    try:
        uri = rag_config.MILVUS_URI.replace("http://", "").replace("https://", "").strip("/")
        if ":" in uri:
            host, port_str = uri.split(":", 1)
            port = int(port_str.split("/")[0])
        else:
            host, port = uri, 19530
        if host in ("localhost", "127.0.0.1"):
            host = "127.0.0.1"
        sock = socket.create_connection((host, port), timeout=0.04)
        sock.close()
        return True
    except Exception:
        return False

@app.route("/api/status", methods=["GET"])
def get_status():
    """获取系统状态：带毫秒级极速探活与 60 秒内存缓存，彻底杜绝服务器阻塞卡死"""
    now = time.time()
    if _status_cache["data"] and (now - _status_cache["last_time"] < 60):
        return jsonify(_status_cache["data"])

    if probe_milvus_online():
        try:
            mgr = MilvusManager()
            count = mgr.count()
            res_data = {
                "status": "online",
                "milvus": {
                    "connected": True,
                    "db_name": rag_config.MILVUS_DB_NAME,
                    "collection": rag_config.MILVUS_COLLECTION_NAME,
                    "chunks_count": count
                },
                "models": {
                    "embedding": rag_config.EMBEDDING_MODEL_NAME,
                    "llm": "deepseek-chat",
                    "base_url": "https://api.deepseek.com"
                }
            }
        except Exception as e:
            res_data = {
                "status": "warning",
                "milvus": {"connected": False, "error": str(e)},
                "models": {
                    "embedding": rag_config.EMBEDDING_MODEL_NAME,
                    "llm": "deepseek-chat",
                    "base_url": "https://api.deepseek.com"
                }
            }
    else:
        res_data = {
            "status": "warning",
            "milvus": {
                "connected": False,
                "db_name": rag_config.MILVUS_DB_NAME,
                "collection": rag_config.MILVUS_COLLECTION_NAME,
                "chunks_count": 0
            },
            "models": {
                "embedding": rag_config.EMBEDDING_MODEL_NAME,
                "llm": "deepseek-chat",
                "base_url": "https://api.deepseek.com"
            },
            "message": "Milvus 服务未就绪"
        }

    _status_cache["last_time"] = now
    _status_cache["data"] = res_data
    return jsonify(res_data)

@app.route("/api/llm/presets", methods=["GET"])
def get_llm_presets():
    """获取大模型服务商预设列表（保护私有 .env，不泄露也不默认提供系统 key）"""
    return jsonify({
        "presets": LLM_PRESETS
    })

@app.route("/api/llm/test", methods=["POST"])
def test_llm():
    """测试指定大模型连接状态"""
    data = request.json or {}
    api_key = data.get("api_key")
    base_url = data.get("base_url")
    model_name = data.get("model_name")

    res = test_llm_connection(api_key=api_key, base_url=base_url, model_name=model_name)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

@app.route("/api/topics", methods=["GET"])
def get_topics():
    """获取预置的历年真题题目列表，供前端一键选取（支持英语一与英语二）"""
    exam_category = request.args.get("exam_category", "英语二").strip()
    if exam_category == "英语一":
        topics_file = PROJECT_ROOT / "knowledge_base" / "question_templates" / "english_one_past_exam_topics.json"
    else:
        topics_file = PROJECT_ROOT / "knowledge_base" / "question_templates" / "past_exam_topics.json"

    if topics_file.exists():
        with open(topics_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return jsonify(data.get("data", {}))
    return jsonify({"small_essays": [], "big_essays": []})

@app.route("/api/upload", methods=["POST"])
def upload_document():
    """上传作文文件并提取识别文本（支持 txt, pdf, doc, docx, md, png, jpg, jpeg）"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未提供上传文件"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "文件名不能为空"}), 400

    try:
        content_bytes = file.read()
        res = DocumentLoader.load_document(content_bytes, filename=file.filename)
        return jsonify({
            "success": True,
            **res
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"文档解析失败: {str(e)}"}), 500

@app.route("/api/evaluate", methods=["POST"])
def evaluate_essay():
    """执行作文评分（支持英语一与英语二，支持自定义大模型 api_key, base_url, model_name）"""
    data = request.json or {}
    essay_text = data.get("essay_text", "").strip()
    prompt_topic = data.get("prompt_topic", "").strip()
    essay_type = data.get("essay_type", None)
    exam_category = data.get("exam_category", "英语二").strip()
    llm_config = data.get("llm_config") or {}

    if not essay_text:
        return jsonify({"error": "作文内容不能为空"}), 400

    try:
        api_key = (llm_config.get("api_key") or "").strip()
        base_url = (llm_config.get("base_url") or "").strip() or "https://api.deepseek.com"
        model_name = (llm_config.get("model_name") or "").strip() or "deepseek-chat"

        # 保护 .env 私人财产：严禁 Web 评卷请求默认借用或回退到服务端的 .env 私有密钥
        if not api_key and "localhost" not in base_url and "127.0.0.1" not in base_url:
            return jsonify({
                "error": "未提供 API Key！.env 属于系统私有配置，禁止默认借用。请在【评卷模型】设置中填入您自己的专属 API Key 后再开始智能评卷。"
            }), 400

        # 实例化评卷器（明确禁用 allow_env_fallback）
        ev = EssayEvaluator(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            allow_env_fallback=False
        )

        result = ev.evaluate(
            essay_text=essay_text,
            prompt_topic=prompt_topic,
            essay_type=essay_type,
            exam_category=exam_category
        )
        if not result or result.get("total_score") is None:
            raise ValueError("评卷大模型未能生成合规的结构化评分结果，请检查模型运行状态或重试。")

        # 保存 Markdown 报告
        report_path = ReportGenerator.save_report(result)
        result["report_filename"] = report_path.name
        result["markdown_report"] = ReportGenerator.generate_markdown(result)

        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"评卷失败: {str(e)}"}), 500

@app.route("/api/essay-library", methods=["GET"])
def get_essay_library():
    """获取往年英语一/英语二作文真题与高分标杆范文库，支持考试类别、年份、题型和关键词过滤"""
    lib_file = PROJECT_ROOT / "knowledge_base" / "sample_essays" / "past_exam_essays_library.json"
    if not lib_file.exists():
        return jsonify({"success": False, "error": "真题范文库数据未找到", "data": []}), 404

    try:
        with open(lib_file, "r", encoding="utf-8") as f:
            essays = json.load(f)

        exam_cat_param = request.args.get("exam_category")
        year_param = request.args.get("year")
        type_param = request.args.get("type")
        query_param = (request.args.get("query") or "").strip().lower()

        filtered = essays
        if exam_cat_param and exam_cat_param != "全部":
            filtered = [e for e in filtered if e.get("exam_category") == exam_cat_param]

        if year_param:
            try:
                y = int(year_param)
                filtered = [e for e in filtered if e.get("year") == y]
            except ValueError:
                pass

        if type_param and type_param != "全部":
            filtered = [e for e in filtered if e.get("type") == type_param]

        if query_param:
            filtered = [
                e for e in filtered
                if query_param in str(e.get("year"))
                or query_param in (e.get("exam_category") or "").lower()
                or query_param in (e.get("title") or "").lower()
                or query_param in (e.get("sub_type") or "").lower()
                or query_param in (e.get("prompt_cn") or "").lower()
                or query_param in (e.get("prompt_en") or "").lower()
                or query_param in (e.get("sample_essay") or "").lower()
            ]

        available_years = sorted(list(set(e.get("year") for e in essays if "year" in e)), reverse=True)
        available_types = ["全部", "小作文", "大作文"]
        available_exam_cats = ["全部", "英语一", "英语二"]

        return jsonify({
            "success": True,
            "total": len(filtered),
            "years": available_years,
            "types": available_types,
            "exam_categories": available_exam_cats,
            "data": filtered
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"读取真题范文库失败: {str(e)}"}), 500

@app.route("/api/reports", methods=["GET"])
def get_history_reports():
    """获取历史评卷报告列表"""
    reports_dir = PROJECT_ROOT / "evaluation_reports"
    reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            reports.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "mtime": f.stat().st_mtime
            })
    return jsonify(reports[:30])

@app.route("/api/report/<filename>", methods=["GET"])
def get_report_content(filename):
    """读取单篇报告内容"""
    # 安全校验：防止跨目录遍历
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"error": "非法文件名"}), 400

    reports_dir = PROJECT_ROOT / "evaluation_reports"
    target_files = list(reports_dir.rglob(filename))
    if target_files and target_files[0].is_file():
        with open(target_files[0], "r", encoding="utf-8") as f:
            return jsonify({"filename": filename, "content": f.read()})

    return jsonify({"error": "文件不存在"}), 404

# 静态前端页面托管路由
@app.route("/")
def index():
    if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
        return send_from_directory(str(DIST_DIR), "index.html")
    return jsonify({"message": "前端应用尚未编译，请在 frontend 目录执行 npm run build"})

@app.route("/<path:path>")
def static_proxy(path):
    if DIST_DIR.exists() and (DIST_DIR / path).exists():
        return send_from_directory(str(DIST_DIR), path)
    if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
        return send_from_directory(str(DIST_DIR), "index.html")
    return jsonify({"error": "资源未找到"}), 404

if __name__ == "__main__":
    print("=" * 65)
    print("[Web Server] 考研英语写作（英语一 / 英语二）智能评卷系统 Web 服务启动中...")
    print("浏览器访问地址: http://127.0.0.1:5000")
    print("=" * 65)

    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
