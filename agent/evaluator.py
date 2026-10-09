import json
import time
import re
from typing import Dict, Any, Optional
from openai import OpenAI

from agent.config import agent_config
from agent.preprocessor import EssayPreprocessor
from agent.prompts import get_system_prompt, build_evaluation_prompt
from rag.retriever import KnowledgeRetriever

class EssayEvaluator:
    """考研英语一 & 英语二作文权威评分 Agent 核心执行器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        allow_env_fallback: bool = True
    ):
        raw_key = (api_key or "").strip()
        if raw_key:
            self.api_key = raw_key
        elif allow_env_fallback:
            self.api_key = agent_config.DEEPSEEK_API_KEY
        else:
            self.api_key = ""

        self.base_url = (base_url or "").strip() or agent_config.DEEPSEEK_BASE_URL
        self.model_name = (model_name or "").strip() or agent_config.DEEPSEEK_MODEL_NAME

        if not self.api_key:
            if "localhost" in (self.base_url or "") or "127.0.0.1" in (self.base_url or ""):
                self.api_key = "ollama"
            else:
                raise ValueError("API Key 未配置！请在模型设置中填入您自己的专属 API Key，或在 .env 中配置 DEEPSEEK_API_KEY！")

        # 初始化 OpenAI 兼容客户端（设置 180 秒超时）
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=180.0)
        # 初始化 RAG 语义检索器
        self.retriever = KnowledgeRetriever()

    @staticmethod
    def _parse_and_repair_json(raw_content: str) -> Optional[Dict[str, Any]]:
        """多阶段高容错 JSON 提取与修复解析器"""
        if not raw_content or not raw_content.strip():
            return None

        # 阶段 1: 过滤 reasoning thinking 标签（适配 DeepSeek-R1, QwQ 等推理模型）
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_content).strip()

        # 阶段 2: 剥离 Markdown ```json ... ``` 标记（含非首行代码块兼容）
        json_code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_code_block:
            cleaned = json_code_block.group(1).strip()
        elif cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # 阶段 3: 提取最外层大括号
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx:end_idx+1]

        # 阶段 4: 标准解析（启用 strict=False 兼容字符串字面未转义换行符/制表符）
        try:
            parsed = json.loads(cleaned, strict=False)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # 阶段 5: 修复尾部多余逗号 (Trailing Commas)
        try:
            fixed = re.sub(r",\s*([\]}])", r"\1", cleaned)
            parsed = json.loads(fixed, strict=False)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # 阶段 6: 修复因 token 达到限制导致的未闭合截断 JSON
        try:
            repaired = cleaned
            if repaired.count('"') % 2 != 0:
                repaired += '"'
            open_braces = repaired.count('{') - repaired.count('}')
            open_brackets = repaired.count('[') - repaired.count(']')
            repaired = re.sub(r",\s*$", "", repaired.strip())
            if open_brackets > 0:
                repaired += ']' * open_brackets
            if open_braces > 0:
                repaired += '}' * open_braces
            parsed = json.loads(repaired, strict=False)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        return None

    @staticmethod
    def _regex_salvage(raw_content: str, essay_type: str, word_count: int, exam_category: str = "英语二") -> Optional[Dict[str, Any]]:
        """从非标准输出中紧急抢救评分核心字段"""
        score_match = re.search(r'["\']?total_score["\']?\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)', raw_content)
        if not score_match:
            score_match = re.search(r'(?:总分|实得分|最终得分|得分)\D*([0-9]+(?:\.[0-9]+)?)', raw_content)
        if not score_match:
            return None

        total_score = float(score_match.group(1))

        # 动态满分与各维度满分划分
        if exam_category == "英语一":
            calculated_max = 10.0 if essay_type == "小作文" else 20.0
            dim_cfg = {
                "content": ("图画描摹与要点" if essay_type != "小作文" else "内容要点完整性", 6.0 if essay_type != "小作文" else 3.0),
                "organization": ("组织连贯性", 4.0 if essay_type != "小作文" else 2.0),
                "language": ("语言质量与多样性", 6.0 if essay_type != "小作文" else 3.0),
                "format": ("论证对策与文体规范" if essay_type != "小作文" else "格式规范与语域", 4.0 if essay_type != "小作文" else 2.0)
            }
        else:
            calculated_max = 10.0 if essay_type == "小作文" else 15.0
            dim_cfg = {
                "content": ("图表描述与内容完整性" if essay_type != "小作文" else "内容要点完整性", 4.0 if essay_type != "小作文" else 3.0),
                "organization": ("组织连贯性", 3.5 if essay_type != "小作文" else 2.0),
                "language": ("语言质量与多样性", 5.0 if essay_type != "小作文" else 3.0),
                "format": ("格式规范与图表特征" if essay_type != "小作文" else "格式规范与语域", 2.5 if essay_type != "小作文" else 2.0)
            }

        total_score = max(0.0, min(calculated_max, total_score))
        ratio = total_score / calculated_max if calculated_max > 0 else 0.5

        # 依据得分率研判大纲标准档次
        band_match = re.search(r'["\']?band["\']?\s*[:=]\s*["\']?([^"\',\n]+)', raw_content)
        if band_match:
            band = band_match.group(1).strip()
        else:
            if ratio >= 0.85:
                band = "第五档（最高档）"
            elif ratio >= 0.70:
                band = "第四档"
            elif ratio >= 0.50:
                band = "第三档"
            elif ratio >= 0.30:
                band = "第二档"
            else:
                band = "第一档"

        comment_match = re.search(r'["\']?summary_comment["\']?\s*[:=]\s*["\']?([^"\']{15,})', raw_content)

        dimensions = {}
        for k, (d_name, d_max) in dim_cfg.items():
            d_score = round(min(d_max, max(0.0, total_score * (d_max / calculated_max))), 1)
            dimensions[k] = {
                "name": d_name,
                "score": d_score,
                "max_score": d_max,
                "analysis": f"依据评分规范，{d_name}得分估评为 {d_score}/{d_max} 分",
                "score_reason": "模型原始返回轻微格式偏差，系统已按得分率标准映射"
            }

        return {
            "exam_category": exam_category,
            "total_score": round(total_score * 2) / 2,
            "max_score": calculated_max,
            "band": band,
            "summary_comment": comment_match.group(1).strip() if comment_match else "评分模型返回格式略有偏差，系统已成功解析其核心评分与意见。",
            "dimensions": dimensions
        }

    def evaluate(
        self,
        essay_text: str,
        prompt_topic: str = "",
        essay_type: Optional[str] = None,
        exam_category: str = "英语二"
    ) -> Dict[str, Any]:
        """
        对学生作文执行全流程 RAG 赋能评估（支持英语一与英语二）
        :param essay_text: 考生提交的作文正文
        :param prompt_topic: 作文题目要求或背景描述
        :param essay_type: "小作文" 或 "大作文"（若不提供则由系统自动研判）
        :param exam_category: "英语一" 或 "英语二"
        :return: 包含多维度得分、评语、扣分明细、语病诊断及升格范文的结构化结果
        """
        start_time = time.time()
        print(f"\n[EssayEvaluator] >>> 步骤 1: 正在对【{exam_category}】作文进行篇章结构与字数预处理...")
        preprocessed = EssayPreprocessor.preprocess(
            text=essay_text,
            essay_type=essay_type,
            prompt_topic=prompt_topic,
            exam_category=exam_category
        )
        resolved_type = preprocessed["essay_type"]
        resolved_subtype = preprocessed["sub_type"]
        word_count = preprocessed["word_count"]
        print(f"[EssayEvaluator] 预处理完成: 识别为【{exam_category} {resolved_type} - {resolved_subtype}】，词数: {word_count} 词，段落: {preprocessed['paragraph_count']} 段")

        # 2. RAG 知识检索
        print(f"[EssayEvaluator] >>> 步骤 2: 正在通过 RAG 知识库检索【{exam_category}】官方评分大纲、标杆范文与错误模式...")
        rag_context = self.retriever.retrieve_evaluation_context(
            essay_type=resolved_type,
            essay_topic=prompt_topic or resolved_subtype,
            essay_text=essay_text,
            exam_category=exam_category
        )
        print(f"[EssayEvaluator] RAG 检索完成: 命中标准 {len(rag_context['scoring_criteria'])} 条, 范文 {len(rag_context['sample_essays'])} 条, 语料 {len(rag_context['writing_knowledge'])} 条, 病句诊断 {len(rag_context['common_errors'])} 条")

        # 3. 组装 Prompt
        print(f"[EssayEvaluator] >>> 步骤 3: 正在组装【{exam_category}】阅卷专家 Prompt 并调用模型 ({self.model_name})...")
        system_prompt = get_system_prompt(exam_category)
        user_prompt = build_evaluation_prompt(
            essay_text=essay_text,
            prompt_topic=prompt_topic,
            preprocessed_info=preprocessed,
            rag_context=rag_context,
            exam_category=exam_category
        )

        # 4. 调用大模型（具备智能多轮退避重试与格式自适应降级）
        raw_content = ""
        finish_reason = ""
        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"[EssayEvaluator] 正在建立与大模型的流式长连接 (stream=True, 尝试 {attempt}/{max_attempts})...")
                response_stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=agent_config.TEMPERATURE,
                    max_tokens=agent_config.MAX_TOKENS,
                    stream=True
                )
                content_chunks = []
                reasoning_chunks = []
                for chunk in response_stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    delta = choice.delta
                    if hasattr(delta, "content") and delta.content:
                        content_chunks.append(delta.content)
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        reasoning_chunks.append(delta.reasoning_content)
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason

                raw_content = "".join(content_chunks)
                reasoning_content = "".join(reasoning_chunks)

                # 兼容推理模型标签输出
                if not raw_content.strip() and reasoning_content.strip():
                    if "{" in reasoning_content and "}" in reasoning_content:
                        raw_content = reasoning_content

                if raw_content.strip():
                    break

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_overload = any(k in err_str for k in ["overload", "503", "429", "rate limit", "busy", "server error", "connection reset", "timeout"])

                if is_overload:
                    if attempt < max_attempts:
                        wait_sec = attempt * 2.5
                        print(f"[EssayEvaluator] 提示: 大模型服务商返回过载或限频 ({e})，正在进行第 {attempt} 次自动退避重试（等待 {wait_sec} 秒）...")
                        time.sleep(wait_sec)
                        continue
                    else:
                        raise RuntimeError(
                            f"大模型云端服务当前严重拥堵（{e}）。\n"
                            f"【原因解析】当前所选服务商（如 DeepSeek 官方）高峰期算力超负荷（Our servers are currently overloaded）。\n"
                            f"【快速解决建议】\n"
                            f"1. 稍等 10-15 秒后再次点击“智能评卷”重试；\n"
                            f"2. 或在页面顶部【评卷模型】中切换为通义千问 (Qwen)、智谱清言 (GLM) 或本地 Ollama 模型，即可秒级评卷。"
                        )

                # 如果是 json_object 不兼容等格式问题，降级为通用流式模式
                if "response_format" in err_str or "json_object" in err_str or "unsupported" in err_str or "400" in err_str or "stream" in err_str:
                    print(f"[EssayEvaluator] 当前模型在 json_object 下报错，降级为通用流式模式...")
                    try:
                        response_stream = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[
                                {"role": "system", "content": system_prompt + "\n\n【重要】请务必直接输出严格合法的 JSON 格式字符串，严禁输出任何多余的开场白或解释。"},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=agent_config.TEMPERATURE,
                            max_tokens=agent_config.MAX_TOKENS,
                            stream=True
                        )
                        content_chunks = []
                        reasoning_chunks = []
                        for chunk in response_stream:
                            if not chunk.choices:
                                continue
                            choice = chunk.choices[0]
                            delta = choice.delta
                            if hasattr(delta, "content") and delta.content:
                                content_chunks.append(delta.content)
                            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                                reasoning_chunks.append(delta.reasoning_content)
                            if choice.finish_reason:
                                finish_reason = choice.finish_reason
                        raw_content = "".join(content_chunks)
                        reasoning_content = "".join(reasoning_chunks)
                        if not raw_content.strip() and reasoning_content.strip():
                            if "{" in reasoning_content and "}" in reasoning_content:
                                raw_content = reasoning_content
                        if raw_content.strip():
                            break
                    except Exception as inner_e:
                        inner_str = str(inner_e).lower()
                        if any(k in inner_str for k in ["overload", "503", "429", "rate limit", "busy"]):
                            if attempt < max_attempts:
                                wait_sec = attempt * 2.5
                                print(f"[EssayEvaluator] 降级流式仍过载，等待 {wait_sec} 秒后重试...")
                                time.sleep(wait_sec)
                                continue

                        print(f"[EssayEvaluator] 流式接口不兼容 ({inner_e})，尝试非流式兜底...")
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[
                                {"role": "system", "content": system_prompt + "\n\n【重要】请务必直接输出严格合法的 JSON 格式字符串，严禁输出任何多余的开场白或解释。"},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=agent_config.TEMPERATURE,
                            max_tokens=agent_config.MAX_TOKENS
                        )
                        raw_content = response.choices[0].message.content or ""
                        finish_reason = getattr(response.choices[0], "finish_reason", "") or ""
                        if raw_content.strip():
                            break
                else:
                    raise e

        latency = time.time() - start_time

        # 5. 解析并强化结构化结果
        result = self._parse_and_repair_json(raw_content)
        if result is None:
            result = self._regex_salvage(raw_content, resolved_type, word_count, exam_category=exam_category)

        if result is None or result.get("total_score") is None:
            err_msg = f"大模型评卷未输出有效评分内容 (模型: '{self.model_name}', finish_reason: '{finish_reason}', 返回长度: {len(raw_content)})"
            if finish_reason == "length":
                err_msg += "。原因：大模型思考或输出超出最大 Token 限制（MAX_TOKENS），输出被截断。"
            print(f"[EssayEvaluator] 错误: {err_msg}")
            if raw_content:
                print(f"[EssayEvaluator] 模型原始输出片段: {raw_content[:300]}")
            raise RuntimeError(err_msg)

        # 满分与维度基准设定
        if exam_category == "英语一":
            calculated_max = 10.0 if resolved_type == "小作文" else 20.0
            std_dim_cfg = {
                "content": ("图画描摹与要点" if resolved_type != "小作文" else "内容要点完整性", 6.0 if resolved_type != "小作文" else 3.0),
                "organization": ("组织连贯性", 4.0 if resolved_type != "小作文" else 2.0),
                "language": ("语言质量与多样性", 6.0 if resolved_type != "小作文" else 3.0),
                "format": ("论证对策与文体规范" if resolved_type != "小作文" else "格式规范与语域", 4.0 if resolved_type != "小作文" else 2.0)
            }
        else:
            calculated_max = 10.0 if resolved_type == "小作文" else 15.0
            std_dim_cfg = {
                "content": ("图表描述与内容完整性" if resolved_type != "小作文" else "内容要点完整性", 4.0 if resolved_type != "小作文" else 3.0),
                "organization": ("组织连贯性", 3.5 if resolved_type != "小作文" else 2.0),
                "language": ("语言质量与多样性", 5.0 if resolved_type != "小作文" else 3.0),
                "format": ("格式规范与图表特征" if resolved_type != "小作文" else "格式规范与语域", 2.5 if resolved_type != "小作文" else 2.0)
            }

        # 强制满分与得分合法性校验（严格钳位在 [0, calculated_max]，规整至考研 0.5 分进制）
        result["max_score"] = calculated_max
        try:
            raw_total = float(result.get("total_score", 0.0))
        except (ValueError, TypeError):
            raw_total = 0.0
        clamped_total = max(0.0, min(calculated_max, raw_total))
        result["total_score"] = round(clamped_total * 2) / 2

        # 强化默认字段与类型
        result["exam_category"] = exam_category
        result["essay_type"] = resolved_type
        result["sub_type"] = resolved_subtype
        result["word_count"] = word_count
        result.setdefault("deductions", [])
        result.setdefault("highlights", [])
        result.setdefault("error_diagnostics", [])
        result.setdefault("study_suggestions", [])
        result.setdefault("polished_essay", "")
        result.setdefault("summary_comment", "评卷完成。")

        # 规范化四大维度得分与分析
        raw_dims = result.get("dimensions") if isinstance(result.get("dimensions"), dict) else {}
        norm_dims = {}
        for dim_key, (dim_name, dim_max) in std_dim_cfg.items():
            dim_val = raw_dims.get(dim_key, {})
            if not isinstance(dim_val, dict):
                dim_val = {}
            try:
                dim_s = float(dim_val.get("score", clamped_total * (dim_max / calculated_max)))
            except (ValueError, TypeError):
                dim_s = clamped_total * (dim_max / calculated_max)
            clamped_s = round(max(0.0, min(dim_max, dim_s)), 1)
            norm_dims[dim_key] = {
                "name": dim_val.get("name") or dim_name,
                "score": clamped_s,
                "max_score": dim_max,
                "analysis": dim_val.get("analysis") or "符合考研大纲对应档次规范要求。",
                "score_reason": dim_val.get("score_reason") or "根据大纲量化细则综合裁定"
            }
        result["dimensions"] = norm_dims

        # 规范化扣分项（杜绝负数符号重复）
        clean_deductions = []
        for d in result.get("deductions", []):
            if isinstance(d, dict):
                try:
                    pts = abs(float(d.get("points", 0.0)))
                except (ValueError, TypeError):
                    pts = 0.0
                clean_deductions.append({
                    "item": str(d.get("item") or "扣分项"),
                    "points": pts,
                    "rule": str(d.get("rule") or "考试大纲规范")
                })
        result["deductions"] = clean_deductions

        # 规范化语病诊断字段映射
        clean_errors = []
        for err in result.get("error_diagnostics", []):
            if isinstance(err, dict):
                orig = err.get("original_text") or err.get("wrong") or err.get("original") or ""
                corr = err.get("correction") or err.get("correct") or err.get("suggestion") or ""
                expl = err.get("explanation") or err.get("reason") or err.get("analysis") or ""
                etype = err.get("error_type") or err.get("type") or "语法规范"
                if orig or corr:
                    clean_errors.append({
                        "original_text": str(orig),
                        "correction": str(corr),
                        "explanation": str(expl),
                        "error_type": str(etype)
                    })
        result["error_diagnostics"] = clean_errors

        # 规范化官方大纲档次
        ratio = result["total_score"] / calculated_max if calculated_max > 0 else 0.5
        if not result.get("band") or result.get("band") == "未定档":
            if ratio >= 0.85:
                result["band"] = "第五档（最高档）"
            elif ratio >= 0.70:
                result["band"] = "第四档"
            elif ratio >= 0.50:
                result["band"] = "第三档"
            elif ratio >= 0.30:
                result["band"] = "第二档"
            else:
                result["band"] = "第一档"

        # 附加元数据
        result["meta"] = {
            "exam_category": exam_category,
            "model_name": self.model_name,
            "latency_seconds": round(latency, 2),
            "word_count": word_count,
            "body_word_count": preprocessed.get("body_word_count", word_count),
            "paragraph_count": preprocessed["paragraph_count"],
            "body_paragraph_count": preprocessed.get("body_paragraph_count", preprocessed["paragraph_count"]),
            "raw_paragraph_count": preprocessed.get("raw_paragraph_count", preprocessed["paragraph_count"]),
            "is_letter": preprocessed.get("is_letter", False),
            "salutation": preprocessed.get("salutation"),
            "sign_off": preprocessed.get("sign_off"),
            "signature": preprocessed.get("signature"),
            "precheck_warnings": preprocessed["warnings"],
            "prompt_topic": prompt_topic,
            "rag_chunks_used": {
                "scoring_criteria": len(rag_context["scoring_criteria"]),
                "sample_essays": len(rag_context["sample_essays"]),
                "writing_knowledge": len(rag_context["writing_knowledge"]),
                "common_errors": len(rag_context["common_errors"])
            }
        }

        print(f"[EssayEvaluator] >>> 评卷完成！得分: {result.get('total_score')}/{result.get('max_score')} ({result.get('band')}), 耗时: {latency:.2f} 秒")
        return result
