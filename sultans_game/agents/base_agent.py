"""基础智能体类"""

from abc import ABC, abstractmethod
from crewai import Agent
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional, Type
from ..models import Character, Card
from ..tools import GameToolsManager


class BaseGameAgent(ABC):
    """游戏智能体基类"""
    
    # 智能体类型标识
    agent_type: str = ""
    
    # 智能体显示名称
    display_name: str = ""
    
    # 智能体描述
    description: str = ""
    
    # 需要的工具类型列表
    required_tools: List[str] = []
    
    def __init__(self, llm: ChatOpenAI, character: Character, 
                 tools_manager: Optional[GameToolsManager] = None,
                 additional_config: Optional[Dict[str, Any]] = None):
        """
        初始化智能体
        
        Args:
            llm: 语言模型实例
            character: 角色对象
            tools_manager: 工具管理器
            additional_config: 额外配置
        """
        self.llm = llm
        self.character = character
        self.tools_manager = tools_manager
        self.additional_config = additional_config or {}
        
        # 初始化工具列表
        self.tools = self.get_tools()
        
        # 创建智能体实例
        self.agent = self._create_agent()
    
    @abstractmethod
    def _create_agent(self) -> Agent:
        """创建CrewAI智能体实例"""
        pass
    
    @abstractmethod
    def get_role(self) -> str:
        """获取智能体角色描述"""
        pass
    
    @abstractmethod
    def get_goal(self) -> str:
        """获取智能体目标"""
        pass
    
    @abstractmethod
    def get_backstory(self) -> str:
        """获取智能体背景故事"""
        pass
    
    def get_tools(self) -> List[Any]:
        """获取智能体工具列表"""
        if not self.tools_manager:
            return []
        return self.tools_manager.get_tools_by_agent_type(self.agent_type)
    
    def get_character_attributes_text(self) -> str:
        """获取角色属性文本描述"""
        attrs = []
        for attr_name, value in self.character.attributes.items():
            attrs.append(f"- {attr_name}：{value}")
        return "\n".join(attrs)
    
    def can_handle_card(self, card: Card) -> bool:
        """检查智能体是否可以处理特定卡牌"""
        # 默认所有智能体都可以处理卡牌，子类可以重写此方法
        return True
    
    def get_agent_instance(self) -> Agent:
        """获取CrewAI智能体实例"""
        return self.agent
    
    @classmethod
    def get_agent_info(cls) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "type": cls.agent_type,
            "display_name": cls.display_name,
            "description": cls.description,
            "required_tools": cls.required_tools
        } 