from typing import List, Dict, Any, Optional
import random
from .models import Card, CardType, CardRank, Character

class CardGenerator:
    """卡牌生成器"""
    
    def __init__(self):
        self.lust_cards = self._create_lust_cards()
        self.luxury_cards = self._create_luxury_cards()
        self.conquest_cards = self._create_conquest_cards()
        self.murder_cards = self._create_murder_cards()
    
    def _create_lust_cards(self) -> Dict[CardRank, List[Dict[str, Any]]]:
        """创建纵欲卡"""
        return {
            CardRank.ROCK: [
                {
                    "title": "街头艳遇",
                    "description": "在集市中寻找一位平民女子，与她度过一夜春宵",
                    "target_character": "平民女子",
                    "required_actions": ["进入集市", "寻找目标", "魅力检定"],
                    "rewards": {"经验": 10, "魅力": 1},
                    "penalty": {"声望": -5}
                },
                {
                    "title": "妓院寻欢",
                    "description": "前往妓院，享受肉体的愉悦",
                    "target_character": "妓女",
                    "required_actions": ["进入妓院", "选择女子", "支付金币"],
                    "rewards": {"经验": 15, "满足感": 20},
                    "penalty": {"金币": -20, "妻子好感": -10}
                }
            ],
            CardRank.BRONZE: [
                {
                    "title": "诱惑侍女",
                    "description": "用你的魅力征服府邸中的一名侍女",
                    "target_character": "府邸侍女",
                    "required_actions": ["与侍女交流", "魅力检定", "私密会面"],
                    "rewards": {"经验": 20, "魅力": 2, "情报": 5},
                    "penalty": {"声望": -10}
                }
            ],
            CardRank.SILVER: [
                {
                    "title": "贵妇密会",
                    "description": "与一位贵族夫人发生不正当关系",
                    "target_character": "贵族夫人",
                    "required_actions": ["接触贵妇", "暗中约会", "保密行动"],
                    "rewards": {"经验": 30, "魅力": 3, "声望": 10, "情报": 15},
                    "penalty": {"危险度": +20}
                }
            ],
            CardRank.GOLD: [
                {
                    "title": "王妃私情",
                    "description": "与苏丹的妃子之一发生关系，这是极其危险的背叛",
                    "target_character": "王妃",
                    "required_actions": ["进入后宫", "接近王妃", "完成私会"],
                    "rewards": {"经验": 50, "魅力": 5, "情报": 30},
                    "penalty": {"危险度": +50, "死亡风险": "极高"}
                }
            ]
        }
    
    def _create_luxury_cards(self) -> Dict[CardRank, List[Dict[str, Any]]]:
        """创建奢靡卡"""
        return {
            CardRank.ROCK: [
                {
                    "title": "购买珠宝",
                    "description": "在市集购买昂贵的珠宝来炫耀财富",
                    "required_actions": ["前往市集", "选择珠宝", "支付金币"],
                    "rewards": {"魅力": 2, "声望": 5},
                    "penalty": {"金币": -50}
                }
            ],
            CardRank.BRONZE: [
                {
                    "title": "举办宴会",
                    "description": "在府邸举办豪华宴会，邀请贵族参加",
                    "required_actions": ["准备宴会", "邀请宾客", "支付费用"],
                    "rewards": {"声望": 15, "人脉": 10},
                    "penalty": {"金币": -100}
                }
            ],
            CardRank.SILVER: [
                {
                    "title": "建造花园",
                    "description": "为府邸建造一座华丽的花园",
                    "required_actions": ["雇佣工匠", "购买材料", "监督建造"],
                    "rewards": {"声望": 25, "魅力": 5},
                    "penalty": {"金币": -200}
                }
            ],
            CardRank.GOLD: [
                {
                    "title": "皇家献礼",
                    "description": "向苏丹献上价值连城的珍宝",
                    "required_actions": ["寻找珍宝", "准备献礼", "觐见苏丹"],
                    "rewards": {"声望": 50, "苏丹好感": 20},
                    "penalty": {"金币": -500}
                }
            ]
        }
    
    def _create_conquest_cards(self) -> Dict[CardRank, List[Dict[str, Any]]]:
        """创建征服卡"""
        return {
            CardRank.ROCK: [
                {
                    "title": "镇压盗匪",
                    "description": "前往边境清剿骚扰商队的盗匪",
                    "required_actions": ["组织队伍", "前往边境", "战斗"],
                    "rewards": {"战斗经验": 20, "声望": 10, "战利品": 30},
                    "penalty": {"伤亡风险": "中等"}
                }
            ],
            CardRank.BRONZE: [
                {
                    "title": "征收税款",
                    "description": "前往偏远村庄征收拖欠的税款",
                    "required_actions": ["前往村庄", "威胁村民", "收取税款"],
                    "rewards": {"金币": 80, "声望": 5},
                    "penalty": {"民心": -15}
                }
            ],
            CardRank.SILVER: [
                {
                    "title": "攻占要塞",
                    "description": "率军攻占敌对势力的要塞",
                    "required_actions": ["集结军队", "制定战术", "攻城战"],
                    "rewards": {"声望": 30, "战利品": 100, "土地": 1},
                    "penalty": {"伤亡风险": "高"}
                }
            ],
            CardRank.GOLD: [
                {
                    "title": "远征异域",
                    "description": "率领大军远征遥远的敌国",
                    "required_actions": ["准备远征", "跨境作战", "占领城池"],
                    "rewards": {"声望": 60, "战利品": 300, "荣誉": 50},
                    "penalty": {"伤亡风险": "极高", "时间": "长期"}
                }
            ]
        }
    
    def _create_murder_cards(self) -> Dict[CardRank, List[Dict[str, Any]]]:
        """创建杀戮卡"""
        return {
            CardRank.ROCK: [
                {
                    "title": "处决罪犯",
                    "description": "公开处决一名被判死刑的罪犯",
                    "target_character": "死囚",
                    "required_actions": ["主持处决", "公开行刑"],
                    "rewards": {"声望": 5, "威慑力": 10},
                    "penalty": {"民心": -5}
                }
            ],
            CardRank.BRONZE: [
                {
                    "title": "暗杀叛徒",
                    "description": "秘密暗杀一名背叛苏丹的官员",
                    "target_character": "叛变官员",
                    "required_actions": ["收集情报", "计划暗杀", "执行刺杀"],
                    "rewards": {"声望": 15, "苏丹好感": 10},
                    "penalty": {"被发现风险": "中等"}
                }
            ],
            CardRank.SILVER: [
                {
                    "title": "决斗致死",
                    "description": "与一名敌对贵族进行生死决斗",
                    "target_character": "敌对贵族",
                    "required_actions": ["发起挑战", "准备决斗", "生死战"],
                    "rewards": {"声望": 25, "荣誉": 20},
                    "penalty": {"死亡风险": "高"}
                }
            ],
            CardRank.GOLD: [
                {
                    "title": "弑君谋反",
                    "description": "策划刺杀苏丹，夺取王位",
                    "target_character": "苏丹",
                    "required_actions": ["秘密策划", "收买内应", "执行刺杀"],
                    "rewards": {"王位": 1, "终极权力": 100},
                    "penalty": {"死亡风险": "极高", "全族诛杀": "可能"}
                }
            ]
        }
    
    def generate_random_card(self, card_type: Optional[CardType] = None, rank: Optional[CardRank] = None) -> Card:
        """生成随机卡牌"""
        if not card_type:
            card_type = random.choice(list(CardType))
        
        if not rank:
            rank = random.choice(list(CardRank))
        
        return self._generate_card_internal(card_type, rank)
    
    def generate_card(self, card_type: CardType, rank: CardRank) -> Card:
        """生成指定类型和品级的卡牌"""
        return self._generate_card_internal(card_type, rank)
    
    def _generate_card_internal(self, card_type: CardType, rank: CardRank) -> Card:
        """内部卡牌生成方法"""
        # 根据类型选择卡牌数据
        cards_data = None
        if card_type == CardType.LUST:
            cards_data = self.lust_cards
        elif card_type == CardType.LUXURY:
            cards_data = self.luxury_cards
        elif card_type == CardType.CONQUEST:
            cards_data = self.conquest_cards
        elif card_type == CardType.MURDER:
            cards_data = self.murder_cards
        
        if not cards_data or rank not in cards_data:
            # 如果没有找到对应卡牌，生成默认卡牌
            return self._create_default_card(card_type, rank)
        
        # 随机选择一张卡牌
        card_options = cards_data[rank]
        if not card_options:
            return self._create_default_card(card_type, rank)
        
        card_data = random.choice(card_options)
        
        return Card(
            card_type=card_type,
            rank=rank,
            title=card_data["title"],
            description=card_data["description"],
            target_character=card_data.get("target_character"),
            required_actions=card_data.get("required_actions", []),
            rewards=card_data.get("rewards", {}),
            penalty=card_data.get("penalty", {}),
            time_limit_days=7
        )
    
    def _create_default_card(self, card_type: CardType, rank: CardRank) -> Card:
        """创建默认卡牌"""
        return Card(
            card_type=card_type,
            rank=rank,
            title=f"默认{card_type.value}任务",
            description=f"一个{rank.value}级别的{card_type.value}任务",
            required_actions=["完成任务"],
            rewards={"经验": 10},
            penalty={"声望": -5}
        )
    
    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        """获取指定类型的所有卡牌"""
        cards = []
        for rank in CardRank:
            try:
                card = self.generate_random_card(card_type, rank)
                cards.append(card)
            except:
                continue
        return cards
    
    def create_tutorial_card(self) -> Card:
        """创建教学卡牌"""
        return Card(
            card_type=CardType.LUST,
            rank=CardRank.ROCK,
            title="初次体验",
            description="派遣你的随从前往妓院，学习如何完成纵欲任务",
            target_character="妓女·雅斯敏",
            required_actions=["进入妓院", "与妓女交流", "评估情况"],
            rewards={"经验": 20, "教学完成": 1},
            penalty={"金币": -10}
        )