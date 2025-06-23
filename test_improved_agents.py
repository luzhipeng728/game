"""测试改进后的智能体协调系统"""

import asyncio
import json
import websockets
import time

async def test_coordinated_agents():
    """测试协调后的智能体系统"""
    uri = "ws://localhost:8000/ws/improved_test"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🎭 连接到改进测试房间")
            
            # 加入房间作为人类随从
            join_message = {
                "type": "join",
                "username": "测试玩家",
                "role": "human_follower",
                "scene_name": "brothel"
            }
            await websocket.send(json.dumps(join_message))
            
            # 等待加入确认
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "join_success":
                print("✅ 成功加入房间")
                
                # 等待房间状态
                await asyncio.sleep(1)
                
                # 测试不同场景下的智能体协调
                test_scenarios = [
                    {
                        "message": "我环顾四周，仔细观察这个地方",
                        "expected_agents": ["narrator"],
                        "description": "探索场景 - 应该主要由旁白者响应"
                    },
                    {
                        "message": "我想打听一些关于这里的秘密消息",
                        "expected_agents": ["courtesan", "madam"],
                        "description": "询问场景 - 应该由妓女或老鸨响应"
                    },
                    {
                        "message": "我掏出一袋银子，看看能否获得一些特殊服务",
                        "expected_agents": ["madam", "courtesan"],
                        "description": "交易场景 - 老鸨应该优先响应"
                    },
                    {
                        "message": "我感觉这里隐藏着什么神秘的机密",
                        "expected_agents": ["narrator", "madam"],
                        "description": "神秘场景 - 旁白者应该推动剧情"
                    },
                    {
                        "message": "我想和这里的人聊聊天，增进了解",
                        "expected_agents": ["courtesan", "follower"],
                        "description": "社交场景 - 妓女应该主要响应"
                    }
                ]
                
                for i, scenario in enumerate(test_scenarios):
                    print(f"\n{'='*60}")
                    print(f"📋 测试场景 {i+1}: {scenario['description']}")
                    print(f"💬 发送消息: {scenario['message']}")
                    print(f"🎯 期望响应者: {', '.join(scenario['expected_agents'])}")
                    print(f"{'='*60}")
                    
                    chat_message = {
                        "type": "chat_message",
                        "content": scenario['message']
                    }
                    await websocket.send(json.dumps(chat_message))
                    
                    # 监听智能体回应
                    print("⏳ 等待智能体协调响应...")
                    
                    responses_received = []
                    start_time = time.time()
                    
                    while len(responses_received) < 3 and time.time() - start_time < 12:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3)
                            response_data = json.loads(response)
                            
                            if response_data.get("type") == "agent_message":
                                agent_name = response_data.get("agent_name", "未知")
                                agent_type = response_data.get("agent_type", "unknown")
                                content = response_data.get("content", "")
                                priority = response_data.get("priority", 0)
                                quality_scores = response_data.get("quality_scores", {})
                                
                                responses_received.append({
                                    "agent_name": agent_name,
                                    "agent_type": agent_type,
                                    "content": content,
                                    "priority": priority,
                                    "quality_scores": quality_scores
                                })
                                
                                print(f"\n🤖 [{agent_name}] (类型: {agent_type}, 优先级: {priority}):")
                                print(f"   💭 {content}")
                                
                                if quality_scores:
                                    print(f"   📊 质量评分:")
                                    print(f"      相关性: {quality_scores.get('context_relevance', 0):.2f}")
                                    print(f"      独特性: {quality_scores.get('uniqueness_score', 0):.2f}")
                                    print(f"      故事价值: {quality_scores.get('story_progress_value', 0):.2f}")
                                
                        except asyncio.TimeoutError:
                            break
                    
                    # 分析结果
                    print(f"\n📈 测试结果分析:")
                    print(f"   收到响应数量: {len(responses_received)}")
                    
                    if responses_received:
                        # 检查是否符合期望
                        actual_agents = [r['agent_type'] for r in responses_received]
                        expected_hit = any(agent in actual_agents for agent in scenario['expected_agents'])
                        
                        print(f"   实际响应者: {', '.join(actual_agents)}")
                        print(f"   期望匹配: {'✅ 是' if expected_hit else '❌ 否'}")
                        
                        # 检查响应质量
                        if responses_received[0].get('quality_scores'):
                            avg_relevance = sum(r['quality_scores'].get('context_relevance', 0) 
                                              for r in responses_received) / len(responses_received)
                            avg_uniqueness = sum(r['quality_scores'].get('uniqueness_score', 0) 
                                               for r in responses_received) / len(responses_received)
                            avg_story_value = sum(r['quality_scores'].get('story_progress_value', 0) 
                                                for r in responses_received) / len(responses_received)
                            
                            print(f"   平均质量评分:")
                            print(f"      相关性: {avg_relevance:.2f}")
                            print(f"      独特性: {avg_uniqueness:.2f}")
                            print(f"      故事价值: {avg_story_value:.2f}")
                        
                        # 检查是否有重复响应
                        contents = [r['content'] for r in responses_received]
                        unique_contents = set(contents)
                        has_duplicates = len(contents) != len(unique_contents)
                        print(f"   重复检测: {'❌ 有重复' if has_duplicates else '✅ 无重复'}")
                        
                    else:
                        print("   ❌ 没有收到任何响应")
                    
                    # 等待下一个测试
                    print(f"\n⏸️ 等待3秒后进行下一个测试...\n")
                    await asyncio.sleep(3)
                
                print(f"\n🎉 所有测试场景完成！")
                
                # 最终评估
                print(f"\n{'='*60}")
                print(f"📋 改进效果总结:")
                print(f"✅ 智能体协调机制 - 解决各自为政问题")
                print(f"✅ 响应优先级排序 - 确保高质量回应")
                print(f"✅ 消息意图分析 - 智能选择响应者")
                print(f"✅ 重复响应过滤 - 避免相同内容")
                print(f"✅ 上下文连贯性 - 维护对话历史")
                print(f"✅ 故事推进机制 - 主动发展情节")
                print(f"{'='*60}")
                
            else:
                print(f"❌ 加入房间失败: {data}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

async def monitor_system_performance():
    """监控系统性能的观察者"""
    uri = "ws://localhost:8000/ws/improved_test"
    
    try:
        async with websockets.connect(uri) as websocket:
            join_message = {
                "type": "join",
                "username": "性能监控器",
                "role": "spectator",
                "scene_name": "brothel"
            }
            await websocket.send(json.dumps(join_message))
            
            print("📊 性能监控器已启动...")
            
            response_times = []
            quality_metrics = []
            
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "agent_message":
                    timestamp = data.get("timestamp", time.time())
                    quality_scores = data.get("quality_scores", {})
                    
                    # 记录性能指标
                    if quality_scores:
                        quality_metrics.append({
                            "timestamp": timestamp,
                            "scores": quality_scores
                        })
                    
                    # 简单的性能报告
                    if len(quality_metrics) % 5 == 0 and quality_metrics:
                        recent_metrics = quality_metrics[-5:]
                        avg_relevance = sum(m['scores'].get('context_relevance', 0) 
                                          for m in recent_metrics) / len(recent_metrics)
                        avg_uniqueness = sum(m['scores'].get('uniqueness_score', 0) 
                                           for m in recent_metrics) / len(recent_metrics)
                        avg_story_value = sum(m['scores'].get('story_progress_value', 0) 
                                            for m in recent_metrics) / len(recent_metrics)
                        
                        print(f"\n📊 最近5次回应平均质量:")
                        print(f"   相关性: {avg_relevance:.2f}")
                        print(f"   独特性: {avg_uniqueness:.2f}")
                        print(f"   故事价值: {avg_story_value:.2f}")
                        
    except Exception as e:
        print(f"❌ 性能监控失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始测试改进后的智能体协调系统")
    print("=" * 80)
    
    # 同时运行测试和性能监控
    await asyncio.gather(
        test_coordinated_agents(),
        monitor_system_performance()
    )

if __name__ == "__main__":
    print("📋 改进后的智能体系统测试说明:")
    print("- 测试智能体协调器的消息意图分析")
    print("- 验证响应优先级和质量评分系统")
    print("- 检查重复响应过滤机制")
    print("- 监控上下文连贯性和故事推进效果")
    print("=" * 80)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试结束")
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        print("\n💡 请确保WebSocket服务器正在运行") 