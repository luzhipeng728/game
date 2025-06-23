"""测试场景数值更新修复"""

import asyncio
import json
import websockets
import time


async def test_scene_values_update():
    """测试场景数值更新功能"""
    uri = "ws://localhost:8000/ws/test_values"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 连接到WebSocket服务器")
            
            # 发送加入消息
            join_message = {
                "type": "join",
                "username": "数值测试员",
                "role": "human_follower", 
                "scene_name": "brothel"
            }
            await websocket.send(json.dumps(join_message))
            print("📤 发送加入请求")
            
            # 等待加入成功
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 收到响应: {data.get('type')}")
            
            if data.get("type") == "join_success":
                print("✅ 成功加入房间")
                
                # 等待房间状态
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data.get("type") == "room_state":
                        print("📊 初始场景数值:", data.get("scene_values", {}))
                        break
                
                # 发送一条会触发智能体回应的消息
                print("\n💬 发送测试消息，期待智能体使用工具...")
                chat_message = {
                    "type": "chat_message",
                    "content": "我想了解一下这个青楼的氛围，请告诉我一些有趣的事情。"
                }
                await websocket.send(json.dumps(chat_message))
                
                # 监听后续消息
                message_count = 0
                start_time = time.time()
                
                while message_count < 5 and (time.time() - start_time) < 60:  # 等待最多1分钟
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        data = json.loads(response)
                        message_type = data.get("type")
                        
                        print(f"\n📨 收到消息: {message_type}")
                        
                        if message_type == "agent_message":
                            agent_name = data.get("agent_name", "未知智能体")
                            content = data.get("content", "")
                            print(f"🤖 {agent_name}: {content[:100]}...")
                            message_count += 1
                        
                        elif message_type == "scene_update":
                            print("🎮 场景数值更新检测到！")
                            scene_values = data.get("scene_values", {})
                            changes = data.get("changes", {})
                            
                            print(f"   新场景数值: {scene_values}")
                            print(f"   变化详情: {changes}")
                            
                            if changes:
                                print("✅ 场景数值更新功能正常工作！")
                                return True
                        
                        elif message_type == "system_message":
                            content = data.get("content", "")
                            print(f"📢 系统: {content}")
                    
                    except asyncio.TimeoutError:
                        print("⏰ 等待超时，继续监听...")
                        continue
                
                print("❌ 测试期间未检测到场景数值更新")
                return False
            
            else:
                print(f"❌ 加入房间失败: {data}")
                return False
                
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False


async def main():
    """主函数"""
    print("🧪 开始测试场景数值更新功能...")
    print("=" * 50)
    
    success = await test_scene_values_update()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 测试通过：场景数值更新功能正常工作！")
    else:
        print("❌ 测试失败：场景数值更新功能存在问题")


if __name__ == "__main__":
    asyncio.run(main()) 