"""WebSocket消息处理器"""

import time
from typing import Dict

from .websocket_models import ChatUser, UserRole, MessageType, ChatRoom
from .message_broadcaster import MessageBroadcaster
from .game_manager import GameManager
from .agent_response_manager import AgentResponseManager

class MessageHandler:
    """消息处理器"""
    
    def __init__(self, room_manager):
        self.room_manager = room_manager
    
    async def handle_message(self, user: ChatUser, data: Dict):
        """处理用户消息"""
        message_type = data.get("type")
        room = self.room_manager.get_room(user.room_id)
        if not room:
            return
        
        user.last_activity = time.time()
        
        if message_type == "chat_message":
            await self.handle_chat_message(user, room, data)
        elif message_type == "pause_request":
            await self.handle_pause_request(user, room, data)
        elif message_type == "resume_request":
            await self.handle_resume_request(user, room, data)
        elif message_type == "typing_start":
            await self.handle_typing_start(user, room)
        elif message_type == "typing_stop":
            await self.handle_typing_stop(user, room)
        elif message_type == "follower_choice_response":
            await self.handle_follower_choice_response(user, room, data)
        else:
            print(f"未知消息类型: {message_type}")
    
    async def handle_chat_message(self, user: ChatUser, room: ChatRoom, data: Dict):
        """处理聊天消息"""
        content = data.get("content", "").strip()
        if not content:
            return
        
        if room.conversation_count >= room.max_conversations:
            await MessageBroadcaster.send_to_user(user, {
                "type": MessageType.SYSTEM_MESSAGE.value, "content": "🔚 游戏已结束"
            })
            return

        if room.is_follower_choice_phase:
            if user.role != UserRole.HUMAN_FOLLOWER:
                await MessageBroadcaster.send_to_user(user, {
                    "type": MessageType.SYSTEM_MESSAGE.value, "content": "⏳ 等待随从选择..."
                })
                return
            await GameManager.process_follower_choice_input(room, user, content)
            return
            
        room.conversation_count += 1
        
        if room.game_state and room.game_state.current_scene:
            speaker_name = f"{user.username} ({user.role.name})"
            room.game_state.current_scene.add_conversation(speaker_name, content, "人类玩家发言")
        
        message = {
            "type": MessageType.CHAT_MESSAGE.value,
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "content": content,
            "timestamp": time.time(),
            "round_info": f"第{room.conversation_count}/{room.max_conversations}轮"
        }
        
        await MessageBroadcaster.broadcast_to_room(room, message)
        room.last_message_time = time.time()
        
        if GameManager.should_trigger_follower_choice(room):
            await GameManager.trigger_follower_choice_simple(room)
            return

        if room.conversation_count >= room.max_conversations:
            await GameManager.end_game_due_to_limit(room)
            return

        if user.role in [UserRole.HUMAN_FOLLOWER, UserRole.HUMAN_COURTESAN, UserRole.HUMAN_MADAM]:
            await AgentResponseManager.coordinate_agent_responses(room, content, user)
    
    async def handle_pause_request(self, user: ChatUser, room: ChatRoom, data: Dict):
        """处理暂停请求"""
        duration = data.get("duration", 10)
        room.pause_requests.add(user.user_id)
        user.pause_until = time.time() + duration
        
        if not room.is_paused:
            room.is_paused = True
            await MessageBroadcaster.broadcast_to_room(room, {
                "type": MessageType.SYSTEM_MESSAGE.value,
                "content": f"{user.username} 正在输入...",
                "is_paused": True,
            }, exclude_user=user.user_id)
    
    async def handle_resume_request(self, user: ChatUser, room: ChatRoom, data: Dict):
        """处理恢复请求"""
        room.pause_requests.discard(user.user_id)
        user.pause_until = 0
        
        if not room.pause_requests:
            room.is_paused = False
            await MessageBroadcaster.broadcast_to_room(room, {
                "type": MessageType.SYSTEM_MESSAGE.value,
                "content": "对话已恢复",
                "is_paused": False,
            })
    
    async def handle_typing_start(self, user: ChatUser, room: ChatRoom):
        """处理开始输入"""
        if not user.is_typing:
            user.is_typing = True
            await MessageBroadcaster.broadcast_typing_status(room, user.username, True, exclude_user=user.user_id)
    
    async def handle_typing_stop(self, user: ChatUser, room: ChatRoom):
        """处理停止输入"""
        if user.is_typing:
            user.is_typing = False
            await MessageBroadcaster.broadcast_typing_status(room, user.username, False, exclude_user=user.user_id)
    
    async def handle_follower_choice_response(self, user: ChatUser, room: ChatRoom, data: Dict):
        """处理随从选择回应"""
        if user.role != UserRole.HUMAN_FOLLOWER:
            return
        
        if not room.game_state:
            return
        
        from ..models import GamePhase
        if room.game_state.current_phase != GamePhase.FOLLOWER_CHOICE:
            return
        
        choice_id = data.get("choice_id")
        custom_input = data.get("custom_input", "").strip()
        
        # This part seems to have more complex logic, which might need to be moved to GameManager
        # For now, keeping it simple
        await GameManager.process_follower_choice_input(room, user, custom_input or choice_id) 