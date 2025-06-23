"""智能体协调器 - 解决智能体各自为政的问题"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from ..models import GameState, GamePhase, FollowerChoice, GameResult
from .evaluator_agent import EvaluatorAgent


class MessageType(Enum):
    """消息类型枚举"""
    EXPLORATION = "exploration"  # 探索动作
    INQUIRY = "inquiry"  # 询问信息
    TRANSACTION = "transaction"  # 交易行为
    SOCIAL = "social"  # 社交互动
    COMBAT = "combat"  # 战斗动作
    MYSTERY = "mystery"  # 神秘事件
    GENERAL = "general"  # 一般对话


class ResponsePriority(Enum):
    """响应优先级"""
    CRITICAL = 5  # 关键响应，必须立即处理
    HIGH = 4      # 高优先级
    MEDIUM = 3    # 中等优先级
    LOW = 2       # 低优先级
    BACKGROUND = 1 # 背景响应


@dataclass
class AgentResponse:
    """智能体响应数据结构"""
    agent_name: str
    agent_type: str
    content: str
    priority: ResponsePriority
    timestamp: float
    context_relevance: float  # 上下文相关性评分 0-1
    uniqueness_score: float   # 独特性评分 0-1
    story_progress_value: float  # 故事推进价值 0-1


class MessageAnalyzer:
    """消息意图分析器"""
    
    @staticmethod
    def analyze_message(content: str, conversation_history: List[Dict]) -> MessageType:
        """分析消息类型"""
        content_lower = content.lower()
        
        # 探索动作关键词
        exploration_keywords = ["环顾", "观察", "查看", "探索", "搜寻", "靠近", "走向"]
        if any(keyword in content_lower for keyword in exploration_keywords):
            return MessageType.EXPLORATION
        
        # 询问信息关键词
        inquiry_keywords = ["询问", "打听", "问", "秘密", "消息", "情报", "知道"]
        if any(keyword in content_lower for keyword in inquiry_keywords):
            return MessageType.INQUIRY
        
        # 交易行为关键词
        transaction_keywords = ["银子", "金钱", "买", "卖", "交易", "付费", "报酬"]
        if any(keyword in content_lower for keyword in transaction_keywords):
            return MessageType.TRANSACTION
        
        # 社交互动关键词
        social_keywords = ["聊天", "交谈", "认识", "朋友", "介绍"]
        if any(keyword in content_lower for keyword in social_keywords):
            return MessageType.SOCIAL
        
        # 神秘事件关键词
        mystery_keywords = ["奇怪", "神秘", "异常", "诡异", "隐藏", "机密"]
        if any(keyword in content_lower for keyword in mystery_keywords):
            return MessageType.MYSTERY
        
        return MessageType.GENERAL
    
    @staticmethod
    def get_preferred_agents(message_type: MessageType) -> List[Tuple[str, ResponsePriority]]:
        """根据消息类型获取优选智能体及其优先级"""
        preference_map = {
            MessageType.EXPLORATION: [
                ("narrator", ResponsePriority.HIGH),
                ("follower", ResponsePriority.MEDIUM),
                ("courtesan", ResponsePriority.LOW)
            ],
            MessageType.INQUIRY: [
                ("courtesan", ResponsePriority.HIGH),
                ("madam", ResponsePriority.MEDIUM),
                ("narrator", ResponsePriority.LOW)
            ],
            MessageType.TRANSACTION: [
                ("madam", ResponsePriority.CRITICAL),
                ("courtesan", ResponsePriority.HIGH),
                ("narrator", ResponsePriority.LOW)
            ],
            MessageType.SOCIAL: [
                ("courtesan", ResponsePriority.HIGH),
                ("follower", ResponsePriority.MEDIUM),
                ("madam", ResponsePriority.LOW)
            ],
            MessageType.MYSTERY: [
                ("narrator", ResponsePriority.CRITICAL),
                ("madam", ResponsePriority.HIGH),
                ("courtesan", ResponsePriority.MEDIUM)
            ],
            MessageType.GENERAL: [
                ("narrator", ResponsePriority.MEDIUM),
                ("courtesan", ResponsePriority.MEDIUM),
                ("follower", ResponsePriority.LOW)
            ]
        }
        
        return preference_map.get(message_type, [])


class ResponseEvaluator:
    """响应质量评估器"""
    
    @staticmethod
    def evaluate_response(response_content: str, 
                         message_content: str,
                         conversation_history: List[Dict],
                         agent_type: str) -> Tuple[float, float, float]:
        """评估响应质量
        
        Returns:
            (context_relevance, uniqueness_score, story_progress_value)
        """
        
        # 上下文相关性评估
        context_relevance = ResponseEvaluator._calculate_context_relevance(
            response_content, message_content, conversation_history
        )
        
        # 独特性评估
        uniqueness_score = ResponseEvaluator._calculate_uniqueness(
            response_content, conversation_history
        )
        
        # 故事推进价值评估
        story_progress_value = ResponseEvaluator._calculate_story_progress_value(
            response_content, agent_type
        )
        
        return context_relevance, uniqueness_score, story_progress_value
    
    @staticmethod
    def _calculate_context_relevance(response: str, message: str, history: List[Dict]) -> float:
        """计算上下文相关性"""
        # 简单的关键词匹配评估
        message_words = set(message.lower().split())
        response_words = set(response.lower().split())
        
        # 计算词汇重叠度
        overlap = len(message_words & response_words)
        relevance = min(overlap / max(len(message_words), 1), 1.0)
        
        # 如果回应太短，降低评分
        if len(response) < 10:
            relevance *= 0.5
        
        return relevance
    
    @staticmethod
    def _calculate_uniqueness(response: str, history: List[Dict]) -> float:
        """计算独特性评分"""
        if not history:
            return 1.0
        
        # 检查与历史消息的相似性
        recent_responses = [msg.get("content", "") for msg in history[-5:]]
        
        similarity_scores = []
        for historical_response in recent_responses:
            # 简单的相似性检测
            if response.strip() == historical_response.strip():
                similarity_scores.append(1.0)  # 完全相同
            elif len(set(response.split()) & set(historical_response.split())) > 3:
                similarity_scores.append(0.7)  # 高度相似
            else:
                similarity_scores.append(0.0)  # 不相似
        
        # 独特性 = 1 - 最高相似性
        max_similarity = max(similarity_scores) if similarity_scores else 0
        return 1.0 - max_similarity
    
    @staticmethod
    def _calculate_story_progress_value(response: str, agent_type: str) -> float:
        """计算故事推进价值"""
        # 故事推进关键词
        progress_keywords = [
            "突然", "忽然", "这时", "接着", "然后", "于是",
            "发现", "注意到", "意识到", "感觉到",
            "传来", "响起", "出现", "消失"
        ]
        
        progress_score = 0.0
        for keyword in progress_keywords:
            if keyword in response:
                progress_score += 0.2
        
        # 不同类型的智能体有不同的基础推进能力
        agent_progress_bonus = {
            "narrator": 0.8,    # 旁白者最擅长推进故事
            "madam": 0.6,       # 老鸨能推进剧情
            "courtesan": 0.4,   # 妓女提供信息
            "follower": 0.3     # 随从观察
        }
        
        base_bonus = agent_progress_bonus.get(agent_type, 0.3)
        return min(progress_score + base_bonus, 1.0)


class AgentCoordinator:
    """智能体协调器 - 解决各自为政的问题"""
    
    def __init__(self, llm, tools_manager=None):
        self.llm = llm
        self.tools_manager = tools_manager
        self.agents = {}
        self.conversation_history = []
        self.last_responses = []
        self.active_agents = set()
        
        # 新增游戏状态管理
        self.game_phase = GamePhase.FREE_CHAT
        self.follower_rounds = 0
        self.max_follower_rounds = 5
        self.scene_values = {
            "tension": 0,    # 紧张度
            "suspicion": 0,  # 怀疑度
            "charm": 0,      # 魅力值
            "skill": 0,      # 技巧值
            "composure": 0   # 镇定值
        }
        self.target_values = {
            "tension": 30,
            "suspicion": -20,
            "charm": 25,
            "skill": 20,
            "composure": 15
        }
        
        # 创建评分智能体
        self.evaluator = EvaluatorAgent(llm, tools_manager=tools_manager)
        
        # 初始化工具
        self._init_tools()
        
    def add_to_history(self, message_type: str, content: str, 
                      username: str = None, agent_name: str = None):
        """添加消息到历史记录"""
        self.conversation_history.append({
            "type": message_type,
            "content": content,
            "username": username,
            "agent_name": agent_name,
            "timestamp": time.time()
        })
        
        # 保持历史记录长度
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-30:]
    
    async def coordinate_agent_responses(self, user_message: str, scene_state: dict, username: str, user_role: str) -> List[Dict]:
        """协调智能体响应 - 现在支持游戏阶段控制"""
        
        # 检查是否是随从角色的选择
        if self.game_phase == GamePhase.FOLLOWER_CHOICE and user_role == 'human_follower':
            return await self._handle_follower_choice(user_message, scene_state, username)
        
        # 检查是否需要进入随从选择阶段
        if self._should_trigger_follower_choice(user_message, scene_state):
            return await self._trigger_follower_choice(scene_state, username)
        
        # 正常的智能体响应流程
        analysis = await self._analyze_message_intent(user_message, scene_state)
        
        # 选择合适的智能体
        selected_agents = self._select_responding_agents(analysis, scene_state)
        
        # 并行生成响应
        responses = await self._generate_agent_responses(
            selected_agents, user_message, scene_state, analysis
        )
        
        # 评估和排序响应
        final_responses = await self._evaluate_and_rank_responses(
            responses, user_message, scene_state, analysis
        )
        
        # 更新对话历史
        self._update_conversation_history(user_message, final_responses, scene_state)
        
        return final_responses
    
    def _should_trigger_follower_choice(self, message: str, scene_state: dict) -> bool:
        """判断是否应该触发随从选择阶段"""
        if self.game_phase != GamePhase.FREE_CHAT:
            return False
        
        if self.follower_rounds >= self.max_follower_rounds:
            return False
        
        # 检查是否有随从在房间中
        has_follower = any(user.get('role') == 'human_follower' 
                          for user in scene_state.get('users', []))
        if not has_follower:
            return False
        
        # 简单的触发条件：消息包含动作词汇或紧张度达到一定程度
        action_keywords = ['行动', '动作', '做什么', '选择', '决定', '怎么办']
        tension = scene_state.get('tension', 0)
        
        return (tension > 10 and self.follower_rounds < 3) or \
               any(keyword in message for keyword in action_keywords)
    
    async def _trigger_follower_choice(self, scene_state: dict, username: str) -> List[Dict]:
        """触发随从选择阶段"""
        self.game_phase = GamePhase.FOLLOWER_CHOICE
        self.follower_rounds += 1
        
        # 获取随从智能体
        follower_agent = self.agents.get('follower')
        if not follower_agent:
            return []
        
        # 生成选择选项
        choices = await self._generate_follower_choices(scene_state)
        
        # 构建特殊响应，通知前端进入选择模式
        response = {
            'agent_type': 'system',
            'agent_name': '游戏系统',
            'content': f'🎯 第{self.follower_rounds}轮：随从需要做出选择...',
            'response_type': 'follower_choices',
            'choices': choices,
            'current_round': self.follower_rounds,
            'max_rounds': self.max_follower_rounds,
            'scene_values': self.scene_values.copy()
        }
        
        return [response]
    
    async def _generate_follower_choices(self, scene_state: dict) -> List[Dict]:
        """生成随从的选择选项"""
        follower_agent = self.agents.get('follower')
        if not follower_agent:
            return []
        
        try:
            # 请求随从智能体生成选择
            prompt = f"""
当前场景状态：{json.dumps(scene_state, ensure_ascii=False, indent=2)}
当前数值状态：{json.dumps(self.scene_values, ensure_ascii=False)}
目标数值：{json.dumps(self.target_values, ensure_ascii=False)}
轮次：{self.follower_rounds}/{self.max_follower_rounds}

请生成3个不同的行动选择，每个选择都应该有不同的风险等级和预期效果。
返回格式必须是JSON数组，每个选择包含：
- choice_id: 唯一ID
- content: 行动描述
- risk_level: 风险等级(1-5)
- expected_values: 预期数值变化(字典格式)
"""
            
            response = await follower_agent.agenerate_response(prompt, scene_state)
            
            # 解析JSON响应
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                choices_data = json.loads(json_match.group())
                return choices_data[:3]  # 限制为3个选择
            
        except Exception as e:
            print(f"生成随从选择时出错: {e}")
        
        # 默认选择
        return [
            {
                "choice_id": "safe_1",
                "content": "小心观察周围环境，寻找安全的路线",
                "risk_level": 1,
                "expected_values": {"composure": 2, "tension": -1}
            },
            {
                "choice_id": "balanced_1", 
                "content": "主动与其他人交谈，试探虚实",
                "risk_level": 3,
                "expected_values": {"charm": 3, "suspicion": 2, "skill": 1}
            },
            {
                "choice_id": "risky_1",
                "content": "大胆行动，直接接近目标",
                "risk_level": 5,
                "expected_values": {"skill": 5, "tension": 8, "suspicion": 5}
            }
        ]
    
    async def _handle_follower_choice(self, choice_data: str, scene_state: dict, username: str) -> List[Dict]:
        """处理随从的选择"""
        try:
            # 解析选择数据
            import json
            if choice_data.startswith('choice:'):
                # 预设选择
                choice_id = choice_data.replace('choice:', '')
                choice_content = f"选择了预设行动: {choice_id}"
            else:
                # 自定义输入
                choice_content = choice_data
                choice_id = "custom"
            
            # 使用评分智能体评估选择
            evaluation = await self._evaluate_choice(choice_content, scene_state)
            
            # 应用数值变化
            self._apply_value_changes(evaluation.get('value_changes', {}))
            
            # 检查游戏结束条件
            game_result = self._check_game_end_conditions()
            
            responses = []
            
            # 添加用户选择的显示
            responses.append({
                'agent_type': 'user_choice',
                'agent_name': username,
                'content': choice_content,
                'response_type': 'user_choice'
            })
            
            # 添加评估结果
            responses.append({
                'agent_type': 'evaluator',
                'agent_name': '智能评分员',
                'content': evaluation.get('explanation', ''),
                'response_type': 'evaluation_result',
                'evaluation': evaluation
            })
            
            # 旁白反应
            narrator_response = await self._generate_narrator_reaction(choice_content, evaluation, scene_state)
            if narrator_response:
                responses.append(narrator_response)
            
            # 检查游戏结束
            if game_result:
                self.game_phase = GamePhase.GAME_ENDED
                responses.append({
                    'agent_type': 'system',
                    'agent_name': '游戏系统',
                    'content': '游戏结束！',
                    'response_type': 'game_ended',
                    'result': game_result['result'],
                    'final_score': game_result['score'],
                    'details': game_result['details']
                })
            else:
                # 回到自由聊天阶段
                self.game_phase = GamePhase.FREE_CHAT
                responses.append({
                    'agent_type': 'system',
                    'agent_name': '游戏系统',
                    'content': '回到自由聊天阶段...',
                    'response_type': 'phase_change',
                    'phase': 'free_chat',
                    'follower_rounds': self.follower_rounds,
                    'max_follower_rounds': self.max_follower_rounds
                })
            
            return responses
                
        except Exception as e:
            print(f"处理随从选择时出错: {e}")
            return [{
                'agent_type': 'system',
                'agent_name': '系统错误',
                'content': f'处理选择时出现错误: {str(e)}',
                'response_type': 'error'
            }]
    
    async def _evaluate_choice(self, choice_content: str, scene_state: dict) -> Dict:
        """使用评分智能体评估选择"""
        try:
            evaluation_prompt = f"""
评估以下随从行动的质量和影响：

行动内容: {choice_content}
当前场景: {json.dumps(scene_state, ensure_ascii=False)}
当前数值: {json.dumps(self.scene_values, ensure_ascii=False)}
目标数值: {json.dumps(self.target_values, ensure_ascii=False)}

请评估这个行动并返回JSON格式的结果，包含：
1. scores: 各维度评分(1-10)
2. value_changes: 数值变化
3. explanation: 详细解释
"""
            
            response = await self.evaluator.agenerate_response(evaluation_prompt, scene_state)
            
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"评估选择时出错: {e}")
        
        # 默认评估
        return {
            "scores": {"quality": 5, "risk": 3, "appropriateness": 5},
            "value_changes": {"tension": 1},
            "explanation": "默认评估结果"
        }
    
    def _apply_value_changes(self, changes: Dict[str, int]):
        """应用数值变化"""
        for key, change in changes.items():
            if key in self.scene_values:
                self.scene_values[key] += change
                # 限制数值范围
                self.scene_values[key] = max(-50, min(100, self.scene_values[key]))
    
    def _check_game_end_conditions(self) -> Optional[Dict]:
        """检查游戏结束条件"""
        # 检查轮数限制
        if self.follower_rounds >= self.max_follower_rounds:
            return self._calculate_final_result("rounds_limit")
        
        # 检查数值达成
        targets_met = sum(1 for key, target in self.target_values.items() 
                         if (target > 0 and self.scene_values[key] >= target) or
                            (target < 0 and self.scene_values[key] <= target))
        
        if targets_met >= len(self.target_values) * 0.7:  # 70%目标达成
            return self._calculate_final_result("success")
        
        # 检查失败条件
        if self.scene_values.get('suspicion', 0) > 80:
            return self._calculate_final_result("failure_caught")
        
        return None
    
    def _calculate_final_result(self, reason: str) -> Dict:
        """计算最终结果"""
        base_score = 0
        result = GameResult.NEUTRAL
        details = ""
        
        if reason == "success":
            result = GameResult.SUCCESS
            base_score = 100
            details = "🎉 恭喜！你成功完成了任务，巧妙地达成了各项目标！"
        elif reason == "failure_caught":
            result = GameResult.FAILURE
            base_score = 0
            details = "💀 糟糕！你的行为引起了过多怀疑，随从被抓住了..."
        elif reason == "rounds_limit":
            # 根据目标达成情况判断
            targets_met = sum(1 for key, target in self.target_values.items() 
                             if (target > 0 and self.scene_values[key] >= target) or
                                (target < 0 and self.scene_values[key] <= target))
            completion_rate = targets_met / len(self.target_values)
            
            if completion_rate >= 0.5:
                result = GameResult.SUCCESS
                base_score = int(50 + completion_rate * 50)
                details = f"⏰ 时间到！你完成了{completion_rate:.0%}的目标，算是成功了！"
        else:
                result = GameResult.NEUTRAL
                base_score = int(completion_rate * 50)
                details = f"⏰ 时间到！你只完成了{completion_rate:.0%}的目标，结果平平..."
        
        # 根据各项数值计算奖励修正
        value_bonus = sum(max(0, v) for v in self.scene_values.values()) // 10
        final_score = max(0, base_score + value_bonus)
        
        return {
            "result": result.value,
            "score": final_score,
            "details": details,
            "final_values": self.scene_values.copy()
        }
    
    async def _generate_narrator_reaction(self, choice_content: str, evaluation: Dict, scene_state: dict) -> Optional[Dict]:
        """生成旁白对选择的反应"""
        narrator_agent = self.agents.get('narrator')
        if not narrator_agent:
            return None
        
        try:
            prompt = f"""
根据随从的行动和评估结果，生成旁白反应：

随从行动: {choice_content}
评估结果: {json.dumps(evaluation, ensure_ascii=False)}
当前数值: {json.dumps(self.scene_values, ensure_ascii=False)}
轮次: {self.follower_rounds}/{self.max_follower_rounds}

请生成一段生动的旁白，描述行动的结果和后果。
"""
            
            response = await narrator_agent.agenerate_response(prompt, scene_state)
            
            return {
                'agent_type': 'narrator',
                'agent_name': narrator_agent.display_name,
                'content': response,
                'response_type': 'narrator_reaction'
            }
            
        except Exception as e:
            print(f"生成旁白反应时出错: {e}")
            return None

    def _init_tools(self):
        # 实现初始化工具的逻辑
        pass

    def _analyze_message_intent(self, user_message: str, scene_state: dict) -> MessageType:
        # 实现分析消息意图的逻辑
        pass

    def _select_responding_agents(self, analysis: MessageType, scene_state: dict) -> List[str]:
        # 实现选择合适的智能体的逻辑
        pass

    def _generate_agent_responses(self, agents: List[str], user_message: str, scene_state: dict, analysis: MessageType) -> List[AgentResponse]:
        # 实现生成智能体响应的逻辑
        pass

    def _evaluate_and_rank_responses(self, responses: List[AgentResponse], user_message: str, scene_state: dict, analysis: MessageType) -> List[AgentResponse]:
        # 实现评估和排序响应的逻辑
        pass

    def _update_conversation_history(self, user_message: str, responses: List[AgentResponse], scene_state: dict):
        # 实现更新对话历史的逻辑
        pass