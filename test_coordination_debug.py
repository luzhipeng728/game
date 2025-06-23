#!/usr/bin/env python3
"""
协调器系统调试测试
测试智能体协调器是否正常工作
"""

import asyncio
import websockets
import json
import time
from typing import Dict, Any

async def test_coordination_system():
    """测试协调系统"""
    print("🔍 开始协调器系统调试测试...")
    
    # 连接到WebSocket服务器
    uri = "ws://localhost:8000/ws/debug_test"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 发送加入消息
            join_message = {
                "type": "join",
                "username": "调试测试者",
                "role": "human_follower",
                "scene_name": "brothel"
            }
            
            await websocket.send(json.dumps(join_message))
            print(f"📤 发送加入消息: {join_message}")
            
            # 等待加入成功
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 收到响应: {data['type']}")
            
            if data.get("type") == "join_success":
                print("🎉 成功加入房间")
                
                # 测试不同类型的消息
                test_messages = [
                    {
                        "message": "我环顾四周，仔细观察这个妓院的布局",
                        "expected": "探索类消息，期望旁白者响应"
                    },
                    {
                        "message": "我想打听一些关于这里的秘密消息",
                        "expected": "询问类消息，期望妓女/老鸨响应"
                    },
                    {
                        "message": "我掏出一袋银子，想获得一些特殊服务",
                        "expected": "交易类消息，期望老鸨响应"
                    }
                ]
                
                for i, test_case in enumerate(test_messages, 1):
                    print(f"\n📝 测试用例 {i}: {test_case['expected']}")
                    print(f"💬 发送消息: {test_case['message']}")
                    
                    # 发送测试消息
                    chat_message = {
                        "type": "chat_message",
                        "content": test_case['message']
                    }
                    
                    await websocket.send(json.dumps(chat_message))
                    
                    # 等待智能体响应
                    print("⏳ 等待智能体响应...")
                    responses_received = 0
                    timeout_count = 0
                    max_timeout = 15  # 15秒超时
                    
                    while responses_received < 2 and timeout_count < max_timeout:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            data = json.loads(response)
                            
                            if data.get("type") == "agent_message":
                                responses_received += 1
                                agent_type = data.get("agent_type", "unknown")
                                agent_name = data.get("agent_name", "未知")
                                content = data.get("content", "")
                                priority = data.get("priority", 0)
                                quality_scores = data.get("quality_scores", {})
                                
                                print(f"🤖 智能体响应 {responses_received}:")
                                print(f"   类型: {agent_type}")
                                print(f"   名称: {agent_name}")
                                print(f"   优先级: {priority}")
                                print(f"   内容: {content[:100]}...")
                                
                                if quality_scores:
                                    print(f"   质量评分:")
                                    print(f"     相关性: {quality_scores.get('context_relevance', 0):.2f}")
                                    print(f"     独特性: {quality_scores.get('uniqueness_score', 0):.2f}")
                                    print(f"     故事价值: {quality_scores.get('story_progress_value', 0):.2f}")
                            
                            elif data.get("type") == "system_message":
                                print(f"📢 系统消息: {data.get('content', '')}")
                            
                        except asyncio.TimeoutError:
                            timeout_count += 1
                            if timeout_count % 3 == 0:
                                print(f"⏰ 等待中... ({timeout_count}/{max_timeout})")
                    
                    if responses_received == 0:
                        print("❌ 没有收到任何智能体响应！")
                        print("🔧 可能的问题:")
                        print("   - 协调器未正确初始化")
                        print("   - 智能体响应生成失败")
                        print("   - 异步调用出现问题")
                    else:
                        print(f"✅ 收到 {responses_received} 个智能体响应")
                    
                    # 等待下一个测试
                    if i < len(test_messages):
                        print(f"\n⏸️ 等待5秒后进行下一个测试...")
                        await asyncio.sleep(5)
                
                print(f"\n🎯 调试测试完成！")
                
            else:
                print(f"❌ 加入房间失败: {data}")
                
    except websockets.exceptions.ConnectionClosed:
        print("❌ WebSocket连接已关闭")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())

async def check_server_status():
    """检查服务器状态"""
    print("🔍 检查服务器状态...")
    
    try:
        # 简单的连接测试
        uri = "ws://localhost:8000/ws/status_check"
        async with websockets.connect(uri) as websocket:
            print("✅ 服务器在线")
            return True
    except Exception as e:
        print(f"❌ 服务器离线或出错: {e}")
        return False

def print_debug_info():
    """打印调试信息"""
    print("="*60)
    print("🔧 协调器系统调试测试")
    print("="*60)
    print("🎯 测试目标:")
    print("   1. 验证协调器是否正确初始化")
    print("   2. 测试消息意图分析功能")
    print("   3. 检查智能体选择逻辑")
    print("   4. 验证质量评分系统")
    print("   5. 确认响应时序控制")
    print("="*60)

async def main():
    """主函数"""
    print_debug_info()
    
    # 检查服务器状态
    if await check_server_status():
        await test_coordination_system()
    else:
        print("\n💡 请先启动WebSocket服务器:")
        print("   python start_websocket_server.py")

if __name__ == "__main__":
    asyncio.run(main()) 