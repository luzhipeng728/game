#!/usr/bin/env python3
"""
苏丹的游戏 - 启动脚本
快速启动游戏的不同组件
"""

import os
import sys
import subprocess
from typing import Optional

def print_header():
    """打印游戏标题"""
    print("🏰" + "="*50)
    print("   苏丹的游戏 - 多智能体卡牌系统")
    print("="*50 + "🏰")
    print()

def print_menu():
    """打印菜单选项"""
    print("请选择要启动的组件：")
    print()
    print("1. 🎮 Streamlit 游戏界面")
    print("2. 🎭 妓院场景演示")
    print("3. 🔧 系统测试")
    print("4. ❌ 退出")
    print()

def run_streamlit():
    """运行Streamlit应用"""
    print("🚀 正在启动 Streamlit 游戏界面...")
    print("📝 访问地址：http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止服务")
    print()
    
    try:
        subprocess.run([
            "streamlit", "run", "sultans_game_app.py",
            "--server.address=0.0.0.0",
            "--server.port=8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ Streamlit 应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
    except FileNotFoundError:
        print("❌ 找不到 streamlit 命令，请确保已安装 streamlit")

def run_demo():
    """运行妓院场景演示"""
    print("🎭 正在启动妓院场景演示...")
    print()
    
    try:
        subprocess.run(["python3", "demo_brothel_scene.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 演示失败: {e}")
    except FileNotFoundError:
        print("❌ 找不到 python3 命令")

def run_tests():
    """运行系统测试"""
    print("🔧 正在运行系统测试...")
    print()
    
    try:
        subprocess.run(["python3", "test_system.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 测试失败: {e}")
    except FileNotFoundError:
        print("❌ 找不到 python3 命令")

def main():
    """主函数"""
    print_header()
    
    # 检查配置
    from sultans_game.config import get_openai_config
    config = get_openai_config()
    print(f"✅ API配置已加载")
    print(f"   模型: {config['model']}")
    print(f"   API Base: {config['base_url']}")
    print()
    
    while True:
        print_menu()
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == "1":
            run_streamlit()
        elif choice == "2":
            run_demo()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选项，请重新选择")
        
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)