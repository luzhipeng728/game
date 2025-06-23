"""消息广播工具"""

import time
from typing import Dict, Optional

from .websocket_models import ChatRoom, ChatUser, MessageType


class MessageBroadcaster:
    """消息广播器"""
    
    @staticmethod
    async def broadcast_to_room(room: ChatRoom, message: Dict, exclude_user: Optional[str] = None):
        """向房间内所有用户广播消息"""
        disconnected_users = []
        
        for user_id, user in room.users.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await user.websocket.send_json(message)
            except Exception as e:
                print(f"发送消息失败给用户 {user.username}: {e}")
                disconnected_users.append(user_id)
        
        return disconnected_users
    
    @staticmethod
    async def send_to_user(user: ChatUser, message: Dict):
        """发送消息给指定用户"""
        try:
            await user.websocket.send_json(message)
        except Exception as e:
            print(f"发送消息失败给用户 {user.username}: {e}")
            raise
    
    @staticmethod
    async def send_room_state(user: ChatUser, room: ChatRoom):
        """发送房间状态给用户"""
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
        
        await MessageBroadcaster.send_to_user(user, state)
    
    @staticmethod
    async def broadcast_scene_update(room: ChatRoom):
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
        
        await MessageBroadcaster.broadcast_to_room(room, update_message)
    
    @staticmethod
    async def broadcast_user_join(room: ChatRoom, username: str, role_value: str, exclude_user: Optional[str] = None):
        """广播用户加入消息"""
        message = {
            "type": MessageType.USER_JOIN.value,
            "username": username,
            "role": role_value,
            "timestamp": time.time()
        }
        return await MessageBroadcaster.broadcast_to_room(room, message, exclude_user)
    
    @staticmethod
    async def broadcast_user_leave(room: ChatRoom, username: str, role_value: str):
        """广播用户离开消息"""
        message = {
            "type": MessageType.USER_LEAVE.value,
            "username": username,
            "role": role_value,
            "timestamp": time.time()
        }
        return await MessageBroadcaster.broadcast_to_room(room, message)
    
    @staticmethod
    async def broadcast_typing_status(room: ChatRoom, username: str, is_typing: bool, exclude_user: Optional[str] = None):
        """广播用户输入状态"""
        message_type = MessageType.USER_TYPING if is_typing else MessageType.USER_STOP_TYPING
        message = {
            "type": message_type.value,
            "username": username,
            "timestamp": time.time()
        }
        return await MessageBroadcaster.broadcast_to_room(room, message, exclude_user) 