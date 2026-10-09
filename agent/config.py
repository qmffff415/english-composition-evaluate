import os
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录下的 .env
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)

class AgentConfig:
    # DeepSeek 模型调用配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL_NAME: str = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

    # 评分参数（低采样温度确保评分稳定性与一致性，8192 确保推理思考与长JSON报告完整生成）
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 8192

    # 路径配置
    OUTPUT_DIR: Path = PROJECT_ROOT / "evaluation_reports"

agent_config = AgentConfig()
