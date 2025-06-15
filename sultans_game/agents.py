from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
from .models import GameState, Character, SceneState, Card, CardType
from .tools import GameToolsManager

class SultansGameAgents:
    """苏丹的游戏智能体集合"""
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
    
    def create_follower_agent(self, character: Character, card: Optional[Card] = None, tools_manager: Optional[GameToolsManager] = None) -> Agent:
        """创建随从智能体"""
        card_info = ""
        if card:
            card_info = f"""
            当前携带的卡牌：
            - 类型：{card.card_type.value}
            - 品级：{card.rank.value}
            - 任务：{card.description}
            - 目标：{card.target_character if card.target_character else '无特定目标'}
            - 所需行动：{', '.join(card.required_actions) if card.required_actions else '无特定要求'}
            """
        
        tools = tools_manager.get_tools_by_agent_type("follower") if tools_manager else []
        
        return Agent(
            role=f"忠诚的随从 - {character.name}",
            goal="忠实执行主人交给的卡牌任务，在妓院中巧妙地完成目标",
            backstory=f"""你是苏丹宫廷中一位忠诚可靠的随从，名叫{character.name}。
            你拥有丰富的社交经验和敏锐的观察力。
            
            你的属性：
            - 魅力：{character.charm}
            - 智慧：{character.wisdom}
            - 体魄：{character.physique}
            - 战斗：{character.combat}
            - 社交：{character.social}
            - 隐匿：{character.stealth}
            
            {card_info}
            
            你的任务是在这家神秘的妓院中，与妓女和老鸨巧妙地交涉，
            既要完成卡牌任务，又要避免引起不必要的怀疑或冲突。
            你善于察言观色，知道何时该慷慨，何时该保持低调。
            """,
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )
    
    def create_courtesan_agent(self, character: Character, tools_manager: Optional[GameToolsManager] = None) -> Agent:
        """创建妓女智能体"""
        tools = tools_manager.get_tools_by_agent_type("courtesan") if tools_manager else []
        
        return Agent(
            role=f"魅惑的妓女 - {character.name}",
            goal="通过魅力和智慧与客人建立关系，探知他们的真实意图，保护自己的利益",
            backstory=f"""你是{character.name}，这家妓院中最有名的花魁之一。
            你拥有倾城倾国的美貌和深不可测的智慧。
            
            你的属性：
            - 魅力：{character.charm}（你最强的武器）
            - 智慧：{character.wisdom}
            - 体魄：{character.physique}
            - 社交：{character.social}
            
            你见过各种各样的男人，从商贾到贵族，从士兵到学者。
            你知道如何用一个眼神、一个微笑来操控人心。
            但你也明白，在这个复杂的世界里，每个客人都可能隐藏着秘密。
            
            你的目标是：
            1. 通过魅力吸引客人，让他们愿意为你花费
            2. 巧妙地探知客人的真实身份和意图
            3. 在获得利益的同时保护自己的安全
            4. 与其他姐妹和老鸨维持良好关系
            
            你的行为风格优雅而神秘，既能展现柔美的一面，
            也能在关键时刻展现出坚强和机智。
            """,
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )
    
    def create_madam_agent(self, character: Character, tools_manager: Optional[GameToolsManager] = None) -> Agent:
        """创建老鸨智能体"""
        tools = tools_manager.get_tools_by_agent_type("madam") if tools_manager else []
        
        return Agent(
            role=f"精明的老鸨 - {character.name}",
            goal="管理妓院的日常运营，保护姑娘们的安全，最大化利润，维护妓院声誉",
            backstory=f"""你是{character.name}，这家妓院的老鸨和管理者。
            你曾经也是一位倾国倾城的美人，但岁月让你从台前走到了幕后。
            现在的你更像一位精明的商人和保护者。
            
            你的属性：
            - 魅力：{character.charm}（成熟的魅力）
            - 智慧：{character.wisdom}（丰富的人生阅历）
            - 社交：{character.social}（优秀的交际能力）
            - 声望：{character.reputation}（在道上的地位）
            
            你的职责：
            1. 保证姑娘们的安全，不让她们受到伤害
            2. 识别危险的客人，必要时采取行动
            3. 维护妓院的良好声誉和秩序
            4. 最大化每一笔交易的利润
            5. 处理各种突发状况和纠纷
            
            你见过太多风浪，知道什么样的客人安全，什么样的客人危险。
            你有自己的一套规则，也有自己的底线。
            对待不同的客人，你会采用不同的策略。
            
            你既慈祥又严厉，既温和又果断。
            在你的管理下，这家妓院成为了城中最有名望的风月场所。
            """,
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )
    
    def create_narrator_agent(self, tools_manager: Optional[GameToolsManager] = None) -> Agent:
        """创建旁白智能体"""
        tools = tools_manager.get_tools_by_agent_type("narrator") if tools_manager else []
        
        return Agent(
            role="全知的旁白者",
            goal="掌控故事节奏，营造氛围，推动剧情发展，确保游戏体验的丰富性和戏剧性",
            backstory="""你是这个故事的全知叙述者，拥有上帝视角的存在。
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
            """,
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )

class GameMaster:
    """游戏主控制器"""
    
    def __init__(self, game_state: GameState, llm_model: str = "gpt-4o-mini"):
        self.game_state = game_state
        self.agents_creator = SultansGameAgents(llm_model)
        self.tools_manager = GameToolsManager(game_state)
        
        # 创建智能体
        self.follower = None
        self.courtesan = None
        self.madam = None
        self.narrator = None
        
        self._initialize_scene()
    
    def _initialize_scene(self):
        """初始化场景"""
        if not self.game_state.current_scene:
            self.game_state.current_scene = SceneState(
                location="妓院大厅",
                atmosphere="奢华而神秘",
                time_of_day="夜晚",
                characters_present=[],
                scene_values={
                    "紧张度": 10,
                    "暧昧度": 30,
                    "危险度": 5,
                    "金钱消费": 0
                }
            )
    
    def setup_brothel_scenario(self, follower_character: Character, card: Card, 
                              courtesan_character: Character, madam_character: Character):
        """设置妓院场景"""
        # 创建智能体
        self.follower = self.agents_creator.create_follower_agent(
            follower_character, card, self.tools_manager
        )
        self.courtesan = self.agents_creator.create_courtesan_agent(
            courtesan_character, self.tools_manager
        )
        self.madam = self.agents_creator.create_madam_agent(
            madam_character, self.tools_manager
        )
        self.narrator = self.agents_creator.create_narrator_agent(self.tools_manager)
        
        # 更新场景状态
        self.game_state.current_scene.characters_present = [
            follower_character.name,
            courtesan_character.name,
            madam_character.name
        ]
        
        # 设置活动卡牌
        self.game_state.active_cards = [card]
    
    def create_interaction_task(self, scenario_description: str, objectives: List[str]) -> Task:
        """创建交互任务"""
        return Task(
            description=f"""
            场景设定：{scenario_description}
            
            当前场景：{self.game_state.current_scene.location}
            氛围：{self.game_state.current_scene.atmosphere}
            时间：{self.game_state.current_scene.time_of_day}
            
            场景数值状态：
            - 紧张度：{self.game_state.current_scene.scene_values.get('紧张度', 0)}
            - 暧昧度：{self.game_state.current_scene.scene_values.get('暧昧度', 0)}
            - 危险度：{self.game_state.current_scene.scene_values.get('危险度', 0)}
            - 金钱消费：{self.game_state.current_scene.scene_values.get('金钱消费', 0)}
            
            目标：
            {chr(10).join([f"- {obj}" for obj in objectives])}
            
            请各位智能体根据自己的角色和目标进行自然的对话交互。
            随着对话的进行，请使用相应的工具来更新关系、场景数值等。
            
            注意：
            1. 保持角色的一致性和真实性
            2. 对话要自然流畅，符合角色身份
            3. 适时使用工具记录重要信息和变化
            4. 营造沉浸式的游戏体验
            5. 推动故事朝着有趣的方向发展
            """,
            expected_output="一段丰富的角色对话交互，包含情节发展、关系变化、场景数值更新等元素，最终形成一个完整的场景剧情。",
            agent=self.narrator  # 由旁白智能体主导任务
        )
    
    def run_brothel_interaction(self, scenario_description: str = None, max_iterations: int = 5) -> Dict[str, Any]:
        """运行妓院交互场景"""
        if not all([self.follower, self.courtesan, self.madam, self.narrator]):
            raise ValueError("智能体未完全初始化，请先调用setup_brothel_scenario方法")
        
        if not scenario_description:
            scenario_description = """
            夜幕降临，华灯初上。随从带着主人的秘密任务来到了城中最著名的妓院。
            这里奢华而神秘，每个人都隐藏着自己的秘密。
            随从必须在不暴露真实意图的情况下，巧妙地完成卡牌任务。
            """
        
        objectives = [
            "随从要巧妙地完成卡牌任务而不暴露真实意图",
            "妓女要通过魅力与客人建立关系并探知其意图",
            "老鸨要保护妓院的利益和姑娘们的安全",
            "旁白要营造氛围并推动剧情发展"
        ]
        
        # 创建任务
        interaction_task = self.create_interaction_task(scenario_description, objectives)
        
        # 创建智能体团队
        crew = Crew(
            agents=[self.narrator, self.follower, self.courtesan, self.madam],
            tasks=[interaction_task],
            verbose=True,
            process_type="sequential",  # 使用顺序流程
            max_iter=max_iterations
        )
        
        # 执行任务
        try:
            result = crew.kickoff()
            return {
                "success": True,
                "story_content": result,
                "final_game_state": self.game_state,
                "dialogue_history": self.game_state.dialogue_history,
                "scene_values": self.game_state.current_scene.scene_values
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "game_state": self.game_state
            }
    
    def get_game_summary(self) -> Dict[str, Any]:
        """获取游戏状态摘要"""
        return {
            "scene": {
                "location": self.game_state.current_scene.location,
                "atmosphere": self.game_state.current_scene.atmosphere,
                "time": self.game_state.current_scene.time_of_day,
                "values": self.game_state.current_scene.scene_values
            },
            "characters": {
                name: {
                    "attributes": {
                        "魅力": char.charm,
                        "智慧": char.wisdom,
                        "体魄": char.physique,
                        "社交": char.social
                    },
                    "relationships": char.relationships
                } for name, char in self.game_state.characters.items()
            },
            "active_cards": [
                {
                    "id": card.card_id,
                    "title": card.title,
                    "type": card.card_type.value,
                    "rank": card.rank.value
                } for card in self.game_state.active_cards
            ],
            "dialogue_count": len(self.game_state.dialogue_history)
        }