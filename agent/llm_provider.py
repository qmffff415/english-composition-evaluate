import time
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from agent.config import agent_config

# 主流大模型服务商预设模板
LLM_PRESETS = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "provider": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "doc_url": "https://platform.deepseek.com/api_keys",
        "description": "最具性价比，深度适配考研英语大纲评分要求"
    },
    {
        "id": "qwen",
        "name": "阿里通义千问 (Qwen)",
        "provider": "Alibaba Cloud",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen2.5-72b-instruct"],
        "doc_url": "https://dashscope.console.aliyun.com/apiKey",
        "description": "中文与中英互译理解能力极强，响应迅速"
    },
    {
        "id": "moonshot",
        "name": "月之暗面 (Kimi)",
        "provider": "Moonshot AI",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k"],
        "doc_url": "https://platform.moonshot.cn/console/api-keys",
        "description": "长上下文与篇章逻辑理解出色"
    },
    {
        "id": "zhipu",
        "name": "智谱清言 (GLM)",
        "provider": "Zhipu AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "models": ["glm-4-flash", "glm-4", "glm-4-plus"],
        "doc_url": "https://open.bigmodel.cn/usercenter/apikeys",
        "description": "国产前沿基座模型，轻量级免费或低成本"
    },
    {
        "id": "ollama",
        "name": "本地部署 Ollama",
        "provider": "Local Ollama",
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:7b",
        "models": ["qwen2.5:7b", "llama3.1:8b", "deepseek-r1:7b"],
        "doc_url": "https://ollama.com",
        "description": "完全离线私有化运行，无需消耗外部 API Token"
    },
    {
        "id": "custom",
        "name": "自定义兼容接口 (Custom)",
        "provider": "Custom",
        "base_url": "",
        "default_model": "",
        "models": [],
        "doc_url": "",
        "description": "支持任意第三方兼容端点或本地自建模型服务"
    }
]

def test_llm_connection(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    轻量级测试大模型 API 连通性
    严禁默认借用或回退到 .env 中的私有密钥，所有云端大模型必须由调用方/用户显式提供 API Key
    """
    resolved_api_key = (api_key or "").strip()
    resolved_base_url = (base_url or "").strip() or "https://api.deepseek.com"
    resolved_model = (model_name or "").strip() or "deepseek-chat"

    # 如果未提供 API Key 且不是无需 key 的本地本地服务，直接拒绝并报错
    if not resolved_api_key and "localhost" not in resolved_base_url and "127.0.0.1" not in resolved_base_url:
        return {
            "success": False,
            "error": "未提供 API Key！系统禁止默认使用私有 .env 密钥，请在卡片中填写您自己的专属 API Key。"
        }

    # 处理本地 Ollama 无需真实 key 的情况
    effective_api_key = resolved_api_key or "ollama"

    start_time = time.time()
    try:
        client = OpenAI(
            api_key=effective_api_key,
            base_url=resolved_base_url,
            timeout=15.0
        )

        # 发送极简校验请求
        response = client.chat.completions.create(
            model=resolved_model,
            messages=[
                {"role": "system", "content": "You are a test probe."},
                {"role": "user", "content": "Reply with 'PONG'"}
            ],
            max_tokens=15,
            temperature=0.1
        )

        latency_ms = int((time.time() - start_time) * 1000)
        reply = response.choices[0].message.content or ""

        return {
            "success": True,
            "latency_ms": latency_ms,
            "model_name": resolved_model,
            "reply": reply.strip(),
            "message": f"连接成功！模型 '{resolved_model}' 响应正常，延迟: {latency_ms}ms"
        }
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        err_msg = str(e)
        # 提供更友好的中文错误归因
        if "401" in err_msg or "authentication" in err_msg.lower():
            friendly_err = f"认证失败 (401): API Key 无效或已过期，请核对后重试。"
        elif "404" in err_msg or "not found" in err_msg.lower():
            friendly_err = f"模型不存在 (404): 服务端未找到名为 '{resolved_model}' 的模型，或 Base URL 地址错误。"
        elif "connection" in err_msg.lower() or "timeout" in err_msg.lower():
            friendly_err = f"网络连接超时: 无法访问端点 '{resolved_base_url}'，请检查网络或代理设置。"
        elif "quota" in err_msg.lower() or "exceeded" in err_msg.lower():
            friendly_err = f"账户配额不足: API 余额不足或并发超出限制。"
        else:
            friendly_err = f"调用失败: {err_msg}"

        return {
            "success": False,
            "latency_ms": latency_ms,
            "model_name": resolved_model,
            "error": friendly_err,
            "raw_error": err_msg
        }
