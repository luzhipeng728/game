"""苏丹的游戏智能体模块"""

from .base_agent import BaseGameAgent
from .agent_registry import AgentRegistry, agent_registry
from .agent_manager import AgentManager
from .scene_config import SceneConfig, SceneConfigManager, scene_config_manager

# 具体的智能体类
from .follower_agent import FollowerAgent
from .courtesan_agent import CourtesanAgent
from .madam_agent import MadamAgent
from .narrator_agent import NarratorAgent

__all__ = [
    'BaseGameAgent',
    'AgentRegistry',
    'agent_registry',
    'AgentManager',
    'SceneConfig',
    'SceneConfigManager',
    'scene_config_manager',
    'FollowerAgent',
    'CourtesanAgent',
    'MadamAgent',
    'NarratorAgent'
] 