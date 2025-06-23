"""随从智能体 - 游戏中的随从角色，负责生成选择选项"""

from crewai import Agent
from typing import Optional, Dict, Any, List
from .base_agent import BaseGameAgent
from ..models import Character, Card, FollowerChoice, GamePhase
import uuid
import json
import re


class FollowerAgent(BaseGameAgent):
    """随从智能体 - 玩家的忠实随从，现在负责生成选择选项而非直接响应"""
    
    agent_type = "follower"
    display_name = "忠诚随从"
    description = "玩家的忠实随从，负责在关键时刻生成行动选择"
    required_tools = ["game_progress", "scene_control"]
    
    def __init__(self, llm, character: Character, tools_manager=None, 
                 additional_config=None, card: Optional[Card] = None):
        self.card = card
        super().__init__(llm, character, tools_manager, additional_config)
    
    def _create_agent(self) -> Agent:
        """创建CrewAI智能体"""
        return Agent(
            role=self.get_role(),
            goal=self.get_goal(),
            backstory=self.get_backstory(),
            llm=self.llm,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            memory=True
        )
    
    def get_role(self) -> str:
        return "忠诚的随从"
    
    def get_goal(self) -> str:
        return "为玩家生成合理的行动选择，帮助玩家在危险的环境中生存并完成任务"
    
    def get_backstory(self) -> str:
        character_info = f"角色: {self.character.name} | 性格: {self.character.personality}"
        return f"""{character_info}

你是一名忠诚的随从，跟随主人进入了这个充满诱惑和危险的世界。你深知每一个选择都可能影响主人的命运。

你的核心职责：
1. 在关键时刻为主人生成3个不同的行动选择
2. 每个选择都有不同的风险等级和预期效果
3. 选择应该体现不同的策略：保守、平衡、激进
4. 考虑当前场景、角色关系和游戏目标

选择生成原则：
- 选择1：保守安全（低风险，稳定收益）
- 选择2：平衡策略（中等风险，合理收益）
- 选择3：激进冒险（高风险，高收益）

每个选择都应该：
- 符合随从的身份和当前情况
- 有明确的行动描述
- 预估可能的后果
- 考虑对场景数值的影响

你必须时刻记住，主人的安全和任务完成是你的首要考虑。但有时候，适当的冒险也是必要的。
"""
    
    def generate_follower_choices(self, context: str, scene_values: Dict[str, int], active_cards: List = None) -> List[FollowerChoice]:
        """生成随从选择选项"""
        
        # 构建当前状态信息
        status_info = f"""
当前场景数值：
- 紧张度: {scene_values.get('紧张度', 0)}
- 暧昧度: {scene_values.get('暧昧度', 0)}
- 危险度: {scene_values.get('危险度', 0)}
- 金钱消费: {scene_values.get('金钱消费', 0)}

当前情况：{context}
"""
        
        # 添加卡片信息
        card_info = ""
        if active_cards:
            card_info = "\n激活的任务卡片：\n"
            for card in active_cards:
                card_info += f"- {card.title}: {card.usage_objective}\n"
                if card.success_condition:
                    card_info += f"  成功条件: {card.success_condition}\n"
        
        prompt = f"""
{status_info}
{card_info}

请为随从生成3个行动选择，每个选择具有不同的策略风格：

1. 保守选择 - 低风险，稳妥的行动
2. 平衡选择 - 中等风险，平衡的策略
3. 激进选择 - 高风险，大胆的行动

每个选择需要包含：
- 具体的行动描述（20-50字）
- 预期的场景数值变化
- 风险等级（1-5）

请返回JSON格式：
{{
    "choices": [
        {{
            "content": "选择1的具体行动描述",
            "risk_level": 1或2,
            "expected_values": {{
                "紧张度": 变化值,
                "暧昧度": 变化值,
                "危险度": 变化值,
                "金钱消费": 变化值
            }},
            "description": "这个选择的预期后果和说明"
        }},
        {{
            "content": "选择2的具体行动描述",
            "risk_level": 3,
            "expected_values": {{
                "紧张度": 变化值,
                "暧昧度": 变化值,
                "危险度": 变化值,
                "金钱消费": 变化值
            }},
            "description": "这个选择的预期后果和说明"
        }},
        {{
            "content": "选择3的具体行动描述",
            "risk_level": 4或5,
            "expected_values": {{
                "紧张度": 变化值,
                "暧昧度": 变化值,
                "危险度": 变化值,
                "金钱消费": 变化值
            }},
            "description": "这个选择的预期后果和说明"
        }}
    ]
}}

注意：选择内容要具体生动，符合当前场景，并体现随从的忠诚和智慧。
"""
        
        try:
            response = self._call_llm_directly(prompt)
            choices_data = self._parse_choices_response(response)
            
            # 转换为FollowerChoice对象
            choices = []
            for i, choice_data in enumerate(choices_data.get('choices', [])):
                choice = FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content=choice_data.get('content', f'选择{i+1}'),
                    risk_level=choice_data.get('risk_level', i+1),
                    expected_values=choice_data.get('expected_values', {}),
                    description=choice_data.get('description', '')
                )
                choices.append(choice)
            
            return choices
            
        except Exception as e:
            print(f"生成选择时出错: {e}")
            return self._get_default_choices()
    
    def _call_llm_directly(self, prompt: str) -> str:
        """直接调用LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return ""
    
    def _parse_choices_response(self, response: str) -> Dict[str, Any]:
        """解析选择响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except Exception as e:
            print(f"解析选择JSON失败: {e}")
        
        return {"choices": []}
    
    def _get_default_choices(self) -> List[FollowerChoice]:
        """获取默认选择"""
        return [
            FollowerChoice(
                choice_id=str(uuid.uuid4())[:8],
                content="保持低调，观察周围情况",
                risk_level=1,
                expected_values={"紧张度": 1, "暧昧度": 0, "危险度": 1, "金钱消费": 0},
                description="安全但可能错过机会"
            ),
            FollowerChoice(
                choice_id=str(uuid.uuid4())[:8],
                content="主动与人交谈，收集信息",
                risk_level=3,
                expected_values={"紧张度": 3, "暧昧度": 2, "危险度": 2, "金钱消费": 1},
                description="平衡的策略，有一定风险"
            ),
            FollowerChoice(
                choice_id=str(uuid.uuid4())[:8],
                content="大胆行动，直接接近目标",
                risk_level=5,
                expected_values={"紧张度": 5, "暧昧度": 4, "危险度": 6, "金钱消费": 3},
                description="高风险高回报的激进策略"
            )
        ]
    
    def should_respond(self, message_content: str, context: Dict[str, Any]) -> bool:
        """随从现在不直接响应聊天，只在需要生成选择时才参与"""
        # 随从不再直接响应聊天消息，只负责生成选择
        return False
    
    def generate_response(self, message_content: str, context: Dict[str, Any]) -> str:
        """随从不再生成直接响应，此方法保留用于兼容性"""
        return ""
    
    def get_choice_generation_summary(self, choices: List[FollowerChoice]) -> str:
        """获取选择生成摘要"""
        if not choices:
            return "随从暂时无法提供选择建议"
        
        summary = "🎯 随从为你提供了以下行动选择：\n\n"
        
        risk_labels = {1: "🟢 极低", 2: "🟡 低", 3: "🟠 中", 4: "🔴 高", 5: "⚫ 极高"}
        
        for i, choice in enumerate(choices, 1):
            risk_label = risk_labels.get(choice.risk_level, "❓ 未知")
            summary += f"**选择{i}** (风险: {risk_label})\n"
            summary += f"📝 {choice.content}\n"
            summary += f"💭 {choice.description}\n"
            
            # 显示预期数值变化
            changes = []
            for key, value in choice.expected_values.items():
                if value != 0:
                    symbol = "+" if value > 0 else ""
                    changes.append(f"{key}{symbol}{value}")
            
            if changes:
                summary += f"📊 预期变化: {' | '.join(changes)}\n"
            
            summary += "\n"
        
        summary += "💡 请选择一个行动，或输入自定义行动内容。"
        return summary
    
    def can_handle_card(self, card: Card) -> bool:
        """随从可以处理所有类型的卡牌"""
        return True 