"""商人智能体 - 扩展示例"""

from crewai import Agent
from .base_agent import BaseGameAgent
from ..models import Character, Card


class MerchantAgent(BaseGameAgent):
    """商人智能体"""
    
    agent_type = "merchant"
    display_name = "精明的商人"
    description = "善于交易和获取信息的商人，在市场中寻找商机和情报"
    required_tools = ["dialogue", "relationship", "scene_control"]
    
    def get_role(self) -> str:
        return f"精明的商人 - {self.character.name}"
    
    def get_goal(self) -> str:
        return "在市场中寻找商机，与客户建立关系，收集有价值的商业情报"
    
    def get_backstory(self) -> str:
        return f"""你是{self.character.name}，一位经验丰富的商人。
        你游走于各个城市之间，既买卖货物，也收集各种有用的信息。
        
        你的属性：
        {self.get_character_attributes_text()}
        
        你的特长：
        1. 敏锐的商业嗅觉，能发现赚钱的机会
        2. 广泛的人脉网络，认识各行各业的人
        3. 善于察言观色，能从闲聊中获取情报
        4. 精通讨价还价，总能争取到最好的价格
        
        你的行为风格：
        - 友善而机敏，善于与人建立关系
        - 对金钱和利润非常敏感
        - 喜欢收集各种小道消息和传闻
        - 在商谈时精明计算，但不会显得刻薄
        
        你的目标：
        1. 寻找有利润的交易机会
        2. 建立新的商业关系
        3. 收集有价值的市场信息
        4. 保护自己的商业利益
        
        工具使用指南：
        - 使用"对话记录工具"记录重要商业信息
        - 使用"关系管理工具"维护客户关系
        - 使用"场景控制工具"调整商业氛围和交易热度
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
    
    def can_handle_card(self, card: Card) -> bool:
        """商人特别适合处理贸易和信息类卡牌"""
        if not card:
            return True
        
        # 商人擅长的卡牌类型
        merchant_related_keywords = [
            "贸易", "交易", "商业", "信息", "情报", 
            "金钱", "货物", "市场", "谈判"
        ]
        
        card_text = f"{card.title} {card.description}".lower()
        return any(keyword in card_text for keyword in merchant_related_keywords) 