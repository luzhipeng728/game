#!/usr/bin/env python3
"""新智能体系统演示"""

from sultans_game.models import GameState, Character, Card, CardType, CardRank
from sultans_game.agents import AgentManager, agent_registry, scene_config_manager


def main():
    print("=== 苏丹的游戏 - 新智能体系统演示 ===\n")
    
    # 1. 查看系统信息
    print("1. 系统信息:")
    print(f"   可用智能体类型: {agent_registry.get_all_agent_types()}")
    print(f"   可用场景: {scene_config_manager.get_all_scene_names()}")
    print()
    
    # 2. 查看场景详情
    print("2. 场景详情:")
    for scene_name in scene_config_manager.get_all_scene_names():
        info = scene_config_manager.get_scene_info(scene_name)
        print(f"   场景: {scene_name}")
        print(f"     描述: {info['description']}")
        print(f"     位置: {info['location']}")
        print(f"     需要智能体: {info['required_agents']}")
        print()
    
    # 3. 创建游戏状态
    print("3. 创建游戏状态...")
    from sultans_game.models import SceneState
    initial_scene = SceneState(
        location="初始场景",
        characters_present=[],
        atmosphere="平静",
        time_of_day="夜晚"
    )
    game_state = GameState(current_scene=initial_scene)
    
    # 4. 创建智能体管理器
    print("4. 创建智能体管理器...")
    agent_manager = AgentManager()
    agent_manager.set_game_state(game_state)
    
    # 5. 设置妓院场景
    print("5. 设置妓院场景...")
    success = agent_manager.setup_scene("brothel")
    if success:
        print("   ✅ 场景设置成功！")
        active_agents = agent_manager.get_active_agents()
        print(f"   活跃智能体: {list(active_agents.keys())}")
    else:
        print("   ❌ 场景设置失败！")
        return
    print()
    
    # 6. 创建测试卡牌
    print("6. 创建测试卡牌...")
    test_card = Card(
        card_id="test_001",
        title="收集情报",
        description="在妓院中巧妙地收集关于城中贵族的情报",
        card_type=CardType.LUST,
        rank=CardRank.BRONZE,
        target_character="妓女",
        required_actions=["对话", "观察"]
    )
    print(f"   卡牌: {test_card.title}")
    print(f"   描述: {test_card.description}")
    print()
    
    # 7. 运行场景对话
    print("7. 运行场景对话...")
    print("   (这将启动智能体自动对话)")
    
    result = agent_manager.run_scene_conversation(test_card)
    
    if result["success"]:
        print("   ✅ 对话执行成功！")
        print("\n=== 对话内容 ===")
        print(result["story_content"])
        print("\n=== 场景数值 ===")
        for key, value in result["scene_values"].items():
            print(f"   {key}: {value}")
    else:
        print(f"   ❌ 对话执行失败: {result.get('error', '未知错误')}")
    
    print("\n=== 演示结束 ===")


def demo_custom_scene():
    """演示自定义场景创建"""
    print("\n=== 自定义场景演示 ===")
    
    # 创建自定义场景配置
    custom_agents = [
        {
            "agent_type": "narrator",
            "character_name": "旁白者",
            "role_name": "旁白",
            "required": True
        },
        {
            "agent_type": "follower",
            "character_name": "间谍",
            "role_name": "间谍",
            "required": True
        }
        # 可以添加更多智能体类型
    ]
    
    custom_scene = scene_config_manager.create_custom_scene(
        scene_name="spy_meeting",
        description="秘密会面场景",
        location="城郊小屋",
        atmosphere="紧张而神秘",
        agent_configs=custom_agents,
        initial_values={
            "紧张度": 70,
            "秘密程度": 90,
            "危险度": 60
        },
        max_rounds=6,
        min_rounds=3
    )
    
    print(f"创建自定义场景: {custom_scene.scene_name}")
    print(f"描述: {custom_scene.description}")
    print(f"智能体配置: {[agent.agent_type for agent in custom_scene.agents]}")


def demo_add_remove_agents():
    """演示动态添加和移除智能体"""
    print("\n=== 动态智能体管理演示 ===")
    
    from sultans_game.models import SceneState
    initial_scene = SceneState(
        location="市场",
        characters_present=[],
        atmosphere="热闹",
        time_of_day="白天"
    )
    game_state = GameState(current_scene=initial_scene)
    agent_manager = AgentManager()
    agent_manager.set_game_state(game_state)
    
    # 设置基础场景
    agent_manager.setup_scene("market")
    print(f"初始智能体: {list(agent_manager.get_active_agents().keys())}")
    
    # 创建新角色并添加智能体
    new_character = Character(
        name="商人",
        role="商人",
        personality="精明的商人",
        attributes={"魅力": 70, "智慧": 80, "社交": 75}
    )
    
    # 这里假设我们有商人智能体类型
    # agent_manager.add_agent_to_scene("merchant", new_character)
    print("注意: 需要先创建商人智能体类型才能添加")


if __name__ == "__main__":
    main()
    demo_custom_scene()
    demo_add_remove_agents() 