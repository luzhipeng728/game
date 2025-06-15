#!/usr/bin/env python3
"""
苏丹的游戏 - 系统测试脚本
测试多智能体交互系统的各个组件
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入游戏模块
from sultans_game.models import GameState, Character, Card, CardType, CardRank, SceneState
from sultans_game.agents import GameMaster
from sultans_game.cards import CardGenerator
from sultans_game.tools import GameToolsManager
from sultans_game.config import get_openai_config

def print_separator(title: str):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)

def print_subsection(title: str):
    """打印子章节标题"""
    print(f"\n--- {title} ---")

def test_config():
    """测试配置"""
    print_separator("配置测试")
    
    try:
        config = get_openai_config()
        print("✅ API配置加载成功")
        print(f"   模型: {config['model']}")
        print(f"   API Base: {config['base_url']}")
        print(f"   API Key: {config['api_key'][:10]}...{config['api_key'][-4:]}")
        return True
    except Exception as e:
        print(f"❌ API配置加载失败: {e}")
        return False

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from sultans_game.models import GameState, SceneState, Card, CardType, CardRank, Character
        from sultans_game.agents import GameMaster, SultansGameAgents
        from sultans_game.cards import CardGenerator
        from sultans_game.tools import GameToolsManager
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_models():
    """测试数据模型"""
    print("\n🔍 测试数据模型...")
    
    try:
        from sultans_game.models import GameState, SceneState, Card, CardType, CardRank, Character
        
        # 测试角色创建
        character = Character(
            name="测试角色",
            role="随从",
            personality="测试性格",
            attributes={
                "魅力": 60,
                "智慧": 70,
                "体魄": 65,
                "战斗": 75,
                "社交": 65,
                "隐匿": 70
            }
        )
        print(f"✅ 角色创建成功: {character.name}")
        
        # 测试便捷属性访问
        assert character.charm == 60, f"魅力属性错误: {character.charm}"
        assert character.wisdom == 70, f"智慧属性错误: {character.wisdom}"
        print("✅ 便捷属性访问正常")
        
        # 测试场景创建
        scene = SceneState(
            location="测试场景",
            characters_present=["测试角色"],
            atmosphere="测试氛围",
            time_of_day="测试时间"
        )
        print(f"✅ 场景创建成功: {scene.location}")
        
        # 测试游戏状态
        game_state = GameState(current_scene=scene)
        game_state.characters["测试角色"] = character
        print("✅ 游戏状态创建成功")
        
        # 测试关系系统
        character.change_relationship("目标角色", 10)
        relationship = character.get_relationship("目标角色")
        print(f"✅ 关系系统测试成功: {relationship}")
        
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_cards():
    """测试卡牌生成器"""
    print("\n🔍 测试卡牌生成器...")
    
    try:
        from sultans_game.cards import CardGenerator
        from sultans_game.models import CardType, CardRank
        
        generator = CardGenerator()
        
        # 测试随机卡牌生成
        random_card = generator.generate_random_card()
        print(f"✅ 随机卡牌生成成功: {random_card.title}")
        
        # 测试指定类型卡牌生成
        lust_card = generator.generate_card(CardType.LUST, CardRank.ROCK)
        print(f"✅ 指定类型卡牌生成成功: {lust_card.title}")
        
        # 测试教学卡牌
        tutorial_card = generator.create_tutorial_card()
        print(f"✅ 教学卡牌创建成功: {tutorial_card.title}")
        
        return True
    except Exception as e:
        print(f"❌ 卡牌生成器测试失败: {e}")
        return False

def test_tools():
    """测试工具系统"""
    print("\n🔍 测试工具系统...")
    
    try:
        from sultans_game.tools import GameToolsManager, relationship_tool, scene_value_tool, dice_roll_tool, set_game_state
        from sultans_game.models import GameState, SceneState, Character
        
        # 创建测试游戏状态
        scene = SceneState(
            location="测试场景",
            characters_present=["角色A", "角色B"],
            atmosphere="测试氛围",
            time_of_day="测试时间"
        )
        
        character_a = Character(name="角色A", role="随从", personality="忠诚")
        character_b = Character(name="角色B", role="妓女", personality="魅惑")
        
        game_state = GameState(current_scene=scene)
        game_state.characters["角色A"] = character_a
        game_state.characters["角色B"] = character_b
        
        # 创建工具管理器并设置全局游戏状态
        tools_manager = GameToolsManager(game_state)
        
        # 测试关系工具 - 直接调用工具函数
        result = relationship_tool.func("角色A", "角色B", 10, "测试互动")
        print("✅ 关系工具测试成功")
        
        # 测试场景数值工具
        result = scene_value_tool.func("紧张度", 5, "测试事件")
        print("✅ 场景数值工具测试成功")
        
        # 测试骰子检定工具
        result = dice_roll_tool.func("角色A", "魅力", 15)
        print("✅ 骰子检定工具测试成功")
        
        return True
    except Exception as e:
        print(f"❌ 工具系统测试失败: {e}")
        return False

def test_agents():
    """测试智能体创建"""
    print("\n🔍 测试智能体创建...")
    
    try:
        from sultans_game.agents import SultansGameAgents
        from sultans_game.models import Character, Card, CardType, CardRank
        from sultans_game.tools import GameToolsManager
        from sultans_game.models import GameState, SceneState
        
        # 创建测试环境
        scene = SceneState(
            location="妓院",
            characters_present=[],
            atmosphere="神秘",
            time_of_day="夜晚"
        )
        
        game_state = GameState(current_scene=scene)
        tools_manager = GameToolsManager(game_state)
        
        # 创建智能体管理器
        agents_creator = SultansGameAgents()
        
        # 创建测试角色
        character = Character(
            name="测试随从",
            role="随从",
            personality="忠诚谨慎",
            attributes={
                "魅力": 60,
                "智慧": 70,
                "体魄": 65,
                "战斗": 75,
                "社交": 65,
                "隐匿": 70
            }
        )
        
        # 创建测试卡牌
        card = Card(
            card_type=CardType.LUST,
            rank=CardRank.BRONZE,
            title="测试卡牌",
            description="这是一张测试卡牌"
        )
        
        # 测试随从智能体创建
        follower_agent = agents_creator.create_follower_agent(character, card, tools_manager)
        print("✅ 随从智能体创建成功")
        
        # 测试其他智能体创建
        courtesan_agent = agents_creator.create_courtesan_agent(character, tools_manager)
        madam_agent = agents_creator.create_madam_agent(character, tools_manager)
        narrator_agent = agents_creator.create_narrator_agent(tools_manager)
        
        print("✅ 所有智能体创建成功")
        return True
    except Exception as e:
        print(f"❌ 智能体创建测试失败: {e}")
        return False

def test_game_master():
    """测试游戏主控制器"""
    print("\n🔍 测试游戏主控制器...")
    
    try:
        from sultans_game.agents import GameMaster
        from sultans_game.models import GameState, SceneState
        
        # 创建游戏状态
        scene = SceneState(
            location="妓院",
            characters_present=[],
            atmosphere="神秘",
            time_of_day="夜晚"
        )
        
        game_state = GameState(current_scene=scene)
        
        # 创建游戏主控制器
        game_master = GameMaster(game_state)
        print("✅ 游戏主控制器创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 游戏主控制器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🏰 苏丹的游戏 - 系统测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_models,
        test_cards,
        test_tools,
        test_config,
        test_agents,
        test_game_master
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查错误信息并修复问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)