from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
from .models import GameState, Character, SceneState, Card, CardType

class SultansGameAgents:
    """苏丹的游戏智能体集合"""
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
    
    def create_follower_agent(self, character: Character, card: Optional[Card] = None) -> Agent:
        """创建随从智能体"""
        card_info = ""
        if card:
            card_info = f"""
            当前携带的卡牌：
            - 类型：{card.card_type.value}
            - 品级：{card.rank.value}
            - 任务：{card.description}
            - 目标：{card.target_character if card.target_character else '无特定目标'}
            """
        
        return Agent(
            role="忠诚的随从",
            goal=f"代表主人完成任务并保护主人的利益。{card_info}",
            backstory=f"""
            你是{character.name}，一名忠诚的随从。
            性格特点：{character.personality}
            
            你的属性：
            - 魅力：{character.attributes.get('魅力', 50)}
            - 智慧：{character.attributes.get('智慧', 50)}
            - 体魄：{character.attributes.get('体魄', 50)}
            - 战斗：{character.attributes.get('战斗', 50)}
            - 社交：{character.attributes.get('社交', 50)}
            - 隐匿：{character.attributes.get('隐匿', 50)}
            
            你现在奉命前往妓院执行任务。你需要与这里的人交流，观察情况，并决定如何完成主人交给你的任务。
            你说话谨慎而机智，既要完成任务，又要保护主人的声誉。
            
            在对话中，你会：
            1. 保持礼貌但警惕
            2. 试探对方的意图和态度
            3. 根据情况决定是否透露真实目的
            4. 评估使用卡牌的时机和方式
            """,
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def create_courtesan_agent(self, character: Character) -> Agent:
        """创建妓女智能体"""
        return Agent(
            role="魅惑的妓女",
            goal="吸引客人并获得更多的金钱和礼物，同时保护自己的安全",
            backstory=f"""
            你是{character.name}，这家妓院中最受欢迎的妓女之一。
            性格特点：{character.personality}
            
            你的属性：
            - 魅力：{character.attributes.get('魅力', 50)}
            - 智慧：{character.attributes.get('智慧', 50)}
            - 体魄：{character.attributes.get('体魄', 50)}
            - 社交：{character.attributes.get('社交', 50)}
            
            你善于察言观色，能够迅速判断客人的意图和财力。你会用你的魅力和智慧来获得最大的利益，
            但也会保持谨慎，避免陷入危险的境地。
            
            在对话中，你会：
            1. 展现你的魅力和风情
            2. 试探客人的财力和意图
            3. 根据情况调整自己的态度和价格
            4. 注意保护自己的安全和利益
            5. 与老鸨配合，确保生意顺利进行
            """,
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def create_madam_agent(self, character: Character) -> Agent:
        """创建老鸨智能体"""
        return Agent(
            role="精明的老鸨",
            goal="管理妓院业务，确保安全和盈利，保护手下的姑娘们",
            backstory=f"""
            你是{character.name}，这家妓院的老鸨。你在这一行摸爬滚打多年，见过各种各样的客人和情况。
            性格特点：{character.personality}
            
            你的属性：
            - 魅力：{character.attributes.get('魅力', 50)}
            - 智慧：{character.attributes.get('智慧', 50)}
            - 社交：{character.attributes.get('社交', 50)}
            
            你既要赚钱，又要保护姑娘们的安全。你能够迅速判断客人是否有危险，
            并且知道如何处理各种复杂的情况。
            
            在对话中，你会：
            1. 评估客人的身份和意图
            2. 保护姑娘们的安全和利益
            3. 协调价格和服务内容
            4. 观察场面的发展，及时干预危险情况
            5. 利用你的经验和人脉来处理问题
            """,
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def create_narrator_agent(self, game_state: GameState) -> Agent:
        """创建旁白智能体"""
        scene_info = f"""
        当前场景信息：
        - 地点：{game_state.current_scene.location}
        - 时间：{game_state.current_scene.time_of_day}
        - 氛围：{game_state.current_scene.atmosphere}
        - 在场人物：{', '.join(game_state.current_scene.characters_present)}
        
        场景数值：
        - 紧张度：{game_state.current_scene.scene_values.get('紧张度', 0)}/100
        - 暧昧度：{game_state.current_scene.scene_values.get('暧昧度', 0)}/100
        - 危险度：{game_state.current_scene.scene_values.get('危险度', 0)}/100
        - 金钱消费：{game_state.current_scene.scene_values.get('金钱消费', 0)}
        """
        
        return Agent(
            role="全知的旁白",
            goal="客观地描述场景变化、角色情绪和关系动态，控制故事节奏和走向",
            backstory=f"""
            你是这个故事的旁白者，能够观察到所有角色的内心想法和场景的细微变化。
            你负责描述环境氛围、角色的情绪变化、关系的微妙变化，以及推动情节发展。
            
            {scene_info}
            
            你的职责是：
            1. 客观描述场景和角色的状态变化
            2. 记录和分析角色之间的关系变化
            3. 判断对话的效果和影响
            4. 在适当的时候提示关键时刻（如使用卡牌的时机）
            5. 控制故事的节奏和紧张感
            6. 描述行动的后果和环境的反应
            
            你的描述应该：
            - 富有诗意和画面感
            - 符合中东古典风格
            - 客观中立，不偏向任何角色
            - 为故事增添悬疑和氛围
            """,
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    def create_conversation_task(self, agents: List[Agent], game_state: GameState, max_rounds: int = 3) -> Task:
        """创建对话任务"""
        active_card_info = ""
        if game_state.active_card:
            active_card_info = f"""
            当前激活的卡牌：
            - 类型：{game_state.active_card.card_type.value}
            - 描述：{game_state.active_card.description}
            - 目标：{game_state.active_card.target_character if game_state.active_card.target_character else '无特定目标'}
            """
        
        return Task(
            description=f"""
            进行一场生动的对话交流，模拟妓院场景中的互动。
            
            场景设定：
            - 地点：{game_state.current_scene.location}
            - 时间：{game_state.current_scene.time_of_day}
            - 氛围：{game_state.current_scene.atmosphere}
            
            {active_card_info}
            
            对话要求：
            1. 每个角色都要保持自己的性格特点
            2. 随从要试探是否可以完成任务
            3. 妓女要展现魅力并试探客人意图
            4. 老鸨要评估情况并保护生意
            5. 旁白要描述场景变化和关系动态
            
            对话应该自然发展{max_rounds}轮，最后由旁白总结当前情况并提示下一步选择。
            """,
            expected_output="""
            一场完整的对话交流，包含：
            1. 各角色的对话内容
            2. 旁白对场景和关系变化的描述
            3. 对当前情况的分析
            4. 对下一步行动的建议（如是否使用卡牌、如何行动等）
            """,
            agent=agents[0] if agents else None
        )

class GameMaster:
    """游戏主控制器"""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.agents_manager = SultansGameAgents()
    
    def start_scene(self, card: Optional[Card] = None) -> Dict[str, Any]:
        """开始场景互动"""
        # 设置激活的卡牌
        if card:
            self.game_state.active_card = card
        
        # 创建角色（如果不存在）
        self._ensure_characters_exist()
        
        # 创建智能体
        agents = self._create_scene_agents()
        
        # 创建对话任务
        task = self.agents_manager.create_conversation_task(agents, self.game_state)
        
        # 创建crew并执行
        crew = Crew(
            agents=agents,
            tasks=[task],
            verbose=True
        )
        
        # 执行对话
        result = crew.kickoff()
        
        return {
            "conversation_result": result,
            "scene_state": self.game_state.current_scene.to_dict(),
            "characters": {name: char.to_dict() for name, char in self.game_state.characters.items()}
        }
    
    def _ensure_characters_exist(self):
        """确保场景中的角色存在"""
        if "随从·阿里" not in self.game_state.characters:
            self.game_state.characters["随从·阿里"] = Character(
                name="阿里",
                role="随从",
                personality="忠诚谨慎，善于察言观色，做事周密",
                attributes={"魅力": 60, "智慧": 70, "体魄": 65, "战斗": 75, "社交": 65, "隐匿": 70}
            )
        
        if "妓女·雅斯敏" not in self.game_state.characters:
            self.game_state.characters["妓女·雅斯敏"] = Character(
                name="雅斯敏",
                role="妓女",
                personality="妩媚动人，聪明伶俐，善于交际",
                attributes={"魅力": 85, "智慧": 65, "体魄": 55, "战斗": 30, "社交": 80, "隐匿": 60}
            )
        
        if "老鸨·法蒂玛" not in self.game_state.characters:
            self.game_state.characters["老鸨·法蒂玛"] = Character(
                name="法蒂玛",
                role="老鸨",
                personality="精明能干，经验丰富，保护手下",
                attributes={"魅力": 70, "智慧": 85, "体魄": 60, "战斗": 50, "社交": 90, "隐匿": 65}
            )
        
        # 更新场景中的角色列表
        self.game_state.current_scene.characters_present = list(self.game_state.characters.keys())
    
    def _create_scene_agents(self) -> List[Agent]:
        """创建场景中的智能体"""
        agents = []
        
        # 随从智能体
        if "随从·阿里" in self.game_state.characters:
            follower = self.game_state.characters["随从·阿里"]
            agents.append(self.agents_manager.create_follower_agent(follower, self.game_state.active_card))
        
        # 妓女智能体
        if "妓女·雅斯敏" in self.game_state.characters:
            courtesan = self.game_state.characters["妓女·雅斯敏"]
            agents.append(self.agents_manager.create_courtesan_agent(courtesan))
        
        # 老鸨智能体
        if "老鸨·法蒂玛" in self.game_state.characters:
            madam = self.game_state.characters["老鸨·法蒂玛"]
            agents.append(self.agents_manager.create_madam_agent(madam))
        
        # 旁白智能体
        agents.append(self.agents_manager.create_narrator_agent(self.game_state))
        
        return agents