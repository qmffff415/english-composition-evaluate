import re
from typing import Dict, Any, List, Optional

class EssayPreprocessor:
    """作文预处理器：词数统计、篇章结构分析、题型自动识别与大纲规则预检（支持英语一与英语二）"""

    @staticmethod
    def count_words(text: str) -> int:
        """精准统计英文单词数（严格遵循考研大纲规范：标点符号不计算在内，连字符与缩写计为一个词）"""
        if not text:
            return 0
        words = re.findall(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b", text)
        return len(words)

    @staticmethod
    def split_paragraphs(text: str) -> List[str]:
        """切分有效段落（剔除纯空白段）"""
        paragraphs = [p.strip() for p in text.strip().split("\n") if p.strip()]
        return paragraphs

    @classmethod
    def parse_essay_structure(cls, text: str, essay_type: str = "小作文") -> Dict[str, Any]:
        """
        智能解析作文篇章结构。
        对于小作文（书信/告示/通知/备忘录等），严格将：
        - 开头称呼（如 Dear ..., To whom it may concern 等）
        - 结尾落款（如 Yours sincerely, 和 Li Ming 等）
        作为应用文独立格式要素剥离，绝不计入正文段落！
        返回正文段落列表、正文段落数、以及区分全篇与正文的真实单词统计。
        """
        if not text or not text.strip():
            return {
                "body_paragraphs": [],
                "body_paragraph_count": 0,
                "raw_paragraph_count": 0,
                "is_letter": False,
                "salutation": None,
                "sign_off": None,
                "signature": None,
                "body_word_count": 0,
                "total_word_count": 0
            }

        total_words = cls.count_words(text)
        raw_blocks = [p.strip() for p in text.strip().split("\n") if p.strip()]

        if essay_type != "小作文":
            return {
                "body_paragraphs": raw_blocks,
                "body_paragraph_count": len(raw_blocks),
                "raw_paragraph_count": len(raw_blocks),
                "is_letter": False,
                "salutation": None,
                "sign_off": None,
                "signature": None,
                "body_word_count": total_words,
                "total_word_count": total_words
            }

        lines = raw_blocks[:]
        salutation = None
        sign_off = None
        signature = None

        # 1. 识别称呼或公文标题
        if lines:
            first_line = lines[0]
            salutation_pattern = re.compile(r"^(dear\b|to\s+whom|to:\s*|hello\b|hi\b)", re.IGNORECASE)
            if salutation_pattern.match(first_line) or (len(first_line.split()) <= 6 and first_line.endswith((",", ":"))):
                salutation = lines.pop(0)
            elif first_line.upper() in ["NOTICE", "ANNOUNCEMENT", "MEMO", "MEMORANDUM"]:
                salutation = lines.pop(0)

        # 2. 识别结尾敬辞与落款署名
        sign_off_pattern = re.compile(
            r"^(yours\s+(sincerely|faithfully|truly|affectionately|warmly|respectfully|cordially)|sincerely\s+yours|sincerely|best\s+regards|warm\s+regards|with\s+(best|warm|kind)\s+wishes|yours)[,\.]?$",
            re.IGNORECASE
        )
        combined_close_sig = re.compile(
            r"^(yours\s+(?:sincerely|faithfully|truly|respectfully)|sincerely\s+yours|sincerely)[,\s]+(li\s*ming|[\w\s]+)$",
            re.IGNORECASE
        )

        if len(lines) >= 1 and combined_close_sig.match(lines[-1]):
            m = combined_close_sig.match(lines[-1])
            sign_off = m.group(1)
            signature = m.group(2)
            lines.pop(-1)
        elif len(lines) >= 2 and sign_off_pattern.match(lines[-2]):
            signature = lines.pop(-1)
            sign_off = lines.pop(-1)
        elif len(lines) >= 1 and sign_off_pattern.match(lines[-1]):
            sign_off = lines.pop(-1)
        elif len(lines) >= 1 and len(lines[-1].split()) <= 4:
            last_lower = lines[-1].lower()
            if any(k in last_lower for k in ["li ming", "liming", "union", "association", "committee", "secretary", "organizer"]):
                signature = lines.pop(-1)

        body_paragraphs = lines
        body_text = "\n".join(body_paragraphs)
        body_words = cls.count_words(body_text)

        return {
            "body_paragraphs": body_paragraphs,
            "body_paragraph_count": len(body_paragraphs),
            "raw_paragraph_count": len(raw_blocks),
            "salutation": salutation,
            "sign_off": sign_off,
            "signature": signature,
            "is_letter": bool(salutation or sign_off or signature),
            "body_word_count": body_words,
            "total_word_count": total_words
        }

    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """简易切分英语句子"""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def detect_essay_type(
        cls,
        text: str,
        prompt_topic: str = "",
        exam_category: str = "英语二",
        forced_essay_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        根据作文文本或题目识别题型（小作文 Part A vs 大作文 Part B 及对应细分子类型）
        若外部显式传入 forced_essay_type，则直接尊重大类，仅研判细分子类型。
        """
        combined = (prompt_topic + " " + text).lower()
        word_count = cls.count_words(text)

        if forced_essay_type in ["小作文", "大作文"]:
            essay_type = forced_essay_type
        else:
            # 1. 信号词权重评分
            small_signals = [
                "dear", "sincerely", "faithfully", "notice", "announcement", "memo", "memorandum",
                "li ming", "proposal", "建议信", "书信", "通知", "告示", "备忘录", "倡议书", "推荐信",
                "邀请信", "感谢信", "道歉信", "投诉信"
            ]

            if exam_category == "英语一":
                big_signals = [
                    "cartoon", "drawing", "picture", "illustration", "caricature", "caption",
                    "metaphorical", "symbolic", "portray", "delineate", "depict", "perseverance",
                    "hotpot", "gathering", "climber", "graph", "chart", "table", "图画", "漫画",
                    "插图", "寓意", "象征", "哲理", "低头族", "文化火锅", "坚持", "柱状图", "表格"
                ]
                length_threshold = 145
            else:
                big_signals = [
                    "chart", "graph", "table", "diagram", "bar", "column", "pie", "percentage",
                    "proportion", "increase", "decrease", "图表", "柱状图", "饼图", "折线图", "表格"
                ]
                length_threshold = 135

            small_score = sum(1 for s in small_signals if s in combined)
            big_score = sum(1 for b in big_signals if b in combined)

            if big_score > small_score:
                essay_type = "大作文"
            elif small_score > big_score:
                essay_type = "小作文"
            else:
                essay_type = "大作文" if word_count > length_threshold else "小作文"

        # 2. 细分子类型研判
        sub_type = "未知"
        if essay_type == "小作文":
            if any(k in combined for k in ["notice", "announcement", "通知", "告示"]):
                sub_type = "告示/通知"
            elif any(k in combined for k in ["memo", "memorandum", "备忘录"]):
                sub_type = "备忘录"
            elif any(k in combined for k in ["proposal", "倡议", "倡议书"]):
                sub_type = "倡议书"
            elif any(k in combined for k in ["recommend", "推荐", "推荐信"]):
                sub_type = "推荐信"
            elif any(k in combined for k in ["suggest", "advice", "建议", "提议"]):
                sub_type = "建议信"
            elif any(k in combined for k in ["invite", "invitation", "邀请"]):
                sub_type = "邀请信"
            elif any(k in combined for k in ["complain", "complaint", "投诉"]):
                sub_type = "投诉信"
            elif any(k in combined for k in ["thank", "gratitude", "感谢"]):
                sub_type = "感谢信"
            elif any(k in combined for k in ["apolog", "sorry", "道歉"]):
                sub_type = "道歉信"
            elif any(k in combined for k in ["inquir", "ask", "询问"]):
                sub_type = "询问信"
            else:
                sub_type = "书信"
        else:
            if exam_category == "英语一":
                if any(k in combined for k in ["culture", "traditional", "heritage", "文化", "传统", "非遗", "火锅", "龙舟"]):
                    sub_type = "图画作文（传统文化与道德）"
                elif any(k in combined for k in ["phone", "mobile", "internet", "social", "screen", "手机", "网络", "低头族", "科技"]):
                    sub_type = "图画作文（社会现象与科技反思）"
                elif any(k in combined for k in ["perseverance", "climb", "habit", "optimis", "persist", "坚持", "习惯", "乐观", "读书"]):
                    sub_type = "图画作文（人生哲理与个人修养）"
                elif any(k in combined for k in ["chart", "table", "graph", "图表", "柱状图", "表格"]):
                    sub_type = "图表与社会发展作文"
                else:
                    sub_type = "图画作文"
            else:
                if any(k in combined for k in ["pie", "饼图"]):
                    sub_type = "饼图"
                elif any(k in combined for k in ["line", "curve", "折线图"]):
                    sub_type = "折线图"
                elif any(k in combined for k in ["table", "表格"]):
                    sub_type = "表格"
                else:
                    sub_type = "柱状图"

        return {
            "essay_type": essay_type,
            "sub_type": sub_type
        }

    @classmethod
    def check_preliminary_rules(cls, text: str, essay_type: str, exam_category: str = "英语二") -> Dict[str, Any]:
        """
        基于考研大纲硬性规则的预检（词数、基本格式、分段），区别英语一与英语二
        """
        struct = cls.parse_essay_structure(text, essay_type)
        word_count = struct["total_word_count"]
        body_word_count = struct["body_word_count"]
        body_paragraph_count = struct["body_paragraph_count"]
        raw_paragraph_count = struct["raw_paragraph_count"]
        is_letter = struct["is_letter"]
        warnings = []
        penalty_estimate = 0.0

        if essay_type == "小作文":
            # 小作文：英语一与英语二均为约 100 词，满分 10 分
            if word_count < 50:
                warnings.append(f"词数严重不足（当前 {word_count} 词，大纲规定约100词），根据大纲最高得分不超过5分")
                penalty_estimate += 3.0
            elif word_count < 80:
                warnings.append(f"词数不足（当前 {word_count} 词，规定约100词），扣1-2分")
                penalty_estimate += 1.5
            elif word_count < 90:
                warnings.append(f"词数略显偏少（当前 {word_count} 词），建议达到100-120词")
                penalty_estimate += 0.5
            elif word_count > 160:
                warnings.append(f"词数偏多（当前 {word_count} 词），建议控制在100-130词之间，避免过多语言错误与时间浪费")

            lower_text = text.lower()
            is_notice = "notice" in lower_text or "announcement" in lower_text
            is_memo = "memo" in lower_text or "to:" in lower_text

            if not is_notice and not is_memo:
                if not struct["salutation"]:
                    warnings.append("缺少应用文规范称呼（如 Dear Sir/Madam, Dear ...）")
                    penalty_estimate += 1.0
                if not struct["sign_off"] and not struct["signature"]:
                    warnings.append("缺少规范书信落款（如 Yours sincerely, Li Ming）")
                    penalty_estimate += 0.5

            if body_paragraph_count < 2:
                warnings.append("正文未进行清晰分段（建议三段式：首段说明目的，中段展开要点，尾段礼貌结语）")
                penalty_estimate += 0.5

        else: # 大作文
            if exam_category == "英语一":
                # 英语一大作文：满分 20 分，大纲要求 160-200 词（图画作文）
                if word_count < 80:
                    warnings.append(f"词数严重不足（当前 {word_count} 词，英语一大纲规定160-200词），属于严重违规，最高得分不超过8分")
                    penalty_estimate += 6.0
                elif word_count < 120:
                    warnings.append(f"词数严重偏少（当前 {word_count} 词，规定160-200词），扣4-5分")
                    penalty_estimate += 4.5
                elif word_count < 140:
                    warnings.append(f"词数偏少（当前 {word_count} 词，大纲底线160词），扣2-3分")
                    penalty_estimate += 2.5
                elif word_count < 160:
                    warnings.append(f"词数略低于160词底线（当前 {word_count} 词），酌情扣1-2分")
                    penalty_estimate += 1.0
                elif word_count > 240:
                    warnings.append(f"词数偏多（当前 {word_count} 词），建议精炼至180-220词，避免卷面拥挤")

                if body_paragraph_count < 3:
                    warnings.append("英语一图画大作文强烈建议采用标准三段式（第一段生动描述图画，第二段阐释深层寓意与多维归因，第三段对策建议与评论），当前段落数不足3段")
                    penalty_estimate += 1.0

            else:
                # 英语二大作文：满分 15 分，大纲要求不少于 150 词（图表作文）
                if word_count < 80:
                    warnings.append(f"词数严重不足（当前 {word_count} 词，规定不少于150词），属于严重违规，最高得分不超过5分")
                    penalty_estimate += 5.0
                elif word_count < 110:
                    warnings.append(f"词数严重偏少（当前 {word_count} 词，规定不少于150词），扣3-4分")
                    penalty_estimate += 3.5
                elif word_count < 140:
                    warnings.append(f"词数未达到150词底线（当前 {word_count} 词），扣1-2分")
                    penalty_estimate += 1.5
                elif word_count < 150:
                    warnings.append(f"词数略低于150词（当前 {word_count} 词），酌情扣0.5-1分")
                    penalty_estimate += 0.5

                if body_paragraph_count < 3:
                    warnings.append("大作文建议采用标准三段式（第一段图表描述，第二段原因分析，第三段总结建议），当前段落数不足3段")
                    penalty_estimate += 1.0

        effective_paragraph_count = body_paragraph_count if (essay_type == "小作文" and is_letter) else raw_paragraph_count

        return {
            "word_count": word_count,
            "body_word_count": body_word_count,
            "paragraph_count": effective_paragraph_count,
            "body_paragraph_count": body_paragraph_count,
            "raw_paragraph_count": raw_paragraph_count,
            "paragraphs": struct["body_paragraphs"],
            "is_letter": is_letter,
            "salutation": struct["salutation"],
            "sign_off": struct["sign_off"],
            "signature": struct["signature"],
            "sentence_count": len(cls.split_sentences(text)),
            "warnings": warnings,
            "penalty_estimate": penalty_estimate
        }

    @classmethod
    def preprocess(
        cls,
        text: str,
        essay_type: Optional[str] = None,
        prompt_topic: str = "",
        exam_category: str = "英语二"
    ) -> Dict[str, Any]:
        """完整预处理流程，接入考试类别"""
        detected = cls.detect_essay_type(text, prompt_topic, exam_category=exam_category, forced_essay_type=essay_type)
        final_type = essay_type or detected["essay_type"]
        final_subtype = detected["sub_type"]

        rule_check = cls.check_preliminary_rules(text, final_type, exam_category=exam_category)

        return {
            "text": text,
            "prompt_topic": prompt_topic,
            "exam_category": exam_category,
            "essay_type": final_type,
            "sub_type": final_subtype,
            **rule_check
        }
