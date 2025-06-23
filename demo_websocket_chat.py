"""WebSocket聊天系统演示"""

import asyncio
import json
import websockets
import time
from sultans_game.models import Card, CardType, CardRank

async def demo_client(username, role, room_id="demo_room"):
    """演示客户端"""
    uri = f"ws://localhost:8000/ws/{room_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"🔌 {username} 连接到房间 {room_id}")
            
            # 发送加入消息
            join_message = {
                "type": "join",
                "username": username,
                "role": role,
                "scene_name": "brothel"
            }
            await websocket.send(json.dumps(join_message))
            
            # 监听消息
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 [{username}] 收到: {data}")
                
                # 如果成功加入，发送几条测试消息
                if data.get("type") == "join_success":
                    await asyncio.sleep(2)
                    for i in range(3):
                        chat_message = {
                            "type": "chat_message",
                            "content": f"这是来自 {username} 的第 {i+1} 条消息！"
                        }
                        await websocket.send(json.dumps(chat_message))
                        await asyncio.sleep(3)
                    
                    # 测试暂停功能
                    print(f"🚀 {username} 测试暂停功能...")
                    pause_message = {
                        "type": "pause_request",
                        "duration": 15
                    }
                    await websocket.send(json.dumps(pause_message))
                    
                    await asyncio.sleep(10)
                    
                    # 恢复对话
                    resume_message = {
                        "type": "resume_request"
                    }
                    await websocket.send(json.dumps(resume_message))
                
    except Exception as e:
        print(f"❌ {username} 连接失败: {e}")

async def test_api_endpoints():
    """测试API端点"""
    import aiohttp
    
    print("🧪 测试API端点...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试根端点
            async with session.get("http://localhost:8000/") as response:
                data = await response.json()
                print(f"✅ 根端点: {data}")
            
            # 测试房间列表
            async with session.get("http://localhost:8000/rooms") as response:
                data = await response.json()
                print(f"✅ 房间列表: {data}")
            
            # 测试设置卡牌
            card_data = {
                "title": "寻找秘密",
                "description": "在妓院中寻找苏丹的秘密文件",
                "card_type": "征服",
                "rank": "白银",
                "target_character": "妓女",
                "required_actions": ["对话", "调查"]
            }
            
            async with session.post("http://localhost:8000/rooms/demo_room/card", json=card_data) as response:
                data = await response.json()
                print(f"✅ 设置卡牌: {data}")
                
    except Exception as e:
        print(f"❌ API测试失败: {e}")

async def run_demo():
    """运行演示"""
    print("🚀 启动WebSocket聊天系统演示")
    print("=" * 50)
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    # 测试API端点
    await test_api_endpoints()
    
    print("\n🎭 创建多个用户进行聊天测试...")
    
    # 创建多个客户端同时连接
    clients = [
        demo_client("张三", "human_follower"),
        demo_client("李四", "human_courtesan"),  
        demo_client("王五", "spectator"),
    ]
    
    # 并发运行客户端
    await asyncio.gather(*clients, return_exceptions=True)

if __name__ == "__main__":
    print("📋 WebSocket聊天系统演示说明:")
    print("1. 请先启动服务器: python start_websocket_server.py")
    print("2. 然后运行此演示: python demo_websocket_chat.py")
    print("3. 或直接在浏览器中打开 chat_client.html")
    print("=" * 50)
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n👋 演示结束")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("\n💡 提示: 请确保先启动WebSocket服务器") 