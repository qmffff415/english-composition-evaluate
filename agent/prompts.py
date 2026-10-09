from typing import Dict, Any

SYSTEM_PROMPT_ENGLISH_ONE = """你是由教育部全国硕士研究生统一招生考试英语（一）阅卷专家组领导的【考研英语一作文权威智能评分系统】。
你的任务是根据《全国硕士研究生招生考试英语（一）考试大纲》的官方评分标准，结合 RAG 知识库检索出的官方大纲档次规范、权威图画范文基准锚点、高分语料库及常见病句辨析库，对考生提交的作文进行严谨、专业、多维度、逐句精细化的客观评卷。

【满分与档次划分标准】
1. 小作文（Part A，应用文如书信、告示Notice、备忘录Memo、倡议书）：满分 10 分
   - 第五档（9-10分）：很好地完成了试题规定的任务，要点齐全，语言地道丰富，结构紧凑，格式与语域完全正确。
   - 第四档（7-8分）：较好地完成了试题规定的任务，包含主要要点，语言有少量小错但不影响理解，格式基本正确。
   - 第三档（5-6分）：基本完成了试题规定的任务，漏掉部分要点或展开不充分，语言错误较多（时态、单复数），格式有小瑕疵。
   - 第二档（3-4分）：未能按要求完成任务，严重偏题或要点大面积遗漏，语言错误严重影响理解，格式错误。
   - 第一档（1-2分）：未完成任务，仅写出零星词句，不成篇章。
   - 零分档（0分）：白卷、完全跑题、纯中文、完全抄袭阅读理解。

2. 大作文（Part B，图画作文 Cartoon/Picture Essay 为主）：满分 20 分（规定词数 160-200 词）
   - 第五档（17-20分）：图画描述生动精准抓核心细节与文字说明；寓意剖析深刻透彻（多维度逻辑归因）；对策建议切实有力；词汇高级丰富、句式多样典雅（状语从句、非谓语、倒装、虚拟语气），行文浑然一体，极少甚至无语法错误。
   - 第四档（13-16分）：切题，包含图画主要内容并揭示寓意，论证较充分；词汇语法较丰富，有少量非关键语法小错，结构清晰，衔接自然。
   - 第三档（9-12分）：基本切题，图画描述较简略或寓意流于表面，论证空泛单薄，模板套话痕迹明显，语言错误较多，词数略有欠缺。
   - 第二档（5-8分）：严重误读图画或严重偏题，论据脱节，断句碎裂，病句连篇，不足110词。
   - 第一档（1-4分）：未完成任务，仅写出零星孤立词句，通篇不成段。
   - 零分档（0分）：白卷、完全抄袭阅读理解、纯中文。

【评分指导原则】
1. 客观公正：严格对照英语一大纲各档次描述打分，分数为 0.5 分进制（如 16.5, 17.0, 17.5）。
2. 四大核心维度：
   - 图画描述与点题（Picture Description & Relevance）
   - 寓意阐释与论证深度（Interpretation & Analytical Depth）
   - 语言质量与多样性（Language Accuracy & Variety）
   - 篇章结构与逻辑连贯（Organization & Coherence）
3. 严格字数与格式扣分：大作文低于160词按大纲强制梯级扣分。
4. 深度诊断：逐一揪出语法错误、Chinglish 与搭配不当，给出地道修改方案。
5. 升格范文：保留考生原有点题逻辑，输出达到第五档（18-20分）高分升格范文。"""

SYSTEM_PROMPT_ENGLISH_TWO = """你是由教育部全国硕士研究生统一招生考试英语（二）阅卷专家组领导的【考研英语二作文权威智能评分系统】。
你的任务是根据《全国硕士研究生招生考试英语（二）考试大纲》的官方评分标准，结合 RAG 检索知识库检索出的官方大纲档次规范、权威范文基准锚点、高分语料库及常见病句辨析库，对考生提交的作文进行严谨、专业、多维度、逐句精细化的客观评卷。

【满分与档次划分标准】
1. 小作文（Part A，应用文如书信、通知、告示）：满分 10 分
   - 第五档（9-10分）：很好地完成了试题规定的任务，要点齐全，语言地道丰富，结构紧凑，格式完全正确。
   - 第四档（7-8分）：较好地完成了试题规定的任务，包含主要要点，语言有少量小错但不影响理解，格式基本正确。
   - 第三档（5-6分）：基本完成了试题规定的任务，漏掉部分要点或展开不充分，语言错误较多，格式有小瑕疵。
   - 第二档（3-4分）：未能按要求完成任务，严重偏题，语言错误严重影响理解。
   - 第一档（1-2分）：未完成任务，仅写出零星词句。
   - 零分档（0分）：白卷、完全跑题、纯中文。

2. 大作文（Part B，图表作文如柱状图、饼图、折线图、表格）：满分 15 分（规定词数不少于 150 词）
   - 第五档（13-15分）：图表描述精准抓核心，原因剖析透彻深刻（多维度），结论辩证前瞻；词汇语法高级丰富，行文流畅自然。
   - 第四档（9-12分）：图表主要数据提及，原因分析基本成立；语言较丰富，有少量语法小错，结构清晰。
   - 第三档（5-8分）：图表数据解读有误或只字不提具体数据，原因分析空泛单薄，模板套话严重，语言错误频发。
   - 第二档（1-4分）：严重误读图表趋势，严重跑题，病句连篇，不足100词。
   - 零分档（0分）：白卷、完全抄袭阅读理解、纯中文。"""

# 默认兼容
SYSTEM_PROMPT = SYSTEM_PROMPT_ENGLISH_TWO

def get_system_prompt(exam_category: str = "英语二") -> str:
    """根据考试类别动态获取阅卷专家 System Prompt"""
    if exam_category == "英语一":
        return SYSTEM_PROMPT_ENGLISH_ONE
    return SYSTEM_PROMPT_ENGLISH_TWO

def build_evaluation_prompt(
    essay_text: str,
    prompt_topic: str,
    preprocessed_info: Dict[str, Any],
    rag_context: Dict[str, Any],
    exam_category: str = "英语二"
) -> str:
    """构建包含作文原文、预检信息与 RAG 知识库检索结果的综合 Prompt（全面适配英语一与英语二）"""

    essay_type = preprocessed_info.get("essay_type", "小作文")
    sub_type = preprocessed_info.get("sub_type", "未知")
    word_count = preprocessed_info.get("word_count", 0)

    # 满分与档次计算
    if exam_category == "英语一":
        max_score = 10 if essay_type == "小作文" else 20
        example_band = "第四档(7-8分)" if essay_type == "小作文" else "第四档(13-16分)"
        default_total = 8.0 if essay_type == "小作文" else 15.5
        content_max = 3.0 if essay_type == "小作文" else 6.0
        org_max = 2.0 if essay_type == "小作文" else 4.0
        lang_max = 3.0 if essay_type == "小作文" else 6.0
        fmt_max = 2.0 if essay_type == "小作文" else 4.0
        content_name = "内容要点完整性" if essay_type == "小作文" else "图画描摹与寓意深刻性"
        fmt_name = "格式规范与语域" if essay_type == "小作文" else "论证对策与文体规范"
    else:
        max_score = 10 if essay_type == "小作文" else 15
        example_band = "第四档(7-8分)" if essay_type == "小作文" else "第四档(9-12分)"
        default_total = 8.0 if essay_type == "小作文" else 11.5
        content_max = 3.0 if essay_type == "小作文" else 4.0
        org_max = 2.0 if essay_type == "小作文" else 3.5
        lang_max = 3.0 if essay_type == "小作文" else 5.0
        fmt_max = 2.0 if essay_type == "小作文" else 2.5
        content_name = "内容要点完整性" if essay_type == "小作文" else "图表描述与内容完整性"
        fmt_name = "格式规范与语域" if essay_type == "小作文" else "格式规范与图表特征"

    # 格式化 RAG 上下文
    criteria_chunks = rag_context.get("scoring_criteria", [])
    criteria_str = "\n".join([f"【{c.get('title')}】\n{c.get('content')}" for c in criteria_chunks]) if criteria_chunks else f"严格遵循系统 Prompt 中指定的考研{exam_category}官方考试大纲档次评定标准与量化分值。"

    sample_chunks = rag_context.get("sample_essays", [])
    samples_str = "\n".join([f"【{s.get('title')}】\n{s.get('content')}" for s in sample_chunks]) if sample_chunks else f"依据官方高分第一档标杆写作范式与篇章展开逻辑实施对标评估。"

    knowledge_chunks = rag_context.get("writing_knowledge", [])
    knowledge_str = "\n".join([f"【{k.get('title')}】\n{k.get('content')}" for k in knowledge_chunks]) if knowledge_chunks else "依据考研学术英语规范、多样化句型（状语从句、非谓语、倒装等）及精准词汇进行考察。"

    error_chunks = rag_context.get("common_errors", [])
    errors_str = "\n".join([f"【{e.get('title')}】\n{e.get('content')}" for e in error_chunks]) if error_chunks else "重点排查时态语态不一致、主谓单复数、冠词与介词误用、中式英语生硬直译等典型语法语病。"

    precheck_warnings = preprocessed_info.get("warnings", [])
    warnings_str = "\n".join([f"- {w}" for w in precheck_warnings]) if precheck_warnings else "无硬性违规"

    body_word_count = preprocessed_info.get("body_word_count", word_count)
    body_p_count = preprocessed_info.get("body_paragraph_count", preprocessed_info.get("paragraph_count", 1))
    is_letter = preprocessed_info.get("is_letter", False) or essay_type == "小作文"
    salutation = preprocessed_info.get("salutation")
    sign_off = preprocessed_info.get("sign_off")
    signature = preprocessed_info.get("signature")

    if is_letter and (salutation or sign_off or signature):
        structure_desc = f"""- 统计词数：{word_count} 词（严格按大纲规范：标点符号不计入；其中正文 {body_word_count} 词，称呼/落款等格式词 {word_count - body_word_count} 词）
- 篇章段落：正文共 {body_p_count} 段（独立称呼【{salutation or '无'}】，结尾落款【{sign_off or ''} {signature or ''}】）
- 篇章格式特别说明（【极其重要，严禁误判扣分】）：
  * 考生的信件格式规范：开头的称呼（如 Dear...）与结尾的落款（如 Yours sincerely, Li Ming）属于应用证书信的独立格式要素，【绝不是正文段落】！
  * 考生的正文实际分为【{body_p_count} 个主体段落】（如标准的三段式：首段说明目的，中段展开要点，尾段礼貌结语与期待）。
  * 【严禁误判】：严禁将独立称呼和落款算作多余碎段！严禁误判为“全文分为5-6段过于零散碎小”并因此扣减组织连贯性或格式分！
  * 【词数容差】：小作文考研大纲要求“约100词（标点符号不计算在内）”。正文在 90-145 词之间且要点充实、行文地道的，属于优秀表现，【严禁机械扣减字数分】！"""
    else:
        structure_desc = f"""- 统计词数：{word_count} 词（严格按大纲规范：标点符号不计入）
- 篇章段落：共 {preprocessed_info.get('paragraph_count', 1)} 段"""

    prompt = f"""请对以下考研{exam_category}考生作文进行权威综合阅卷评分。
【核心要求】
1. 必须输出完整客观的评卷内容，包括四大维度详尽分析、逐句语法病句改错、亮点表达与第一档升格范文。
2. polished_essay 字段请直接输出纯文本升格范文，切勿使用 markdown 反引号代码块（如 ```text）包裹，保证 JSON 纯净解析。
3. 请严格按照下方 JSON 模板结构输出合法 JSON，严禁添加任何多余前后缀。

============================================================
【一、试题与作答信息】
- 考试类别：全国硕士研究生招生考试【{exam_category}】
- 作文类别：考研{exam_category} {essay_type}（满分 {max_score} 分）
- 细分题型：{sub_type}
- 作文题目/要求：{prompt_topic or "未指定具体题目（请根据考生作文内容判断主题契合度）"}
{structure_desc}
- 系统硬性预检提示：
{warnings_str}

【考生作文正文】
------------------------------------------------------------
{essay_text}
------------------------------------------------------------

============================================================
【二、RAG 向量知识库检索出的评卷参考依据】

【1. 官方考试大纲标准与档次规范（{exam_category}）】
{criteria_str}

【2. 权威同类真题范文与打分锚点】
{samples_str}

【3. 推荐高分学术词汇与高级句式】
{knowledge_str}

【4. 考研常见病句与中式英语（Chinglish）纠正对照】
{errors_str}

============================================================
【三、评分与输出要求】
请结合上述 RAG 依据，输出如下格式的 JSON 字符串（严禁包含其他非JSON字符）：

{{
  "exam_category": "{exam_category}",
  "essay_type": "{essay_type}",
  "sub_type": "{sub_type}",
  "word_count": {word_count},
  "max_score": {max_score},
  "total_score": {default_total},
  "band": "{example_band}",
  "summary_comment": "阅卷组长对全文的总体综合评语（200字以内，客观深刻）",
  "dimensions": {{
    "content": {{
      "name": "{content_name}",
      "score": {round(content_max * 0.75, 1)},
      "max_score": {content_max},
      "analysis": "对要点覆盖、寓意提炼、论点展开的具体分析",
      "score_reason": "得分或失分原因"
    }},
    "organization": {{
      "name": "组织连贯性",
      "score": {round(org_max * 0.75, 1)},
      "max_score": {org_max},
      "analysis": "对篇章结构、分段逻辑、衔接词自然度的具体分析",
      "score_reason": "得分或失分原因"
    }},
    "language": {{
      "name": "语言质量与多样性",
      "score": {round(lang_max * 0.75, 1)},
      "max_score": {lang_max},
      "analysis": "对词汇丰富度、句式多样性及语病数量的分析",
      "score_reason": "得分或失分原因"
    }},
    "format": {{
      "name": "{fmt_name}",
      "score": {round(fmt_max * 0.75, 1)},
      "max_score": {fmt_max},
      "analysis": "对称呼落款、首段点题、行文格式规范性的分析",
      "score_reason": "得分或失分原因"
    }}
  }},
  "deductions": [
    {{
      "item": "扣分项目名称（如字数不足扣分、格式缺陷扣分）",
      "points": 1.0,
      "rule": "对应的大纲扣分依据"
    }}
  ],
  "highlights": [
    {{
      "quote": "文中的亮点短语或句式",
      "praise": "阅卷亮点点评"
    }}
  ],
  "error_diagnostics": [
    {{
      "original_text": "文中的错误原句或词汇",
      "error_type": "主谓不一致 / 中式英语 / 搭配不当 / 时态错误 / 拼写错误 / 标点错误",
      "explanation": "错误语法或逻辑机理剖析",
      "correction": "地道纯正的权威修改建议"
    }}
  ],
  "polished_essay": "完整升格范文（在保留原作者核心观点的基础上，升级词汇、高级句式与段落衔接，达到大纲第五档卓越高分水准）",
  "study_suggestions": [
    "针对考生的首要提升建议1",
    "针对考生的首要提升建议2",
    "针对考生的首要提升建议3"
  ]
}}
"""
    return prompt
