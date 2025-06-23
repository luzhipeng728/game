#!/usr/bin/env python3
"""测试卡片自动触发系统"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sultans_game.models import GameState, SceneState, Character
from sultans_game.cards import create_sample_cards, get_card_by_type, CardType
from sultans_game.tools import set_game_state

def test_card_auto_trigger():
    """测试卡片自动触发机制"""
    print("=== 测试卡片自动触发系统 ===\n")
    
    # 创建游戏状态
    scene = SceneState(
        location="妓院大厅",
        characters_present=["旁白者", "随从", "妓女", "老鸨"],
        atmosphere="奢华而神秘",
        time_of_day="夜晚",
        scene_values={
            "紧张度": 10,
            "暧昧度": 45,  # 接近触发条件
            "危险度": 5,
            "金钱消费": 20
        }
    )
    
    game_state = GameState(current_scene=scene)
    
    # 创建随从角色
    follower = Character(
        name="忠诚的随从",
        role="随从",
        personality="忠诚、谨慎、机智"
    )
    game_state.characters["随从"] = follower
    
    # 添加示例卡片
    cards = create_sample_cards()
    game_state.active_cards = cards[:2]  # 添加前两张卡片：杀戮卡和纵欲卡
    
    set_game_state(game_state)
    
    print("初始状态：")
    print(f"场景数值：{scene.scene_values}")
    print(f"激活卡片：{[card.title for card in game_state.active_cards]}")
    print()
    
    # 测试1：检查初始触发条件
    print("=== 测试1：检查初始触发条件 ===")
    available_cards = game_state.check_card_triggers()
    print(f"可用卡片数量：{len(available_cards)}")
    for card in available_cards:
        print(f"- {card.title}：触发条件 {card.trigger_condition}")
    print()
    
    # 测试2：提高暧昧度，触发纵欲卡
    print("=== 测试2：提高暧昧度，触发纵欲卡 ===")
    scene.scene_values["暧昧度"] = 65  # 超过60的触发条件
    available_cards = game_state.check_card_triggers()
    print(f"暧昧度提升到 {scene.scene_values['暧昧度']}")
    print(f"可用卡片数量：{len(available_cards)}")
    for card in available_cards:
        print(f"✅ {card.title} 可以使用！")
        print(f"   目标：{card.usage_objective}")
    print()
    
    # 测试3：获取卡片使用提示
    print("=== 测试3：获取卡片使用提示 ===")
    prompts = game_state.get_card_usage_prompts()
    print("智能体会收到的提示：")
    print(prompts)
    print()
    
    # 测试4：提高危险度，触发杀戮卡
    print("=== 测试4：提高危险度，触发杀戮卡 ===")
    scene.scene_values["危险度"] = 70  # 超过60的触发条件
    available_cards = game_state.check_card_triggers()
    print(f"危险度提升到 {scene.scene_values['危险度']}")
    print(f"可用卡片数量：{len(available_cards)}")
    for card in available_cards:
        print(f"⚠️ {card.title} 可以使用！")
        print(f"   触发条件：{card.trigger_condition}")
        print(f"   目标：{card.usage_objective}")
    print()
    
    # 测试5：模拟智能体决策提示
    print("=== 测试5：智能体决策提示 ===")
    print("随从智能体在上下文中会看到：")
    print("=" * 50)
    print("=== 卡片使用提示 ===")
    for card in game_state.active_cards:
        if card.can_be_used:
            print(f"🎴 {card.title}（{card.card_type.value}）现在可以使用！")
            print(f"   目标：{card.usage_objective}")
            print(f"   触发条件已满足：{card.trigger_condition}")
            print("   ⚡ 你可以考虑使用此卡片！")
    print("=" * 50)
    print()
    
    print("✅ 卡片自动触发系统测试完成！")
    print("随从智能体现在可以根据场景数值自动判断何时使用卡片。")

if __name__ == "__main__":
    test_card_auto_trigger() 