"""智能体注册系统"""

import importlib
import os
from typing import Dict, Type, List, Optional
from .base_agent import BaseGameAgent


class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseGameAgent]] = {}
        self._auto_discover()
    
    def _auto_discover(self):
        """自动发现并注册智能体"""
        agents_dir = os.path.dirname(__file__)
        
        for filename in os.listdir(agents_dir):
            if (filename.endswith('_agent.py') and 
                filename != 'base_agent.py' and 
                not filename.startswith('__')):
                
                module_name = filename[:-3]  # 移除.py后缀
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'.{module_name}', package='sultans_game.agents')
                    
                    # 查找继承自BaseGameAgent的类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseGameAgent) and 
                            attr != BaseGameAgent and
                            hasattr(attr, 'agent_type') and
                            attr.agent_type):
                            
                            self.register_agent(attr.agent_type, attr)
                            print(f"自动注册智能体: {attr.agent_type} -> {attr.__name__}")
                
                except Exception as e:
                    print(f"加载智能体模块 {module_name} 时出错: {e}")
    
    def register_agent(self, agent_type: str, agent_class: Type[BaseGameAgent]):
        """注册智能体类型"""
        if not issubclass(agent_class, BaseGameAgent):
            raise ValueError(f"{agent_class} 必须继承自 BaseGameAgent")
        
        self._agents[agent_type] = agent_class
    
    def get_agent_class(self, agent_type: str) -> Optional[Type[BaseGameAgent]]:
        """获取智能体类"""
        return self._agents.get(agent_type)
    
    def get_all_agent_types(self) -> List[str]:
        """获取所有已注册的智能体类型"""
        return list(self._agents.keys())
    
    def get_agent_info(self, agent_type: str) -> Optional[Dict]:
        """获取智能体信息"""
        agent_class = self._agents.get(agent_type)
        if agent_class:
            return agent_class.get_agent_info()
        return None
    
    def get_all_agents_info(self) -> Dict[str, Dict]:
        """获取所有智能体信息"""
        return {
            agent_type: agent_class.get_agent_info() 
            for agent_type, agent_class in self._agents.items()
        }
    
    def create_agent(self, agent_type: str, llm, character, tools_manager=None, **kwargs):
        """创建智能体实例"""
        agent_class = self._agents.get(agent_type)
        if not agent_class:
            raise ValueError(f"未找到智能体类型: {agent_type}")
        
        return agent_class(llm, character, tools_manager, **kwargs)


# 全局注册表实例
agent_registry = AgentRegistry() 