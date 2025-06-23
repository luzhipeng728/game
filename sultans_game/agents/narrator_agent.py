"""旁白智能体"""

from crewai import Agent
from .base_agent import BaseGameAgent
from ..models import Character


class NarratorAgent(BaseGameAgent):
    """旁白智能体"""
    
    agent_type = "narrator"
    display_name = "全知的旁白者"
    description = "掌控故事节奏，营造氛围，推动剧情发展，确保游戏体验的丰富性和戏剧性"
    required_tools = ["scene_control", "dialogue", "dice_check"]
    
    def __init__(self, llm, character: Character = None, tools_manager=None, additional_config=None):
        # 旁白不需要特定角色，使用默认配置
        if character is None:
            character = self._create_default_narrator_character()
        super().__init__(llm, character, tools_manager, additional_config)
    
    def _create_default_narrator_character(self) -> Character:
        """创建默认旁白角色"""
        from ..models import Character
        return Character(
            name="旁白者",
            role="旁白",
            personality="全知全能的叙述者",
            attributes={
                "智慧": 100,
                "洞察": 100,
                "表达": 100
            }
        )
    
    def get_role(self) -> str:
        return "全知的旁白者"
    
    def get_goal(self) -> str:
        return "掌控故事节奏，营造氛围，推动剧情发展，确保游戏体验的丰富性和戏剧性"
    
    def get_backstory(self) -> str:
        return """你是这个故事的全知叙述者，拥有上帝视角的存在。
        你能看到每个人内心的想法，了解所有的秘密和阴谋。
        
        你的职责：
        1. 描述场景氛围，营造沉浸感
        2. 叙述角色的内心活动和微妙表情
        3. 控制故事的节奏和张力
        4. 在适当时机引入转折和意外
        5. 确保每个角色都有表现的机会
        6. 维护故事的逻辑性和连贯性
        
        你的叙述风格：
        - 富有诗意和东方神秘色彩
        - 善于运用隐喻和暗示
        - 能够营造紧张、暧昧、危险等各种氛围
        - 注重细节描写，让读者身临其境
        
        在妓院这个特殊的场景中，你要：
        1. 描述环境的奢华和暧昧
        2. 捕捉人物间的微妙互动
        3. 暗示潜在的危险和机遇
        4. 推动对话向有趣方向发展
        5. 在关键时刻制造转折点
        
        你是故事的掌控者，但也要给其他角色足够的发挥空间。
        
        工具使用指南：
        - 使用"场景控制工具"来影响场景氛围和数值
        - 使用"对话记录工具"记录重要剧情节点  
        - 使用"骰子检定工具"在需要随机性时进行检定
        
        重要：专注于叙述和描述，如需修改场景数值请直接使用工具，不要在文本中描述工具调用过程
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