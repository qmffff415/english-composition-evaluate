import os
import sys
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

from agent.evaluator import EssayEvaluator
from agent.report_generator import ReportGenerator

def test_evaluation():
    print("=" * 70)
    print("【考研英语二评分 Agent 核心功能评卷演示】")
    print("=" * 70)

    evaluator = EssayEvaluator()

    # ----------------------------------------------------
    # 测试案例 1：小作文（Part A 建议信典型考生作答）
    # ----------------------------------------------------
    small_essay_topic = "外国友人想了解中国传统节日，请写一封建议信推荐一个节日并说明理由。"
    small_essay_student_text = """Dear Tom,

    I know you want to learn Chinese festival. I want to tell you about Spring Festival. It is very important festival in China.

    During this festival, all families get together and have a big dinner. We eat dumplings and watch TV show. Children can get red money from old people, which makes them very happy. Furthermore, there have many interesting activities, like firework and dragon dance.

    I hope you can come China to enjoy Spring Festival. Welcome to China!

Yours sincerely,
Li Ming"""

    print("\n" + "=" * 50)
    print("【评卷任务 1】小作文（建议信，满分10分）")
    print("--------------------------------------------------")
    print("考生作文：\n" + small_essay_student_text)
    print("--------------------------------------------------")

    result_small = evaluator.evaluate(
        essay_text=small_essay_student_text,
        prompt_topic=small_essay_topic,
        essay_type="小作文"
    )

    report_path_small = ReportGenerator.save_report(result_small)
    print("\n" + ReportGenerator.generate_markdown(result_small))

    # ----------------------------------------------------
    # 测试案例 2：大作文（Part B 柱状图典型考生作答）
    # ----------------------------------------------------
    big_essay_topic = "柱状图：大学生毕业去向规划调查（考研占48.5%，就业占32.2%，出国占12.1%，创业占7.2%）。"
    big_essay_student_text = """The bar chart show the choices of university graduates in a Chinese college. According to the data, 48.5% of students choose to take the postgraduate entrance exam, which is the biggest part. Meanwhile, 32.2% students choose to find a job directly. In addition, studying abroad and starting business take up 12.1% and 7.2% respectively.

There are several reasons for this phenomenon. First, because the job market is very competitive now, so many students think higher degree can help them get better job and high salary. Second, university encourage students to study more. Third, some students don't want to face the society too early, so they continue to study in school.

In conclusion, more and more students choose to take postgraduate exam. I think students should make choice based on their own situation."""

    print("\n" + "=" * 50)
    print("【评卷任务 2】大作文（柱状图，满分15分）")
    print("--------------------------------------------------")
    print("考生作文：\n" + big_essay_student_text)
    print("--------------------------------------------------")

    result_big = evaluator.evaluate(
        essay_text=big_essay_student_text,
        prompt_topic=big_essay_topic,
        essay_type="大作文"
    )

    report_path_big = ReportGenerator.save_report(result_big)
    print("\n" + ReportGenerator.generate_markdown(result_big))

    print("\n" + "=" * 70)
    print(f"【两篇作文评卷成功完成！】报告已分别保存至：\n- {report_path_small}\n- {report_path_big}")
    print("=" * 70)

if __name__ == "__main__":
    test_evaluation()
