#!/usr/bin/env python3

"""
苏丹的游戏 - 妓院场景演示
展示多智能体卡牌任务系统的完整交互流程
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_demo_characters():
    """创建演示角色"""
    from sultans_game.models import Character
    
    # 随从角色
    follower = Character(
        name="阿里",
        role="忠诚的随从",
        personality="谨慎而机智，擅长察言观色，对主人忠诚不二",
        attributes={
            "魅力": 65,
            "智慧": 75,
            "体魄": 70,
            "战斗": 80,
            "社交": 68,
            "隐匿": 85,
            "防御": 60,
            "声望": 45
        }
    )
    
    # 妓女角色
    courtesan = Character(
        name="雅斯敏",
        role="花魁",
        personality="魅惑动人，聪慧机敏，善于用美色和智慧获得想要的一切",
        attributes={
            "魅力": 95,
            "智慧": 70,
            "体魄": 55,
            "战斗": 25,
            "社交": 88,
            "隐匿": 65,
            "防御": 40,
            "声望": 75
        }
    )
    
    # 老鸨角色
    madam = Character(
        name="法蒂玛",
        role="老鸨",
        personality="精明能干，阅历丰富，既慈祥又严厉，保护手下姑娘们",
        attributes={
            "魅力": 70,
            "智慧": 90,
            "体魄": 60,
            "战斗": 45,
            "社交": 95,
            "隐匿": 70,
            "防御": 75,
            "声望": 85
        }
    )
    
    return follower, courtesan, madam

def create_demo_card():
    """创建演示卡牌"""
    from sultans_game.models import Card, CardType, CardRank
    
    return Card(
        card_type=CardType.LUST,
        rank=CardRank.BRONZE,
        title="美人心计",
        description="通过魅力和金钱在妓院中获得一位花魁的好感，并从她那里获得关于贵族客人的秘密情报",
        target_character="雅斯敏",
        required_actions=["展现魅力", "慷慨消费", "巧妙询问", "获得信任"],
        rewards={"情报": 20, "魅力": 2, "声望": 5, "经验": 25},
        penalty={"金币": -100, "被识破风险": "中等"},
        time_limit_days=3
    )

def setup_demo_scenario():
    """设置演示场景"""
    from sultans_game.models import GameState, SceneState
    from sultans_game.agents import GameMaster
    
    # 创建场景
    scene = SceneState(
        location="月牙湾妓院",
        atmosphere="烛光摇曳，香气弥漫，丝竹之声轻柔，暧昧而神秘",
        time_of_day="深夜",
        characters_present=[],
        scene_values={
            "紧张度": 15,
            "暧昧度": 45,
            "危险度": 10,
            "金钱消费": 0
        }
    )
    
    # 创建游戏状态
    game_state = GameState(current_scene=scene)
    
    # 创建角色
    follower, courtesan, madam = create_demo_characters()
    game_state.characters[follower.name] = follower
    game_state.characters[courtesan.name] = courtesan
    game_state.characters[madam.name] = madam
    
    # 设置关系
    follower.relationships[courtesan.name] = 50  # 初次相遇，中性
    follower.relationships[madam.name] = 45      # 稍有戒备
    courtesan.relationships[follower.name] = 55  # 略有好感
    madam.relationships[follower.name] = 40      # 警惕的商人态度
    
    # 创建游戏主控制器
    game_master = GameMaster(game_state)
    
    return game_master, follower, courtesan, madam

def run_demo():
    """运行演示"""
    print("🏰 《苏丹的游戏》- 妓院场景演示")
    print("=" * 60)
    print()
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 警告：未设置 OPENAI_API_KEY")
        print("   演示将创建智能体但不会执行实际对话")
        print("   请在 .env 文件中设置 API 密钥以体验完整功能")
        print()
    
    try:
        # 设置演示场景
        print("🎭 正在设置演示场景...")
        game_master, follower, courtesan, madam = setup_demo_scenario()
        card = create_demo_card()
        
        # 设置妓院场景
        game_master.setup_brothel_scenario(follower, card, courtesan, madam)
        
        print("✅ 场景设置完成")
        print()
        
        # 显示场景信息
        print("📍 场景信息:")
        print(f"   地点: {game_master.game_state.current_scene.location}")
        print(f"   氛围: {game_master.game_state.current_scene.atmosphere}")
        print(f"   时间: {game_master.game_state.current_scene.time_of_day}")
        print()
        
        print("🎴 当前卡牌任务:")
        print(f"   标题: {card.title}")
        print(f"   描述: {card.description}")
        print(f"   目标: {card.target_character}")
        print(f"   奖励: {card.rewards}")
        print()
        
        print("👥 角色介绍:")
        for name, char in game_master.game_state.characters.items():
            print(f"   • {name} ({char.role})")
            print(f"     性格: {char.personality}")
            print(f"     魅力: {char.charm}, 智慧: {char.wisdom}, 社交: {char.social}")
            print()
        
        # 如果有API密钥，运行实际对话
        if os.getenv("OPENAI_API_KEY"):
            print("🎬 开始多智能体对话交互...")
            print("=" * 60)
            
            # 运行妓院交互
            result = game_master.run_brothel_interaction(
                scenario_description="""
                夜深人静，月牙湾妓院内华灯初上。随从阿里奉主人之命，带着秘密任务踏进了这座城中最著名的风月场所。
                他必须巧妙地接近花魁雅斯敏，在不暴露真实意图的情况下获得关于贵族客人的珍贵情报。
                
                妓院内，老鸨法蒂玛正精明地观察着每一位客人，她的经验告诉她这位新来的客人并不简单。
                而美艳的雅斯敏则用她那双如星辰般的眼眸打量着这位英俊的陌生人，心中琢磨着他的来意...
                """,
                max_iterations=3  # 限制轮次以避免过长的对话
            )
            
            if result["success"]:
                print("\n🎉 对话交互完成!")
                print("\n📜 故事内容:")
                print("-" * 40)
                print(result["story_content"])
                print("-" * 40)
                
                # 显示最终状态
                print("\n📊 最终场景状态:")
                for key, value in result["scene_values"].items():
                    print(f"   {key}: {value}")
                
                print(f"\n💬 对话记录数: {len(result['dialogue_history'])}")
                
            else:
                print(f"\n❌ 对话执行失败: {result.get('error', '未知错误')}")
        
        else:
            print("💡 演示场景已准备就绪!")
            print("   设置 OPENAI_API_KEY 后重新运行以体验完整的 AI 对话")
        
        print("\n🎯 演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_demo()