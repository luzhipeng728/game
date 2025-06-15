"""
苏丹的游戏 - API配置
"""
import os

# OpenAI API 配置
OPENAI_API_KEY = "hypr-lab-AhlUmIPK999Z51T1zq3sT3BlbkFJMtsLVnBefsOcvFSJSlNV"
OPENAI_API_BASE_URL = "https://api.hyprlab.io/v1"
OPENAI_MODEL = "gpt-4.1-nano"

# 设置环境变量
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE_URL

def get_openai_config():
    """获取OpenAI配置"""
    return {
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_API_BASE_URL,
        "model": OPENAI_MODEL
    }