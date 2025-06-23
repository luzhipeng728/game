"""启动WebSocket聊天服务器"""

import uvicorn

if __name__ == "__main__":
    print("🚀 启动苏丹游戏WebSocket聊天服务器...")
    print("📡 WebSocket地址: ws://localhost:8000/ws/{room_id}")
    print("🌐 API文档: http://localhost:8000/docs")
    print("📋 房间列表: http://localhost:8000/rooms")
    print("=" * 50)
    
    uvicorn.run(
        "sultans_game.websocket_server:app",  # 使用字符串导入
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # 关闭自动重载以避免警告
    ) 