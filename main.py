import sys
import argparse
from pathlib import Path

# 设置 Windows 控制台 UTF-8 输出编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.evaluator import EssayEvaluator
from agent.report_generator import ReportGenerator
from agent.document_loader import DocumentLoader

def run_interactive(model: str = None, api_key: str = None, base_url: str = None, category: str = "英语二"):
    """交互式终端评卷模式"""
    print("=" * 65)
    print("🎓 考研英语写作（英语一 / 英语二）权威智能评卷系统 (RAG + 多模型支持)")
    print("=" * 65)

    print("\n请选择考试试卷类别：")
    print("  [1] 英语一 (Part A 应用文10分 / Part B 图画作文20分)")
    print("  [2] 英语二 (Part A 应用文10分 / Part B 图表作文15分)")
    cat_choice = input(f"请输入选项 [1/2，默认 2 为英语二]: ").strip()
    exam_category = "英语一" if cat_choice == "1" else "英语二"

    print(f"\n已选择【{exam_category}】。请选择作文题型：")
    print(f"  [1] 小作文 (Part A，应用文如书信、告示、通知，满分10分)")
    if exam_category == "英语一":
        print(f"  [2] 大作文 (Part B，图画作文 Cartoon Essay，满分20分)")
    else:
        print(f"  [2] 大作文 (Part B，图表作文 Chart Essay，满分15分)")
    print("  [3] 自动识别 (系统根据内容与词数自动研判)")
    choice = input("请输入选项 [1/2/3，默认3]: ").strip()

    essay_type_map = {"1": "小作文", "2": "大作文", "3": None}
    essay_type = essay_type_map.get(choice, None)

    topic = input("\n请输入作文题目或写作要求（可选，直接回车跳过）: ").strip()

    print("\n请输入考生作文正文（输入完成后在新起一行输入 EOF 并回车结束输入）：")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "EOF":
                break
            lines.append(line)
        except EOFError:
            break
    
    essay_text = "\n".join(lines).strip()
    if not essay_text:
        print("[错误] 未输入任何作文内容，退出评卷。")
        return

    print("\n" + "=" * 50)
    print(f"正在启动 RAG 检索并调用【{exam_category}】阅卷专家 Agent 进行深度评分，请稍候...")
    print("=" * 50)

    evaluator = EssayEvaluator(api_key=api_key, base_url=base_url, model_name=model)
    result = evaluator.evaluate(
        essay_text=essay_text,
        prompt_topic=topic,
        essay_type=essay_type,
        exam_category=exam_category
    )

    # 导出并打印报告
    saved_path = ReportGenerator.save_report(result)
    print("\n" + ReportGenerator.generate_markdown(result))
    print("\n" + "=" * 65)
    print(f"✅ 评卷完成！详细 Markdown 报告已保存至：\n{saved_path}")
    print("=" * 65)

def run_file(file_path: str, topic: str = "", essay_type: str = None, exam_category: str = "英语二", model: str = None, api_key: str = None, base_url: str = None):
    """从本地文档或图片读取作文并评卷（支持 txt, pdf, doc, docx, md, png, jpg, jpeg）"""
    path = Path(file_path)
    if not path.exists():
        print(f"[错误] 文件不存在: {file_path}")
        return

    print(f"\n[文档解析] 正在加载并识别文件: '{file_path}' ...")
    try:
        doc_res = DocumentLoader.load_document(path)
    except Exception as e:
        print(f"[错误] 文档识别失败: {e}")
        return

    essay_text = doc_res["text"].strip()
    if not essay_text:
        print("[错误] 未能从该文档中提取到有效文本内容。")
        return

    ocr_info = " (已启用 OCR 引擎识别)" if doc_res.get("ocr_used") else ""
    print(f"[文档解析成功] 格式: .{doc_res['format']} | 识别词数: {doc_res['word_count']} 词{ocr_info}")
    print("-" * 50)
    print("【解析出的作文前瞻预览】:")
    preview_lines = [l for l in essay_text.splitlines() if l.strip()][:5]
    for line in preview_lines:
        print(f"  > {line}")
    if len(preview_lines) < len([l for l in essay_text.splitlines() if l.strip()]):
        print("  > ... (后续内容已加载完成)")
    print("-" * 50)

    print(f"正在启动 RAG 检索并调用【{exam_category}】阅卷专家 Agent 进行深度评分，请稍候...")
    evaluator = EssayEvaluator(api_key=api_key, base_url=base_url, model_name=model)
    result = evaluator.evaluate(
        essay_text=essay_text,
        prompt_topic=topic,
        essay_type=essay_type,
        exam_category=exam_category
    )

    saved_path = ReportGenerator.save_report(result)
    print("\n" + ReportGenerator.generate_markdown(result))
    print(f"\n[提示] 详细评卷报告已保存至: {saved_path}")

def main():
    parser = argparse.ArgumentParser(description="考研英语写作（英语一 / 英语二）权威智能评分系统 (RAG + 多模型支持)")
    parser.add_argument("--file", "-f", type=str, help="从指定文件读取作文(支持 txt, pdf, doc, docx, md, png, jpg, jpeg)")
    parser.add_argument("--category", "-c", choices=["英语一", "英语二"], default="英语二", help="指定考研试卷类型（英语一 / 英语二，默认英语二）")
    parser.add_argument("--topic", "-t", type=str, default="", help="作文题目要求或背景")
    parser.add_argument("--type", choices=["小作文", "大作文"], default=None, help="指定作文类别")
    parser.add_argument("--model", "-m", type=str, default=None, help="指定大模型名称 (如 deepseek-chat, qwen-plus, glm-4-flash)")
    parser.add_argument("--api-key", type=str, default=None, help="自定义 API Key")
    parser.add_argument("--base-url", type=str, default=None, help="自定义 Base URL")
    parser.add_argument("--demo", action="store_true", help="直接运行真题典型案例对比评卷演示")

    args = parser.parse_args()

    if args.demo:
        from agent.run_evaluation import test_evaluation
        test_evaluation()
    elif args.file:
        run_file(args.file, topic=args.topic, essay_type=args.type, exam_category=args.category, model=args.model, api_key=args.api_key, base_url=args.base_url)
    else:
        run_interactive(model=args.model, api_key=args.api_key, base_url=args.base_url, category=args.category)

if __name__ == "__main__":
    main()
