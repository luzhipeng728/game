"""
苏丹的游戏 - API配置
"""
import os

# API 配置
API_KEY = "hypr-lab-AhlUmIPK999Z51T1zq3sT3BlbkFJMtsLVnBefsOcvFSJSlNV"
API_BASE_URL = "https://api.hyprlab.io/v1"

# 可用模型列表（全部使用 OpenAI 兼容格式）
# 可用的AI模型配置
AVAILABLE_MODELS = {
    "gpt-4.1-mini": {
        "model": "gpt-4.1-mini",  # 使用原始模型名，通过 model_kwargs 控制 provider
        "name": "GPT-4.1 Mini",
        "description": "OpenAI 最新的 GPT-4.1 Mini 模型，性能优异且成本较低",
        "type": "OpenAI Compatible",
        "base_url": "https://api.hyprlab.io/v1"
    },
    "gpt-4.1-nano": {
        "model": "gpt-4.1-nano",  # 使用原始模型名
        "name": "GPT-4.1 Nano", 
        "description": "OpenAI 超轻量级 GPT-4.1 Nano 模型，响应速度极快",
        "type": "OpenAI Compatible",
        "base_url": "https://api.hyprlab.io/v1"
    },
    "gpt-4.1": {
        "model": "gpt-4.1",  # 使用原始模型名
        "name": "GPT-4.1",
        "description": "OpenAI 最新的 GPT-4.1 完整版本，功能最强大",
        "type": "OpenAI Compatible", 
        "base_url": "https://api.hyprlab.io/v1"
    },
    "gemini-2.5-flash-preview-05-20": {
        "model": "gemini-2.5-flash-preview-05-20",  # 使用原始模型名
        "name": "Gemini 2.5 Flash Preview",
        "description": "Google 最新的 Gemini 2.5 Flash 预览版本，速度极快",
        "type": "OpenAI Compatible",
        "base_url": "https://api.hyprlab.io/v1"
    },
    "gemini-2.0-flash": {
        "model": "gemini-2.0-flash",  # 使用原始模型名
        "name": "Gemini 2.0 Flash",
        "description": "Google Gemini 2.0 Flash 模型，平衡性能与速度",
        "type": "OpenAI Compatible",
        "base_url": "https://api.hyprlab.io/v1"
    },
    "claude-3-5-haiku-20241022": {
        "model": "claude-3-5-haiku-20241022",  # 使用原始模型名
        "name": "Claude 3.5 Haiku",
        "description": "Anthropic Claude 3.5 Haiku 模型，轻量级且高效",
        "type": "OpenAI Compatible",
        "base_url": "https://api.hyprlab.io/v1"
    }
}

# 默认模型
DEFAULT_MODEL = "gpt-4.1"

# 设置环境变量
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_API_BASE"] = API_BASE_URL

def get_available_models():
    """获取可用模型列表"""
    return AVAILABLE_MODELS

def get_model_config(model_name: str = None):
    """获取模型配置
    
    Args:
        model_name: 模型名称，如果为None则使用默认模型
        
    Returns:
        包含API配置的字典
    """
    if model_name is None:
        model_name = DEFAULT_MODEL
    
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"不支持的模型: {model_name}。可用模型: {list(AVAILABLE_MODELS.keys())}")
    
    model_info = AVAILABLE_MODELS[model_name]
    
    return {
        "api_key": API_KEY,
        "base_url": API_BASE_URL,
        "model": model_info["model"],  # 使用带有 openai/ 前缀的模型名，LiteLLM 会自动处理
        "model_info": model_info
    }

def get_openai_config(model_name: str = None):
    """获取OpenAI配置（保持向后兼容）"""
    return get_model_config(model_name)