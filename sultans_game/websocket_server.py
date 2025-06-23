"""WebSocket多人聊天服务器"""

import asyncio
import json
import os
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# 全局禁用CrewAI遥测避免网络错误
os.environ["OTEL_SDK_DISABLED"] = "true"

from ..cards import create_sample_cards, get_card_by_type, CardType
from ..tools import card_usage_tool, set_game_state
from .server.websocket_models import ChatUser, UserRole, MessageType
from .server.room_manager import RoomManager
from .server.message_handler import MessageHandler
from .server.message_broadcaster import MessageBroadcaster
from .server.game_manager import GameManager
from .server.agent_response_manager import AgentResponseManager


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
        
        self.room_manager = RoomManager()
        self.message_handler = MessageHandler(self.room_manager)
        self.broadcaster = MessageBroadcaster()
        self.game_manager = GameManager()
        self.agent_response_manager = AgentResponseManager()
        self.agent_response_manager.broadcaster = self.broadcaster
        self.agent_response_manager.game_manager = self.game_manager
        
        self.setup_routes()
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
            self._background_task = asyncio.create_task(self.background_tasks())
        
        # HTTP端点
        self.setup_http_routes()

    def setup_http_routes(self):
        """设置HTTP路由"""
        @self.app.get("/rooms")
        async def list_rooms():
            rooms = self.room_manager.get_all_rooms()
            return {
                "rooms": [
                    {
                        "room_id": room.room_id,
                        "scene_name": room.scene_name,
                        "user_count": len(room.users),
                        "users": [
                            {"username": user.username, "role": user.role.value} 
                            for user in room.users.values()
                        ]
                    } for room in rooms.values()
                ]
            }
        
        @self.app.get("/rooms/{room_id}/cards")
        async def get_available_cards(room_id: str):
            room = self.room_manager.get_room(room_id)
            if not room:
                return {"success": False, "message": "房间不存在"}
            
            available_cards = create_sample_cards()
            if room.game_state:
                for card in available_cards:
                    if card.check_trigger_conditions(room.game_state.current_scene.scene_values):
                        card.can_be_used = True
            
            return {
                "success": True,
                "cards": [card.to_dict() for card in available_cards],
                "scene_values": room.game_state.current_scene.scene_values if room.game_state else {}
            }
        
        @self.app.post("/rooms/{room_id}/card/activate")
        async def activate_card(room_id: str, card_data: Dict):
            room = self.room_manager.get_room(room_id)
            if not room:
                return {"success": False, "message": "房间不存在"}
            if not room.game_state:
                return {"success": False, "message": "游戏状态未初始化"}
            
            card_type = CardType(card_data["card_type"])
            card = get_card_by_type(card_type)
            card.is_active = True
            room.game_state.active_cards.append(card)
            room.card_activated = True
            
            await self.broadcaster.broadcast_to_room(room, {
                "type": MessageType.SYSTEM_MESSAGE.value,
                "content": f"🎴 卡片已激活：{card.title}",
                "card_activated": card.to_dict()
            })
            
            await self.game_manager.announce_card_mission(room, card)
            
            return {"success": True, "message": "卡片激活成功", "card": card.to_dict()}
    
    async def handle_websocket(self, websocket: WebSocket, room_id: str):
        """处理WebSocket连接"""
        await websocket.accept()
        user = None
        
        try:
            join_data = await websocket.receive_json()
            if join_data.get("type") != "join":
                await websocket.send_json({"error": "首条消息必须是join类型"})
                return
            
            user = await self.handle_user_join(websocket, room_id, join_data)
            if not user:
                return
            
            while True:
                data = await websocket.receive_json()
                await self.message_handler.handle_message(user, data)
                
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
            username = join_data["username"]
            role = UserRole(join_data["role"])
            scene_name = join_data.get("scene_name", "brothel")
            
            user = ChatUser(
                user_id=str(uuid.uuid4()),
                websocket=websocket,
                username=username,
                role=role,
                room_id=room_id
            )
            
            room = await self.room_manager.join_room(user, room_id, scene_name)
            
            await websocket.send_json({
                "type": "join_success",
                "user_id": user.user_id,
                "room_id": room_id,
                "scene_name": room.scene_name
            })
            
            return user
            
        except (ValueError, KeyError) as e:
            await websocket.send_json({"error": f"加入房间失败: {str(e)}"})
            return None
    
    async def handle_user_leave(self, user: ChatUser):
        """处理用户离开"""
        await self.room_manager.leave_room(user)
    
    async def background_tasks(self):
        """后台任务"""
        while True:
            await asyncio.sleep(1)
            # Placeholder for background tasks like checking for inactive rooms
            self.room_manager.cleanup_inactive_rooms()

# 创建全局服务器实例
chat_server = WebSocketChatServer()
app = chat_server.app 