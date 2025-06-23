"""场景配置系统"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import os


@dataclass
class AgentConfig:
    """智能体配置"""
    agent_type: str
    character_name: str
    role_name: str
    required: bool = True
    config: Optional[Dict[str, Any]] = None


@dataclass
class SceneConfig:
    """场景配置"""
    scene_name: str
    description: str
    location: str
    atmosphere: str
    agents: List[AgentConfig]
    initial_scene_values: Optional[Dict[str, int]] = None
    max_rounds: int = 10
    min_rounds: int = 5


class SceneConfigManager:
    """场景配置管理器"""
    
    def __init__(self):
        self._configs: Dict[str, SceneConfig] = {}
        self._load_default_configs()
    
    def _load_default_configs(self):
        """加载默认场景配置"""
        
        # 妓院场景配置
        brothel_config = SceneConfig(
            scene_name="brothel",
            description="夜幕降临，华灯初上的妓院场景",
            location="妓院大厅",
            atmosphere="奢华而神秘",
            agents=[
                AgentConfig(
                    agent_type="narrator",
                    character_name="旁白者",
                    role_name="旁白",
                    required=True
                ),
                AgentConfig(
                    agent_type="follower",
                    character_name="随从",
                    role_name="随从",
                    required=True
                ),
                AgentConfig(
                    agent_type="courtesan",
                    character_name="妓女",
                    role_name="妓女",
                    required=True
                ),
                AgentConfig(
                    agent_type="madam",
                    character_name="老鸨",
                    role_name="老鸨",
                    required=True
                )
            ],
            initial_scene_values={
                "紧张度": 10,
                "暧昧度": 30,
                "危险度": 5,
                "金钱消费": 0
            },
            max_rounds=10,
            min_rounds=5
        )
        
        # 市场场景配置（示例）
        market_config = SceneConfig(
            scene_name="market",
            description="熙熙攘攘的市场交易场景",
            location="城市市场",
            atmosphere="热闹而混乱",
            agents=[
                AgentConfig(
                    agent_type="narrator",
                    character_name="旁白者",
                    role_name="旁白",
                    required=True
                ),
                AgentConfig(
                    agent_type="follower",
                    character_name="随从",
                    role_name="随从",
                    required=True
                ),
                # 可以在这里添加商人、守卫等其他智能体
            ],
            initial_scene_values={
                "喧嚣度": 50,
                "商业氛围": 70,
                "危险度": 15
            },
            max_rounds=8,
            min_rounds=3
        )
        
        # 宫廷场景配置（示例）
        palace_config = SceneConfig(
            scene_name="palace",
            description="森严而华丽的宫廷场景",
            location="苏丹宫殿",
            atmosphere="庄严而危险",
            agents=[
                AgentConfig(
                    agent_type="narrator",
                    character_name="旁白者",
                    role_name="旁白",
                    required=True
                ),
                AgentConfig(
                    agent_type="follower",
                    character_name="随从",
                    role_name="随从",
                    required=True
                ),
                # 可以在这里添加贵族、侍卫、大臣等智能体
            ],
            initial_scene_values={
                "威严度": 80,
                "紧张度": 60,
                "权力斗争": 40
            },
            max_rounds=12,
            min_rounds=6
        )
        
        self.register_config(brothel_config)
        self.register_config(market_config)
        self.register_config(palace_config)
    
    def register_config(self, config: SceneConfig):
        """注册场景配置"""
        self._configs[config.scene_name] = config
    
    def get_config(self, scene_name: str) -> Optional[SceneConfig]:
        """获取场景配置"""
        return self._configs.get(scene_name)
    
    def get_all_scene_names(self) -> List[str]:
        """获取所有场景名称"""
        return list(self._configs.keys())
    
    def get_scene_info(self, scene_name: str) -> Optional[Dict[str, Any]]:
        """获取场景信息"""
        config = self._configs.get(scene_name)
        if not config:
            return None
        
        return {
            "name": config.scene_name,
            "description": config.description,
            "location": config.location,
            "atmosphere": config.atmosphere,
            "agent_types": [agent.agent_type for agent in config.agents],
            "required_agents": [agent.agent_type for agent in config.agents if agent.required],
            "optional_agents": [agent.agent_type for agent in config.agents if not agent.required],
            "initial_values": config.initial_scene_values,
            "max_rounds": config.max_rounds,
            "min_rounds": config.min_rounds
        }
    
    def get_all_scenes_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有场景信息"""
        return {
            scene_name: self.get_scene_info(scene_name)
            for scene_name in self._configs.keys()
        }
    
    def load_from_file(self, file_path: str):
        """从文件加载场景配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for scene_data in data.get('scenes', []):
                agents = [
                    AgentConfig(**agent_data) 
                    for agent_data in scene_data.get('agents', [])
                ]
                
                config = SceneConfig(
                    scene_name=scene_data['scene_name'],
                    description=scene_data['description'],
                    location=scene_data['location'],
                    atmosphere=scene_data['atmosphere'],
                    agents=agents,
                    initial_scene_values=scene_data.get('initial_scene_values'),
                    max_rounds=scene_data.get('max_rounds', 10),
                    min_rounds=scene_data.get('min_rounds', 5)
                )
                
                self.register_config(config)
                
        except Exception as e:
            print(f"加载场景配置文件时出错: {e}")
    
    def save_to_file(self, file_path: str):
        """保存场景配置到文件"""
        try:
            data = {
                "scenes": []
            }
            
            for config in self._configs.values():
                scene_data = {
                    "scene_name": config.scene_name,
                    "description": config.description,
                    "location": config.location,
                    "atmosphere": config.atmosphere,
                    "agents": [
                        {
                            "agent_type": agent.agent_type,
                            "character_name": agent.character_name,
                            "role_name": agent.role_name,
                            "required": agent.required,
                            "config": agent.config
                        }
                        for agent in config.agents
                    ],
                    "initial_scene_values": config.initial_scene_values,
                    "max_rounds": config.max_rounds,
                    "min_rounds": config.min_rounds
                }
                data["scenes"].append(scene_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存场景配置文件时出错: {e}")
    
    def create_custom_scene(self, scene_name: str, description: str, 
                          location: str, atmosphere: str,
                          agent_configs: List[Dict[str, Any]],
                          initial_values: Optional[Dict[str, int]] = None,
                          max_rounds: int = 10, min_rounds: int = 5) -> SceneConfig:
        """创建自定义场景配置"""
        
        agents = []
        for agent_config in agent_configs:
            agents.append(AgentConfig(
                agent_type=agent_config['agent_type'],
                character_name=agent_config['character_name'],
                role_name=agent_config['role_name'],
                required=agent_config.get('required', True),
                config=agent_config.get('config')
            ))
        
        config = SceneConfig(
            scene_name=scene_name,
            description=description,
            location=location,
            atmosphere=atmosphere,
            agents=agents,
            initial_scene_values=initial_values,
            max_rounds=max_rounds,
            min_rounds=min_rounds
        )
        
        self.register_config(config)
        return config


# 全局场景配置管理器实例
scene_config_manager = SceneConfigManager() 