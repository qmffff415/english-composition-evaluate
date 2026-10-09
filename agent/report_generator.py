import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from agent.config import agent_config

class ReportGenerator:
    """评分报告生成器：将结构化评分结果转化为排版精美的 Markdown 报告（支持英语一与英语二）"""

    @staticmethod
    def generate_markdown(result: Dict[str, Any]) -> str:
        meta = result.get("meta", {})
        exam_category = result.get("exam_category") or meta.get("exam_category", "英语二")
        essay_type = result.get("essay_type") or meta.get("essay_type", "小作文")
        sub_type = result.get("sub_type") or meta.get("sub_type", "通用")
        word_count = result.get("word_count") or meta.get("word_count", 0)

        default_max = 10 if essay_type == "小作文" else (20 if exam_category == "英语一" else 15)
        max_score = result.get("max_score") or default_max
        total_score = result.get("total_score", 0.0)
        band = result.get("band", "未定档")

        # 得分进度条渲染
        pct = (total_score / max_score) * 100 if max_score > 0 else 0
        bar_len = 20
        filled = int((pct / 100) * bar_len)
        score_bar = "█" * filled + "░" * (bar_len - filled)

        is_letter = meta.get("is_letter", False) or essay_type == "小作文"
        body_p_count = meta.get("body_paragraph_count") or meta.get("paragraph_count", 0)
        body_w_count = meta.get("body_word_count", word_count)

        if is_letter and (meta.get("salutation") or meta.get("sign_off") or meta.get("signature")):
            para_desc = f"正文 {body_p_count} 段（规范书信结构：含独立称呼与落款）"
        else:
            para_desc = f"{body_p_count} 段"

        if is_letter and body_w_count and body_w_count != word_count:
            word_desc = f"**{word_count} 词**（正文 {body_w_count} 词，标点不计）"
        else:
            word_desc = f"**{word_count} 词**（标点不计）"

        lines = [
            f"# 🎓 考研{exam_category}写作权威智能评卷报告",
            f"",
            f"> **评卷系统**：考研{exam_category} RAG 权威评分专家系统 | **模型**：`{meta.get('model_name', 'DeepSeek-V3')}` | **耗时**：{meta.get('latency_seconds', 0)}s",
            f"",
            f"---",
            f"",
            f"## 一、 评卷总览",
            f"",
            f"| 评卷指标 | 评定结果 | 详细参数 |",
            f"| :--- | :--- | :--- |",
            f"| **考试试卷** | **{exam_category}** | 目标题型：{meta.get('prompt_topic', '常规命题')} |",
            f"| **作文类型** | **{essay_type}**（{sub_type}） | 篇章段落：{para_desc} |",
            f"| **实测词数** | {word_desc} | 规范区间：{'约100词（标点不计）' if essay_type == '小作文' else ('160-200词' if exam_category == '英语一' else '不少于150词')} |",
            f"| **总分评定** | <font size='5' color='#d9534f'>**{total_score}**</font> / {max_score} 分 | 百分比：`{pct:.1f}%` `[{score_bar}]` |",
            f"| **官方大纲档次** | <font color='#0275d8'>**{band}**</font> | 评级状态：规范完成 |",
            f"",
            f"### 📋 阅卷组长综合评语",
            f"> {result.get('summary_comment', '无综合评语')}",
            f"",
            f"---",
            f"",
            f"## 二、 四大核心维度量化评分",
            f"",
            f"| 评价维度 | 满分 | 实得分 | 得分率 | 维度评定原因 |",
            f"| :--- | :---: | :---: | :---: | :--- |"
        ]

        dims = result.get("dimensions", {})
        for dim_key, dim_info in dims.items():
            name = dim_info.get("name", dim_key)
            s = dim_info.get("score", 0.0)
            ms = dim_info.get("max_score", 1.0)
            r = (s / ms * 100) if ms > 0 else 0
            reason = dim_info.get("score_reason", dim_info.get("analysis", ""))
            lines.append(f"| **{name}** | {ms} | **{s}** | {r:.0f}% | {reason} |")

        lines.extend([
            f"",
            f"### 各维度深入分析：",
        ])
        for dim_key, dim_info in dims.items():
            lines.append(f"- **{dim_info.get('name', dim_key)}**：{dim_info.get('analysis', '')}")

        # 扣分明细
        deductions = result.get("deductions", [])
        if deductions:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 三、 扣分规则明细",
                f"",
                f"| 扣分项目 | 扣分分值 | 考试大纲扣分依据 |",
                f"| :--- | :---: | :--- |"
            ])
            for d in deductions:
                pts = abs(float(d.get('points', 0.0)))
                lines.append(f"| {d.get('item', '扣分项')} | <font color='red'>-{pts} 分</font> | {d.get('rule', '大纲规范')} |")

        # 亮点表达
        highlights = result.get("highlights", [])
        if highlights:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 四、 🌟 亮点表达与得分点",
                f""
            ])
            for h in highlights:
                lines.append(f"- ✨ **`{h.get('quote', '')}`**：{h.get('praise', '')}")

        # 语病诊断与修改
        errors = result.get("error_diagnostics", [])
        lines.extend([
            f"",
            f"---",
            f"",
            f"## 五、 🔍 语言与语法精细化诊断（逐句改错）",
            f"",
            f"| 原文错误片段 | 错误类型 | 权威机理解析 | 建议纯正修改 |",
            f"| :--- | :--- | :--- | :--- |"
        ])
        if errors:
            for err in errors:
                lines.append(f"| `{err.get('original_text', '')}` | <font color='#d9534f'>{err.get('error_type', '语病')}</font> | {err.get('explanation', '')} | **`{err.get('correction', '')}`** |")
        else:
            lines.append(f"| 全文无重大语法语病 | 语言优良 | 句子结构规范地道 | 保持当前写作水准 |")

        # 升格范文
        polished = result.get("polished_essay", "")
        if polished:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 六、 🚀 高分升格示范范文（大纲第五档卓越水准 · 保留原思路润色）",
                f"",
                f"```text",
                f"{polished.strip()}",
                f"```"
            ])

        # 备考提升建议
        suggestions = result.get("study_suggestions", [])
        if suggestions:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 七、 💡 阅卷组长给考生的提分建议",
                f""
            ])
            for i, sug in enumerate(suggestions, 1):
                lines.append(f"{i}. **{sug}**")

        lines.extend([
            f"",
            f"---",
            f"*本报告由基于 RAG 知识库与 DeepSeek 大模型的考研{exam_category}智能评卷系统生成*"
        ])

        return "\n".join(lines)

    @classmethod
    def save_report(cls, result: Dict[str, Any], output_dir: Optional[Path] = None, user_id: Optional[int] = None) -> Path:
        """将生成的报告保存为本地 Markdown 文件"""
        out_dir = output_dir or agent_config.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        meta = result.get("meta", {})
        exam_category = result.get("exam_category") or meta.get("exam_category", "英语二")
        essay_type = result.get("essay_type") or meta.get("essay_type", "小作文")
        score = result.get("total_score", 0.0)
        filename = f"report_{exam_category}_{essay_type}_{score}pts_{timestamp}.md"
        filepath = out_dir / filename

        md_content = cls.generate_markdown(result)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"[ReportGenerator] 评卷报告已成功保存至: {filepath}")
        return filepath
