"""智能体响应管理器"""

import asyncio
import time
import random
from typing import Dict, List, Optional

from .websocket_models import ChatRoom, ChatUser, UserRole, MessageType
from .message_broadcaster import MessageBroadcaster
from ..tools import set_game_state


class AgentResponseManager:
    """智能体响应管理器"""
    
    @staticmethod
    def get_role_display_name(role: UserRole) -> str:
        """获取角色显示名称"""
        role_names = {
            UserRole.HUMAN_FOLLOWER: "人类随从",
            UserRole.HUMAN_COURTESAN: "人类妓女", 
            UserRole.HUMAN_MADAM: "人类老鸨",
            UserRole.SPECTATOR: "旁观者"
        }
        return role_names.get(role, role.value)
    
    @staticmethod
    def get_agent_display_name(agent_type: str) -> str:
        """获取智能体显示名称"""
        agent_names = {
            "narrator": "旁白者",
            "follower": "随从",
            "courtesan": "妓女",
            "madam": "老鸨",
            "merchant": "商人"
        }
        return agent_names.get(agent_type, agent_type)
    
    @staticmethod
    async def coordinate_agent_responses(room: ChatRoom, user_message: str, user: ChatUser):
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
                agent_display_name = AgentResponseManager.get_agent_display_name(corresponding_agent_type)
                room.agent_coordinator.add_to_history(
                    "agent_message", user_message, 
                    agent_name=f"{agent_display_name}(由{user.username}扮演)"
                )
            else:
                # 用户是旁观者，作为普通聊天消息
                room.agent_coordinator.add_to_history(
                    "chat_message", user_message, username=user.username
                )
            
            active_agents = room.agent_manager.get_active_agents()
            
            if not active_agents:
                return
            
            # 确保全局游戏状态最新
            if room.game_state:
                set_game_state(room.game_state)
            
            # 记录协调器调用前的场景数值状态
            old_scene_values_coord = None
            if room.game_state and room.game_state.current_scene:
                old_scene_values_coord = room.game_state.current_scene.scene_values.copy()
            
            # 使用协调器生成响应
            coordinated_responses = await room.agent_coordinator.coordinate_response(
                user_message, active_agents
            )
            
            if not coordinated_responses:
                return
            
            # 按质量顺序发送响应
            for i, response in enumerate(coordinated_responses):
                delay = 0.5 + i * 0.8
                old_values = old_scene_values_coord if i == 0 else None
                asyncio.create_task(
                    AgentResponseManager.send_coordinated_response(room, response, delay, old_values)
                )
                
        except Exception as e:
            print(f"协调智能体响应时出错: {e}")
    
    @staticmethod
    async def send_coordinated_response(room: ChatRoom, response, delay: float, old_scene_values: Optional[Dict] = None):
        """发送协调的响应"""
        await asyncio.sleep(delay)
        
        if (room.room_id not in room.manager.rooms or room.is_paused):
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
            
            await MessageBroadcaster.broadcast_to_room(room, message)
            
            # 检查场景数值是否发生变化
            if old_scene_values and room.game_state and room.game_state.current_scene:
                new_scene_values = room.game_state.current_scene.scene_values
                changes = {
                    key: new_scene_values.get(key, 0) - old_scene_values.get(key, 0)
                    for key in new_scene_values
                    if new_scene_values.get(key, 0) != old_scene_values.get(key, 0)
                }
                
                if changes:
                    await MessageBroadcaster.broadcast_scene_update(room)
                    print(f"🎮 协调器场景数值更新: {changes}")
            
            room.last_message_time = time.time()
            
            # 触发后续的自动对话
            if random.random() < 0.8:
                await AgentResponseManager.schedule_next_agent_response(room)
            
        except Exception as e:
            print(f"发送协调响应时出错: {e}")

    @staticmethod
    async def schedule_next_agent_response(room: ChatRoom, exclude_role: Optional[UserRole] = None):
        """安排下一个智能体回应"""
        if not room.agent_manager or room.is_paused:
            return
        
        available_agents = room.agent_manager.get_active_agent_types(exclude_role=exclude_role)
        
        if not available_agents:
            return
        
        next_agent = AgentResponseManager._select_next_agent_strategically(room, available_agents, exclude_role)
        asyncio.create_task(AgentResponseManager.delayed_agent_response(room, next_agent, 0))
    
    @staticmethod
    def _select_next_agent_strategically(room: ChatRoom, available_agents: List[str], exclude_role: Optional[UserRole] = None) -> str:
        """策略性选择下一个智能体发言"""
        if not available_agents:
            return "narrator"
        
        priority_order = ["narrator", "madam", "courtesan", "follower", "merchant"]
        
        recent_speakers = []
        if room.game_state and room.game_state.current_scene:
            for msg in room.game_state.current_scene.conversation_history[-6:]:
                context = msg.get("context", "")
                if "AI智能体回应" in context and " - " in context:
                    recent_speakers.append(context.split(" - ")[-1])
        
        if recent_speakers:
            last_speaker = recent_speakers[-1]
            candidates = [agent for agent in priority_order if agent in available_agents and agent != last_speaker]
            if candidates:
                return candidates[0]
        
        return next((agent for agent in priority_order if agent in available_agents), random.choice(available_agents))
    
    @staticmethod
    async def delayed_agent_response(self, room: ChatRoom, agent_type: str, delay: float):
        """延迟的智能体回应"""
        await asyncio.sleep(delay)
        
        if (room.room_id not in self.manager.rooms or room.is_paused):
            return
        
        if room.agent_locks.get(agent_type, False):
            return
        
        room.agent_locks[agent_type] = True
        
        try:
            agent = room.agent_manager.get_agent(agent_type)
            if not agent:
                return
            
            if room.game_state:
                set_game_state(room.game_state)
            
            old_scene_values = room.game_state.current_scene.scene_values.copy() if room.game_state and room.game_state.current_scene else None
            
            response_content = await self.generate_agent_response(room, agent_type)
            
            if response_content:
                if room.game_state and room.game_state.current_scene:
                    display_name = self.get_agent_display_name(agent_type)
                    room.game_state.current_scene.add_conversation(
                        display_name, response_content, f"AI智能体回应 - {agent_type}"
                    )
                
                display_name = self.get_agent_display_name(agent_type)
                message = {
                    "type": MessageType.AGENT_MESSAGE.value,
                    "agent_type": agent_type,
                    "agent_name": display_name,
                    "content": response_content,
                    "timestamp": time.time()
                }
                
                await self.broadcaster.broadcast_to_room(room, message)
                
                if old_scene_values and room.game_state and room.game_state.current_scene:
                    new_scene_values = room.game_state.current_scene.scene_values
                    changes = {
                        key: new_scene_values.get(key, 0) - old_scene_values.get(key, 0)
                        for key in new_scene_values
                        if new_scene_values.get(key, 0) != old_scene_values.get(key, 0)
                    }
                    if changes:
                        await self.broadcaster.broadcast_scene_update(room)
                        await self.game_manager.check_follower_choice_trigger(room)
                
                room.last_message_time = time.time()
                
                if random.random() < 0.85:
                    await asyncio.sleep(random.uniform(1, 2))
                    await self.schedule_next_agent_response(room)
        
        except Exception as e:
            print(f"智能体回应生成失败: {e}")
        
        finally:
            room.agent_locks[agent_type] = False
    
    @staticmethod
    async def generate_agent_response(room: ChatRoom, agent_type: str) -> Optional[str]:
        """生成智能体回应"""
        try:
            agent = room.agent_manager.get_agent(agent_type)
            if not agent:
                return None
            
            from .game_manager import GameManager
            recent_messages = GameManager.get_recent_conversation_context(room, limit=10)
            context = AgentResponseManager._build_agent_context(room, recent_messages, agent_type)
            
            response = await AgentResponseManager._call_crewai_agent(agent, context)
            
            print(f"✅ 智能体 {agent_type} 成功生成响应: {len(response)} 字符")
            return response
                
        except Exception as e:
            print(f"❌ 智能体 {agent_type} 生成回应失败: {type(e).__name__}: {e}")
            fallback = AgentResponseManager._generate_fallback_response(agent_type)
            print(f"🔄 使用备用响应: {fallback}")
            return fallback
    
    @staticmethod
    def _build_agent_context(room: ChatRoom, recent_messages: List[Dict], agent_type: str) -> str:
        """为智能体构建对话上下文"""
        from .game_manager import GameManager
        base_context = GameManager._build_agent_context(room, recent_messages, agent_type)
        
        human_role_info = ""
        role_tips = ""
        
        for user in room.users.values():
            role_to_agent = {
                UserRole.HUMAN_FOLLOWER: "follower",
                UserRole.HUMAN_COURTESAN: "courtesan", 
                UserRole.HUMAN_MADAM: "madam"
            }
            if role_to_agent.get(user.role) == agent_type:
                human_role_info = f"\n⚠️ 注意：有真人玩家 {user.username} 正在扮演{AgentResponseManager.get_agent_display_name(agent_type)}角色。"
                role_tips = "..."
                break
        
        task_description = "..." # 根据agent_type定义
        
        return f"{base_context}\n{human_role_info}\n{task_description}\n{role_tips}"
    
    @staticmethod
    async def _call_crewai_agent(agent, context: str) -> str:
        """调用CrewAI智能体生成响应"""
        from crewai import Task, Crew
        
        try:
            agent_instance = agent.get_agent_instance()
            
            task = Task(
                description=context,
                expected_output="角色的自然回应",
                agent=agent_instance
            )
            
            crew = Crew(
                agents=[agent_instance],
                tasks=[task],
                verbose=False,
                process_type="sequential",
                max_iter=1
            )
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, lambda: crew.kickoff()),
                timeout=30.0
            )
            
            response_text = str(response.raw if hasattr(response, 'raw') else response).strip()
            
            if not response_text or len(response_text) < 3:
                raise ValueError("响应内容无效")
            
            return AgentResponseManager._clean_tool_artifacts(response_text)
            
        except Exception as e:
            print(f"❌ CrewAI调用失败: {type(e).__name__}: {e}")
            raise e
    
    @staticmethod
    def _clean_tool_artifacts(response: str) -> str:
        """清理响应中的工具调用残留文本"""
        import re
        response = re.sub(r'\{\{[^}]*"action"[^}]*\}\}', '', response)
        response = re.sub(r'\{[^}]*"action"[^}]*\}', '', response)
        response = re.sub(r'.*(?:改变数值|触发事件|使用工具|tool|Tool).*', '', response, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', response).strip()
    
    @staticmethod
    def _generate_fallback_response(agent_type: str) -> str:
        """生成备用响应"""
        timestamp_factor = int(time.time()) % 100
        responses = {
            "narrator": [f"夜色更深了... ({timestamp_factor})"],
            "courtesan": [f"公子看起来有些心事重重呢... ({timestamp_factor})"],
            "madam": [f"客官，老身这里规矩多着呢... ({timestamp_factor})"],
            "follower": [f"属下在此等候指示... ({timestamp_factor})"]
        }
        return random.choice(responses.get(agent_type, [f"智能体{agent_type}正在思考... ({timestamp_factor})"])) 