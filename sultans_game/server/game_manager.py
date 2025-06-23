"""游戏逻辑管理器"""

import uuid
import time
from typing import List, Optional, Dict

from .websocket_models import ChatRoom, ChatUser, UserRole, MessageType
from .message_broadcaster import MessageBroadcaster


class GameManager:
    """游戏逻辑管理器"""
    
    @staticmethod
    def should_trigger_follower_choice(room: ChatRoom) -> bool:
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
    
    @staticmethod
    async def trigger_follower_choice_simple(room: ChatRoom):
        """触发随从选择（简化版本）"""
        try:
            print(f"🎯 触发随从选择阶段（第{room.conversation_count}轮）")
            
            # 进入随从选择阶段
            room.is_follower_choice_phase = True
            room.last_follower_round = room.conversation_count
            
            # 生成3个简单的选择项
            choices = await GameManager.generate_simple_follower_choices(room)
            room.pending_follower_choices = choices
            
            # 通知所有用户进入随从选择阶段
            await MessageBroadcaster.broadcast_to_room(room, {
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
    
    @staticmethod
    async def generate_simple_follower_choices(room: ChatRoom) -> List:
        """生成简单的随从选择项（不依赖复杂的AI调用）"""
        from ..models import FollowerChoice
        
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
    
    @staticmethod
    async def process_follower_choice_input(room: ChatRoom, user: ChatUser, input_content: str):
        """处理随从选择输入"""
        if not room.is_follower_choice_phase:
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
        await GameManager.execute_follower_choice(room, choice_selected, custom_input, user)
    
    @staticmethod
    async def execute_follower_choice(room: ChatRoom, choice: Optional[object], custom_input: Optional[str], user: ChatUser):
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
                await MessageBroadcaster.broadcast_to_room(room, {
                    "type": MessageType.CHAT_MESSAGE.value,
                    "username": user.username,
                    "role": user.role.value,
                    "role_display": "随从",
                    "content": f"🎯 {action_content}",
                    "timestamp": time.time()
                })
                
                # 显示数值变化
                changes_text = ", ".join([f"{k}{v:+d}" for k, v in value_changes.items() if v != 0])
                await MessageBroadcaster.broadcast_to_room(room, {
                    "type": MessageType.SYSTEM_MESSAGE.value,
                    "content": f"📊 数值变化：{changes_text}",
                    "timestamp": time.time()
                })
                
            else:
                # 使用自定义输入
                action_content = custom_input or "进行了一个神秘的行动"
                
                # 广播自定义行动
                await MessageBroadcaster.broadcast_to_room(room, {
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
            await MessageBroadcaster.broadcast_scene_update(room)
            
            # 记录对话历史
            if room.game_state and room.game_state.current_scene:
                room.game_state.current_scene.add_conversation("随从", action_content)
            
            # 增加对话计数
            room.conversation_count += 1
            
        except Exception as e:
            print(f"❌ 执行随从选择失败: {e}")
            room.is_follower_choice_phase = False
    
    @staticmethod
    async def end_game_due_to_limit(room: ChatRoom):
        """因为轮数限制结束游戏"""
        await MessageBroadcaster.broadcast_to_room(room, {
            "type": MessageType.GAME_END.value,
            "content": "🔚 游戏结束：已达到20轮对话限制",
            "reason": "对话轮数达到上限",
            "final_values": room.game_state.current_scene.scene_values if room.game_state else {},
            "timestamp": time.time()
        })
    
    @staticmethod
    async def announce_card_mission(room: ChatRoom, card):
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
        await MessageBroadcaster.broadcast_to_room(room, {
            "type": MessageType.AGENT_MESSAGE.value,
            "agent_type": "narrator",
            "agent_name": "旁白者",
            "content": mission_content,
            "timestamp": time.time()
        })
    
    @staticmethod
    async def check_follower_choice_trigger(room: ChatRoom):
        """检查是否满足随从选择触发条件"""
        if not room.game_state:
            return
        
        # 检查是否有随从玩家
        has_follower = any(user.role == UserRole.HUMAN_FOLLOWER for user in room.users.values())
        if not has_follower:
            return
        
        from ..models import GamePhase
        
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
        last_trigger_time = getattr(room, '_last_follower_trigger', 0)
        min_interval = 30  # 至少间隔30秒
        
        if should_trigger and (time.time() - last_trigger_time) > min_interval:
            print(f"🎯 自动触发随从选择：暧昧度={ambiguity}, 紧张度={tension}, 危险度={danger}")
            room._last_follower_trigger = time.time()
            await GameManager.trigger_follower_choice_phase(room)
    
    @staticmethod
    async def trigger_follower_choice_phase(room: ChatRoom):
        """触发随从选择阶段"""
        if not room.game_state or not room.agent_coordinator:
            return
        
        from ..models import GamePhase
        
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
            from ..tools import set_game_state
            set_game_state(room.game_state)
            
            # 生成选择项
            choices = await GameManager.generate_follower_choices(room, follower_agent)
            
            if choices:
                # 将选择项添加到游戏状态
                room.game_state.pending_follower_choices = choices
                
                # 广播选择请求
                await MessageBroadcaster.broadcast_to_room(room, {
                    "type": "follower_choices",  # 使用前端识别的消息类型
                    "choices": [choice.__dict__ for choice in choices],
                    "round_number": room.game_state.follower_rounds_used,
                    "max_rounds": room.game_state.max_follower_rounds,
                    "scene_values": room.game_state.current_scene.scene_values,
                    "message": "🎯 随从，现在需要你做出选择来推进计划..."
                })
                
                # 广播阶段变化
                await MessageBroadcaster.broadcast_to_room(room, {
                    "type": MessageType.GAME_PHASE_CHANGE.value,
                    "old_phase": "free_chat",
                    "new_phase": "follower_choice",
                    "round_number": room.game_state.follower_rounds_used,
                    "max_rounds": room.game_state.max_follower_rounds
                })
                
        except Exception as e:
            print(f"触发随从选择阶段时出错: {e}")
    
    @staticmethod
    async def generate_follower_choices(room: ChatRoom, follower_agent) -> List:
        """生成随从选择项"""
        try:
            # 构建上下文
            recent_messages = GameManager.get_recent_conversation_context(room, limit=8)
            context = GameManager._build_agent_context(room, recent_messages, "follower")
            
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
            from .agent_response_manager import AgentResponseManager
            response = await AgentResponseManager._call_crewai_agent(follower_agent, choice_prompt)
            
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
                    from ..models import FollowerChoice
                    
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
        from ..models import FollowerChoice
        
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
    
    @staticmethod
    def get_recent_conversation_context(room: ChatRoom, limit: int = 10) -> List[Dict]:
        """获取最近的对话上下文"""
        if not room.game_state or not room.game_state.current_scene:
            return []
        
        conversation_history = room.game_state.current_scene.conversation_history
        return conversation_history[-limit:] if conversation_history else []
    
    @staticmethod
    def _build_agent_context(room: ChatRoom, recent_messages: List[Dict], agent_type: str) -> str:
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
        
        return f"{conversation_text}\n{scene_info}\n{card_info}" 