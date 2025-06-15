from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import uuid

class CardType(Enum):
    """卡牌类型"""
    LUST = "纵欲"  # 纵欲卡
    LUXURY = "奢靡"  # 奢靡卡
    CONQUEST = "征服"  # 征服卡
    MURDER = "杀戮"  # 杀戮卡

class CardRank(Enum):
    """卡牌品级"""
    ROCK = "岩石"
    BRONZE = "青铜"
    SILVER = "白银"
    GOLD = "黄金"

@dataclass
class Card:
    """卡牌类"""
    card_type: CardType
    rank: CardRank
    title: str
    description: str
    target_character: Optional[str] = None
    required_actions: List[str] = field(default_factory=list)
    rewards: Dict[str, int] = field(default_factory=dict)
    penalty: Dict[str, int] = field(default_factory=dict)
    time_limit_days: int = 7
    card_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "card_type": self.card_type.value,
            "rank": self.rank.value,
            "title": self.title,
            "description": self.description,
            "target_character": self.target_character,
            "required_actions": self.required_actions,
            "rewards": self.rewards,
            "penalty": self.penalty,
            "time_limit_days": self.time_limit_days
        }

@dataclass
class Character:
    """角色类"""
    name: str
    role: str  # 随从、妓女、老鸨等
    personality: str
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "魅力": 50,
        "智慧": 50,
        "体魄": 50,
        "战斗": 50,
        "社交": 50,
        "隐匿": 50,
        "防御": 50,
        "声望": 50
    })
    relationships: Dict[str, int] = field(default_factory=dict)  # 与其他角色的关系值
    status: Dict[str, Any] = field(default_factory=dict)  # 状态信息
    inventory: List[str] = field(default_factory=list)
    alive: bool = True
    
    # 便捷属性访问
    @property
    def charm(self) -> int:
        return self.attributes.get("魅力", 50)
    
    @property
    def wisdom(self) -> int:
        return self.attributes.get("智慧", 50)
    
    @property
    def physique(self) -> int:
        return self.attributes.get("体魄", 50)
    
    @property
    def combat(self) -> int:
        return self.attributes.get("战斗", 50)
    
    @property
    def social(self) -> int:
        return self.attributes.get("社交", 50)
    
    @property
    def stealth(self) -> int:
        return self.attributes.get("隐匿", 50)
    
    @property
    def defense(self) -> int:
        return self.attributes.get("防御", 50)
    
    @property
    def reputation(self) -> int:
        return self.attributes.get("声望", 50)
    
    def get_relationship(self, target: str) -> int:
        """获取与目标角色的关系值"""
        return self.relationships.get(target, 50)
    
    def change_relationship(self, target: str, change: int):
        """改变与目标角色的关系"""
        current = self.relationships.get(target, 50)
        self.relationships[target] = max(0, min(100, current + change))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "personality": self.personality,
            "attributes": self.attributes,
            "relationships": self.relationships,
            "status": self.status,
            "inventory": self.inventory,
            "alive": self.alive
        }

@dataclass
class SceneState:
    """场景状态类"""
    location: str
    characters_present: List[str]
    atmosphere: str
    time_of_day: str
    special_conditions: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    scene_values: Dict[str, int] = field(default_factory=lambda: {
        "紧张度": 0,
        "暧昧度": 0,
        "危险度": 0,
        "金钱消费": 0
    })
    
    def add_conversation(self, speaker: str, content: str, context: str = ""):
        """添加对话记录"""
        self.conversation_history.append({
            "speaker": speaker,
            "content": content,
            "context": context,
            "timestamp": len(self.conversation_history)
        })
    
    def update_scene_value(self, key: str, change: int):
        """更新场景数值"""
        current = self.scene_values.get(key, 0)
        self.scene_values[key] = max(0, min(100, current + change))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "location": self.location,
            "characters_present": self.characters_present,
            "atmosphere": self.atmosphere,
            "time_of_day": self.time_of_day,
            "special_conditions": self.special_conditions,
            "conversation_history": self.conversation_history,
            "scene_values": self.scene_values
        }

@dataclass
class GameState:
    """游戏状态类"""
    current_scene: SceneState
    active_cards: List[Card] = field(default_factory=list)  # 支持多张激活卡牌
    characters: Dict[str, Character] = field(default_factory=dict)
    dialogue_history: List[Dict[str, Any]] = field(default_factory=list)  # 对话历史
    day: int = 1
    resources: Dict[str, int] = field(default_factory=lambda: {
        "金币": 100,
        "声望": 50,
        "情报": 0
    })
    flags: Dict[str, bool] = field(default_factory=dict)
    
    # 为了向后兼容，保留active_card属性
    @property
    def active_card(self) -> Optional[Card]:
        return self.active_cards[0] if self.active_cards else None
    
    @active_card.setter
    def active_card(self, card: Optional[Card]):
        if card:
            self.active_cards = [card]
        else:
            self.active_cards = []
    
    def save_to_json(self) -> str:
        """保存游戏状态为JSON"""
        data = {
            "current_scene": self.current_scene.to_dict(),
            "active_cards": [card.to_dict() for card in self.active_cards],
            "characters": {name: char.to_dict() for name, char in self.characters.items()},
            "dialogue_history": self.dialogue_history,
            "day": self.day,
            "resources": self.resources,
            "flags": self.flags
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_json(cls, json_str: str) -> 'GameState':
        """从JSON加载游戏状态"""
        # 简化版加载，实际应用中需要完整的反序列化逻辑
        data = json.loads(json_str)
        # 这里需要完整的反序列化逻辑，暂时返回默认状态
        return cls(current_scene=SceneState(location="妓院", characters_present=[], atmosphere="暧昧", time_of_day="夜晚"))