"""WebSocket多人聊天服务器"""

import asyncio
import json
import time
import uuid
import os
from typing import Dict, List, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass, field
from enum import Enum

# 全局禁用CrewAI遥测避免网络错误
os.environ["OTEL_SDK_DISABLED"] = "true"

from .agents.agent_manager import AgentManager
from .agents.agent_coordinator import AgentCoordinator, MessageType as CoordinatorMessageType
from .models import GameState, SceneState, Character, Card, CardType, CardRank


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
    agent_manager: Optional[AgentManager] = None
    agent_coordinator: Optional[AgentCoordinator] = None  # 新增协调器
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


class WebSocketChatServer:
    """WebSocket聊天服务器"""
    
    def __init__(self):
        self.app = FastAPI(title="苏丹游戏聊天服务器")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.rooms: Dict[str, ChatRoom] = {}
        self.setup_routes()
        
        # 后台任务将在应用启动时启动
        self._background_task = None
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.websocket("/ws/{room_id}")
        async def websocket_endpoint(websocket: WebSocket, room_id: str):
            await self.handle_websocket(websocket, room_id)
        
        @self.app.get("/")
        async def root():
            return {"message": "苏丹游戏聊天服务器运行中"}
        
        @self.app.on_event("startup")
        async def startup_event():
            # 启动后台任务
            self._background_task = asyncio.create_task(self.background_tasks())
        
        @self.app.get("/rooms")
        async def list_rooms():
            return {
                "rooms": [
                    {
                        "room_id": room.room_id,
                        "scene_name": room.scene_name,
                        "user_count": len(room.users),
                        "users": [
                            {
                                "username": user.username,
                                "role": user.role.value
                            } for user in room.users.values()
                        ]
                    } for room in self.rooms.values()
                ]
            }
        
        @self.app.get("/rooms/{room_id}/cards")
        async def get_available_cards(room_id: str):
            """获取房间可用的卡片列表"""
            from .cards import create_sample_cards
            
            if room_id in self.rooms:
                room = self.rooms[room_id]
                available_cards = create_sample_cards()
                
                # 检查触发条件
                if room.game_state:
                    for card in available_cards:
                        card.is_active = True  # 设为激活状态以便测试
                        if card.check_trigger_conditions(room.game_state.current_scene.scene_values):
                            card.can_be_used = True
                
                return {
                    "success": True,
                    "cards": [card.to_dict() for card in available_cards],
                    "scene_values": room.game_state.current_scene.scene_values if room.game_state else {}
                }
            
            return {"success": False, "message": "房间不存在"}
        
        @self.app.post("/rooms/{room_id}/card/activate")
        async def activate_card(room_id: str, card_data: Dict):
            """激活卡片到游戏状态"""
            if room_id in self.rooms:
                room = self.rooms[room_id]
                
                # 创建卡片对象
                from .cards import get_card_by_type
                card_type = CardType(card_data["card_type"])
                card = get_card_by_type(card_type)
                card.is_active = True
                
                # 添加到游戏状态
                if room.game_state:
                    room.game_state.active_cards.append(card)
                    room.card_activated = True
                    
                    # 通知房间内所有用户
                    await self.broadcast_to_room(room_id, {
                        "type": MessageType.SYSTEM_MESSAGE.value,
                        "content": f"🎴 卡片已激活：{card.title}",
                        "card_activated": card.to_dict()
                    })
                    
                    # 🎯 让旁白宣布任务目标
                    await self.announce_card_mission(room, card)
                    
                    return {"success": True, "message": "卡片激活成功", "card": card.to_dict()}
                
                return {"success": False, "message": "游戏状态未初始化"}
            
            return {"success": False, "message": "房间不存在"}
        
        @self.app.post("/rooms/{room_id}/card/use")
        async def use_card(room_id: str, use_data: Dict):
            """使用卡片"""
            if room_id in self.rooms:
                room = self.rooms[room_id]
                card_id = use_data.get("card_id")
                action = use_data.get("action", "使用")
                target = use_data.get("target", "")
                
                if room.game_state:
                    # 使用卡片工具
                    from .tools import card_usage_tool, set_game_state
                    set_game_state(room.game_state)
                    
                    result = card_usage_tool(card_id, action, target)
                    result_data = json.loads(result)
                    
                    # 如果有场景数值变化，广播更新
                    if result_data.get("scene_changes"):
                        await self.broadcast_scene_update(room)
                    
                    # 通知使用结果
                    await self.broadcast_to_room(room_id, {
                        "type": MessageType.SYSTEM_MESSAGE.value,
                        "content": f"🎴 卡片使用结果：{', '.join(result_data.get('consequences', []))}",
                        "card_usage_result": result_data
                    })
                    
                    return {"success": True, "result": result_data}
                
                return {"success": False, "message": "游戏状态未初始化"}
            
            return {"success": False, "message": "房间不存在"}
        
        @self.app.post("/rooms/{room_id}/follower_choice/trigger")
        async def trigger_follower_choice(room_id: str):
            """手动触发随从选择阶段"""
            if room_id in self.rooms:
                room = self.rooms[room_id]
                
                # 检查是否有随从玩家
                has_follower = any(user.role == UserRole.HUMAN_FOLLOWER for user in room.users.values())
                if not has_follower:
                    return {"success": False, "message": "房间内没有随从玩家"}
                
                # 检查游戏状态
                if not room.game_state:
                    return {"success": False, "message": "游戏状态未初始化"}
                
                from .models import GamePhase
                if room.game_state.current_phase == GamePhase.FOLLOWER_CHOICE:
                    return {"success": False, "message": "已经在随从选择阶段"}
                
                if room.game_state.current_phase == GamePhase.GAME_ENDED:
                    return {"success": False, "message": "游戏已结束"}
                
                # 触发随从选择阶段
                await self.trigger_follower_choice_phase(room)
                
                return {"success": True, "message": "随从选择阶段已触发"}
            
            return {"success": False, "message": "房间不存在"}
    
    async def handle_websocket(self, websocket: WebSocket, room_id: str):
        """处理WebSocket连接"""
        await websocket.accept()
        user = None
        
        try:
            # 等待用户加入信息
            join_data = await websocket.receive_json()
            
            if join_data.get("type") != "join":
                await websocket.send_json({"error": "首条消息必须是join类型"})
                return
            
            user = await self.handle_user_join(websocket, room_id, join_data)
            
            if not user:
                await websocket.send_json({"error": "加入房间失败"})
                return
            
            # 处理消息循环
            while True:
                data = await websocket.receive_json()
                await self.handle_message(user, data)
                
        except WebSocketDisconnect:
            if user:
                await self.handle_user_leave(user)
        except Exception as e:
            print(f"WebSocket错误: {e}")
            if user:
                await self.handle_user_leave(user)
    
    async def handle_user_join(self, websocket: WebSocket, room_id: str, join_data: Dict) -> Optional[ChatUser]:
        """处理用户加入"""
        try:
            # 检查必需字段
            if "username" not in join_data:
                await websocket.send_json({"error": "缺少用户名"})
                return None
            
            if "role" not in join_data:
                await websocket.send_json({"error": "缺少角色信息"})
                return None
            
            username = join_data["username"]
            
            # 验证角色值
            try:
                role = UserRole(join_data["role"])
            except ValueError:
                await websocket.send_json({"error": f"无效的角色: {join_data['role']}"})
                return None
            
            scene_name = join_data.get("scene_name", "brothel")
            
            # 创建用户
            user = ChatUser(
                user_id=str(uuid.uuid4()),
                websocket=websocket,
                username=username,
                role=role,
                room_id=room_id
            )
            
            # 创建或获取房间
            if room_id not in self.rooms:
                try:
                    room = await self.create_room(room_id, scene_name)
                except Exception as room_error:
                    await websocket.send_json({"error": f"创建房间失败: {str(room_error)}"})
                    return None
            else:
                room = self.rooms[room_id]
            
            # 检查角色冲突
            for existing_user in room.users.values():
                if existing_user.role == role and role != UserRole.SPECTATOR:
                    await websocket.send_json({
                        "error": f"角色 {role.value} 已被占用"
                    })
                    return None
            
            # 🔥 关键修复：如果是房间第一个用户，重置协调器对话历史
            if not room.users:  # 房间之前是空的
                if room.agent_coordinator:
                    room.agent_coordinator.conversation_history.clear()
                    print(f"🧠 房间 {room_id} 重置协调器对话历史（新用户加入空房间）")
            
            # 添加用户到房间
            room.users[user.user_id] = user
            
            # 发送加入成功消息
            await websocket.send_json({
                "type": "join_success",
                "user_id": user.user_id,
                "room_id": room_id,
                "scene_name": room.scene_name
            })
            
            # 广播用户加入消息
            await self.broadcast_to_room(room_id, {
                "type": MessageType.USER_JOIN.value,
                "username": username,
                "role": role.value,
                "timestamp": time.time()
            }, exclude_user=user.user_id)
            
            # 发送当前房间状态
            await self.send_room_state(user)
            
            print(f"用户 {username} 以角色 {role.value} 加入房间 {room_id}")
            return user
            
        except Exception as e:
            print(f"用户加入失败: {e}")
            await websocket.send_json({
                "error": f"加入房间失败: {str(e)}"
            })
            return None
    
    async def handle_user_leave(self, user: ChatUser):
        """处理用户离开"""
        room_id = user.room_id
        
        if room_id in self.rooms:
            room = self.rooms[room_id]
            
            # 移除用户
            if user.user_id in room.users:
                del room.users[user.user_id]
            
            # 移除暂停请求
            room.pause_requests.discard(user.user_id)
            
            # 广播用户离开消息
            await self.broadcast_to_room(room_id, {
                "type": MessageType.USER_LEAVE.value,
                "username": user.username,
                "role": user.role.value,
                "timestamp": time.time()
            })
            
            # 如果房间空了，立即停止所有智能体任务并删除房间
            if not room.users:
                # 🔥 关键修复：停止所有正在进行的智能体任务
                self._stop_all_agent_tasks(room)
                
                # 🔥 关键修复：清空协调器对话历史（为下次使用准备）
                if room.agent_coordinator:
                    room.agent_coordinator.conversation_history.clear()
                    print(f"🧠 房间 {room_id} 清空协调器对话历史")
                
                del self.rooms[room_id]
                print(f"房间 {room_id} 已删除（无用户），所有智能体任务已停止")
            
            print(f"用户 {user.username} 离开房间 {room_id}")
    
    async def handle_message(self, user: ChatUser, data: Dict):
        """处理用户消息"""
        message_type = data.get("type")
        room = self.rooms[user.room_id]
        
        # 更新用户活动时间
        user.last_activity = time.time()
        
        if message_type == "chat_message":
            await self.handle_chat_message(user, data)
        
        elif message_type == "pause_request":
            await self.handle_pause_request(user, data)
        
        elif message_type == "resume_request":
            await self.handle_resume_request(user, data)
        
        elif message_type == "typing_start":
            await self.handle_typing_start(user)
        
        elif message_type == "typing_stop":
            await self.handle_typing_stop(user)
        
        elif message_type == "follower_choice_response":
            await self.handle_follower_choice_response(user, data)
        
        else:
            print(f"未知消息类型: {message_type}")
    
    async def handle_chat_message(self, user: ChatUser, data: Dict):
        """处理聊天消息 - 简化版本"""
        content = data.get("content", "").strip()
        if not content:
            return
        
        room = self.rooms[user.room_id]
        
        # 🎮 检查游戏状态
        if room.conversation_count >= room.max_conversations:
            await self.send_to_user(user, {
                "type": MessageType.SYSTEM_MESSAGE.value,
                "content": "🔚 游戏已结束（达到20轮对话限制）",
                "timestamp": time.time()
            })
            return

        # 如果在随从选择阶段，只有随从角色能发言
        if room.is_follower_choice_phase:
            if user.role != UserRole.HUMAN_FOLLOWER:
                await self.send_to_user(user, {
                    "type": MessageType.SYSTEM_MESSAGE.value,
                    "content": "⏳ 正在等待随从做出选择...",
                    "timestamp": time.time()
                })
                return
            
            # 处理随从选择
            await self.process_follower_choice_input(user, content)
            return
            
        # 增加对话计数
        room.conversation_count += 1
        
        # 记录人类消息到游戏状态的对话历史
        if room.game_state and room.game_state.current_scene:
            # 根据用户角色确定发言者名称
            role_to_agent = {
                UserRole.HUMAN_FOLLOWER: "follower",
                UserRole.HUMAN_COURTESAN: "courtesan", 
                UserRole.HUMAN_MADAM: "madam"
            }
            
            corresponding_agent_type = role_to_agent.get(user.role)
            if corresponding_agent_type:
                # 如果用户扮演智能体角色，使用角色名称而不是用户名
                agent_display_name = self.get_agent_display_name(corresponding_agent_type)
                speaker_name = f"{agent_display_name} (由{user.username}扮演)"
                context_type = f"人类扮演{corresponding_agent_type}角色"
            else:
                # 旁观者或其他角色
                speaker_name = f"{user.username} ({self.get_role_display_name(user.role)})"
                context_type = "人类玩家发言"
            
            room.game_state.current_scene.add_conversation(
                speaker_name, content, context_type
            )
            
            # 如果用户扮演的是智能体角色，将其内容也添加到对应智能体的上下文中
            role_to_agent = {
                UserRole.HUMAN_FOLLOWER: "follower",
                UserRole.HUMAN_COURTESAN: "courtesan", 
                UserRole.HUMAN_MADAM: "madam"
            }
            
            corresponding_agent_type = role_to_agent.get(user.role)
            if corresponding_agent_type and room.agent_manager:
                # 获取对应的智能体
                agent = room.agent_manager.get_agent(corresponding_agent_type)
                if agent:
                    # 将人类角色扮演的内容添加到智能体的角色理解中
                    # 这样智能体在后续回应时会考虑人类的扮演风格
                    if not hasattr(agent, 'human_role_context'):
                        agent.human_role_context = []
                    
                    agent.human_role_context.append({
                        'username': user.username,
                        'content': content,
                        'timestamp': time.time(),
                        'context_type': 'human_role_play'
                    })
                    
                    # 保持上下文长度合理（最多保留10条记录）
                    if len(agent.human_role_context) > 10:
                        agent.human_role_context = agent.human_role_context[-10:]
        
        # 创建消息
        message = {
            "type": MessageType.CHAT_MESSAGE.value,
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "content": content,
            "timestamp": time.time(),
            "round_info": f"第{room.conversation_count}/{room.max_conversations}轮"
        }
        
        # 广播消息
        await self.broadcast_to_room(user.room_id, message)
        
        # 更新房间状态
        room.last_message_time = time.time()
        
        # 🎯 检查是否需要触发随从选择
        if self.should_trigger_follower_choice(room):
            await self.trigger_follower_choice_simple(room)
            return

        # 检查游戏结束条件
        if room.conversation_count >= room.max_conversations:
            await self.end_game_due_to_limit(room)
            return

        # 如果是人类扮演的角色，触发AI智能体回应
        if user.role in [UserRole.HUMAN_FOLLOWER, UserRole.HUMAN_COURTESAN, UserRole.HUMAN_MADAM]:
            # 使用新的协调器来生成智能体回应
            await self.coordinate_agent_responses(room, content, user)
    
    def get_role_display_name(self, role: UserRole) -> str:
        """获取角色显示名称"""
        role_names = {
            UserRole.HUMAN_FOLLOWER: "人类随从",
            UserRole.HUMAN_COURTESAN: "人类妓女", 
            UserRole.HUMAN_MADAM: "人类老鸨",
            UserRole.SPECTATOR: "旁观者"
        }
        return role_names.get(role, role.value)
    
    def get_agent_display_name(self, agent_type: str) -> str:
        """获取智能体显示名称"""
        agent_names = {
            "narrator": "旁白者",
            "follower": "随从",
            "courtesan": "妓女",
            "madam": "老鸨",
            "merchant": "商人"
        }
        return agent_names.get(agent_type, agent_type)
    
    async def coordinate_agent_responses(self, room: ChatRoom, user_message: str, user: ChatUser):
        """协调智能体响应 - 使用新的协调器"""
        if not room.agent_manager or not room.agent_coordinator or room.is_paused:
            return
        
        try:
            # 根据用户角色确定发言者身份
            role_to_agent = {
                UserRole.HUMAN_FOLLOWER: "follower",
                UserRole.HUMAN_COURTESAN: "courtesan", 
                UserRole.HUMAN_MADAM: "madam"
            }
            
            corresponding_agent_type = role_to_agent.get(user.role)
            if corresponding_agent_type:
                # 用户扮演智能体角色，将消息作为该角色的发言添加到历史中
                agent_display_name = self.get_agent_display_name(corresponding_agent_type)
                room.agent_coordinator.add_to_history(
                    "agent_message", user_message, 
                    agent_name=f"{agent_display_name}(由{user.username}扮演)"
                )
            else:
                # 用户是旁观者，作为普通聊天消息
                room.agent_coordinator.add_to_history(
                    "chat_message", user_message, username=user.username
                )
            
            # 获取可用的智能体 - 注意：不排除人类扮演的角色！
            # 因为用户的输入已经代表了该角色的发言，其他智能体应该能够回应
            active_agents = room.agent_manager.get_active_agents()
            
            # 如果用户扮演某个角色，优先让其他角色智能体回应
            # 但不完全排除该角色的AI智能体，让AI学习用户的扮演风格
            if corresponding_agent_type:
                # 优先选择其他智能体，但保留该角色智能体参与的可能性
                available_agents = {}
                for agent_type, agent in active_agents.items():
                    if agent_type != corresponding_agent_type:
                        # 其他智能体优先级高
                        available_agents[agent_type] = agent
                    else:
                        # 用户扮演的角色智能体仍可参与，但优先级较低
                        # 这样AI可以学习用户的角色扮演风格并补充
                        import random
                        if random.random() < 0.3:  # 30%概率让AI版本的该角色也参与
                            available_agents[agent_type] = agent
            else:
                # 旁观者发言，所有智能体都可以回应
                available_agents = active_agents
            
            if not available_agents:
                return
            
            # 确保全局游戏状态最新（关键修复！）
            if room.game_state:
                from .tools import set_game_state
                set_game_state(room.game_state)
            
            # 记录协调器调用前的场景数值状态（关键修复！）
            old_scene_values_coord = None
            if room.game_state and room.game_state.current_scene:
                old_scene_values_coord = room.game_state.current_scene.scene_values.copy()
            
            # 使用协调器生成响应
            coordinated_responses = await room.agent_coordinator.coordinate_response(
                user_message, available_agents
            )
            
            if not coordinated_responses:
                return
            
            # 按质量顺序发送响应，添加较短延迟以加快故事推进
            for i, response in enumerate(coordinated_responses):
                # 延迟发送，第一个响应最快，但整体更快
                delay = 0.5 + i * 0.8  # 0.5s, 1.3s, 2.1s...
                # 只有第一个响应需要检查场景数值变化
                old_values = old_scene_values_coord if i == 0 else None
                asyncio.create_task(
                    self.send_coordinated_response(room, response, delay, old_values)
                )
                
        except Exception as e:
            print(f"协调智能体响应时出错: {e}")
            # 回退到原有的简单响应机制
            await self.schedule_story_driven_response(room, user.role)
    
    async def send_coordinated_response(self, room: ChatRoom, response, delay: float, old_scene_values: Optional[Dict] = None):
        """发送协调的响应"""
        await asyncio.sleep(delay)
        
        # 检查房间是否还存在且未被暂停
        if (room.room_id not in self.rooms or room.is_paused):
            return
        
        try:
            # 添加响应到协调器历史
            room.agent_coordinator.add_to_history(
                "agent_message", response.content, agent_name=response.agent_name
            )
            
            # 记录AI消息到游戏状态的对话历史
            if room.game_state and room.game_state.current_scene:
                room.game_state.current_scene.add_conversation(
                    response.agent_name, response.content, 
                    f"AI智能体回应 - {response.agent_type}"
                )
            
            # 发送智能体消息
            message = {
                "type": MessageType.AGENT_MESSAGE.value,
                "agent_type": response.agent_type,
                "agent_name": response.agent_name,
                "content": response.content,
                "timestamp": response.timestamp,
                "priority": response.priority.value,
                "quality_scores": {
                    "context_relevance": response.context_relevance,
                    "uniqueness_score": response.uniqueness_score,
                    "story_progress_value": response.story_progress_value
                }
            }
            
            await self.broadcast_to_room(room.room_id, message)
            
            # 检查场景数值是否发生变化，如果有变化则广播更新
            if old_scene_values and room.game_state and room.game_state.current_scene:
                new_scene_values = room.game_state.current_scene.scene_values
                changes = {}
                
                print(f"🔍 协调器场景数值变化检查:")
                print(f"   旧值: {old_scene_values}")
                print(f"   新值: {new_scene_values}")
                
                for key, new_value in new_scene_values.items():
                    old_value = old_scene_values.get(key, 0)
                    if old_value != new_value:
                        changes[key] = {
                            "old": old_value,
                            "new": new_value,
                            "change": new_value - old_value
                        }
                        print(f"   📊 {key}: {old_value} → {new_value} (变化: {new_value - old_value})")
                
                # 如果有数值变化，广播场景更新
                if changes:
                    scene_update_message = {
                        "type": MessageType.SCENE_UPDATE.value,
                        "scene_values": new_scene_values,
                        "changes": changes,
                        "timestamp": time.time()
                    }
                    await self.broadcast_to_room(room.room_id, scene_update_message)
                    print(f"🎮 协调器场景数值更新: {changes}")
                else:
                    print("   ❌ 协调器没有检测到数值变化")
            
            room.last_message_time = time.time()
            
            # 触发后续的自动对话 - 提高概率让智能体继续对话
            import random
            if random.random() < 0.8:  # 80% 概率继续自动对话
                await self.schedule_next_agent_response(room)
            
        except Exception as e:
            print(f"发送协调响应时出错: {e}")
    
    async def schedule_story_driven_response(self, room: ChatRoom, human_role: UserRole):
        """安排故事驱动的AI回应"""
        if not room.agent_manager or room.is_paused:
            return
        
        # 获取可用的智能体（排除人类扮演的角色）
        available_agents = []
        active_agents = room.agent_manager.get_active_agents()
        
        # 映射人类角色到智能体类型
        role_to_agent = {
            UserRole.HUMAN_FOLLOWER: "follower",
            UserRole.HUMAN_COURTESAN: "courtesan", 
            UserRole.HUMAN_MADAM: "madam"
        }
        
        excluded_agent = role_to_agent.get(human_role)
        
        for agent_type, agent in active_agents.items():
            if agent_type != excluded_agent:
                available_agents.append(agent_type)
        
        if not available_agents:
            return
        
        # 使用策略性智能体选择，确保均衡发言
        next_agent = self._select_next_agent_strategically(room, available_agents, human_role)
        
        # 故事驱动的回应延迟进一步缩短（0.5-2秒）
        delay = 0
        
        # 安排延迟回应
        asyncio.create_task(self.delayed_agent_response(room, next_agent, delay))
    
    async def handle_pause_request(self, user: ChatUser, data: Dict):
        """处理暂停请求"""
        room = self.rooms[user.room_id]
        duration = data.get("duration", 10)  # 默认暂停10秒
        
        # 添加暂停请求
        room.pause_requests.add(user.user_id)
        user.pause_until = time.time() + duration
        
        # 如果房间没有被暂停，设置暂停
        if not room.is_paused:
            room.is_paused = True
            await self.broadcast_to_room(user.room_id, {
                "type": MessageType.SYSTEM_MESSAGE.value,
                "content": f"{user.username} 正在输入中...",
                "is_paused": True,
                "timestamp": time.time()
            }, exclude_user=user.user_id)
    
    async def handle_resume_request(self, user: ChatUser, data: Dict):
        """处理恢复请求"""
        room = self.rooms[user.room_id]
        
        # 移除暂停请求
        room.pause_requests.discard(user.user_id)
        user.pause_until = 0
        
        # 如果没有其他暂停请求，恢复对话
        if not room.pause_requests:
            room.is_paused = False
            await self.broadcast_to_room(user.room_id, {
                "type": MessageType.SYSTEM_MESSAGE.value,
                "content": "对话已恢复",
                "is_paused": False,
                "timestamp": time.time()
            })
    
    async def handle_typing_start(self, user: ChatUser):
        """处理开始输入"""
        if not user.is_typing:
            user.is_typing = True
            await self.broadcast_to_room(user.room_id, {
                "type": MessageType.USER_TYPING.value,
                "username": user.username,
                "timestamp": time.time()
            }, exclude_user=user.user_id)
    
    async def handle_typing_stop(self, user: ChatUser):
        """处理停止输入"""
        if user.is_typing:
            user.is_typing = False
            await self.broadcast_to_room(user.room_id, {
                "type": MessageType.USER_STOP_TYPING.value,
                "username": user.username,
                "timestamp": time.time()
            }, exclude_user=user.user_id)
    
    async def handle_follower_choice_response(self, user: ChatUser, data: Dict):
        """处理随从选择回应"""
        if user.role != UserRole.HUMAN_FOLLOWER:
            await user.websocket.send_json({
                "type": "error",
                "message": "只有随从玩家可以做出选择"
            })
            return
        
        room = self.rooms[user.room_id]
        if not room.game_state:
            await user.websocket.send_json({
                "type": "error", 
                "message": "游戏状态未初始化"
            })
            return
        
        from .models import GamePhase
        if room.game_state.current_phase != GamePhase.FOLLOWER_CHOICE:
            await user.websocket.send_json({
                "type": "error",
                "message": "当前不在随从选择阶段"
            })
            return
        
        choice_id = data.get("choice_id")
        custom_input = data.get("custom_input", "").strip()
        
        # 处理选择结果
        await self.process_follower_choice(room, user, choice_id, custom_input)
    
    async def create_room(self, room_id: str, scene_name: str) -> ChatRoom:
        """创建聊天房间"""
        # 创建游戏状态
        initial_scene = SceneState(
            location="游戏场景",
            characters_present=[],
            atmosphere="神秘",
            time_of_day="夜晚"
        )
        game_state = GameState(current_scene=initial_scene)
        
        # 创建智能体管理器
        agent_manager = AgentManager()
        agent_manager.set_game_state(game_state)
        
        # 设置场景
        success = agent_manager.setup_scene(scene_name)
        if not success:
            print(f"警告: 场景 {scene_name} 设置失败，使用默认场景")
            agent_manager.setup_scene("brothel")
        
        # 创建智能体协调器（每个房间独立的对话历史）
        agent_coordinator = AgentCoordinator(llm=agent_manager.llm)
        print(f"🧠 为房间 {room_id} 创建全新的协调器，对话历史已清空")
        
        room = ChatRoom(
            room_id=room_id,
            scene_name=scene_name,
            agent_manager=agent_manager,
            agent_coordinator=agent_coordinator,
            game_state=game_state
        )
        
        self.rooms[room_id] = room
        print(f"创建房间 {room_id}，场景: {scene_name}")
        return room
    
    async def broadcast_to_room(self, room_id: str, message: Dict, exclude_user: Optional[str] = None):
        """向房间内所有用户广播消息"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        disconnected_users = []
        
        for user_id, user in room.users.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await user.websocket.send_json(message)
            except Exception as e:
                print(f"发送消息失败给用户 {user.username}: {e}")
                disconnected_users.append(user_id)
        
        # 清理断开连接的用户
        for user_id in disconnected_users:
            if user_id in room.users:
                await self.handle_user_leave(room.users[user_id])
    
    async def send_room_state(self, user: ChatUser):
        """发送房间状态给用户"""
        room = self.rooms[user.room_id]
        
        # 获取激活的卡片信息
        active_cards = []
        if room.game_state and room.game_state.active_cards:
            active_cards = [card.to_dict() for card in room.game_state.active_cards]
        
        state = {
            "type": "room_state",
            "room_id": room.room_id,
            "scene_name": room.scene_name,
            "users": [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "role": u.role.value,
                    "is_typing": u.is_typing
                } for u in room.users.values()
            ],
            "is_paused": room.is_paused,
            "active_cards": active_cards,
            "scene_values": room.game_state.current_scene.scene_values if room.game_state else {}
        }
        
        await user.websocket.send_json(state)
    
    async def broadcast_scene_update(self, room: ChatRoom):
        """广播场景数值更新"""
        if not room.game_state:
            return
            
        scene_values = room.game_state.current_scene.scene_values
        
        # 检查卡片触发条件
        available_cards = room.game_state.check_card_triggers()
        
        update_message = {
            "type": "scene_update",
            "scene_values": scene_values,
            "available_cards": [card.to_dict() for card in available_cards]
        }
        
        await self.broadcast_to_room(room.room_id, update_message)
    
    async def schedule_next_agent_response(self, room: ChatRoom, exclude_role: Optional[UserRole] = None):
        """安排下一个智能体回应"""
        if not room.agent_manager or room.is_paused:
            return
        
        # 获取可用的智能体（排除人类扮演的角色）
        available_agents = []
        active_agents = room.agent_manager.get_active_agents()
        
        # 映射人类角色到智能体类型
        role_to_agent = {
            UserRole.HUMAN_FOLLOWER: "follower",
            UserRole.HUMAN_COURTESAN: "courtesan", 
            UserRole.HUMAN_MADAM: "madam"
        }
        
        excluded_agent = role_to_agent.get(exclude_role) if exclude_role else None
        
        for agent_type, agent in active_agents.items():
            if agent_type != excluded_agent:
                available_agents.append(agent_type)
        
        if not available_agents:
            return
        
        # 使用轮询策略选择智能体，确保均衡发言
        import random
        next_agent = self._select_next_agent_strategically(room, available_agents, exclude_role)
        delay = random.uniform(0.5, 1.5)  # 减少延迟提高响应速度
        
        # 安排延迟回应
        asyncio.create_task(self.delayed_agent_response(room, next_agent, 0))
    
    def _select_next_agent_strategically(self, room: ChatRoom, available_agents: List[str], exclude_role: Optional[UserRole] = None) -> str:
        """策略性选择下一个智能体发言"""
        if not available_agents:
            return available_agents[0] if available_agents else "narrator"
        
        # 核心角色优先级顺序：旁白 -> 老鸨 -> 妓女 -> 随从 -> 商人
        priority_order = ["narrator", "madam", "courtesan", "follower", "merchant"]
        
        # 获取最近发言的智能体历史
        recent_speakers = []
        if room.game_state and room.game_state.current_scene:
            # 分析最近的对话，提取AI智能体发言者
            for msg in room.game_state.current_scene.conversation_history[-6:]:  # 看最近6条
                speaker = msg.get("speaker", "")
                context = msg.get("context", "")
                if "AI智能体回应" in context:
                    # 从context中提取智能体类型
                    if " - " in context:
                        agent_type = context.split(" - ")[-1]
                        recent_speakers.append(agent_type)
        
        # 如果有最近发言历史，尽量避免重复
        if recent_speakers:
            last_speaker = recent_speakers[-1] if recent_speakers else None
            
            # 检查每个重要角色的发言次数
            speaker_counts = {}
            for speaker in recent_speakers[-6:]:  # 检查最近6次发言
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            # 找出发言最少的重要角色
            important_agents = ["narrator", "madam", "courtesan"]  # 重要角色
            available_important = [a for a in important_agents if a in available_agents]
            
            if available_important:
                # 按发言次数排序，优先选择发言最少的
                available_important.sort(key=lambda x: speaker_counts.get(x, 0))
                selected = available_important[0]
                print(f"🎯 策略选择智能体: {selected} (平衡发言, 当前次数: {speaker_counts.get(selected, 0)})")
                return selected
            
            # 如果没有重要角色可用，构建候选列表，排除最近发言的智能体
            candidates = []
            for agent_type in priority_order:
                if agent_type in available_agents and agent_type != last_speaker:
                    candidates.append(agent_type)
            
            # 如果有候选者，优先选择
            if candidates:
                # 在候选者中按优先级选择
                for agent_type in priority_order:
                    if agent_type in candidates:
                        print(f"🎯 策略选择智能体: {agent_type} (避免重复: {last_speaker})")
                        return agent_type
        
        # 如果没有历史或需要回退，按优先级选择第一个可用的
        for agent_type in priority_order:
            if agent_type in available_agents:
                print(f"🎯 优先级选择智能体: {agent_type}")
                return agent_type
        
        # 最后回退到随机选择
        import random
        selected = random.choice(available_agents)
        print(f"🎯 随机选择智能体: {selected}")
        return selected
    
    async def delayed_agent_response(self, room: ChatRoom, agent_type: str, delay: float):
        """延迟的智能体回应"""
        await asyncio.sleep(delay)
        
        # 检查房间是否还存在且未被暂停
        if (room.room_id not in self.rooms or 
            room.is_paused):
            return
        
        # 检查这个智能体是否已经在生成响应中（防止重复调用）
        if room.agent_locks.get(agent_type, False):
            print(f"智能体 {agent_type} 已在生成响应中，跳过重复调用")
            return
        
        # 设置锁
        room.agent_locks[agent_type] = True
        
        try:
            # 让指定智能体生成回应
            agent = room.agent_manager.get_agent(agent_type)
            if not agent:
                return
            
            # 确保全局游戏状态最新（关键修复！）
            if room.game_state:
                from .tools import set_game_state
                set_game_state(room.game_state)
            
            # 在智能体生成响应前记录场景数值状态（关键修复！）
            old_scene_values = None
            if room.game_state and room.game_state.current_scene:
                old_scene_values = room.game_state.current_scene.scene_values.copy()
            
            # 使用真正的CrewAI智能体生成回应
            response_content = await self.generate_agent_response(room, agent_type)
            
            if response_content:
                
                # 记录AI消息到游戏状态的对话历史
                if room.game_state and room.game_state.current_scene:
                    display_name = self.get_agent_display_name(agent_type)
                    room.game_state.current_scene.add_conversation(
                        display_name, response_content, f"AI智能体回应 - {agent_type}"
                    )
                
                # 发送智能体消息 - 统一使用中文显示名称
                display_name = self.get_agent_display_name(agent_type)
                message = {
                    "type": MessageType.AGENT_MESSAGE.value,
                    "agent_type": agent_type,
                    "agent_name": display_name,
                    "content": response_content,
                    "timestamp": time.time()
                }
                
                await self.broadcast_to_room(room.room_id, message)
                
                # 检查场景数值是否发生变化，如果有变化则广播更新
                if old_scene_values and room.game_state and room.game_state.current_scene:
                    new_scene_values = room.game_state.current_scene.scene_values
                    changes = {}
                    
                    print(f"🔍 单独智能体场景数值变化检查:")
                    print(f"   旧值: {old_scene_values}")
                    print(f"   新值: {new_scene_values}")
                    
                    for key, new_value in new_scene_values.items():
                        old_value = old_scene_values.get(key, 0)
                        if old_value != new_value:
                            changes[key] = {
                                "old": old_value,
                                "new": new_value,
                                "change": new_value - old_value
                            }
                            print(f"   📊 {key}: {old_value} → {new_value} (变化: {new_value - old_value})")
                    
                    # 如果有数值变化，广播场景更新
                    if changes:
                        scene_update_message = {
                            "type": MessageType.SCENE_UPDATE.value,
                            "scene_values": new_scene_values,
                            "changes": changes,
                            "timestamp": time.time()
                        }
                        await self.broadcast_to_room(room.room_id, scene_update_message)
                        print(f"🎮 场景数值更新: {changes}")
                        
                        # 🎯 检查是否满足随从选择触发条件
                        await self.check_follower_choice_trigger(room)
                    else:
                        print("   ❌ 没有检测到数值变化")
                
                # 更新房间状态
                room.last_message_time = time.time()
                
                # 继续故事发展 - 提高概率让其他智能体也回应，加快故事推进
                import random
                if random.random() < 0.85:  # 85% 概率继续链式对话
                    # 减少延迟，加快对话节奏
                    await asyncio.sleep(random.uniform(1, 2))
                    await self.schedule_next_agent_response(room)
        
        except Exception as e:
            print(f"智能体回应生成失败: {e}")
        
        finally:
            # 释放锁
            room.agent_locks[agent_type] = False
    
    async def generate_agent_response(self, room: ChatRoom, agent_type: str) -> Optional[str]:
        """生成智能体回应 - 使用真正的CrewAI智能体"""
        try:
            agent = room.agent_manager.get_agent(agent_type)
            if not agent:
                print(f"❌ 找不到智能体: {agent_type}")
                return None
            
            # 获取最近的对话历史
            recent_messages = self.get_recent_conversation_context(room, limit=10)
            
            # 构建对话上下文
            context = self._build_agent_context(room, recent_messages, agent_type)
            
            # 使用真正的CrewAI智能体生成响应
            response = await self._call_crewai_agent(agent, context)
            
            print(f"✅ 智能体 {agent_type} 成功生成响应: {len(response)} 字符")
            return response
                
        except Exception as e:
            print(f"❌ 智能体 {agent_type} 生成回应失败: {type(e).__name__}: {e}")
            # 使用fallback响应确保用户体验
            fallback = self._generate_fallback_response(agent_type)
            print(f"🔄 使用备用响应: {fallback}")
            return fallback
    
    def get_recent_conversation_context(self, room: ChatRoom, limit: int = 10) -> List[Dict]:
        """获取最近的对话上下文"""
        if not room.game_state or not room.game_state.current_scene:
            return []
        
        conversation_history = room.game_state.current_scene.conversation_history
        return conversation_history[-limit:] if conversation_history else []
    
    def _build_agent_context(self, room: ChatRoom, recent_messages: List[Dict], agent_type: str) -> str:
        """为智能体构建对话上下文"""
        if not room.game_state or not room.game_state.current_scene:
            return "对话开始。"
        
        scene = room.game_state.current_scene
        
        # 构建对话历史文本
        conversation_text = "=== 最近对话 ===\n"
        for msg in recent_messages[-8:]:  # 取最近8条
            speaker = msg.get("speaker", "未知")
            content = msg.get("content", "")
            conversation_text += f"[{speaker}]: {content}\n"
        
        # 构建场景状态文本
        scene_info = f"""
=== 当前场景 ===
地点：{scene.location}
氛围：{scene.atmosphere}
时间：{scene.time_of_day}
在场角色：{', '.join(scene.characters_present)}

场景数值：
- 紧张度：{scene.scene_values.get('紧张度', 0)}
- 暧昧度：{scene.scene_values.get('暧昧度', 0)}
- 危险度：{scene.scene_values.get('危险度', 0)}
- 金钱消费：{scene.scene_values.get('金钱消费', 0)}
"""
        
        # 构建活动卡牌信息
        card_info = ""
        if room.active_card:
            card_info = f"""
=== 当前任务 ===
卡牌：{room.active_card.title}
描述：{room.active_card.description}
"""
        
        # 检查是否有用户扮演的角色信息
        human_role_info = ""
        role_tips = ""
        
        # 查找当前房间中是否有用户扮演相同角色
        for user in room.users.values():
            role_to_agent = {
                UserRole.HUMAN_FOLLOWER: "follower",
                UserRole.HUMAN_COURTESAN: "courtesan", 
                UserRole.HUMAN_MADAM: "madam"
            }
            user_agent_type = role_to_agent.get(user.role)
            if user_agent_type == agent_type:
                human_role_info = f"\n⚠️ 注意：有真人玩家 {user.username} 正在扮演{self.get_agent_display_name(agent_type)}角色。"
                role_tips = f"""
特别提示：
- 你可能需要与真人玩家扮演的{self.get_agent_display_name(agent_type)}互动或呼应
- 避免重复真人玩家刚说过的内容
- 可以补充、延续或回应真人玩家的角色扮演
- 保持角色的一致性，但允许不同的表现风格
"""
                break
        
        # 根据智能体类型构建不同的任务要求
        if agent_type == "narrator":
            # 旁白者：负责场景描述和故事推动
            task_description = """=== 你的任务 ===
作为旁白者，你负责：
1. 描述场景氛围和环境变化
2. 叙述角色的内心活动和微妙表情
3. 推动故事发展，制造转折
4. 控制游戏节奏和张力
5. 可以修改场景数值（紧张度、暧昧度、危险度、金钱消费）

回应要求：
- 50-150字的场景描述或叙述
- 富有诗意和东方神秘色彩
- 营造沉浸感，让读者身临其境
- 不要进行角色对话，专注于叙述"""

        elif agent_type == "follower":
            # 随从：角色对话 + 数值修改能力
            task_description = f"""=== 你的任务 ===
作为随从 - {self.get_agent_display_name(agent_type)}，你负责：
1. 进行角色对话，直接说出随从的话语
2. 执行主人的任务，与其他角色互动
3. 可以通过行动影响场景数值

回应要求：
- 30-100字的直接对话
- 保持随从身份的忠诚和谨慎
- 不要描述场景背景或环境
- 不要叙述行动或氛围，只说话"""

        else:
            # 其他角色（妓女、老鸨等）：只进行角色对话
            task_description = f"""=== 你的任务 ===
作为{self.get_agent_display_name(agent_type)}，你负责：
1. 进行角色对话，表达角色的想法和情感
2. 与其他角色互动，推进人物关系
3. 保持角色的个性和立场

回应要求：
- 30-100字的角色对话
- 保持角色身份的一致性
- 不要描述场景背景或环境，专注于对话
- 不要叙述气氛或他人行为，只表达自己的话语和直接行动"""

        # 构建完整上下文
        full_context = f"""
{conversation_text}
{scene_info}
{card_info}
{human_role_info}

{task_description}
{role_tips}

请直接给出你的回应内容，不需要任何前缀或解释。
"""
        return full_context

    async def _call_crewai_agent(self, agent, context: str) -> str:
        """调用CrewAI智能体生成响应 - 使用真正的CrewAI工具系统"""
        import os
        from crewai import Task, Crew
        from .tools import set_game_state
        
        # 禁用CrewAI遥测避免网络错误
        os.environ["OTEL_SDK_DISABLED"] = "true"
        
        try:
            agent_instance = agent.get_agent_instance()
            
            # 确保全局GameState是最新的（关键修复！）
            if hasattr(agent, 'tools_manager') and hasattr(agent.tools_manager, 'game_state'):
                set_game_state(agent.tools_manager.game_state)
            
            # 构建简化的任务描述
            task_prompt = f"""
{context}

请根据你的角色身份和以上情况，生成一段自然的回应。

要求：
1. 严格保持你的角色身份
2. 50-150字的简洁回应  
3. 如需修改场景数值，请使用你的工具
4. 推动剧情发展
5. 不要重复之前说过的话

请直接给出你的回应内容。
"""
            
            # 创建单一任务
            task = Task(
                description=task_prompt,
                expected_output="角色的自然回应，可能包含工具调用",
                agent=agent_instance
            )
            
            # 创建只包含当前智能体的团队
            crew = Crew(
                agents=[agent_instance],
                tasks=[task],
                verbose=False,  # 减少输出噪音
                process_type="sequential",
                max_iter=1  # 限制迭代次数
            )
            
            # 执行任务 - 添加超时保护
            def run_crew():
                try:
                    result = crew.kickoff()
                    if hasattr(result, 'raw'):
                        # 如果是CrewAI的TaskOutput对象，取raw内容
                        response_text = str(result.raw).strip()
                    else:
                        response_text = str(result).strip()
                    
                    # 基本有效性检查
                    if not response_text or len(response_text) < 3:
                        raise ValueError(f"响应内容无效: '{response_text}'")
                    
                    return response_text
                except Exception as e:
                    print(f"❌ Crew执行内部错误: {type(e).__name__}: {e}")
                    # 记录更详细的错误信息
                    import traceback
                    print(f"完整错误堆栈: {traceback.format_exc()}")
                    raise
            
            # 使用asyncio执行器，添加超时
            try:
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, run_crew),
                    timeout=30.0  # 30秒超时
                )
            except asyncio.TimeoutError:
                raise Exception("智能体响应超时（30秒）")
            
            # 清理可能的工具调用残留文本
            response = self._clean_tool_artifacts(response)
            
            # 最终检查
            if not response or len(response.strip()) < 3:
                raise ValueError(f"清理后响应仍然无效: '{response}'")
            
            return response.strip()
            
        except Exception as e:
            print(f"❌ CrewAI调用完全失败: {type(e).__name__}: {e}")
            # 记录详细信息用于调试
            agent_type = getattr(agent, 'agent_type', 'unknown')
            print(f"   智能体类型: {agent_type}")
            print(f"   上下文长度: {len(context) if context else 0}")
            # 抛出异常，让上层的generate_agent_response处理fallback
            raise e

    def _clean_tool_artifacts(self, response: str) -> str:
        """清理响应中的工具调用残留文本"""
        import re
        
        # 移除双大括号JSON格式的工具调用文本（如 {{"action": "改变数值", ...}}）
        response = re.sub(r'\{\{[^}]*"action"[^}]*\}\}', '', response)
        
        # 移除单大括号JSON格式的工具调用文本（如 {"action": "改变数值", ...}）
        response = re.sub(r'\{[^}]*"action"[^}]*\}', '', response)
        
        # 移除其他可能的工具调用格式
        response = re.sub(r'action\s*[:=]\s*["\'][^"\']*["\']', '', response)
        response = re.sub(r'parameter\s*[:=]\s*["\'][^"\']*["\']', '', response)
        response = re.sub(r'value\s*[:=]\s*["\'][^"\']*["\']', '', response)
        
        # 移除包含"改变数值"、"触发事件"等工具相关关键词的行
        response = re.sub(r'.*(?:改变数值|触发事件|使用工具|tool|Tool).*', '', response)
        
        # 清理多余的空白和换行
        response = re.sub(r'\s+', ' ', response)
        response = response.strip()
        
        return response
    
    def _generate_fallback_response(self, agent_type: str) -> str:
        """生成备用响应（仅在CrewAI失败时使用）"""
        import random
        import time
        
        # 使用时间戳让回应更加多样化
        timestamp_factor = int(time.time()) % 100
        
        fallback_responses = {
            "narrator": [
                f"夜色更深了，烛光在轻风中摇曳不定... ({timestamp_factor})",
                f"空气中弥漫着神秘的气息，预示着即将发生的事情... ({timestamp_factor})",
                f"这个地方充满了说不尽的秘密，每一个角落都可能隐藏着惊喜... ({timestamp_factor})",
                f"突然，远处传来了一阵轻微的声响... ({timestamp_factor})",
                f"烛影摇曳间，似乎有什么东西在暗中观察着一切... ({timestamp_factor})",
                f"气氛变得微妙起来，仿佛有无形的力量在操控着局面... ({timestamp_factor})"
            ],
            "courtesan": [
                f"妾身在此恭候已久，公子终于来了... ({timestamp_factor})",
                f"公子看起来有些心事重重呢，不如说与妾身听听？ ({timestamp_factor})",
                f"这夜色如此迷人，正适合谈心... ({timestamp_factor})",
                f"妾身略通音律，不知公子可有雅兴一听？ ({timestamp_factor})",
                f"公子远道而来，想必是为了什么要紧事吧... ({timestamp_factor})"
            ],
            "madam": [
                f"客官，老身这里规矩多着呢，还望遵守... ({timestamp_factor})",
                f"有什么需要老身帮忙的吗？这里什么都有... ({timestamp_factor})",
                f"我们这里可是正经生意，童叟无欺... ({timestamp_factor})",
                f"客官眼光不错，老身这里的姑娘都是一等一的... ({timestamp_factor})",
                f"既然来了，就别客气，有什么需要尽管开口... ({timestamp_factor})"
            ],
            "follower": [
                f"属下在此等候指示，请主人吩咐... ({timestamp_factor})",
                f"主人，这里的情况似乎有些复杂，需要小心应对... ({timestamp_factor})",
                f"属下觉得需要小心行事，此地不宜久留... ({timestamp_factor})",
                f"属下已经观察过了，这里确实有些蹊跷... ({timestamp_factor})",
                f"主人，属下建议我们保持警惕... ({timestamp_factor})"
            ]
        }
        
        responses = fallback_responses.get(agent_type, [f"智能体{agent_type}正在思考... ({timestamp_factor})"])
        return random.choice(responses)
    
    def _stop_all_agent_tasks(self, room: ChatRoom):
        """停止房间内所有智能体任务"""
        if room:
            # 设置暂停标志，阻止新的智能体响应
            room.is_paused = True
            
            # 清空所有智能体锁
            room.agent_locks.clear()
            
            # 清空对话队列
            room.conversation_queue.clear()
            
            print(f"🛑 房间 {room.room_id} 的所有智能体任务已停止")
    
    async def background_tasks(self):
        """后台任务"""
        while True:
            try:
                await asyncio.sleep(1)  # 每秒检查一次
                
                current_time = time.time()
                
                for room in list(self.rooms.values()):
                    # 检查暂停超时
                    expired_pauses = []
                    for user_id in list(room.pause_requests):
                        user = room.users.get(user_id)
                        if user and user.pause_until > 0 and current_time > user.pause_until:
                            expired_pauses.append(user_id)
                    
                    # 移除过期的暂停请求
                    for user_id in expired_pauses:
                        room.pause_requests.discard(user_id)
                        user = room.users.get(user_id)
                        if user:
                            user.pause_until = 0
                    
                    # 如果没有暂停请求了，恢复对话
                    if room.is_paused and not room.pause_requests:
                        room.is_paused = False
                        await self.broadcast_to_room(room.room_id, {
                            "type": MessageType.SYSTEM_MESSAGE.value,
                            "content": "输入超时，对话自动恢复",
                            "is_paused": False,
                            "timestamp": current_time
                        })
                        
                        # 让智能体继续对话
                        await self.schedule_next_agent_response(room)
                    
                    # 自动启动智能体对话 - 如果15秒没有新消息且有用户在线
                    if (current_time - room.last_message_time > 15 and  # 15秒无消息
                        room.users and  # 🔥 关键：必须有用户在线
                        not room.is_paused and  # 未暂停
                        room.agent_manager):  # 有智能体管理器
                        
                        print(f"🤖 房间 {room.room_id} 触发自动对话")
                        # 触发智能体自发对话
                        await self.schedule_next_agent_response(room)
                        # 更新最后消息时间，避免频繁触发
                        room.last_message_time = current_time
                    
                    # 检查长时间无活动的房间
                    if (current_time - room.last_message_time > 300 and  # 5分钟无消息
                        not room.users):  # 且无用户
                        print(f"清理无活动房间: {room.room_id}")
                        # 🔥 关键修复：停止智能体任务后再删除
                        self._stop_all_agent_tasks(room)
                        
                        # 🔥 关键修复：清空协调器对话历史
                        if room.agent_coordinator:
                            room.agent_coordinator.conversation_history.clear()
                            print(f"🧠 清理房间 {room.room_id} 协调器对话历史")
                        
                        del self.rooms[room.room_id]
            
            except Exception as e:
                print(f"后台任务错误: {e}")


    async def process_follower_choice(self, room: ChatRoom, user: ChatUser, choice_id: Optional[str], custom_input: str):
        """处理随从选择并推进游戏"""
        try:
            # 结束随从选择阶段
            room.game_state.end_follower_choice_phase(choice_id, custom_input)
            
            # 找到选择的内容
            selected_choice = None
            if choice_id:
                for choice in room.game_state.pending_follower_choices:
                    if choice.choice_id == choice_id:
                        selected_choice = choice
                        break
            
            # 构建选择结果消息
            choice_content = ""
            if selected_choice:
                choice_content = f"选择了：{selected_choice.content}"
                # 应用数值变化
                for value_name, change in selected_choice.expected_values.items():
                    room.game_state.current_scene.update_scene_value(value_name, change)
            elif custom_input:
                choice_content = f"自定义行动：{custom_input}"
                # 自定义行动需要评估数值变化
                await self.evaluate_custom_choice(room, custom_input)
            
            # 广播选择结果
            await self.broadcast_to_room(room.room_id, {
                "type": MessageType.FOLLOWER_CHOICE_RESPONSE.value,
                "username": user.username,
                "choice_content": choice_content,
                "custom_input": custom_input,
                "scene_values": room.game_state.current_scene.scene_values,
                "round_number": room.game_state.follower_rounds_used
            })
            
            # 检查游戏结束条件
            if room.game_state.check_game_end_conditions():
                await self.handle_game_end(room)
            else:
                # 继续游戏，广播阶段变化
                await self.broadcast_to_room(room.room_id, {
                    "type": MessageType.GAME_PHASE_CHANGE.value,
                    "old_phase": "follower_choice",
                    "new_phase": room.game_state.current_phase.value,
                    "round_number": room.game_state.follower_rounds_used,
                    "max_rounds": room.game_state.max_follower_rounds
                })
                
                # 触发后续的剧情发展
                await self.trigger_story_continuation(room, choice_content)
                
        except Exception as e:
            print(f"处理随从选择时出错: {e}")
            await user.websocket.send_json({
                "type": "error",
                "message": f"处理选择时出错: {str(e)}"
            })
    
    async def evaluate_custom_choice(self, room: ChatRoom, custom_input: str):
        """评估自定义选择的数值变化"""
        try:
            # 获取评估智能体
            evaluator = room.agent_manager.get_agent("evaluator")
            if not evaluator:
                # 简单评估逻辑
                risk_change = len(custom_input) // 10
                room.game_state.current_scene.update_scene_value("危险度", risk_change)
                return
            
            # 构建评估上下文
            eval_prompt = f"""
请评估以下随从的自定义行动对场景数值的影响：

行动内容：{custom_input}
当前场景数值：{room.game_state.current_scene.scene_values}

请按以下JSON格式返回评估结果（只返回JSON）：
{{
    "value_changes": {{
        "危险度": 变化值,
        "暧昧度": 变化值,
        "紧张度": 变化值,
        "金钱消费": 变化值
    }},
    "quality_score": 1-10,
    "evaluation_reason": "评估原因"
}}
"""
            
            response = await self._call_crewai_agent(evaluator, eval_prompt)
            
            if response:
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    eval_data = json.loads(json_match.group())
                    value_changes = eval_data.get("value_changes", {})
                    
                    # 应用数值变化
                    for value_name, change in value_changes.items():
                        if isinstance(change, (int, float)):
                            room.game_state.current_scene.update_scene_value(value_name, int(change))
                    
                    return eval_data.get("quality_score", 5)
                    
        except Exception as e:
            print(f"评估自定义选择时出错: {e}")
            # 简单的备用评估
            risk_change = max(1, len(custom_input) // 15)
            room.game_state.current_scene.update_scene_value("危险度", risk_change)
            return 5
    
    async def check_follower_choice_trigger(self, room: ChatRoom):
        """检查是否满足随从选择触发条件"""
        if not room.game_state:
            return
        
        # 检查是否有随从玩家
        has_follower = any(user.role == UserRole.HUMAN_FOLLOWER for user in room.users.values())
        if not has_follower:
            return
        
        from .models import GamePhase
        
        # 检查游戏阶段
        if room.game_state.current_phase != GamePhase.FREE_CHAT:
            return
        
        # 检查触发条件：暧昧度或紧张度达到一定阈值
        scene_values = room.game_state.current_scene.scene_values
        ambiguity = scene_values.get('暧昧度', 0)
        tension = scene_values.get('紧张度', 0)
        danger = scene_values.get('危险度', 0)
        
        # 触发条件：暧昧度>=15 或 紧张度>=12 或 危险度>=8 (降低阈值便于测试)
        should_trigger = (ambiguity >= 15 or tension >= 12 or danger >= 8)
        
        # 额外条件：限制频率，避免频繁触发
        import time
        last_trigger_time = getattr(room, '_last_follower_trigger', 0)
        min_interval = 30  # 至少间隔30秒
        
        if should_trigger and (time.time() - last_trigger_time) > min_interval:
            print(f"🎯 自动触发随从选择：暧昧度={ambiguity}, 紧张度={tension}, 危险度={danger}")
            room._last_follower_trigger = time.time()
            await self.trigger_follower_choice_phase(room)
    
    async def trigger_follower_choice_phase(self, room: ChatRoom):
        """触发随从选择阶段"""
        if not room.game_state or not room.agent_coordinator:
            return
        
        from .models import GamePhase
        
        # 开始随从选择阶段
        room.game_state.start_follower_choice_phase()
        
        # 使用随从智能体生成选择项
        try:
            # 获取随从智能体
            follower_agent = room.agent_manager.get_agent("follower")
            if not follower_agent:
                print("随从智能体不存在")
                return
            
            # 确保游戏状态是最新的
            from .tools import set_game_state
            set_game_state(room.game_state)
            
            # 生成选择项
            choices = await self.generate_follower_choices(room, follower_agent)
            
            if choices:
                # 将选择项添加到游戏状态
                room.game_state.pending_follower_choices = choices
                
                # 广播选择请求
                await self.broadcast_to_room(room.room_id, {
                    "type": "follower_choices",  # 使用前端识别的消息类型
                    "choices": [choice.__dict__ for choice in choices],
                    "round_number": room.game_state.follower_rounds_used,
                    "max_rounds": room.game_state.max_follower_rounds,
                    "scene_values": room.game_state.current_scene.scene_values,
                    "message": "🎯 随从，现在需要你做出选择来推进计划..."
                })
                
                # 广播阶段变化
                await self.broadcast_to_room(room.room_id, {
                    "type": MessageType.GAME_PHASE_CHANGE.value,
                    "old_phase": "free_chat",
                    "new_phase": "follower_choice",
                    "round_number": room.game_state.follower_rounds_used,
                    "max_rounds": room.game_state.max_follower_rounds
                })
                
        except Exception as e:
            print(f"触发随从选择阶段时出错: {e}")
    
    async def generate_follower_choices(self, room: ChatRoom, follower_agent) -> List:
        """生成随从选择项"""
        try:
            # 构建上下文
            recent_messages = self.get_recent_conversation_context(room, limit=8)
            context = self._build_agent_context(room, recent_messages, "follower")
            
            # 添加选择生成指令
            choice_prompt = f"""
{context}

🎯 **随从选择阶段**
当前轮次：{room.game_state.follower_rounds_used}/{room.game_state.max_follower_rounds}
场景数值：{room.game_state.current_scene.scene_values}

请生成3个具体的行动选择，每个选择都应该：
1. 符合当前情境和对话
2. 推进剧情发展
3. 有不同的风险等级和预期效果

请按以下JSON格式回应（只返回JSON，不要其他内容）：
{{
    "choices": [
        {{
            "content": "选择描述",
            "risk_level": 风险等级(1-5),
            "expected_values": {{"危险度": 变化值, "暧昧度": 变化值}},
            "description": "选择后果提示"
        }}
    ]
}}
"""
            
            # 调用智能体生成选择
            response = await self._call_crewai_agent(follower_agent, choice_prompt)
            
            if response:
                # 解析JSON响应
                import json
                import re
                
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    choice_data = json.loads(json_str)
                    
                    # 创建FollowerChoice对象
                    from .models import FollowerChoice
                    import uuid
                    
                    choices = []
                    for i, choice_dict in enumerate(choice_data.get("choices", [])):
                        choice = FollowerChoice(
                            choice_id=str(uuid.uuid4())[:8],
                            content=choice_dict.get("content", f"选择{i+1}"),
                            risk_level=choice_dict.get("risk_level", 3),
                            expected_values=choice_dict.get("expected_values", {}),
                            description=choice_dict.get("description", "")
                        )
                        choices.append(choice)
                    
                    return choices
                    
        except Exception as e:
            print(f"生成随从选择时出错: {e}")
        
        # 失败时返回默认选择
        from .models import FollowerChoice
        import uuid
        
        return [
            FollowerChoice(
                choice_id=str(uuid.uuid4())[:8],
                content="谨慎观察，寻找机会",
                risk_level=2,
                expected_values={"危险度": 5, "紧张度": 10},
                description="安全但进展缓慢"
            ),
            FollowerChoice(
                choice_id=str(uuid.uuid4())[:8],
                content="主动出击，积极行动",
                risk_level=4,
                expected_values={"危险度": 15, "暧昧度": 20},
                description="有风险但效果显著"
            ),
            FollowerChoice(
                choice_id=str(uuid.uuid4())[:8],
                content="等待时机，保持低调",
                risk_level=1,
                expected_values={"紧张度": -5},
                description="最安全的选择"
            )
        ]
    
    async def trigger_story_continuation(self, room: ChatRoom, choice_content: str):
        """触发剧情继续发展"""
        if not room.agent_coordinator:
            return
        
        # 构建剧情推进消息
        story_prompt = f"随从做出了选择：{choice_content}。请各位角色根据这个选择继续推进剧情。"
        
        # 使用协调器生成后续响应
        active_agents = room.agent_manager.get_active_agents()
        if active_agents:
            coordinated_responses = await room.agent_coordinator.coordinate_response(
                story_prompt, active_agents
            )
            
            if coordinated_responses:
                # 发送响应
                for i, response in enumerate(coordinated_responses):
                    delay = 1.0 + i * 1.5  # 给用户一些时间消化选择结果
                    asyncio.create_task(
                        self.send_coordinated_response(room, response, delay)
                    )
    
    async def handle_game_end(self, room: ChatRoom):
        """处理游戏结束"""
        if not room.game_state:
            return
        
        from .models import GamePhase
        room.game_state.current_phase = GamePhase.GAME_ENDED
        
        # 计算最终结果和得分
        final_result = room.game_state.calculate_final_result()
        final_score = room.game_state.calculate_final_score()
        
        # 计算详细奖励信息
        reward_info = self.calculate_detailed_rewards(room.game_state, final_result, final_score)
        
        # 准备结果消息
        result_messages = {
            "success": "🎉 任务成功完成！",
            "failure": "💀 任务失败，被发现了！",
            "neutral": "😐 任务结束，结果平平。"
        }
        
        # 广播游戏结束
        await self.broadcast_to_room(room.room_id, {
            "type": "game_ended",  # 使用前端识别的消息类型
            "result": final_result.value,
            "score": final_score,
            "message": result_messages.get(final_result.value, "游戏结束"),
            "rounds_used": room.game_state.follower_rounds_used,
            "max_rounds": room.game_state.max_follower_rounds,
            "final_scene_values": room.game_state.current_scene.scene_values,
            "reward_info": reward_info,
            "active_cards": [card.to_dict() for card in room.game_state.active_cards if card.is_active] if hasattr(room.game_state, 'active_cards') else []
        })
        
        # 生成结局总结
        await self.generate_ending_summary(room, final_result, final_score)
    
    def calculate_detailed_rewards(self, game_state, final_result, final_score: int) -> Dict:
        """计算详细的奖励惩罚信息"""
        from .models import GameResult
        
        scene_values = game_state.current_scene.scene_values
        rounds_used = game_state.follower_rounds_used
        max_rounds = game_state.max_follower_rounds
        
        # 基础奖励计算
        base_reward = 0
        reward_multiplier = 1.0
        punishment = 0
        status = "存活"
        
        # 成功条件判断
        ambiguity = scene_values.get('暧昧度', 0)
        danger = scene_values.get('危险度', 0)
        tension = scene_values.get('紧张度', 0)
        money = scene_values.get('金钱消费', 0)
        
        if final_result == GameResult.SUCCESS:
            # 成功奖励
            base_reward = 1000
            
            # 数值越高奖励越多
            base_reward += ambiguity * 20  # 暧昧度每点20金币
            base_reward += tension * 15   # 紧张度每点15金币
            base_reward += max(0, 100 - danger) * 5  # 低危险度奖励
            
            # 轮数奖励（用时越少奖励越高）
            rounds_bonus = (max_rounds - rounds_used) * 200
            base_reward += rounds_bonus
            
            # 效率乘数
            if rounds_used <= 2:
                reward_multiplier = 1.5  # 高效完成
            elif rounds_used <= 3:
                reward_multiplier = 1.2
            
            status = "大获成功"
            
        elif final_result == GameResult.FAILURE:
            # 失败惩罚
            if danger >= 80:
                # 被抓惩罚
                punishment = 500
                status = "被抓处死"
            elif ambiguity < 20:
                # 任务失败
                punishment = 300
                status = "任务失败，被驱逐"
            else:
                # 轻微失败
                punishment = 200
                status = "任务失败"
                
        else:  # NEUTRAL
            # 中性结果
            base_reward = 200  # 基础生存奖励
            base_reward += ambiguity * 5  # 部分成果奖励
            status = "平安退出"
        
        # 计算最终奖励
        final_reward = max(0, int(base_reward * reward_multiplier) - punishment)
        
        return {
            "base_reward": base_reward,
            "reward_multiplier": reward_multiplier,
            "punishment": punishment,
            "final_reward": final_reward,
            "status": status,
            "breakdown": {
                "暧昧度奖励": ambiguity * (20 if final_result == GameResult.SUCCESS else 5),
                "紧张度奖励": tension * (15 if final_result == GameResult.SUCCESS else 0),
                "危险度影响": max(0, 100 - danger) * 5 if final_result == GameResult.SUCCESS else -danger * 5,
                "轮数奖励": (max_rounds - rounds_used) * 200 if final_result == GameResult.SUCCESS else 0,
                "金钱消费": -money  # 花费的钱是损失
            }
        }
    
    async def generate_ending_summary(self, room: ChatRoom, final_result, final_score: int):
        """生成游戏结局总结"""
        try:
            narrator_agent = room.agent_manager.get_agent("narrator")
            if not narrator_agent:
                return
            
            summary_prompt = f"""
请根据游戏结果生成一个精彩的结局总结：

游戏结果：{final_result.value}
最终得分：{final_score}
轮数使用：{room.game_state.follower_rounds_used}/{room.game_state.max_follower_rounds}
最终场景数值：{room.game_state.current_scene.scene_values}

请生成一段100-200字的结局总结，要有文学性和戏剧性。
"""
            
            summary = await self._call_crewai_agent(narrator_agent, summary_prompt)
            
            if summary:
                await self.broadcast_to_room(room.room_id, {
                    "type": MessageType.AGENT_MESSAGE.value,
                    "agent_type": "narrator",
                    "agent_name": "旁白者",
                    "content": f"📖 **游戏结局**\n\n{summary}",
                    "timestamp": time.time()
                })
                
        except Exception as e:
            print(f"生成结局总结时出错: {e}")

    # ====================================
    # 🎮 简化游戏管理系统
    # ====================================

    def should_trigger_follower_choice(self, room: ChatRoom) -> bool:
        """检查是否应该触发随从选择"""
        # 检查是否有随从玩家
        has_follower = any(user.role == UserRole.HUMAN_FOLLOWER for user in room.users.values())
        if not has_follower:
            return False
        
        # 检查是否已经在选择阶段
        if room.is_follower_choice_phase:
            return False
        
        # 每4轮触发一次随从选择
        rounds_since_last = room.conversation_count - room.last_follower_round
        if rounds_since_last >= room.follower_action_interval:
            return True
            
        return False

    async def trigger_follower_choice_simple(self, room: ChatRoom):
        """触发随从选择（简化版本）"""
        try:
            print(f"🎯 触发随从选择阶段（第{room.conversation_count}轮）")
            
            # 进入随从选择阶段
            room.is_follower_choice_phase = True
            room.last_follower_round = room.conversation_count
            
            # 生成3个简单的选择项
            choices = await self.generate_simple_follower_choices(room)
            room.pending_follower_choices = choices
            
            # 通知所有用户进入随从选择阶段
            await self.broadcast_to_room(room.room_id, {
                "type": "follower_choices",  # 确保前端能识别
                "choices": [
                    {
                        "choice_id": choice.choice_id,
                        "content": choice.content,
                        "risk_level": choice.risk_level,
                        "expected_values": choice.expected_values,
                        "description": choice.description
                    }
                    for choice in choices
                ],
                "current_round": room.conversation_count,
                "max_rounds": room.max_conversations,
                "message": "🎯 随从，请选择你的行动方案：",
                "timestamp": time.time()
            })
            
        except Exception as e:
            print(f"❌ 触发随从选择失败: {e}")
            room.is_follower_choice_phase = False

    async def generate_simple_follower_choices(self, room: ChatRoom) -> List:
        """生成简单的随从选择项（不依赖复杂的AI调用）"""
        from .models import FollowerChoice
        import uuid
        
        # 根据当前场景数值生成相应的选择
        scene_values = room.game_state.current_scene.scene_values if room.game_state else {}
        danger = scene_values.get("危险度", 0)
        tension = scene_values.get("紧张度", 0)
        
        # 基础选择模板，根据情况调整
        if danger < 30:
            # 低危险阶段
            choices = [
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="低调观察，收集周围信息",
                    risk_level=1,
                    expected_values={"紧张度": 5, "危险度": 2},
                    description="安全但进展缓慢的选择"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="主动与他人交谈，试探情况",
                    risk_level=3,
                    expected_values={"暧昧度": 10, "危险度": 8, "紧张度": 12},
                    description="平衡风险与收益的策略"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="大胆行动，直接接近目标",
                    risk_level=5,
                    expected_values={"暧昧度": 20, "危险度": 18, "金钱消费": 5},
                    description="高风险高回报的激进做法"
                )
            ]
        else:
            # 高危险阶段
            choices = [
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="保持冷静，寻找安全退路",
                    risk_level=2,
                    expected_values={"危险度": -5, "紧张度": 8},
                    description="优先考虑安全的保守策略"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="利用现有信息，巧妙应对",
                    risk_level=3,
                    expected_values={"暧昧度": 15, "危险度": 10},
                    description="充分利用已有优势"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="孤注一掷，全力一搏",
                    risk_level=5,
                    expected_values={"暧昧度": 25, "危险度": 25, "金钱消费": 10},
                    description="背水一战的最后尝试"
                )
            ]
        
        return choices

    async def process_follower_choice_input(self, user: ChatUser, input_content: str):
        """处理随从选择输入"""
        room = self.rooms.get(user.room_id)
        if not room or not room.is_follower_choice_phase:
            return
        
        # 检查是否是选择编号
        choice_selected = None
        custom_input = None
        
        if input_content in ["1", "2", "3"]:
            choice_index = int(input_content) - 1
            if 0 <= choice_index < len(room.pending_follower_choices):
                choice_selected = room.pending_follower_choices[choice_index]
        else:
            # 自定义输入
            custom_input = input_content
        
        # 处理选择结果
        await self.execute_follower_choice(room, choice_selected, custom_input, user)

    async def execute_follower_choice(self, room: ChatRoom, choice: Optional[object], custom_input: Optional[str], user: ChatUser):
        """执行随从选择"""
        try:
            # 结束选择阶段
            room.is_follower_choice_phase = False
            room.pending_follower_choices = []
            
            if choice:
                # 使用预设选择
                action_content = choice.content
                value_changes = choice.expected_values
                
                # 应用数值变化
                for key, change in value_changes.items():
                    if room.game_state and room.game_state.current_scene:
                        room.game_state.current_scene.update_scene_value(key, change)
                
                # 广播选择结果
                await self.broadcast_to_room(room.room_id, {
                    "type": MessageType.CHAT_MESSAGE.value,
                    "username": user.username,
                    "role": user.role.value,
                    "role_display": "随从",
                    "content": f"🎯 {action_content}",
                    "timestamp": time.time()
                })
                
                # 显示数值变化
                changes_text = ", ".join([f"{k}{v:+d}" for k, v in value_changes.items() if v != 0])
                await self.broadcast_to_room(room.room_id, {
                    "type": MessageType.SYSTEM_MESSAGE.value,
                    "content": f"📊 数值变化：{changes_text}",
                    "timestamp": time.time()
                })
                
            else:
                # 使用自定义输入
                action_content = custom_input or "进行了一个神秘的行动"
                
                # 广播自定义行动
                await self.broadcast_to_room(room.room_id, {
                    "type": MessageType.CHAT_MESSAGE.value,
                    "username": user.username,
                    "role": user.role.value,
                    "role_display": "随从",
                    "content": f"🎯 {action_content}",
                    "timestamp": time.time()
                })
                
                # 简单的自定义行动数值影响
                if room.game_state and room.game_state.current_scene:
                    room.game_state.current_scene.update_scene_value("紧张度", 5)
                    room.game_state.current_scene.update_scene_value("暧昧度", 8)
            
            # 广播场景更新
            await self.broadcast_scene_update(room)
            
            # 记录对话历史
            if room.game_state and room.game_state.current_scene:
                room.game_state.current_scene.add_conversation("随从", action_content)
            
            # 增加对话计数
            room.conversation_count += 1
            
            # 检查游戏结束
            if room.conversation_count >= room.max_conversations:
                await self.end_game_due_to_limit(room)
                return
            
            # 触发智能体响应
            await self.schedule_next_agent_response(room)
            
        except Exception as e:
            print(f"❌ 执行随从选择失败: {e}")
            room.is_follower_choice_phase = False

    async def end_game_due_to_limit(self, room: ChatRoom):
        """因为轮数限制结束游戏"""
        await self.broadcast_to_room(room.room_id, {
            "type": MessageType.GAME_END.value,
            "content": "🔚 游戏结束：已达到20轮对话限制",
            "reason": "对话轮数达到上限",
            "final_values": room.game_state.current_scene.scene_values if room.game_state else {},
            "timestamp": time.time()
        })

    async def announce_card_mission(self, room: ChatRoom, card):
        """激活卡片后让旁白宣布任务目标"""
        if room.mission_announced:
            return
        
        room.mission_announced = True
        
        # 构建任务宣布内容
        mission_content = f"""
🎴 一张神秘的卡牌被激活了...

📜 **{card.title}**
{card.description}

🎯 **你的目标：**
{card.usage_objective}

📋 **成功条件：**
{', '.join([f'{k}达到{v}' for k, v in card.success_condition.items()])}

⏰ **剩余轮数：** {room.max_conversations - room.conversation_count}轮

现在，让故事开始吧...
"""
        
        # 旁白宣布任务
        await self.broadcast_to_room(room.room_id, {
            "type": MessageType.AGENT_MESSAGE.value,
            "agent_type": "narrator",
            "agent_name": "旁白者",
            "content": mission_content,
            "timestamp": time.time()
        })
        
        # 触发初始智能体对话
        await self.schedule_next_agent_response(room)

    async def send_to_user(self, user: ChatUser, message: Dict):
        """发送消息给指定用户"""
        try:
            await user.websocket.send_json(message)
        except Exception as e:
            print(f"发送消息失败给用户 {user.username}: {e}")


# 创建全局服务器实例
chat_server = WebSocketChatServer()
app = chat_server.app 