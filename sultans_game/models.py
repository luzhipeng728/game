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

class GamePhase(Enum):
    """游戏阶段"""
    FREE_CHAT = "free_chat"  # 自由聊天阶段
    FOLLOWER_CHOICE = "follower_choice"  # 随从选择阶段
    GAME_ENDED = "game_ended"  # 游戏结束

class GameResult(Enum):
    """游戏结果"""
    SUCCESS = "success"  # 成功完成
    FAILURE = "failure"  # 失败被抓
    NEUTRAL = "neutral"  # 中性结局

@dataclass
class FollowerChoice:
    """随从选择项"""
    choice_id: str
    content: str
    risk_level: int  # 风险等级 1-5
    expected_values: Dict[str, int]  # 预期数值变化
    description: str = ""  # 选择描述/后果提示

@dataclass
class GameRound:
    """游戏轮次记录"""
    round_number: int
    phase: GamePhase
    messages: List[Dict[str, Any]] = field(default_factory=list)
    follower_choices: List[FollowerChoice] = field(default_factory=list)
    selected_choice: Optional[str] = None
    user_custom_input: Optional[str] = None
    value_changes: Dict[str, int] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__('time').time())

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
    
    # 新增卡片系统字段
    usage_objective: str = ""  # 使用目标/目的
    trigger_condition: Dict[str, int] = field(default_factory=dict)  # 触发条件（如："危险度": 60）
    success_condition: Dict[str, int] = field(default_factory=dict)  # 成功条件
    is_active: bool = False  # 是否已激活
    can_be_used: bool = False  # 是否可以使用
    game_ending: str = ""  # 游戏结局类型（"success", "failure", "neutral")
    auto_trigger: bool = True  # 是否允许智能体自动判断使用时机
    priority: int = 1  # 卡片使用优先级（1-10，越高越优先）
    
    # 奖励计算相关
    base_reward: int = 100  # 基础奖励
    reward_multiplier: float = 1.0  # 奖励倍数
    
    def check_trigger_conditions(self, scene_values: Dict[str, int]) -> bool:
        """检查是否满足触发条件"""
        if not self.trigger_condition or not self.auto_trigger:
            return False
            
        for condition_key, condition_value in self.trigger_condition.items():
            current_value = scene_values.get(condition_key, 0)
            if current_value < condition_value:
                return False
        return True
    
    def check_success_condition(self, scene_values: Dict[str, int]) -> bool:
        """检查是否满足成功条件"""
        if not self.success_condition:
            return False
            
        for condition_key, condition_value in self.success_condition.items():
            current_value = scene_values.get(condition_key, 0)
            if current_value < condition_value:
                return False
        return True
    
    def calculate_reward(self, rounds_used: int, max_rounds: int = 5) -> int:
        """计算奖励"""
        # 基础奖励 * 卡片等级倍数 * 轮数效率奖励
        rank_multipliers = {
            CardRank.ROCK: 1.0,
            CardRank.BRONZE: 1.5,
            CardRank.SILVER: 2.0,
            CardRank.GOLD: 3.0
        }
        
        efficiency_bonus = max(0, (max_rounds - rounds_used) * 0.2)  # 越少轮数奖励越高
        total_multiplier = rank_multipliers[self.rank] * (1 + efficiency_bonus) * self.reward_multiplier
        
        return int(self.base_reward * total_multiplier)
    
    def calculate_penalty(self) -> int:
        """计算惩罚"""
        rank_penalties = {
            CardRank.ROCK: 20,
            CardRank.BRONZE: 50,
            CardRank.SILVER: 100,
            CardRank.GOLD: 200
        }
        return rank_penalties[self.rank]
    
    def get_usage_prompt(self) -> str:
        """获取使用提示信息"""
        if not self.is_active or not self.auto_trigger:
            return ""
            
        prompt = f"""
🎴 卡片使用提示：
- 卡片：{self.title}（{self.card_type.value}）
- 目标：{self.usage_objective}
- 条件：{self.trigger_condition}
- 成功要求：{self.success_condition}
- 可以使用：{'是' if self.can_be_used else '否'}
"""
        if self.can_be_used:
            prompt += f"\n⚡ 你现在可以考虑使用此卡片来{self.usage_objective}！"
        
        return prompt
    
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
            "time_limit_days": self.time_limit_days,
            "usage_objective": self.usage_objective,
            "trigger_condition": self.trigger_condition,
            "success_condition": self.success_condition,
            "is_active": self.is_active,
            "can_be_used": self.can_be_used,
            "game_ending": self.game_ending,
            "auto_trigger": self.auto_trigger,
            "priority": self.priority,
            "base_reward": self.base_reward,
            "reward_multiplier": self.reward_multiplier
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
    
    # 新增游戏机制字段
    current_phase: GamePhase = GamePhase.FREE_CHAT
    follower_rounds_used: int = 0  # 已使用的随从轮数
    max_follower_rounds: int = 5  # 最大随从轮数
    game_rounds: List[GameRound] = field(default_factory=list)  # 游戏轮次记录
    pending_follower_choices: List[FollowerChoice] = field(default_factory=list)  # 待选择的随从选项
    game_result: Optional[GameResult] = None
    final_score: int = 0
    
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
    
    def check_card_triggers(self) -> List[Card]:
        """检查所有激活卡片的触发条件，返回可以使用的卡片列表"""
        available_cards = []
        scene_values = self.current_scene.scene_values
        
        for card in self.active_cards:
            if card.is_active and card.check_trigger_conditions(scene_values):
                card.can_be_used = True
                available_cards.append(card)
            else:
                card.can_be_used = False
                
        return available_cards
    
    def check_game_end_conditions(self) -> bool:
        """检查游戏结束条件"""
        # 检查轮数限制
        if self.follower_rounds_used >= self.max_follower_rounds:
            return True
        
        # 检查卡片成功条件
        for card in self.active_cards:
            if card.is_active and card.check_success_condition(self.current_scene.scene_values):
                return True
        
        # 检查危险度过高（失败条件）
        if self.current_scene.scene_values.get("危险度", 0) >= 90:
            return True
            
        return False
    
    def calculate_final_result(self) -> GameResult:
        """计算最终游戏结果"""
        scene_values = self.current_scene.scene_values
        danger_level = scene_values.get("危险度", 0)
        
        # 检查失败条件
        if danger_level >= 90:
            self.game_result = GameResult.FAILURE
            return GameResult.FAILURE
        
        # 检查成功条件
        for card in self.active_cards:
            if card.is_active and card.check_success_condition(scene_values):
                self.game_result = GameResult.SUCCESS
                return GameResult.SUCCESS
        
        # 中性结局
        self.game_result = GameResult.NEUTRAL
        return GameResult.NEUTRAL
    
    def calculate_final_score(self) -> int:
        """计算最终得分"""
        if not self.game_result:
            self.calculate_final_result()
        
        total_score = 0
        
        for card in self.active_cards:
            if card.is_active:
                if self.game_result == GameResult.SUCCESS:
                    total_score += card.calculate_reward(self.follower_rounds_used, self.max_follower_rounds)
                elif self.game_result == GameResult.FAILURE:
                    total_score -= card.calculate_penalty()
                # NEUTRAL 结局不加分不扣分
        
        # 额外奖励/惩罚
        if self.game_result == GameResult.SUCCESS:
            # 效率奖励
            efficiency_bonus = max(0, (self.max_follower_rounds - self.follower_rounds_used) * 50)
            total_score += efficiency_bonus
        elif self.game_result == GameResult.FAILURE:
            # 失败惩罚
            total_score -= 500
        
        self.final_score = total_score
        return total_score
    
    def start_follower_choice_phase(self):
        """开始随从选择阶段"""
        self.current_phase = GamePhase.FOLLOWER_CHOICE
        self.follower_rounds_used += 1
    
    def end_follower_choice_phase(self, selected_choice_id: Optional[str] = None, custom_input: Optional[str] = None):
        """结束随从选择阶段"""
        if self.game_rounds:
            current_round = self.game_rounds[-1]
            current_round.selected_choice = selected_choice_id
            current_round.user_custom_input = custom_input
        
        self.current_phase = GamePhase.FREE_CHAT
        self.pending_follower_choices = []
        
        # 检查游戏结束条件
        if self.check_game_end_conditions():
            self.current_phase = GamePhase.GAME_ENDED
            self.calculate_final_result()
            self.calculate_final_score()
    
    def add_game_round(self, phase: GamePhase) -> GameRound:
        """添加新的游戏轮次"""
        round_number = len(self.game_rounds) + 1
        new_round = GameRound(round_number=round_number, phase=phase)
        self.game_rounds.append(new_round)
        return new_round
    
    def get_card_usage_prompts(self) -> str:
        """获取所有可用卡片的使用提示"""
        prompts = []
        for card in self.active_cards:
            if card.is_active:
                prompt = card.get_usage_prompt()
                if prompt:
                    prompts.append(prompt)
        
        return "\n".join(prompts) if prompts else ""
    
    def save_to_json(self) -> str:
        """保存游戏状态为JSON"""
        data = {
            "current_scene": self.current_scene.to_dict(),
            "active_cards": [card.to_dict() for card in self.active_cards],
            "characters": {name: char.to_dict() for name, char in self.characters.items()},
            "dialogue_history": self.dialogue_history,
            "day": self.day,
            "resources": self.resources,
            "flags": self.flags,
            "current_phase": self.current_phase.value,
            "follower_rounds_used": self.follower_rounds_used,
            "max_follower_rounds": self.max_follower_rounds,
            "game_result": self.game_result.value if self.game_result else None,
            "final_score": self.final_score
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_json(cls, json_str: str) -> 'GameState':
        """从JSON加载游戏状态"""
        # 简化版加载，实际应用中需要完整的反序列化逻辑
        data = json.loads(json_str)
        # 这里需要完整的反序列化逻辑，暂时返回默认状态
        return cls(current_scene=SceneState(location="妓院", characters_present=[], atmosphere="暧昧", time_of_day="夜晚"))