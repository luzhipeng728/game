from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
from .models import GameState, Character, SceneState, Card, CardType
from .tools import GameToolsManager
from .config import get_model_config

class SultansGameAgents:
    """苏丹的游戏智能体集合"""
    
    def __init__(self, llm_model: str = None):
        config = get_model_config(llm_model)  # 使用新的 get_model_config 函数
        print(config)
        self.llm = ChatOpenAI(
            model=config["model"],  # 使用原始模型名（不带前缀）
            temperature=0.7,
            openai_api_base=config["base_url"],
            openai_api_key=config["api_key"],
        )
    
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
            
            工具使用指南：
            - 使用"对话记录工具"记录重要对话内容
            - 使用"骰子检定工具"进行属性检定
            - 使用"卡牌使用工具"在合适时机使用卡牌
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
            
            工具使用指南：
            - 使用"关系管理工具"管理与客人的关系
            - 使用"场景数值管理工具"调整暧昧度、紧张度等场景数值
            - 使用"对话记录工具"记录重要对话内容
            
            注意：如果你有"场景控制工具"，要改变场景数值请使用：action="改变数值", parameter="紧张度/暧昧度/危险度/金钱消费", value="数值变化量"
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
            
            工具使用指南：
            - 使用"关系管理工具"管理与客人和姑娘们的关系
            - 使用"场景数值管理工具"调整紧张度、危险度等场景数值
            - 使用"场景控制工具"控制场景：
              
              ⚠️ 重要：要改变场景数值，必须使用 action="改变数值"
              
              正确示例：
              * 增加紧张度：{{"action": "改变数值", "parameter": "紧张度", "value": "10"}}
              * 增加暧昧度：{{"action": "改变数值", "parameter": "暧昧度", "value": "15"}}
              * 增加危险度：{{"action": "改变数值", "parameter": "危险度", "value": "5"}}
              * 增加金钱消费：{{"action": "改变数值", "parameter": "金钱消费", "value": "20"}}
              
              错误示例（不会改变数值）：
              * {{"action": "改变氛围", "parameter": "紧张度", "value": "10"}} ❌
              * {{"action": "触发事件", "parameter": "紧张度", "value": "10"}} ❌
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
            
            工具使用指南：
            - 使用"场景控制工具"控制场景：
              
              ⚠️ 重要：要改变场景数值，必须使用 action="改变数值"
              
              正确示例：
              * 增加紧张度：{{"action": "改变数值", "parameter": "紧张度", "value": "10"}}
              * 增加暧昧度：{{"action": "改变数值", "parameter": "暧昧度", "value": "15"}}
              * 增加危险度：{{"action": "改变数值", "parameter": "危险度", "value": "5"}}
              * 增加金钱消费：{{"action": "改变数值", "parameter": "金钱消费", "value": "20"}}
              
              错误示例（不会改变数值）：
              * {{"action": "改变氛围", "parameter": "紧张度", "value": "10"}} ❌
              * {{"action": "触发事件", "parameter": "紧张度", "value": "10"}} ❌
              
            - 使用"对话记录工具"记录重要剧情节点
            - 使用"骰子检定工具"在需要随机性时进行检定
            """,
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        )

class GameMaster:
    """游戏主控制器"""
    
    def __init__(self, game_state: GameState, llm_model: str = None):
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
    
    def start_scene(self, card: Card) -> Dict[str, Any]:
        """开始场景对话
        
        Args:
            card: 要执行的卡牌
            
        Returns:
            包含对话结果的字典
        """
        try:
            # 创建默认角色（如果不存在）
            if "随从" not in self.game_state.characters:
                self._create_default_follower()
            
            if "妓女" not in self.game_state.characters:
                self._create_default_courtesan()
            
            if "老鸨" not in self.game_state.characters:
                self._create_default_madam()
            
            # 设置妓院场景
            self.setup_brothel_scenario(
                self.game_state.characters["随从"],
                card,
                self.game_state.characters["妓女"],
                self.game_state.characters["老鸨"]
            )
            
            # 运行自动对话（使用带回调的版本）
            result = self.run_auto_conversation_with_callback(card)
            
            if result["success"]:
                # 格式化返回结果以匹配 sultans_game_app.py 的期望
                return {
                    "success": True,
                    "conversation_result": result["story_content"],
                    "scene_state": result["scene_values"],
                    "characters": {
                        name: {
                            "relationships": char.relationships,
                            "attributes": {
                                "魅力": char.charm,
                                "智慧": char.wisdom,
                                "体魄": char.physique,
                                "社交": char.social
                            }
                        } for name, char in self.game_state.characters.items()
                    }
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"启动场景时发生错误: {str(e)}"
            }
    
    def run_auto_conversation(self, card: Card, max_rounds: int = 10, min_rounds: int = 5) -> Dict[str, Any]:
        """运行自动多轮对话
        
        Args:
            card: 当前执行的卡牌
            max_rounds: 最大对话轮数
            min_rounds: 最小对话轮数
            
        Returns:
            对话结果字典
        """
        if not all([self.follower, self.courtesan, self.madam, self.narrator]):
            raise ValueError("智能体未完全初始化，请先调用setup_brothel_scenario方法")
        
        conversation_log = []
        current_round = 0
        
        # 初始场景描述
        initial_context = f"""
        【场景开始】
        夜幕降临，华灯初上。随从带着一张"{card.title}"卡牌来到了城中最著名的妓院。
        卡牌描述：{card.description}
        
        妓院内奢华而神秘，烛光摇曳，香气弥漫。每个人都隐藏着自己的秘密。
        随从必须在不暴露真实意图的情况下，巧妙地完成卡牌任务。
        
        当前场景数值：
        - 紧张度：{self.game_state.current_scene.scene_values.get('紧张度', 0)}
        - 暧昧度：{self.game_state.current_scene.scene_values.get('暧昧度', 0)}
        - 危险度：{self.game_state.current_scene.scene_values.get('危险度', 0)}
        - 金钱消费：{self.game_state.current_scene.scene_values.get('金钱消费', 0)}
        """
        
        conversation_log.append(f"【旁白】{initial_context}")
        
        # 智能体轮换顺序
        agents_order = [
            ("旁白", self.narrator),
            ("随从", self.follower), 
            ("妓女", self.courtesan),
            ("老鸨", self.madam)
        ]
        
        try:
            while current_round < max_rounds:
                current_round += 1
                round_conversations = []
                
                # 每轮让所有智能体都有机会发言
                for agent_name, agent in agents_order:
                    # 构建当前对话上下文
                    context = self._build_conversation_context(
                        conversation_log, card, current_round, agent_name
                    )
                    
                    # 创建单轮对话任务
                    task = Task(
                        description=context,
                        expected_output=f"作为{agent_name}，根据当前情况进行一次自然的对话或行动描述（50-200字）",
                        agent=agent
                    )
                    
                    # 执行单个智能体的对话
                    crew = Crew(
                        agents=[agent],
                        tasks=[task],
                        verbose=False
                    )
                    
                    try:
                        response = crew.kickoff()
                        dialogue_entry = f"【{agent_name}】{response}"
                        round_conversations.append(dialogue_entry)
                        conversation_log.append(dialogue_entry)
                        
                        # 记录到游戏状态
                        self.game_state.current_scene.add_conversation(
                            agent_name, str(response), f"第{current_round}轮对话"
                        )
                        
                    except Exception as e:
                        error_msg = f"【系统】{agent_name}暂时无法回应：{str(e)}"
                        round_conversations.append(error_msg)
                        conversation_log.append(error_msg)
                
                # 检查是否应该结束对话
                if current_round >= min_rounds:
                    should_end = self._should_end_conversation(
                        conversation_log, current_round, card
                    )
                    if should_end:
                        ending_msg = f"【旁白】经过{current_round}轮精彩的对话，这个场景告一段落..."
                        conversation_log.append(ending_msg)
                        break
            
            # 生成最终总结
            final_summary = self._generate_conversation_summary(conversation_log, card)
            
            return {
                "success": True,
                "story_content": "\n\n".join(conversation_log),
                "conversation_rounds": current_round,
                "final_summary": final_summary,
                "scene_values": self.game_state.current_scene.scene_values,
                "dialogue_history": self.game_state.dialogue_history
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"自动对话过程中发生错误: {str(e)}",
                "partial_conversation": "\n\n".join(conversation_log) if conversation_log else "无对话记录"
            }
    
    def run_auto_conversation_with_callback(self, card: Card, callback_func=None, max_rounds: int = 10, min_rounds: int = 5) -> Dict[str, Any]:
        """运行自动多轮对话（支持实时回调）
        
        Args:
            card: 当前执行的卡牌
            callback_func: 回调函数，用于实时更新界面
            max_rounds: 最大对话轮数
            min_rounds: 最小对话轮数
            
        Returns:
            对话结果字典
        """
        if not all([self.follower, self.courtesan, self.madam, self.narrator]):
            raise ValueError("智能体未完全初始化，请先调用setup_brothel_scenario方法")
        
        conversation_log = []
        current_round = 0
        
        # 初始场景描述
        initial_context = f"""
        【场景开始】
        夜幕降临，华灯初上。随从带着一张"{card.title}"卡牌来到了城中最著名的妓院。
        卡牌描述：{card.description}
        
        妓院内奢华而神秘，烛光摇曳，香气弥漫。每个人都隐藏着自己的秘密。
        随从必须在不暴露真实意图的情况下，巧妙地完成卡牌任务。
        """
        
        conversation_log.append(f"【旁白】{initial_context}")
        
        # 调用回调函数更新界面
        if callback_func:
            callback_func("init", 0, max_rounds, "旁白", initial_context, conversation_log)
        
        # 智能体轮换顺序
        agents_order = [
            ("旁白", self.narrator),
            ("随从", self.follower), 
            ("妓女", self.courtesan),
            ("老鸨", self.madam)
        ]
        
        try:
            while current_round < max_rounds:
                current_round += 1
                
                # 每轮让所有智能体都有机会发言
                for agent_name, agent in agents_order:
                    # 通知界面当前发言者
                    if callback_func:
                        callback_func("speaking", current_round, max_rounds, agent_name, "", conversation_log)
                    
                    # 构建当前对话上下文
                    context = self._build_conversation_context(
                        conversation_log, card, current_round, agent_name
                    )
                    
                    # 创建单轮对话任务
                    task = Task(
                        description=context,
                        expected_output=f"作为{agent_name}，根据当前情况进行一次自然的对话或行动描述（50-200字）",
                        agent=agent
                    )
                    
                    # 执行单个智能体的对话
                    crew = Crew(
                        agents=[agent],
                        tasks=[task],
                        verbose=False
                    )
                    
                    try:
                        response = crew.kickoff()
                        dialogue_entry = f"【{agent_name}】{response}"
                        conversation_log.append(dialogue_entry)
                        
                        # 记录到游戏状态
                        self.game_state.current_scene.add_conversation(
                            agent_name, str(response), f"第{current_round}轮对话"
                        )
                        
                        # 调用回调函数更新界面
                        if callback_func:
                            callback_func("response", current_round, max_rounds, agent_name, str(response), conversation_log)
                        
                    except Exception as e:
                        error_msg = f"【系统】{agent_name}暂时无法回应：{str(e)}"
                        conversation_log.append(error_msg)
                        
                        # 调用回调函数更新界面
                        if callback_func:
                            callback_func("error", current_round, max_rounds, agent_name, error_msg, conversation_log)
                
                # 检查是否应该结束对话
                if current_round >= min_rounds:
                    should_end = self._should_end_conversation(
                        conversation_log, current_round, card
                    )
                    if should_end:
                        ending_msg = f"【旁白】经过{current_round}轮精彩的对话，这个场景告一段落..."
                        conversation_log.append(ending_msg)
                        
                        # 调用回调函数更新界面
                        if callback_func:
                            callback_func("ending", current_round, max_rounds, "旁白", ending_msg, conversation_log)
                        break
            
            # 生成最终总结
            final_summary = self._generate_conversation_summary(conversation_log, card)
            
            # 调用回调函数更新界面
            if callback_func:
                callback_func("complete", current_round, max_rounds, "系统", final_summary, conversation_log)
            
            return {
                "success": True,
                "story_content": "\n\n".join(conversation_log),
                "conversation_rounds": current_round,
                "final_summary": final_summary,
                "scene_values": self.game_state.current_scene.scene_values,
                "dialogue_history": self.game_state.dialogue_history
            }
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"自动对话过程中发生错误: {str(e)}",
                "partial_conversation": "\n\n".join(conversation_log) if conversation_log else "无对话记录"
            }
            
            # 调用回调函数更新界面
            if callback_func:
                callback_func("error", current_round, max_rounds, "系统", str(e), conversation_log)
            
            return error_result
    
    def _build_conversation_context(self, conversation_log: List[str], card: Card, 
                                  current_round: int, agent_name: str) -> str:
        """构建对话上下文"""
        recent_conversations = conversation_log[-6:] if len(conversation_log) > 6 else conversation_log
        
        context = f"""
        你是{agent_name}，现在是第{current_round}轮对话。
        
        卡牌任务：{card.title} - {card.description}
        
        最近的对话内容：
        {chr(10).join(recent_conversations)}
        
        当前场景状态：
        - 位置：{self.game_state.current_scene.location}
        - 氛围：{self.game_state.current_scene.atmosphere}
        - 紧张度：{self.game_state.current_scene.scene_values.get('紧张度', 0)}
        - 暧昧度：{self.game_state.current_scene.scene_values.get('暧昧度', 0)}
        - 危险度：{self.game_state.current_scene.scene_values.get('危险度', 0)}
        
        请根据你的角色身份和当前情况，进行自然的对话或行动。
        注意：
        1. 保持角色一致性
        2. 推动剧情发展
        3. 与其他角色产生有意义的互动
        4. 不要重复之前说过的话
        5. 回应要简洁有力（50-200字）
        """
        
        return context
    
    def _should_end_conversation(self, conversation_log: List[str], current_round: int, card: Card) -> bool:
        """判断是否应该结束对话"""
        # 基本结束条件
        if current_round >= 10:  # 最大轮数限制
            return True
        
        # 检查是否达到了某些剧情节点
        recent_text = " ".join(conversation_log[-4:]).lower()
        
        # 结束关键词
        end_keywords = [
            "离开", "告辞", "结束", "完成", "任务达成", 
            "不欢而散", "心满意足", "目标完成", "时间不早"
        ]
        
        for keyword in end_keywords:
            if keyword in recent_text:
                return True
        
        # 检查场景数值是否达到极值
        scene_values = self.game_state.current_scene.scene_values
        if (scene_values.get('紧张度', 0) >= 80 or 
            scene_values.get('危险度', 0) >= 80 or
            scene_values.get('金钱消费', 0) >= 100):
            return True
        
        return False
    
    def _generate_conversation_summary(self, conversation_log: List[str], card: Card) -> str:
        """生成对话总结"""
        total_rounds = len([log for log in conversation_log if "【" in log and "】" in log])
        
        summary = f"""
        【场景总结】
        卡牌任务：{card.title}
        对话轮数：{total_rounds}
        最终场景数值：
        - 紧张度：{self.game_state.current_scene.scene_values.get('紧张度', 0)}
        - 暧昧度：{self.game_state.current_scene.scene_values.get('暧昧度', 0)}
        - 危险度：{self.game_state.current_scene.scene_values.get('危险度', 0)}
        - 金钱消费：{self.game_state.current_scene.scene_values.get('金钱消费', 0)}
        
        这次妓院之行充满了戏剧性，每个角色都展现了自己的特色，
        故事在紧张与暧昧中展开，最终形成了一个完整的剧情片段。
        """
        
        return summary
    
    def _create_default_follower(self):
        """创建默认随从角色"""
        from sultans_game.models import Character
        follower = Character(
            name="随从",
            role="随从",
            personality="忠诚而机智，善于隐藏真实意图",
            attributes={
                "体魄": 70,
                "魅力": 60,
                "智慧": 75,
                "隐匿": 80,
                "战斗": 65,
                "防御": 60,
                "社交": 70,
                "声望": 50
            }
        )
        self.game_state.characters["随从"] = follower
        return follower
    
    def _create_default_courtesan(self):
        """创建默认妓女角色"""
        from sultans_game.models import Character
        courtesan = Character(
            name="妓女",
            role="妓女",
            personality="魅力四射，善于察言观色",
            attributes={
                "体魄": 60,
                "魅力": 90,
                "智慧": 70,
                "隐匿": 75,
                "战斗": 30,
                "防御": 40,
                "社交": 85,
                "声望": 60
            }
        )
        self.game_state.characters["妓女"] = courtesan
        return courtesan
    
    def _create_default_madam(self):
        """创建默认老鸨角色"""
        from sultans_game.models import Character
        madam = Character(
            name="老鸨",
            role="老鸨",
            personality="精明能干，保护妓院利益",
            attributes={
                "体魄": 50,
                "魅力": 70,
                "智慧": 85,
                "隐匿": 60,
                "战斗": 40,
                "防御": 50,
                "社交": 90,
                "声望": 75
            }
        )
        self.game_state.characters["老鸨"] = madam
        return madam