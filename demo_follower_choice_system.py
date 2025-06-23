#!/usr/bin/env python3
"""
随从选择系统演示
展示新的基于选择的游戏机制
"""

import asyncio
import json
from sultans_game.models import GamePhase, GameResult
from sultans_game.agents.agent_coordinator import AgentCoordinator
from sultans_game.agents.evaluator_agent import EvaluatorAgent
from sultans_game.agents.follower_agent import FollowerAgent
from sultans_game.agents.narrator_agent import NarratorAgent

async def demo_follower_choice_system():
    """演示随从选择系统"""
    print("🎮 随从选择系统演示")
    print("=" * 50)
    
    # 模拟LLM (这里用简单的mock)
    class MockLLM:
        def __init__(self):
            pass
        
        def invoke(self, messages):
            # 简单的模拟响应
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            message_content = messages[0].content if messages else ""
            
            if "生成3个不同的行动选择" in message_content:
                return MockResponse(json.dumps([
                    {
                        "choice_id": "safe_approach",
                        "content": "小心翼翼地观察周围环境，寻找最安全的接近路线",
                        "risk_level": 1,
                        "expected_values": {"composure": 3, "tension": -1, "suspicion": 0}
                    },
                    {
                        "choice_id": "social_blend",
                        "content": "主动与其他客人交谈，试图融入环境获取信息",
                        "risk_level": 3,
                        "expected_values": {"charm": 4, "skill": 2, "suspicion": 2}
                    },
                    {
                        "choice_id": "bold_action",
                        "content": "大胆直接地接近目标，展现自信和魅力",
                        "risk_level": 5,
                        "expected_values": {"charm": 6, "skill": 3, "tension": 5, "suspicion": 4}
                    }
                ]))
            
            elif "评估以下随从行动的质量和影响" in message_content:
                return MockResponse(json.dumps({
                    "scores": {
                        "quality": 7,
                        "risk_assessment": 6,
                        "appropriateness": 8,
                        "strategic_value": 7
                    },
                    "value_changes": {
                        "charm": 3,
                        "skill": 2,
                        "tension": 2,
                        "suspicion": 1
                    },
                    "explanation": "这个行动展现了良好的社交技巧，有效提升了魅力值，同时控制了风险在可接受范围内。"
                }))
            
            elif "生成一段生动的旁白" in message_content:
                return MockResponse("🎭 随从巧妙地融入了人群中，他的举止优雅而自然，几个客人开始对他产生兴趣。烛光摇曳间，你注意到他正在缓慢而有效地接近目标区域...")
            
            else:
                return MockResponse("模拟AI响应")
    
    # 创建协调器
    mock_llm = MockLLM()
    coordinator = AgentCoordinator(mock_llm)
    
    # 注册智能体
    coordinator.agents = {
        'follower': FollowerAgent(mock_llm),
        'narrator': NarratorAgent(mock_llm),
        'evaluator': EvaluatorAgent(mock_llm)
    }
    
    print(f"游戏初始状态:")
    print(f"阶段: {coordinator.game_phase}")
    print(f"随从轮次: {coordinator.follower_rounds}/{coordinator.max_follower_rounds}")
    print(f"场景数值: {coordinator.scene_values}")
    print(f"目标数值: {coordinator.target_values}")
    print()
    
    # 模拟场景状态
    scene_state = {
        'location': '雅致阁',
        'atmosphere': '神秘而诱惑',
        'users': [
            {'username': 'player1', 'role': 'human_follower'},
            {'username': 'player2', 'role': 'observer'}
        ],
        'tension': 5,
        'characters_present': ['妓女小翠', '老鸨', '其他客人']
    }
    
    # 场景1：触发随从选择
    print("🎯 场景1：触发随从选择")
    print("-" * 30)
    
    user_message = "我们应该怎么行动？"
    username = "player1"
    user_role = "human_follower"
    
    # 检查是否触发选择
    should_trigger = coordinator._should_trigger_follower_choice(user_message, scene_state)
    print(f"是否触发随从选择: {should_trigger}")
    
    if should_trigger:
        responses = await coordinator._trigger_follower_choice(scene_state, username)
        for response in responses:
            print(f"🤖 {response['agent_name']}: {response['content']}")
            if 'choices' in response:
                print("📝 生成的选择选项:")
                for i, choice in enumerate(response['choices'], 1):
                    risk_label = {1: '🟢极低', 2: '🟡低', 3: '🟠中', 4: '🔴高', 5: '⚫极高'}
                    print(f"   选择{i} [{risk_label.get(choice['risk_level'], '❓')}]: {choice['content']}")
                    expected = choice.get('expected_values', {})
                    if expected:
                        changes = ', '.join([f"{k}{v:+}" for k, v in expected.items() if v != 0])
                        print(f"          预期变化: {changes}")
        print()
    
    # 场景2：处理玩家选择
    print("🎯 场景2：处理玩家选择")
    print("-" * 30)
    
    # 模拟玩家选择第2个选项
    choice_data = "social_blend"
    responses = await coordinator._handle_follower_choice(choice_data, scene_state, username)
    
    for response in responses:
        print(f"🤖 {response['agent_name']}: {response['content']}")
        if 'evaluation' in response:
            eval_data = response['evaluation']
            print("   📊 评估详情:")
            if 'scores' in eval_data:
                for key, value in eval_data['scores'].items():
                    print(f"      {key}: {value}/10")
            if 'value_changes' in eval_data:
                changes = eval_data['value_changes']
                change_str = ', '.join([f"{k}{v:+}" for k, v in changes.items() if v != 0])
                print(f"      数值变化: {change_str}")
        
        if response.get('response_type') == 'game_ended':
            print(f"   🏁 游戏结果: {response['result']}")
            print(f"   🏆 最终得分: {response['final_score']}")
            print(f"   📝 详情: {response['details']}")
    
    print()
    print(f"更新后的数值状态: {coordinator.scene_values}")
    print(f"当前轮次: {coordinator.follower_rounds}/{coordinator.max_follower_rounds}")
    print()
    
    # 场景3：测试自定义输入
    print("🎯 场景3：测试自定义输入")
    print("-" * 30)
    
    # 重置到选择阶段
    coordinator.game_phase = GamePhase.FOLLOWER_CHOICE
    coordinator.follower_rounds = 2
    
    custom_input = "我试图偷偷摸摸地溜到后院去"
    responses = await coordinator._handle_follower_choice(custom_input, scene_state, username)
    
    for response in responses:
        print(f"🤖 {response['agent_name']}: {response['content']}")
    
    print()
    print(f"最终数值状态: {coordinator.scene_values}")
    print()
    
    # 场景4：测试游戏结束条件
    print("🎯 场景4：测试游戏结束条件")
    print("-" * 30)
    
    # 模拟达到轮数限制
    coordinator.follower_rounds = coordinator.max_follower_rounds
    game_result = coordinator._check_game_end_conditions()
    
    if game_result:
        print("🏁 游戏结束触发!")
        print(f"   结果: {game_result['result']}")
        print(f"   得分: {game_result['score']}")
        print(f"   详情: {game_result['details']}")
        print(f"   最终数值: {game_result['final_values']}")
    
    print()
    print("🎉 演示完成！")
    print("=" * 50)
    print("新的随从选择系统特点:")
    print("✅ 随从角色基于选择而非自由输入")
    print("✅ 系统生成3个风险等级不同的选择")
    print("✅ 支持玩家自定义输入作为第4选择")
    print("✅ 智能评分系统评估每个选择")
    print("✅ 实时数值变化和游戏进度控制")
    print("✅ 多种游戏结束条件和奖励计算")
    print("✅ 旁白智能体生成故事反应")

if __name__ == "__main__":
    asyncio.run(demo_follower_choice_system()) 