import streamlit as st
import os
from datetime import datetime
import json
from typing import Optional

# 设置页面配置
st.set_page_config(
    page_title="苏丹的游戏 - 多智能体卡牌系统",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入游戏模块
try:
    from sultans_game.models import GameState, SceneState, Card, CardType, CardRank
    from sultans_game.agents import GameMaster
    from sultans_game.cards import CardGenerator
    from sultans_game.tools import GameToolsManager
    from sultans_game.config import get_openai_config  # 导入配置
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.stop()

# 初始化API配置
config = get_openai_config()

# 初始化会话状态
def initialize_session_state():
    """初始化会话状态"""
    if 'game_state' not in st.session_state:
        scene = SceneState(
            location="妓院",
            characters_present=[],
            atmosphere="暧昧而神秘",
            time_of_day="夜晚"
        )
        st.session_state.game_state = GameState(current_scene=scene)
    
    if 'game_master' not in st.session_state:
        st.session_state.game_master = GameMaster(st.session_state.game_state)
    
    if 'card_generator' not in st.session_state:
        st.session_state.card_generator = CardGenerator()
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'current_card' not in st.session_state:
        st.session_state.current_card = None

def display_character_info(character_name: str):
    """显示角色信息"""
    if character_name in st.session_state.game_state.characters:
        char = st.session_state.game_state.characters[character_name]
        
        with st.expander(f"🎭 {char.name} ({char.role})"):
            st.write(f"**性格特点:** {char.personality}")
            
            # 属性显示
            st.write("**属性:**")
            cols = st.columns(3)
            attrs = list(char.attributes.items())
            for i, (attr, value) in enumerate(attrs):
                with cols[i % 3]:
                    st.metric(attr, value)
            
            # 关系显示
            if char.relationships:
                st.write("**关系:**")
                for target, relationship in char.relationships.items():
                    color = "green" if relationship >= 70 else "orange" if relationship >= 30 else "red"
                    st.markdown(f"- {target}: :{color}[{relationship}]")

def display_scene_info():
    """显示场景信息"""
    scene = st.session_state.game_state.current_scene
    
    with st.expander("🏛️ 场景信息"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**地点:** {scene.location}")
            st.write(f"**时间:** {scene.time_of_day}")
            st.write(f"**氛围:** {scene.atmosphere}")
            st.write(f"**在场人物:** {', '.join(scene.characters_present)}")
        
        with col2:
            st.write("**场景数值:**")
            for key, value in scene.scene_values.items():
                if key == "金钱消费":
                    st.metric(key, f"{value} 金币")
                else:
                    st.metric(key, f"{value}/100")

def display_card_info(card: Card):
    """显示卡牌信息"""
    with st.expander(f"🎴 {card.title} ({card.card_type.value} - {card.rank.value})"):
        st.write(f"**描述:** {card.description}")
        
        if card.target_character:
            st.write(f"**目标角色:** {card.target_character}")
        
        if card.required_actions:
            st.write("**所需行动:**")
            for action in card.required_actions:
                st.write(f"- {action}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if card.rewards:
                st.write("**奖励:**")
                for reward, amount in card.rewards.items():
                    st.write(f"- {reward}: +{amount}")
        
        with col2:
            if card.penalty:
                st.write("**惩罚:**")
                for penalty, amount in card.penalty.items():
                    st.write(f"- {penalty}: {amount}")
        
        st.write(f"**时限:** {card.time_limit_days} 天")

def main():
    # 初始化会话状态
    initialize_session_state()
    
    # 主标题
    st.title("🏰 苏丹的游戏 - 多智能体卡牌系统")
    st.markdown("*一个基于CrewAI的多智能体对话系统，模拟《苏丹的游戏》中的妓院场景*")
    st.info(f"🤖 使用模型: {config['model']} | API Base: {config['base_url']}")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 游戏设置")
        
        st.success("✅ API已配置完成")
        st.info(f"当前模型: {config['model']}")
        
        st.divider()
        
        # 卡牌生成
        st.header("🎴 卡牌管理")
        
        # 卡牌类型选择
        card_type_option = st.selectbox(
            "选择卡牌类型",
            options=["随机"] + [ct.value for ct in CardType],
            index=0
        )
        
        # 卡牌品级选择
        card_rank_option = st.selectbox(
            "选择卡牌品级",
            options=["随机"] + [cr.value for cr in CardRank],
            index=0
        )
        
        # 生成卡牌按钮
        if st.button("🎲 生成新卡牌"):
            try:
                card_type = None if card_type_option == "随机" else CardType(card_type_option)
                card_rank = None if card_rank_option == "随机" else CardRank(card_rank_option)
                
                new_card = st.session_state.card_generator.generate_random_card(card_type, card_rank)
                st.session_state.current_card = new_card
                st.success("新卡牌生成成功！")
                st.rerun()
            except Exception as e:
                st.error(f"生成卡牌失败: {e}")
        
        # 使用教学卡牌
        if st.button("📚 使用教学卡牌"):
            tutorial_card = st.session_state.card_generator.create_tutorial_card()
            st.session_state.current_card = tutorial_card
            st.success("教学卡牌已加载！")
            st.rerun()
        
        st.divider()
        
        # 清除历史记录
        if st.button("🗑️ 清除对话历史"):
            st.session_state.conversation_history = []
            st.success("对话历史已清除")
            st.rerun()
        
        # 重置游戏状态
        if st.button("🔄 重置游戏"):
            for key in ['game_state', 'game_master', 'conversation_history', 'current_card']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("游戏状态已重置")
            st.rerun()
    
    # 主要内容区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 对话场景")
        
        # 显示当前卡牌
        if st.session_state.current_card:
            display_card_info(st.session_state.current_card)
        else:
            st.info("请先生成一张卡牌来开始游戏")
        
        # 开始对话按钮
        if st.button("🎭 开始场景对话", disabled=st.session_state.current_card is None):
            with st.spinner("智能体们正在交流中..."):
                try:
                    # 执行对话
                    result = st.session_state.game_master.start_scene(st.session_state.current_card)
                    
                    if result.get("success", False):
                        # 添加到对话历史
                        conversation_entry = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "card": st.session_state.current_card.title,
                            "result": result["conversation_result"],
                            "scene_state": result["scene_state"],
                            "characters": result["characters"]
                        }
                        st.session_state.conversation_history.append(conversation_entry)
                        
                        st.success("对话完成！")
                        st.rerun()
                    else:
                        st.error(f"对话执行失败: {result.get('error', '未知错误')}")
                        
                except Exception as e:
                    st.error(f"执行对话时发生错误: {e}")
        
        # 显示对话历史
        if st.session_state.conversation_history:
            st.header("📖 对话历史")
            
            for i, entry in enumerate(reversed(st.session_state.conversation_history)):
                with st.expander(f"对话 {len(st.session_state.conversation_history) - i}: {entry['card']} ({entry['timestamp']})"):
                    st.markdown(entry["result"])
                    
                    # 显示角色状态变化
                    if "characters" in entry:
                        st.subheader("角色状态")
                        for char_name, char_data in entry["characters"].items():
                            if char_data.get("relationships"):
                                st.write(f"**{char_name} 的关系变化:**")
                                for target, relationship in char_data["relationships"].items():
                                    st.write(f"- 对 {target}: {relationship}")
    
    with col2:
        st.header("🎮 游戏状态")
        
        # 显示场景信息
        display_scene_info()
        
        # 显示角色信息
        st.subheader("👥 角色信息")
        for char_name in st.session_state.game_state.characters:
            display_character_info(char_name)
        
        # 显示资源信息
        st.subheader("💰 资源状态")
        resources = st.session_state.game_state.resources
        for resource, amount in resources.items():
            st.metric(resource, amount)
        
        # 游戏状态导出
        st.subheader("💾 游戏数据")
        if st.button("📤 导出游戏状态"):
            game_data = st.session_state.game_state.save_to_json()
            st.download_button(
                label="下载游戏状态",
                data=game_data,
                file_name=f"sultans_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    🏰 苏丹的游戏 - 多智能体卡牌系统 | 基于 CrewAI 构建
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()