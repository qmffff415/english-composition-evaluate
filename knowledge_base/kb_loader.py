"""
考研英语一 & 英语二写作知识库加载与分块索引器 (KB Loader & Chunk Indexer)
用于将 knowledge_base 目录下的各 JSON 结构化数据解析、校验并转化为
适用于向量化检索（RAG Retrieval）与本地倒排语义匹配的 Chunks with Metadata。
支持区分考研英语一（图画作文/应用文/20分大纲）与考研英语二（图表作文/应用文/15分大纲）。
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

KB_ROOT = Path(__file__).parent.resolve()

def load_json(filepath: Path) -> Any:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_knowledge_chunks() -> List[Dict[str, Any]]:
    chunks = []

    # 1. 评分标准模块 (Scoring Criteria)
    criteria_dir = KB_ROOT / "scoring_criteria"
    if criteria_dir.exists():
        for file in criteria_dir.glob("*.json"):
            data = load_json(file)
            file_name = file.stem
            exam_cat = data.get("exam_category", "英语一" if "english_one" in file_name else ("英语二" if "criteria" in file_name or "band" in file_name else "通用"))

            if "criteria" in file_name:
                essay_type = "小作文" if "small" in file_name else "大作文"
                total_score = data.get("total_score", 10 if essay_type == "小作文" else (20 if exam_cat == "英语一" else 15))
                # 按评分维度分块
                dimensions = data.get("scoring_dimensions", [])
                for dim in dimensions:
                    chunks.append({
                        "id": f"crit_{file_name}_{dim.get('dimension')}",
                        "module": "scoring_criteria",
                        "exam_category": exam_cat,
                        "essay_type": essay_type,
                        "category": dim.get("dimension"),
                        "title": f"【{exam_cat}】{essay_type}评分维度：{dim.get('name_cn')}（满分{total_score}分）",
                        "content": f"【{exam_cat} {essay_type}评分维度 - {dim.get('name_cn')}】\n满分权重：{dim.get('weight', '')}\n描述：{dim.get('description', '')}\n考察要点：\n" + "\n".join(f"- {p}" for p in dim.get("evaluation_points", [])),
                        "metadata": {
                            "source": file.name,
                            "type": "scoring_dimension",
                            "exam_category": exam_cat,
                            "essay_type": essay_type,
                            "dimension": dim.get("dimension"),
                            "total_score": total_score
                        }
                    })

                # 按档次分数区间分块
                bands = data.get("bands", [])
                for b in bands:
                    chunks.append({
                        "id": f"crit_{file_name}_band_{b.get('band', '')}",
                        "module": "scoring_criteria",
                        "exam_category": exam_cat,
                        "essay_type": essay_type,
                        "category": "band_score",
                        "title": f"【{exam_cat}】{essay_type}评分档次：{b.get('band_name', '')} ({b.get('score_range', '')})",
                        "content": f"【{exam_cat} {essay_type}评分档次 - {b.get('band_name', '')} ({b.get('score_range', '')})】\n描述：{b.get('description', '')}\n标准：\n" + "\n".join(f"- {c}" for c in b.get("criteria", [])),
                        "metadata": {
                            "source": file.name,
                            "type": "band_criteria",
                            "exam_category": exam_cat,
                            "essay_type": essay_type,
                            "score_range": b.get("score_range", "")
                        }
                    })

            elif "band_descriptors" in file_name:
                for prefix, band_list in [("small", data.get("small_essay_bands", [])), ("big", data.get("big_essay_bands", []))]:
                    etype = "小作文" if prefix == "small" else "大作文"
                    for b in band_list:
                        breakdown = b.get("criteria_breakdown", {})
                        breakdown_text = "\n".join(f"- {k}: {v}" for k, v in breakdown.items())
                        typical_text = "\n".join(f"- {item}" for item in b.get("typical_features", []))
                        chunks.append({
                            "id": f"band_desc_{file_name}_{prefix}_{b.get('band')}",
                            "module": "scoring_criteria",
                            "exam_category": exam_cat,
                            "essay_type": etype,
                            "category": "band_descriptor",
                            "title": f"【{exam_cat}】{etype}大纲档次详细描述：{b.get('band_name')} ({b.get('score_range')})",
                            "content": f"【{exam_cat} {etype}大纲详细档次描述：{b.get('band_name')} ({b.get('score_range')})】\n总体描述：{b.get('general_description')}\n分项细则：\n{breakdown_text}\n典型特征：\n{typical_text}",
                            "metadata": {
                                "source": file.name,
                                "type": "official_band_descriptor",
                                "exam_category": exam_cat,
                                "essay_type": etype,
                                "band": b.get("band"),
                                "score_range": b.get("score_range")
                            }
                        })

            elif file_name == "penalty_rules":
                rules = data.get("rules", [])
                for r in rules:
                    situations = r.get("situations", [])
                    sit_text = "\n".join(f"- {s.get('condition')}: {s.get('penalty')} ({s.get('explanation', '')})" for s in situations)
                    chunks.append({
                        "id": f"penalty_{r.get('rule_id')}",
                        "module": "scoring_criteria",
                        "exam_category": "通用",
                        "essay_type": "通用",
                        "category": "penalty_rule",
                        "title": f"扣分规范细则：{r.get('rule_name')}",
                        "content": f"【扣分规范 - {r.get('rule_name')}】\n规则描述：{r.get('description')}\n具体情形与扣分幅度：\n{sit_text}",
                        "metadata": {
                            "source": file.name,
                            "type": "penalty_rule",
                            "exam_category": "通用",
                            "rule_id": r.get("rule_id")
                        }
                    })

    # 2. 范文语料模块 (Sample Essays)
    sample_dir = KB_ROOT / "sample_essays"
    if sample_dir.exists():
        for collection_file in sample_dir.rglob("*.json"):
            # 如果是 library 文件，也同样解析或按结构解析
            samples = load_json(collection_file)
            if isinstance(samples, list):
                for s in samples:
                    if not isinstance(s, dict):
                        continue
                    exam_cat = s.get("exam_category", "英语一" if "eng1" in str(s.get("id")) or "english_one" in collection_file.name else "英语二")
                    comments = s.get("comments") or s.get("analysis") or {}
                    if isinstance(comments, dict):
                        comm_text = "\n".join(f"- {k}: {v}" for k, v in comments.items())
                    else:
                        comm_text = str(comments)

                    highlights = s.get("highlights") or []
                    if isinstance(highlights, list):
                        highlights_text = ", ".join(highlights) if highlights else "无"
                    else:
                        highlights_text = str(highlights)

                    errors = s.get("errors") or []
                    if isinstance(errors, list):
                        errors_text = "\n".join(f"- {e}" for e in errors) if errors else "无明显语言错误"
                    else:
                        errors_text = str(errors)

                    essay_text = s.get("essay") or s.get("sample_essay", "")
                    topic_name = s.get("topic") or s.get("title") or "真题范文"
                    score_info = f"{s.get('score')}分" if s.get('score') else ""
                    band_info = f"({s.get('band')})" if s.get('band') else ""

                    chunks.append({
                        "id": f"sample_{s.get('id', hash(topic_name))}",
                        "module": "sample_essays",
                        "exam_category": exam_cat,
                        "essay_type": s.get("type", "大作文"),
                        "category": s.get("sub_type", "范文"),
                        "title": f"【{exam_cat}】范文参考[{s.get('type')}-{s.get('sub_type')}] {s.get('year', '')}年 {topic_name} {score_info} {band_info}",
                        "content": f"【{exam_cat} 范文参考：{topic_name}】\n类型：{s.get('type')} - {s.get('sub_type')} | 年份：{s.get('year')} | 得分：{s.get('score')} ({s.get('band')}) | 词数：{s.get('word_count')}\n\n范文正文：\n{essay_text}\n\n阅卷点评：\n{comm_text}\n\n亮点表达：\n{highlights_text}\n\n错误分析与修改：\n{errors_text}",
                        "metadata": {
                            "source": collection_file.name,
                            "type": "sample_essay",
                            "exam_category": exam_cat,
                            "essay_type": s.get("type"),
                            "sub_type": s.get("sub_type"),
                            "score": s.get("score"),
                            "band": s.get("band"),
                            "year": s.get("year")
                        }
                    })

    # 3. 常见错误模块 (Common Errors)
    error_dir = KB_ROOT / "common_errors"
    if error_dir.exists():
        for file in error_dir.glob("*.json"):
            data = load_json(file)
            file_name = file.stem
            categories = data.get("error_categories", [])
            for cat in categories:
                items = cat.get("examples", []) or cat.get("cases", []) or cat.get("types", [])
                items_text = ""
                for it in items:
                    if isinstance(it, dict):
                        wrong = it.get("wrong") or it.get("issue") or it.get("mistake") or it.get("error_example") or ""
                        correct = it.get("correct") or it.get("suggestion") or it.get("correction") or it.get("proper_usage") or ""
                        explain = it.get("explanation") or it.get("reason") or it.get("rule") or ""
                        items_text += f"\n- 错误：{wrong}\n  正确：{correct}\n  说明：{explain}"
                    else:
                        items_text += f"\n- {it}"

                chunks.append({
                    "id": f"err_{file_name}_{cat.get('category', 'cat')}",
                    "module": "common_errors",
                    "exam_category": "通用",
                    "essay_type": "通用",
                    "category": file_name,
                    "title": f"常见错误归纳：{cat.get('name_cn', cat.get('category', ''))}",
                    "content": f"【常见错误类型 - {cat.get('name_cn', '')} ({cat.get('category', '')})】\n错误描述与识别要点：{cat.get('description', '')}\n案例与纠错指南：{items_text}",
                    "metadata": {
                        "source": file.name,
                        "type": "error_pattern",
                        "exam_category": "通用",
                        "error_category": file_name,
                        "subcategory": cat.get("category", "")
                    }
                })

            pairs = data.get("error_pairs", [])
            if pairs:
                for pair_cat in pairs:
                    cname = pair_cat.get("category", "")
                    ex_list = pair_cat.get("examples", [])
                    pair_lines = "\n".join(f"- 中式：{e.get('chinglish')} -> 地道：{e.get('natural')} (说明：{e.get('explanation', '')})" for e in ex_list)
                    chunks.append({
                        "id": f"chinglish_{cname}",
                        "module": "common_errors",
                        "exam_category": "通用",
                        "essay_type": "通用",
                        "category": "chinglish",
                        "title": f"中式英语识别与纠正：{cname}",
                        "content": f"【中式英语（Chinglish）纠正对照 - {cname}】\n{pair_lines}",
                        "metadata": {
                            "source": file.name,
                            "type": "chinglish_pattern",
                            "exam_category": "通用",
                            "subcategory": cname
                        }
                    })

    # 4. 写作知识模块 (Writing Knowledge)
    wk_dir = KB_ROOT / "writing_knowledge"
    if wk_dir.exists():
        # vocabulary
        for file in (wk_dir / "vocabulary").glob("*.json"):
            data = load_json(file)
            file_name = file.stem
            exam_cat = data.get("exam_category", "英语一" if "picture" in file_name or "philosophical" in file_name else ("英语二" if "chart" in file_name else "通用"))
            cats = data.get("categories", [])
            for cat in cats:
                cat_name = cat.get("name_cn", cat.get("category", ""))
                words = cat.get("words", []) or cat.get("expressions", []) or cat.get("items", []) or cat.get("replacements", [])
                word_lines = []
                for w in words:
                    if isinstance(w, dict):
                        word_str = f"- {w.get('word') or w.get('basic', '')} -> {w.get('advanced') or w.get('meaning', '')} ({w.get('example', '')})"
                    else:
                        word_str = f"- {w}"
                    word_lines.append(word_str)

                essay_type = "大作文" if ("chart" in file_name or "picture" in file_name or "philosophical" in file_name) else ("小作文" if "letter" in file_name else "通用")
                chunks.append({
                    "id": f"vocab_{file_name}_{cat.get('category', '')}",
                    "module": "writing_knowledge",
                    "exam_category": exam_cat,
                    "essay_type": essay_type,
                    "category": "vocabulary",
                    "title": f"【{exam_cat}】写作语料库：{data.get('description', '')} - {cat_name}",
                    "content": f"【{exam_cat} 写作词汇与表达 - {cat_name}】\n说明：{cat.get('description', '')}\n词汇与例句列表：\n" + "\n".join(word_lines),
                    "metadata": {
                        "source": file.name,
                        "type": "vocabulary",
                        "exam_category": exam_cat,
                        "subtype": file_name,
                        "category": cat_name
                    }
                })

        # sentence patterns
        sp_dir = wk_dir / "sentence_patterns"
        if sp_dir.exists():
            for sp_file in sp_dir.glob("*.json"):
                data = load_json(sp_file)
                file_stem = sp_file.stem
                if file_stem == "advanced_structures":
                    structures = data.get("structures", [])
                    for st in structures:
                        examples_text = "\n".join(f"  * 句型公式：{ex.get('formula', '')}\n    例句：{ex.get('sentence', '')}\n    中文：{ex.get('translation', '')}" for ex in st.get("templates", st.get("examples", [])))
                        chunks.append({
                            "id": f"sent_struct_{st.get('name')}",
                            "module": "writing_knowledge",
                            "exam_category": "通用",
                            "essay_type": "通用",
                            "category": "sentence_patterns",
                            "title": f"高分高级句型：{st.get('name')}",
                            "content": f"【高分句式结构 - {st.get('name')}】\n功能与应用价值：{st.get('function', '')}\n经典模板与实战例句：\n{examples_text}\n常见易错点：{st.get('common_mistakes', '')}",
                            "metadata": {
                                "source": sp_file.name,
                                "type": "sentence_pattern",
                                "exam_category": "通用",
                                "structure_name": st.get("name")
                            }
                        })
                elif file_stem == "picture_essay_patterns":
                    paragraphs = data.get("paragraphs", {})
                    for p_key, p_val in paragraphs.items():
                        patterns = p_val.get("patterns", [])
                        pat_lines = []
                        for pat in patterns:
                            pat_lines.append(f"- 句型：{pat.get('type')}\n  模板：{pat.get('template')}\n  范例：{pat.get('example')}\n  亮点分析：{pat.get('highlights')}")
                        chunks.append({
                            "id": f"pattern_pic_{p_key}",
                            "module": "writing_knowledge",
                            "exam_category": "英语一",
                            "essay_type": "大作文",
                            "category": "picture_essay_pattern",
                            "title": f"【英语一】图画大作文高分段落句型：{p_val.get('name')}",
                            "content": f"【英语一 图画作文段落句型 - {p_val.get('name')}】\n大纲建议篇幅：{p_val.get('standard_length')}\n推荐高分句型列表：\n" + "\n".join(pat_lines),
                            "metadata": {
                                "source": sp_file.name,
                                "type": "picture_pattern",
                                "exam_category": "英语一",
                                "essay_type": "大作文",
                                "paragraph_part": p_key
                            }
                        })
                elif file_stem == "practical_writing_patterns":
                    genres = data.get("genres", {})
                    for g_key, g_val in genres.items():
                        openings = "\n".join(f"  * {op}" for op in g_val.get("opening_patterns", []))
                        bodies = "\n".join(f"  * {bd}" for bd in g_val.get("body_patterns", []))
                        closings = "\n".join(f"  * {cl}" for cl in g_val.get("closing_patterns", []))
                        chunks.append({
                            "id": f"pattern_practical_{g_key}",
                            "module": "writing_knowledge",
                            "exam_category": "英语一",
                            "essay_type": "小作文",
                            "category": "practical_writing_pattern",
                            "title": f"【英语一】应用文小作文高分句型与模板：{g_val.get('name')}",
                            "content": f"【英语一 应用文句式规范 - {g_val.get('name')}】\n格式与考查特征：{g_val.get('format_features', '')}\n经典开篇句：\n{openings}\n正文要点展开句：\n{bodies}\n结语与期盼句：\n{closings}",
                            "metadata": {
                                "source": sp_file.name,
                                "type": "practical_pattern",
                                "exam_category": "英语一",
                                "essay_type": "小作文",
                                "genre": g_key
                            }
                        })

        # thematic materials (英语一专属五大核心母题深度语料库)
        tm_dir = wk_dir / "thematic_materials"
        if tm_dir.exists():
            for tm_file in tm_dir.glob("*.json"):
                data = load_json(tm_file)
                theme_title = data.get("theme", "")
                sub_themes = data.get("sub_themes", [])
                for st in sub_themes:
                    st_name = st.get("name", "")
                    vocab_lines = "\n".join(f"  * {v.get('word')} ({v.get('meaning')}): 搭配={v.get('collocation')}" for v in st.get("core_vocabulary", []))
                    quote_lines = "\n".join(f"  * \"{q.get('quote')}\" —— {q.get('author')} ({q.get('translation')}) [应用场景: {q.get('usage')}]" for q in st.get("proverbs_and_quotes", []))
                    arg_lines = "\n".join(f"  * {a.get('point_en')}\n    译文：{a.get('point_cn')}" for a in st.get("argument_points", []))
                    sample_sent_lines = "\n".join(f"  * {s}" for s in st.get("sample_sentence_patterns", []))
                    applicable = ", ".join(st.get("applicable_topics", []))

                    chunks.append({
                        "id": f"theme_{tm_file.stem}_{st_name.split()[0]}",
                        "module": "writing_knowledge",
                        "exam_category": "英语一",
                        "essay_type": "大作文",
                        "category": "thematic_corpus",
                        "title": f"【英语一】图画大作文核心母题论据库：{theme_title} - {st_name}",
                        "content": f"【英语一 核心母题论据语料 - {theme_title} ({st_name})】\n适用历年真题与话题：{applicable}\n核心高阶词汇与搭配：\n{vocab_lines}\n权威名人名言与谚语：\n{quote_lines}\n核心论证论点链：\n{arg_lines}\n经典示范句式：\n{sample_sent_lines}",
                        "metadata": {
                            "source": tm_file.name,
                            "type": "thematic_corpus",
                            "exam_category": "英语一",
                            "essay_type": "大作文",
                            "theme": theme_title,
                            "sub_theme": st_name
                        }
                    })

        # format guidelines
        for file in (wk_dir / "format_guidelines").glob("*.json"):
            data = load_json(file)
            file_stem = file.stem
            exam_cat = data.get("exam_category", "英语一" if "english_one" in file_stem else ("通用" if "notice" in file_stem else "英语二"))
            etype = "小作文" if ("small" in file_stem or "notice" in file_stem) else "大作文"
            chunks.append({
                "id": f"format_{file_stem}",
                "module": "writing_knowledge",
                "exam_category": exam_cat,
                "essay_type": etype,
                "category": "format_guidelines",
                "title": f"【{exam_cat}】{etype}格式与排版规范：{data.get('description', '')}",
                "content": f"【{exam_cat} 写作格式规范 - {data.get('description', '')}】\n" + json.dumps(data, ensure_ascii=False, indent=2),
                "metadata": {
                    "source": file.name,
                    "type": "format_guideline",
                    "exam_category": exam_cat,
                    "essay_type": etype
                }
            })

    # 5. 题型模板与历年真题 (Question Templates)
    qt_dir = KB_ROOT / "question_templates"
    if qt_dir.exists():
        for file in qt_dir.glob("*.json"):
            data = load_json(file)
            file_name = file.stem
            exam_cat = data.get("exam_category", "英语一" if "english_one" in file_name else "英语二")

            if "past_exam_topics" in file_name:
                topics_data = data.get("data", {})
                for etype_key, etype_cn in [("small_essays", "小作文"), ("big_essays", "大作文")]:
                    exam_list = topics_data.get(etype_key, [])
                    for exam in exam_list:
                        category_tag = exam.get("sub_type") or exam.get("chart_type") or exam.get("type")
                        topic_cn = exam.get("topic_cn", "")
                        prompt_en = exam.get("prompt_en", "")
                        chunks.append({
                            "id": f"exam_{exam_cat}_{exam.get('year')}_{etype_key}",
                            "module": "question_templates",
                            "exam_category": exam_cat,
                            "essay_type": etype_cn,
                            "category": "past_exam_topic",
                            "title": f"【{exam_cat}】{exam.get('year')}年考研{exam_cat}{etype_cn}真题 [{category_tag}] {topic_cn}",
                            "content": f"【{exam.get('year')}年考研{exam_cat}{etype_cn}真题】\n分类：{category_tag}\n中文主题：{topic_cn}\n题目英文要求（Prompt/Directions）：\n{prompt_en}\n关键要点与说明：\n" + json.dumps(exam.get("key_points") or exam.get("data_description") or {}, ensure_ascii=False),
                            "metadata": {
                                "source": file.name,
                                "type": "past_exam",
                                "year": exam.get("year"),
                                "exam_category": exam_cat,
                                "essay_type": etype_cn,
                                "topic_type": category_tag,
                                "topic_cn": topic_cn
                            }
                        })
            elif "templates" in file_name:
                templates = data.get("templates", [])
                etype_cn = "小作文" if "small" in file_name else "大作文"
                for t in templates:
                    t_name = t.get("name_cn", t.get("type", "template"))
                    chunks.append({
                        "id": f"template_{file_name}_{t.get('type', t.get('chart_type', t.get('theme_type', 'item')))}",
                        "module": "question_templates",
                        "exam_category": exam_cat,
                        "essay_type": etype_cn,
                        "category": "essay_template",
                        "title": f"【{exam_cat}】{etype_cn}高分模板框架：{t_name}",
                        "content": f"【{exam_cat} {etype_cn}写作框架模板 - {t_name}】\n详细框架结构与推荐句型：\n" + json.dumps(t, ensure_ascii=False, indent=2),
                        "metadata": {
                            "source": file.name,
                            "type": "writing_template",
                            "exam_category": exam_cat,
                            "essay_type": etype_cn,
                            "template_name": t_name
                        }
                    })

    return chunks

def export_index():
    chunks = build_knowledge_chunks()
    index_path = KB_ROOT / "index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_chunks": len(chunks),
            "modules": {
                "scoring_criteria": len([c for c in chunks if c['module'] == 'scoring_criteria']),
                "sample_essays": len([c for c in chunks if c['module'] == 'sample_essays']),
                "writing_knowledge": len([c for c in chunks if c['module'] == 'writing_knowledge']),
                "common_errors": len([c for c in chunks if c['module'] == 'common_errors']),
                "question_templates": len([c for c in chunks if c['module'] == 'question_templates']),
            },
            "exam_categories": {
                "英语一": len([c for c in chunks if c.get('exam_category') == '英语一']),
                "英语二": len([c for c in chunks if c.get('exam_category') == '英语二']),
                "通用": len([c for c in chunks if c.get('exam_category') == '通用']),
            },
            "chunks": chunks
        }, f, ensure_ascii=False, indent=2)

    print(f"Index successfully exported to {index_path}!")
    print(f"Total Chunks: {len(chunks)}")
    for mod in ["scoring_criteria", "sample_essays", "writing_knowledge", "common_errors", "question_templates"]:
        count = len([c for c in chunks if c['module'] == mod])
        print(f"  - {mod}: {count} chunks")
    print(f"Exam Categories breakdown:")
    for ec in ["英语一", "英语二", "通用"]:
        cnt = len([c for c in chunks if c.get('exam_category') == ec])
        print(f"  * {ec}: {cnt} chunks")

if __name__ == "__main__":
    export_index()
