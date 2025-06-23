 

from crewai import Agent
from .base_agent import BaseGameAgent
from ..models import Character, FollowerChoice, GamePhase
from typing import Dict, Any, List, Optional
import re
import json


class EvaluatorAgent(BaseGameAgent):
    """评分智能体 - 专门负责评估玩家选择和输入的质量，并分配相应的场景数值变化"""
    
    agent_type = "evaluator"
    display_name = "智能评分员"
    description = "专业的游戏评分系统，负责评估玩家选择的质量和风险，并据此分配场景数值变化"
    required_tools = ["scene_control"]
    
    def __init__(self, llm, character: Character = None, tools_manager=None, additional_config=None):
        if character is None:
            character = self._create_default_evaluator_character()
        super().__init__(llm, character, tools_manager, additional_config)
    
    def _create_default_evaluator_character(self) -> Character:
        """创建默认评分员角色"""
        from ..models import Character
        return Character(
            name="智能评分员",
            role="评分员",
            personality="公正、专业、严谨的评分系统",
            attributes={
                "智慧": 100,
                "公正": 100,
                "分析": 100,
                "严谨": 100
            }
        )
    
    def get_role(self) -> str:
        return "智能场景数值评估员"
    
    def get_goal(self) -> str:
        return "根据玩家的选择和输入内容，公正地评估其质量和风险，并分配合理的场景数值变化"
    
    def get_backstory(self) -> str:
        return """你是游戏中的智能评分系统，拥有完善的评估机制和丰富的经验。

你的职责：
1. 评估随从玩家的选择质量
2. 分析玩家自定义输入的内容质量
3. 根据内容合理性分配场景数值变化
4. 识别不当内容（粗口、无意义输入等）并给予低分

评估维度：
- 内容质量（0-10分）：是否有意义、是否符合场景
- 创意程度（0-10分）：是否有创新性和想象力
- 风险评估（0-10分）：行为的危险程度
- 角色契合度（0-10分）：是否符合随从角色设定

数值分配原则：
1. 高质量选择：增加正面数值（魅力、智慧等）
2. 创意选择：增加暧昧度、情报等
3. 高风险选择：增加危险度、紧张度
4. 粗口/无意义输入：大幅增加危险度，减少其他数值

你必须始终保持公正和一致性，确保评分结果能够推动游戏的平衡发展。

重要：你的回应必须是JSON格式，包含评分详情和数值变化。
"""
    
    def _create_agent(self) -> Agent:
        return Agent(
            role=self.get_role(),
            goal=self.get_goal(),
            backstory=self.get_backstory(),
            tools=self.get_tools(),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )
    
    def evaluate_follower_choice(self, choice: FollowerChoice, context: str) -> Dict[str, Any]:
        """评估随从选择"""
        prompt = f"""
请评估以下随从选择的质量：

选择内容：{choice.content}
风险等级：{choice.risk_level}
预期变化：{choice.expected_values}
游戏上下文：{context}

请返回JSON格式的评估结果：
{{
    "content_quality": 整数0-10，
    "creativity": 整数0-10，
    "risk_assessment": 整数0-10，
    "role_fitting": 整数0-10，
    "value_changes": {{
        "紧张度": 整数变化值,
        "暧昧度": 整数变化值,
        "危险度": 整数变化值,
        "金钱消费": 整数变化值
    }},
    "explanation": "评分理由说明"
}}
"""
        
        try:
            response = self._call_llm_directly(prompt)
            return self._parse_evaluation_response(response)
        except Exception as e:
            print(f"评估选择时出错: {e}")
            return self._get_default_evaluation()
    
    def evaluate_user_input(self, user_input: str, context: str) -> Dict[str, Any]:
        """评估用户自定义输入"""
        prompt = f"""
请评估以下用户输入的质量：

用户输入：{user_input}
游戏上下文：{context}

评估标准：
1. 内容质量：是否有意义、是否符合游戏场景
2. 创意程度：是否有创新性
3. 不当内容检测：是否包含粗口、无意义文字、恶意内容
4. 角色契合度：是否符合随从身份

特别注意：
- 粗口、脏话：大幅增加危险度（+15到+25）
- 无意义输入（如"aaaa"、"哈哈哈"）：增加危险度（+10）
- 高质量创意内容：增加正面数值
- 符合角色设定的内容：适当奖励

请返回JSON格式的评估结果：
{{
    "content_quality": 整数0-10，
    "creativity": 整数0-10，
    "inappropriate_content": 布尔值，
    "role_fitting": 整数0-10，
    "value_changes": {{
        "紧张度": 整数变化值,
        "暧昧度": 整数变化值,
        "危险度": 整数变化值,
        "金钱消费": 整数变化值
    }},
    "explanation": "评分理由说明"
}}
"""
        
        try:
            response = self._call_llm_directly(prompt)
            return self._parse_evaluation_response(response)
        except Exception as e:
            print(f"评估用户输入时出错: {e}")
            return self._get_default_user_evaluation(user_input)
    
    def _call_llm_directly(self, prompt: str) -> str:
        """直接调用LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return ""
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """解析评估响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except Exception as e:
            print(f"解析JSON失败: {e}")
        
        return self._get_default_evaluation()
    
    def _get_default_evaluation(self) -> Dict[str, Any]:
        """获取默认评估结果"""
        return {
            "content_quality": 5,
            "creativity": 5,
            "risk_assessment": 5,
            "role_fitting": 5,
            "value_changes": {
                "紧张度": 2,
                "暧昧度": 1,
                "危险度": 3,
                "金钱消费": 1
            },
            "explanation": "默认评估结果"
        }
    
    def _get_default_user_evaluation(self, user_input: str) -> Dict[str, Any]:
        """获取用户输入的默认评估结果"""
        # 简单的不当内容检测
        inappropriate_keywords = ["操", "草", "傻逼", "妈的", "卧槽", "shit", "fuck"]
        has_inappropriate = any(keyword in user_input.lower() for keyword in inappropriate_keywords)
        
        # 检测无意义输入
        is_meaningless = (len(set(user_input)) <= 2 and len(user_input) > 3) or len(user_input.strip()) == 0
        
        if has_inappropriate or is_meaningless:
            return {
                "content_quality": 1,
                "creativity": 1,
                "inappropriate_content": True,
                "role_fitting": 1,
                "value_changes": {
                    "紧张度": 8,
                    "暧昧度": -3,
                    "危险度": 15,
                    "金钱消费": 0
                },
                "explanation": "检测到不当内容或无意义输入，严重扣分"
            }
        
        return {
            "content_quality": 6,
            "creativity": 5,
            "inappropriate_content": False,
            "role_fitting": 6,
            "value_changes": {
                "紧张度": 3,
                "暧昧度": 2,
                "危险度": 4,
                "金钱消费": 1
            },
            "explanation": "一般质量的用户输入"
        }
    
    def get_evaluation_summary(self, evaluation: Dict[str, Any]) -> str:
        """获取评估摘要信息"""
        scores = []
        scores.append(f"内容质量: {evaluation.get('content_quality', 0)}/10")
        scores.append(f"创意程度: {evaluation.get('creativity', 0)}/10")
        
        if 'risk_assessment' in evaluation:
            scores.append(f"风险评估: {evaluation.get('risk_assessment', 0)}/10")
        
        scores.append(f"角色契合: {evaluation.get('role_fitting', 0)}/10")
        
        value_changes = evaluation.get('value_changes', {})
        changes = []
        for key, value in value_changes.items():
            if value != 0:
                symbol = "+" if value > 0 else ""
                changes.append(f"{key}{symbol}{value}")
        
        summary = f"📊 评分: {' | '.join(scores)}"
        if changes:
            summary += f"\n📈 数值变化: {' | '.join(changes)}"
        
        explanation = evaluation.get('explanation', '')
        if explanation:
            summary += f"\n💬 评价: {explanation}"
        
        return summary