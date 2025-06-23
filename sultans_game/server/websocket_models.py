"""WebSocket相关的数据模型和枚举"""

import time
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from dataclasses import dataclass, field
from enum import Enum

from ..models import GameState, Card


class UserRole(Enum):
    """用户角色"""
    HUMAN_FOLLOWER = "human_follower"  # 人类扮演随从
    HUMAN_COURTESAN = "human_courtesan"  # 人类扮演妓女
    HUMAN_MADAM = "human_madam"  # 人类扮演老鸨
    SPECTATOR = "spectator"  # 旁观者


class MessageType(Enum):
    """消息类型"""
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    CHAT_MESSAGE = "chat_message"
    AGENT_MESSAGE = "agent_message"
    SYSTEM_MESSAGE = "system_message"
    PAUSE_REQUEST = "pause_request"
    RESUME_REQUEST = "resume_request"
    SCENE_UPDATE = "scene_update"
    USER_TYPING = "user_typing"
    USER_STOP_TYPING = "user_stop_typing"
    FOLLOWER_CHOICE_REQUEST = "follower_choice_request"  # 随从选择请求
    FOLLOWER_CHOICE_RESPONSE = "follower_choice_response"  # 随从选择回应
    GAME_PHASE_CHANGE = "game_phase_change"  # 游戏阶段变化
    GAME_END = "game_end"  # 游戏结束


@dataclass
class ChatUser:
    """聊天用户"""
    user_id: str
    websocket: WebSocket
    username: str
    role: UserRole
    room_id: str
    last_activity: float = field(default_factory=time.time)
    is_typing: bool = False
    pause_until: float = 0  # 暂停到什么时候


@dataclass
class ChatRoom:
    """聊天房间"""
    room_id: str
    scene_name: str
    users: Dict[str, ChatUser] = field(default_factory=dict)
    agent_manager: Optional[object] = None  # AgentManager类型
    agent_coordinator: Optional[object] = None  # AgentCoordinator类型
    game_state: Optional[GameState] = None
    active_card: Optional[Card] = None
    conversation_queue: List[Dict] = field(default_factory=list)
    is_paused: bool = False
    pause_requests: Set[str] = field(default_factory=set)  # 发送暂停请求的用户
    last_message_time: float = field(default_factory=time.time)
    next_speaker: Optional[str] = None  # 下一个应该发言的角色
    
    # 防止重复调用的锁
    agent_locks: Dict[str, bool] = field(default_factory=dict)  # 智能体是否正在生成响应
    
    # 🎮 简化游戏管理字段
    conversation_count: int = 0  # 对话计数器
    max_conversations: int = 20  # 最大20轮对话
    follower_action_interval: int = 4  # 每4轮随从行动
    last_follower_round: int = 0  # 上次随从行动的轮数
    pending_follower_choices: List = field(default_factory=list)  # 待处理的随从选择
    is_follower_choice_phase: bool = False  # 是否在随从选择阶段
    card_activated: bool = False  # 卡片是否已激活
    mission_announced: bool = False  # 任务是否已宣布 