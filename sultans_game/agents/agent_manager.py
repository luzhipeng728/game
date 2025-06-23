"""智能体管理器"""

from typing import Dict, List, Any, Optional, Callable
from crewai import Crew, Task
from langchain_openai import ChatOpenAI

from .agent_registry import agent_registry
from .scene_config import scene_config_manager, SceneConfig, AgentConfig
from .base_agent import BaseGameAgent
from ..models import GameState, Character, Card, SceneState
from ..tools import GameToolsManager
from ..config import get_model_config


class AgentManager:
    """智能体管理器"""
    
    def __init__(self, llm_model: str = "gpt-4.1"):
        self.llm_model = llm_model
        self.llm = self._create_llm()
        self.tools_manager: Optional[GameToolsManager] = None
        self.game_state: Optional[GameState] = None
        
        # 当前场景的智能体实例
        self.active_agents: Dict[str, BaseGameAgent] = {}
        self.current_scene_config: Optional[SceneConfig] = None
    
    def _create_llm(self) -> ChatOpenAI:
        """创建语言模型实例"""
        config = get_model_config(self.llm_model)
        print(f"self.llm_model: {self.llm_model}")
        return ChatOpenAI(
            model=config["model"],
            temperature=0.7,
            base_url=config["base_url"],  # 新版本参数名
            api_key=config["api_key"],    # 新版本参数名
        )
    
    def set_game_state(self, game_state: GameState):
        """设置游戏状态"""
        self.game_state = game_state
        self.tools_manager = GameToolsManager(game_state)
        
        # 设置全局游戏状态，让工具能够访问到
        from ..tools import set_game_state
        set_game_state(game_state)
    
    def get_available_scenes(self) -> List[str]:
        """获取可用的场景列表"""
        return scene_config_manager.get_all_scene_names()
    
    def get_scene_info(self, scene_name: str) -> Optional[Dict[str, Any]]:
        """获取场景信息"""
        return scene_config_manager.get_scene_info(scene_name)
    
    def get_available_agents(self) -> List[str]:
        """获取可用的智能体类型列表"""
        return agent_registry.get_all_agent_types()
    
    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """获取智能体信息"""
        return agent_registry.get_agent_info(agent_type)
    
    def setup_scene(self, scene_name: str, characters: Optional[Dict[str, Character]] = None) -> bool:
        """设置场景并创建智能体"""
        # 获取场景配置
        scene_config = scene_config_manager.get_config(scene_name)
        if not scene_config:
            print(f"未找到场景配置: {scene_name}")
            return False
        
        self.current_scene_config = scene_config
        
        # 清理之前的智能体
        self.active_agents.clear()
        
        # 初始化场景状态
        if self.game_state:
            # 🔥 关键修复：确保每次都创建全新的场景数值，不共享状态
            if scene_config.initial_scene_values:
                # 如果有配置的初始值，使用配置值的副本
                initial_values = scene_config.initial_scene_values.copy()
            else:
                # 否则使用默认初始值
                initial_values = {
                    "紧张度": 0,
                    "暧昧度": 0,
                    "危险度": 0,
                    "金钱消费": 0
                }
            
            self.game_state.current_scene = SceneState(
                location=scene_config.location,
                atmosphere=scene_config.atmosphere,
                time_of_day="夜晚",
                characters_present=[],
                scene_values=initial_values  # 使用副本，避免共享状态
            )
            print(f"🎮 场景初始化完成，初始数值: {initial_values}")
        
        # 创建智能体
        success = True
        for agent_config in scene_config.agents:
            try:
                agent = self._create_agent_from_config(agent_config, characters)
                if agent:
                    self.active_agents[agent_config.agent_type] = agent
                    if self.game_state:
                        self.game_state.current_scene.characters_present.append(
                            agent_config.character_name
                        )
                elif agent_config.required:
                    print(f"无法创建必需的智能体: {agent_config.agent_type}")
                    success = False
            except Exception as e:
                print(f"创建智能体 {agent_config.agent_type} 时出错: {e}")
                if agent_config.required:
                    success = False
        
        if success:
            print(f"成功设置场景 '{scene_name}'，创建了 {len(self.active_agents)} 个智能体")
        
        return success
    
    def _create_agent_from_config(self, agent_config: AgentConfig, 
                                 characters: Optional[Dict[str, Character]] = None) -> Optional[BaseGameAgent]:
        """根据配置创建智能体"""
        # 获取或创建角色
        character = None
        if characters and agent_config.character_name in characters:
            character = characters[agent_config.character_name]
        elif self.game_state and agent_config.character_name in self.game_state.characters:
            character = self.game_state.characters[agent_config.character_name]
        else:
            # 创建默认角色
            character = self._create_default_character(agent_config)
        
        if not character:
            print(f"无法获取或创建角色: {agent_config.character_name}")
            return None
        
        # 创建智能体
        try:
            agent = agent_registry.create_agent(
                agent_type=agent_config.agent_type,
                llm=self.llm,
                character=character,
                tools_manager=self.tools_manager,
                additional_config=agent_config.config
            )
            
            print(f"成功创建智能体: {agent_config.agent_type} ({agent_config.character_name})")
            return agent
            
        except Exception as e:
            print(f"创建智能体失败: {e}")
            return None
    
    def _create_default_character(self, agent_config: AgentConfig) -> Optional[Character]:
        """创建默认角色"""
        from ..models import Character
        
        # 根据智能体类型创建默认角色属性
        default_attributes = {
            "follower": {
                "体魄": 70, "魅力": 60, "智慧": 75, "隐匿": 80,
                "战斗": 65, "防御": 60, "社交": 70, "声望": 50
            },
            "courtesan": {
                "体魄": 60, "魅力": 90, "智慧": 70, "隐匿": 75,
                "战斗": 30, "防御": 40, "社交": 85, "声望": 60
            },
            "madam": {
                "体魄": 50, "魅力": 70, "智慧": 85, "隐匿": 60,
                "战斗": 40, "防御": 50, "社交": 90, "声望": 75
            },
            "narrator": {
                "智慧": 100, "洞察": 100, "表达": 100
            }
        }
        
        attributes = default_attributes.get(agent_config.agent_type, {
            "体魄": 50, "魅力": 50, "智慧": 50, "社交": 50
        })
        
        character = Character(
            name=agent_config.character_name,
            role=agent_config.role_name,
            personality=f"默认{agent_config.role_name}性格",
            attributes=attributes
        )
        
        # 将角色添加到游戏状态
        if self.game_state:
            self.game_state.characters[agent_config.character_name] = character
        
        return character
    
    def get_active_agents(self) -> Dict[str, Any]:
        """获取当前激活的智能体"""
        return self.active_agents.copy()
    
    def get_agent(self, agent_type: str) -> Optional[Any]:
        """获取指定类型的智能体"""
        return self.active_agents.get(agent_type)
    
    def run_scene_conversation(self, card: Optional[Card] = None, 
                             callback_func: Optional[Callable] = None) -> Dict[str, Any]:
        """运行场景对话"""
        if not self.current_scene_config or not self.active_agents:
            return {
                "success": False,
                "error": "场景未设置或没有活跃的智能体"
            }
        
        # 设置活动卡牌
        if card and self.game_state:
            self.game_state.active_cards = [card]
        
        # 创建对话任务
        scenario_description = self._build_scenario_description(card)
        task = self._create_conversation_task(scenario_description)
        
        # 获取智能体实例列表
        agents = [agent.get_agent_instance() for agent in self.active_agents.values()]
        
        # 创建智能体团队
        crew = Crew(
            agents=agents,
            tasks=[task],
            verbose=True,
            process_type="sequential",
            max_iter=self.current_scene_config.max_rounds
        )
        
        try:
            # 运行对话
            if callback_func:
                return self._run_conversation_with_callback(crew, callback_func)
            else:
                result = crew.kickoff()
                return {
                    "success": True,
                    "story_content": result,
                    "scene_values": self.game_state.current_scene.scene_values if self.game_state else {},
                    "dialogue_history": self.game_state.dialogue_history if self.game_state else []
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"运行对话时出错: {str(e)}"
            }
    
    def _build_scenario_description(self, card: Optional[Card] = None) -> str:
        """构建场景描述"""
        base_description = self.current_scene_config.description
        
        if card:
            card_description = f"""
            当前卡牌任务：{card.title}
            任务描述：{card.description}
            """
            return base_description + card_description
        
        return base_description
    
    def _create_conversation_task(self, scenario_description: str) -> Task:
        """创建对话任务"""
        scene_values = ""
        if self.game_state and self.game_state.current_scene:
            values = self.game_state.current_scene.scene_values
            scene_values = "\n".join([f"- {k}：{v}" for k, v in values.items()])
        
        # 获取旁白智能体作为主导者
        narrator_agent = self.active_agents.get("narrator")
        if not narrator_agent:
            # 如果没有旁白，使用第一个智能体
            narrator_agent = list(self.active_agents.values())[0]
        
        return Task(
            description=f"""
            场景设定：{scenario_description}
            
            当前场景：{self.current_scene_config.location}
            氛围：{self.current_scene_config.atmosphere}
            
            场景数值状态：
            {scene_values}
            
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
            agent=narrator_agent.get_agent_instance()
        )
    
    def _run_conversation_with_callback(self, crew: Crew, callback_func: Callable) -> Dict[str, Any]:
        """运行带回调的对话"""
        # 这里可以实现更细粒度的回调控制
        # 暂时使用简单的执行方式
        try:
            result = crew.kickoff()
            return {
                "success": True,
                "story_content": result,
                "scene_values": self.game_state.current_scene.scene_values if self.game_state else {},
                "dialogue_history": self.game_state.dialogue_history if self.game_state else []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"运行对话时出错: {str(e)}"
            }
    
    def add_agent_to_scene(self, agent_type: str, character: Character, 
                          config: Optional[Dict[str, Any]] = None) -> bool:
        """向当前场景添加智能体"""
        if agent_type in self.active_agents:
            print(f"智能体类型 {agent_type} 已存在")
            return False
        
        try:
            agent = agent_registry.create_agent(
                agent_type=agent_type,
                llm=self.llm,
                character=character,
                tools_manager=self.tools_manager,
                additional_config=config
            )
            
            self.active_agents[agent_type] = agent
            
            # 更新场景状态
            if self.game_state and self.game_state.current_scene:
                self.game_state.current_scene.characters_present.append(character.name)
            
            print(f"成功添加智能体: {agent_type} ({character.name})")
            return True
            
        except Exception as e:
            print(f"添加智能体失败: {e}")
            return False
    
    def remove_agent_from_scene(self, agent_type: str) -> bool:
        """从当前场景移除智能体"""
        if agent_type not in self.active_agents:
            print(f"智能体类型 {agent_type} 不存在")
            return False
        
        agent = self.active_agents.pop(agent_type)
        
        # 更新场景状态
        if self.game_state and self.game_state.current_scene:
            character_name = agent.character.name
            if character_name in self.game_state.current_scene.characters_present:
                self.game_state.current_scene.characters_present.remove(character_name)
        
        print(f"成功移除智能体: {agent_type}")
        return True 