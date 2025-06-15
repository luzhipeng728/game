#!/usr/bin/env python3

"""
苏丹的游戏 - 妓院场景演示
展示多智能体交互系统的完整功能
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
from sultans_game.config import get_openai_config

def print_header(title: str):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🏰 {title}")
    print("="*60)

def print_section(title: str):
    """打印章节标题"""
    print(f"\n--- {title} ---")

def setup_demo_characters():
    """设置演示角色"""
    print_section("创建角色")
    
    # 创建随从
    follower = Character(
        name="阿里·伊本·萨利姆",
        role="忠诚的随从",
        personality="机智谨慎，善于观察，对主人绝对忠诚",
        attributes={
            "魅力": 65,
            "智慧": 80,
            "体魄": 70,
            "战斗": 75,
            "社交": 70,
            "隐匿": 85
        }
    )
    print(f"✅ 随从创建成功: {follower.name}")
    
    # 创建妓女
    courtesan = Character(
        name="雅丝敏·月光之女",
        role="魅惑的妓女",
        personality="聪慧美丽，善于读心，在温柔中藏着锋芒",
        attributes={
            "魅力": 95,
            "智慧": 85,
            "体魄": 60,
            "战斗": 40,
            "社交": 90,
            "隐匿": 70
        }
    )
    print(f"✅ 妓女创建成功: {courtesan.name}")
    
    # 创建老鸨
    madam = Character(
        name="哈蒂嘉·金蔷薇夫人",
        role="精明的老鸨",
        personality="经验丰富，眼光毒辣，既慈祥又严厉，保护着她的姑娘们",
        attributes={
            "魅力": 75,
            "智慧": 90,
            "体魄": 65,
            "战斗": 60,
            "社交": 95,
            "隐匿": 80
        }
    )
    madam.attributes["声望"] = 85  # 特殊属性
    print(f"✅ 老鸨创建成功: {madam.name}")
    
    return follower, courtesan, madam

def setup_demo_scene():
    """设置演示场景"""
    print_section("设置场景")
    
    scene = SceneState(
        location="金蔷薇妓院 - 华丽的接待大厅",
        atmosphere="奢华而神秘，弥漫着檀香和玫瑰花的香味，烛光摇曳",
        time_of_day="深夜时分",
        characters_present=[],
        scene_values={
            "紧张度": 15,
            "暧昧度": 40,
            "危险度": 10,
            "金钱消费": 0,
            "老鸨关注度": 20,
            "妓女兴趣度": 30
        }
    )
    
    print(f"📍 场景: {scene.location}")
    print(f"🕰️ 时间: {scene.time_of_day}")
    print(f"🎭 氛围: {scene.atmosphere}")
    
    return scene

def create_demo_card():
    """创建演示卡牌"""
    print_section("生成任务卡牌")
    
    generator = CardGenerator()
    card = generator.generate_card(CardType.LUST, CardRank.BRONZE)
    
    print(f"🎴 卡牌: {card.title}")
    print(f"📝 类型: {card.card_type.value} - {card.rank.value}")
    print(f"📄 描述: {card.description}")
    
    if card.required_actions:
        print("📋 所需行动:")
        for action in card.required_actions:
            print(f"   - {action}")
    
    return card

def display_character_stats(characters):
    """显示角色状态"""
    print_section("角色状态")
    
    for char in characters:
        print(f"\n👤 {char.name} ({char.role})")
        print(f"   性格: {char.personality}")
        
        # 显示属性
        attrs = []
        for attr, value in char.attributes.items():
            attrs.append(f"{attr}:{value}")
        print(f"   属性: {' | '.join(attrs)}")
        
        # 显示关系
        if char.relationships:
            relationships = []
            for target, value in char.relationships.items():
                relationships.append(f"{target}:{value}")
            print(f"   关系: {' | '.join(relationships)}")

def run_demo_interaction(game_master, card):
    """运行演示交互"""
    print_section("开始智能体交互")
    
    print("🎭 智能体们开始交流...")
    print("📝 场景描述:")
    print("""
    夜幕深垂，金蔷薇妓院的华丽大厅里灯火辉煌。
    随从阿里带着主人的秘密任务来到这里，他必须小心翼翼地接近目标，
    完成卡牌任务而不暴露自己的真实意图。
    
    美丽的雅丝敏正在大厅中与其他客人交谈，
    而经验丰富的哈蒂嘉夫人则在一旁观察着每一个进入她领域的人...
    """)
    
    try:
        # 执行智能体交互
        result = game_master.run_brothel_interaction(
            scenario_description="""
            深夜的金蔷薇妓院，奢华而危险。随从必须在这个充满诱惑和陷阱的地方
            完成一项纵欲类任务，而妓女和老鸨都有着自己的盘算...
            """,
            max_iterations=3
        )
        
        if result["success"]:
            print("\n🎉 智能体交互完成！")
            
            # 显示故事内容
            if "story_content" in result:
                print_section("故事内容")
                print(result["story_content"])
            
            # 显示场景数值变化
            if "scene_values" in result:
                print_section("场景数值变化")
                for key, value in result["scene_values"].items():
                    print(f"   {key}: {value}")
            
            # 显示对话历史
            if result["dialogue_history"]:
                print_section("对话记录")
                for i, dialogue in enumerate(result["dialogue_history"]):
                    print(f"   {i+1}. {dialogue}")
        
        else:
            print(f"❌ 交互失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 执行交互时发生错误: {e}")

def main():
    """主演示函数"""
    print_header("苏丹的游戏 - 妓院场景演示")
    
    # 检查配置
    print_section("检查系统配置")
    config = get_openai_config()
    print("✅ API配置加载成功")
    print(f"   模型: {config['model']}")
    print(f"   API Base: {config['base_url']}")
    
    try:
        # 设置角色
        follower, courtesan, madam = setup_demo_characters()
        
        # 设置场景
        scene = setup_demo_scene()
        
        # 创建游戏状态
        game_state = GameState(current_scene=scene)
        game_state.characters[follower.name] = follower
        game_state.characters[courtesan.name] = courtesan
        game_state.characters[madam.name] = madam
        
        # 创建卡牌
        card = create_demo_card()
        
        # 显示角色状态
        display_character_stats([follower, courtesan, madam])
        
        # 创建游戏主控制器
        print_section("初始化游戏系统")
        game_master = GameMaster(game_state)
        print("✅ 游戏主控制器创建成功")
        
        # 设置妓院场景
        game_master.setup_brothel_scenario(follower, card, courtesan, madam)
        print("✅ 妓院场景设置完成")
        
        # 执行演示交互
        print("🎭 准备开始智能体交互...")
        print("   这可能需要几分钟时间，请耐心等待...")
        
        run_demo_interaction(game_master, card)
        
        # 显示最终游戏摘要
        print_section("游戏摘要")
        summary = game_master.get_game_summary()
        
        print("📊 最终状态:")
        print(f"   场景: {summary['scene']['location']}")
        print(f"   氛围: {summary['scene']['atmosphere']}")
        print(f"   对话轮数: {summary['dialogue_count']}")
        
        print("\n🎯 角色关系变化:")
        for char_name, char_data in summary['characters'].items():
            if char_data['relationships']:
                print(f"   {char_name}:")
                for target, relationship in char_data['relationships'].items():
                    print(f"     - 对 {target}: {relationship}")
        
        print("\n🏆 演示完成！")
        print("   如果想要体验完整的 AI 对话，请确保:")
        print("   ✅ API配置正确")
        print("   ✅ 网络连接正常")
        print("   ✅ 模型服务可用")
        
    except Exception as e:
        print(f"❌ 演示执行失败: {e}")
        print("📝 请检查:")
        print("   - API配置是否正确")
        print("   - 网络连接是否正常")
        print("   - 所有依赖是否已安装")

if __name__ == "__main__":
    main()