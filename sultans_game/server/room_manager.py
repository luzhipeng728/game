"""房间管理器"""

import uuid
from typing import Dict, Optional

from .websocket_models import ChatRoom, ChatUser, UserRole
from .message_broadcaster import MessageBroadcaster
from ..agents.agent_manager import AgentManager
from ..agents.agent_coordinator import AgentCoordinator
from ..models import GameState, SceneState


class RoomManager:
    """房间管理器"""
    
    def __init__(self):
        self.rooms: Dict[str, ChatRoom] = {}
    
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
    
    def get_room(self, room_id: str) -> Optional[ChatRoom]:
        """获取房间"""
        return self.rooms.get(room_id)
    
    def get_all_rooms(self) -> Dict[str, ChatRoom]:
        """获取所有房间"""
        return self.rooms
    
    async def join_room(self, user: ChatUser, room_id: str, scene_name: str = "brothel") -> ChatRoom:
        """用户加入房间"""
        # 创建或获取房间
        if room_id not in self.rooms:
            room = await self.create_room(room_id, scene_name)
        else:
            room = self.rooms[room_id]
        
        # 检查角色冲突
        for existing_user in room.users.values():
            if existing_user.role == user.role and user.role != UserRole.SPECTATOR:
                raise ValueError(f"角色 {user.role.value} 已被占用")
        
        # 🔥 关键修复：如果是房间第一个用户，重置协调器对话历史
        if not room.users:  # 房间之前是空的
            if room.agent_coordinator:
                room.agent_coordinator.conversation_history.clear()
                print(f"🧠 房间 {room_id} 重置协调器对话历史（新用户加入空房间）")
        
        # 添加用户到房间
        room.users[user.user_id] = user
        
        # 广播用户加入消息
        await MessageBroadcaster.broadcast_user_join(
            room, user.username, user.role.value, exclude_user=user.user_id
        )
        
        # 发送当前房间状态
        await MessageBroadcaster.send_room_state(user, room)
        
        print(f"用户 {user.username} 以角色 {user.role.value} 加入房间 {room_id}")
        return room
    
    async def leave_room(self, user: ChatUser) -> bool:
        """用户离开房间"""
        room_id = user.room_id
        
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        
        # 移除用户
        if user.user_id in room.users:
            del room.users[user.user_id]
        
        # 移除暂停请求
        room.pause_requests.discard(user.user_id)
        
        # 广播用户离开消息
        await MessageBroadcaster.broadcast_user_leave(room, user.username, user.role.value)
        
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
        return True
    
    def check_role_conflict(self, room: ChatRoom, role: UserRole) -> bool:
        """检查角色冲突"""
        for existing_user in room.users.values():
            if existing_user.role == role and role != UserRole.SPECTATOR:
                return True
        return False
    
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
    
    def cleanup_inactive_rooms(self, max_inactive_time: float = 300.0):
        """清理长时间无活动的房间"""
        import time
        current_time = time.time()
        rooms_to_delete = []
        
        for room_id, room in self.rooms.items():
            # 检查长时间无活动的房间
            if (current_time - room.last_message_time > max_inactive_time and  # 5分钟无消息
                not room.users):  # 且无用户
                rooms_to_delete.append(room_id)
        
        for room_id in rooms_to_delete:
            room = self.rooms[room_id]
            print(f"清理无活动房间: {room_id}")
            # 🔥 关键修复：停止智能体任务后再删除
            self._stop_all_agent_tasks(room)
            
            # 🔥 关键修复：清空协调器对话历史
            if room.agent_coordinator:
                room.agent_coordinator.conversation_history.clear()
                print(f"🧠 清理房间 {room_id} 协调器对话历史")
            
            del self.rooms[room_id]
        
        return len(rooms_to_delete) 