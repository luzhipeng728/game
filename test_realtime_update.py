#!/usr/bin/env python3
"""
测试实时场景数值更新功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sultans_game.models import GameState, SceneState
from sultans_game.agents import GameMaster
from sultans_game.cards import CardGenerator

def test_realtime_update():
    """测试实时更新功能"""
    print("🧪 测试实时场景数值更新功能")
    print("=" * 50)
    
    # 创建游戏状态
    scene = SceneState(
        location="妓院",
        characters_present=[],
        atmosphere="暧昧而神秘",
        time_of_day="夜晚"
    )
    game_state = GameState(current_scene=scene)
    
    print(f"初始场景数值: {scene.scene_values}")
    
    # 创建游戏管理器
    game_master = GameMaster(game_state)
    
    # 创建教学卡牌
    card_generator = CardGenerator()
    tutorial_card = card_generator.create_tutorial_card()
    
    print(f"使用卡牌: {tutorial_card.title}")
    print(f"卡牌描述: {tutorial_card.description}")
    
    # 创建默认角色
    follower = game_master._create_default_follower()
    courtesan = game_master._create_default_courtesan()
    madam = game_master._create_default_madam()
    
    print(f"创建角色: {follower.name}, {courtesan.name}, {madam.name}")
    
    # 设置妓院场景
    game_master.setup_brothel_scenario(follower, tutorial_card, courtesan, madam)
    
    print(f"场景设置后数值: {scene.scene_values}")
    
    # 模拟场景数值变化
    print("\n🎭 模拟智能体对话过程中的数值变化:")
    
    # 模拟第1轮对话后的数值变化
    print("\n第1轮对话后:")
    scene.scene_values['暧昧度'] = 20
    scene.scene_values['金钱消费'] = 10
    print(f"数值变化: {scene.scene_values}")
    
    # 模拟第2轮对话后的数值变化
    print("\n第2轮对话后:")
    scene.scene_values['暧昧度'] = 45
    scene.scene_values['紧张度'] = 15
    scene.scene_values['金钱消费'] = 25
    print(f"数值变化: {scene.scene_values}")
    
    # 模拟第3轮对话后的数值变化
    print("\n第3轮对话后:")
    scene.scene_values['暧昧度'] = 70
    scene.scene_values['紧张度'] = 25
    scene.scene_values['危险度'] = 10
    scene.scene_values['金钱消费'] = 40
    print(f"数值变化: {scene.scene_values}")
    
    # 模拟最终状态
    print("\n最终状态:")
    scene.scene_values['暧昧度'] = 100
    scene.scene_values['紧张度'] = 30
    scene.scene_values['危险度'] = 15
    scene.scene_values['金钱消费'] = 70
    print(f"最终数值: {scene.scene_values}")
    
    print("\n✅ 实时更新功能测试完成！")
    print("💡 在Streamlit应用中，这些数值变化将实时显示在对话区域和侧边栏中")

if __name__ == "__main__":
    test_realtime_update() 