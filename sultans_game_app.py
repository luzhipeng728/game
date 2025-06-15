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
        
        # 实时场景数值显示
        st.header("📊 实时场景数值")
        
        # 显示最后更新时间
        if 'last_update_time' in st.session_state:
            st.caption(f"🕒 最后更新: {st.session_state.last_update_time}")
        
        # 创建场景数值显示容器 - 使用 st.empty() 来支持实时更新
        if 'scene_values_placeholder' not in st.session_state:
            st.session_state.scene_values_placeholder = st.empty()
        
        # 定义更新场景数值显示的函数
        def update_scene_values_display():
            scene = st.session_state.game_state.current_scene
            
            # 获取当前数值
            tension_value = scene.scene_values.get('紧张度', 0)
            romance_value = scene.scene_values.get('暧昧度', 0)
            danger_value = scene.scene_values.get('危险度', 0)
            money_value = scene.scene_values.get('金钱消费', 0)
            
            # 计算数值变化（如果有历史数据）
            tension_delta = None
            romance_delta = None
            danger_delta = None
            money_delta = None
            
            if 'previous_scene_values' in st.session_state:
                prev_values = st.session_state.previous_scene_values
                tension_delta = tension_value - prev_values.get('紧张度', 0)
                romance_delta = romance_value - prev_values.get('暧昧度', 0)
                danger_delta = danger_value - prev_values.get('危险度', 0)
                money_delta = money_value - prev_values.get('金钱消费', 0)
            
            # 更新历史数据
            st.session_state.previous_scene_values = scene.scene_values.copy()
            
            # 使用 with 语句来更新 placeholder 的内容
            with st.session_state.scene_values_placeholder.container():
                # 数值显示
                col1, col2 = st.columns(2)
                
                with col1:
                    # 紧张度
                    st.metric(
                        label="⚡ 紧张度",
                        value=f"{tension_value}/100",
                        delta=tension_delta if tension_delta and tension_delta != 0 else None,
                        help="场景的紧张程度，影响事件发生的概率"
                    )
                    
                    # 危险度
                    st.metric(
                        label="⚠️ 危险度",
                        value=f"{danger_value}/100",
                        delta=danger_delta if danger_delta and danger_delta != 0 else None,
                        help="当前场景的危险程度，影响安全性"
                    )
                
                with col2:
                    # 暧昧度
                    st.metric(
                        label="💕 暧昧度",
                        value=f"{romance_value}/100",
                        delta=romance_delta if romance_delta and romance_delta != 0 else None,
                        help="角色间的暧昧程度，影响关系发展"
                    )
                    
                    # 金钱消费
                    st.metric(
                        label="💰 金钱消费",
                        value=f"{money_value} 金币",
                        delta=money_delta if money_delta and money_delta != 0 else None,
                        help="本次场景中的金钱花费"
                    )
                
                # 数值条形图显示
                st.write("**数值可视化:**")
                
                # 使用进度条显示各项数值，并添加颜色
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("⚡ 紧张度")
                    st.progress(tension_value / 100)
                    
                    st.write("⚠️ 危险度")  
                    st.progress(danger_value / 100)
                
                with col_b:
                    st.write("💕 暧昧度")
                    st.progress(romance_value / 100)
                    
                    # 金钱消费用不同的显示方式
                    st.write("💰 金钱消费")
                    if money_value > 0:
                        st.write(f"💸 已花费 {money_value} 金币")
                    else:
                        st.write("💰 尚未消费")
                
                # 数值状态提示
                status_messages = []
                if tension_value >= 80:
                    status_messages.append("⚡ 场面非常紧张！")
                elif tension_value >= 60:
                    status_messages.append("⚡ 气氛有些紧张")
                    
                if romance_value >= 80:
                    status_messages.append("💕 暧昧气氛浓厚")
                elif romance_value >= 60:
                    status_messages.append("💕 关系逐渐亲密")
                    
                if danger_value >= 80:
                    status_messages.append("⚠️ 危险！需要小心")
                elif danger_value >= 60:
                    status_messages.append("⚠️ 情况有些危险")
                    
                if money_value >= 50:
                    status_messages.append("💰 花费不少金钱")
                
                if status_messages:
                    st.info(" | ".join(status_messages))
        
        # 初始显示场景数值
        update_scene_values_display()
        
        # 将更新函数保存到 session_state 中，供回调函数使用
        st.session_state.update_scene_values_display = update_scene_values_display
        
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
        
        # 对话设置
        st.subheader("🎛️ 对话设置")
        col_a, col_b = st.columns(2)
        with col_a:
            max_rounds = st.slider("最大对话轮数", 5, 15, 10)
        with col_b:
            min_rounds = st.slider("最小对话轮数", 3, 8, 5)
        
        # 开始自动对话按钮
        if st.button("🎭 开始自动对话", disabled=st.session_state.current_card is None):
            # 初始化实时对话状态
            if 'live_dialogue' not in st.session_state:
                st.session_state.live_dialogue = []
            if 'dialogue_in_progress' not in st.session_state:
                st.session_state.dialogue_in_progress = False
            
            # 设置对话进行中状态
            st.session_state.dialogue_in_progress = True
            st.session_state.live_dialogue = []
            
            # 创建实时对话显示区域
            st.markdown("### 🎭 实时对话")
            
            # 进度和状态显示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 实时场景数值显示（在对话区域）
            st.markdown("#### 📊 实时场景数值")
            realtime_values_area = st.empty()
            
            # 实时对话显示区域
            dialogue_area = st.empty()
            
            def format_dialogue_for_display(dialogue_list):
                """格式化对话内容用于显示"""
                formatted_content = []
                for dialogue in dialogue_list[-15:]:  # 显示最近15条对话
                    if "【旁白】" in dialogue:
                        formatted_content.append(f"🎭 {dialogue}")
                    elif "【随从】" in dialogue:
                        formatted_content.append(f"🤵 {dialogue}")
                    elif "【妓女】" in dialogue:
                        formatted_content.append(f"💃 {dialogue}")
                    elif "【老鸨】" in dialogue:
                        formatted_content.append(f"👩‍💼 {dialogue}")
                    elif "【系统】" in dialogue:
                        formatted_content.append(f"⚙️ {dialogue}")
                    else:
                        formatted_content.append(dialogue)
                return "\n\n".join(formatted_content)
            
            # 使用 st.empty() 和定期更新来模拟实时显示
            class StreamlitCallback:
                def __init__(self, progress_bar, status_text, dialogue_area, realtime_values_area):
                    self.progress_bar = progress_bar
                    self.status_text = status_text
                    self.dialogue_area = dialogue_area
                    self.realtime_values_area = realtime_values_area
                    self.dialogue_log = []
                
                def update_realtime_values(self):
                    """更新实时场景数值显示"""
                    try:
                        scene = st.session_state.game_state.current_scene
                        
                        # 获取当前数值
                        tension_value = scene.scene_values.get('紧张度', 0)
                        romance_value = scene.scene_values.get('暧昧度', 0)
                        danger_value = scene.scene_values.get('危险度', 0)
                        money_value = scene.scene_values.get('金钱消费', 0)
                        
                        # 创建实时数值显示内容
                        values_content = f"""
                        **当前场景数值：**
                        
                        ⚡ 紧张度：{tension_value}/100 | 💕 暧昧度：{romance_value}/100 | ⚠️ 危险度：{danger_value}/100 | 💰 金钱消费：{money_value} 金币
                        
                        ---
                        """
                        
                        # 更新显示
                        self.realtime_values_area.markdown(values_content)
                        
                    except Exception as e:
                        print(f"更新实时数值显示时出错: {e}")
                        pass
                
                def __call__(self, event_type, current_round, total_rounds, agent_name, content, full_log):
                    # 更新进度
                    if total_rounds > 0:
                        progress = current_round / total_rounds
                        self.progress_bar.progress(min(progress, 1.0))
                    
                    # 更新状态文本
                    if event_type == "init":
                        self.status_text.text("🎬 场景初始化中...")
                        self.dialogue_log.append(content)
                    elif event_type == "speaking":
                        self.status_text.text(f"🎤 第 {current_round}/{total_rounds} 轮 - {agent_name} 正在思考...")
                    elif event_type == "response":
                        self.status_text.text(f"💬 第 {current_round}/{total_rounds} 轮 - {agent_name} 发言完毕")
                        self.dialogue_log.append(f"【{agent_name}】{content}")
                        
                        # 更新实时场景数值显示
                        self.update_realtime_values()
                        
                        # 触发页面重新渲染以更新侧边栏数值
                        try:
                            # 更新时间戳
                            st.session_state.last_update_time = datetime.now().strftime("%H:%M:%S")
                            
                            # 调用场景数值更新函数（如果存在）
                            if hasattr(st.session_state, 'update_scene_values_display'):
                                st.session_state.update_scene_values_display()
                                
                        except Exception as e:
                            # 忽略可能的错误，但记录到日志
                            print(f"更新场景数值时出错: {e}")
                            pass
                            
                    elif event_type == "error":
                        self.status_text.text(f"❌ {agent_name} 发生错误")
                        self.dialogue_log.append(f"【系统】{content}")
                    elif event_type == "ending":
                        self.status_text.text("🎬 对话即将结束...")
                        self.dialogue_log.append(content)
                    elif event_type == "complete":
                        self.status_text.text("✅ 对话完成！")
                        self.progress_bar.progress(1.0)
                        
                        # 最终更新实时场景数值显示
                        self.update_realtime_values()
                        
                        # 最终更新侧边栏数值
                        try:
                            st.session_state.last_update_time = datetime.now().strftime("%H:%M:%S")
                            
                            # 最终调用场景数值更新函数
                            if hasattr(st.session_state, 'update_scene_values_display'):
                                st.session_state.update_scene_values_display()
                        except Exception as e:
                            print(f"最终更新场景数值时出错: {e}")
                            pass
                    
                    # 更新对话显示
                    formatted_dialogue = format_dialogue_for_display(self.dialogue_log)
                    self.dialogue_area.markdown(formatted_dialogue)
            
            # 创建回调实例
            callback = StreamlitCallback(progress_bar, status_text, dialogue_area, realtime_values_area)
            
            try:
                # 显示开始信息
                status_text.text("🚀 正在启动自动对话...")
                
                # 确保角色存在，如果不存在则创建默认角色
                if "随从" not in st.session_state.game_state.characters:
                    follower = st.session_state.game_master._create_default_follower()
                else:
                    follower = st.session_state.game_state.characters["随从"]
                
                if "妓女" not in st.session_state.game_state.characters:
                    courtesan = st.session_state.game_master._create_default_courtesan()
                else:
                    courtesan = st.session_state.game_state.characters["妓女"]
                
                if "老鸨" not in st.session_state.game_state.characters:
                    madam = st.session_state.game_master._create_default_madam()
                else:
                    madam = st.session_state.game_state.characters["老鸨"]
                
                # 设置妓院场景和智能体
                st.session_state.game_master.setup_brothel_scenario(
                    follower,
                    st.session_state.current_card,
                    courtesan,
                    madam
                )
                
                # 执行自动对话（带实时回调）
                result = st.session_state.game_master.run_auto_conversation_with_callback(
                    st.session_state.current_card,
                    callback_func=callback,
                    max_rounds=max_rounds,
                    min_rounds=min_rounds
                )
                
                # 重置对话状态
                st.session_state.dialogue_in_progress = False
                
                if result.get("success", False):
                    # 添加到对话历史
                    conversation_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "card": st.session_state.current_card.title,
                        "result": result["story_content"],
                        "scene_state": result["scene_values"],
                        "characters": {
                            name: {
                                "relationships": char.relationships,
                                "attributes": {
                                    "魅力": char.charm,
                                    "智慧": char.wisdom,
                                    "体魄": char.physique,
                                    "社交": char.social
                                }
                            } for name, char in st.session_state.game_state.characters.items()
                        },
                        "rounds": result.get("conversation_rounds", 0),
                        "summary": result.get("final_summary", "")
                    }
                    st.session_state.conversation_history.append(conversation_entry)
                    
                    # 显示成功信息
                    st.success(f"🎉 自动对话完成！共进行了 {result.get('conversation_rounds', 0)} 轮对话")
                    
                    # 显示最终总结
                    if result.get("final_summary"):
                        st.markdown("### 📋 场景总结")
                        st.markdown(result["final_summary"])
                    
                    # 提示用户刷新查看历史记录
                    st.info("💡 对话已保存到历史记录中，您可以在下方查看完整内容")
                    
                else:
                    st.error(f"对话执行失败: {result.get('error', '未知错误')}")
                    if result.get("partial_conversation"):
                        st.markdown("### 部分对话内容")
                        st.text(result["partial_conversation"])
                    
            except Exception as e:
                st.session_state.dialogue_in_progress = False
                st.error(f"执行对话时发生错误: {e}")
                import traceback
                st.text(traceback.format_exc())
        
        # 添加说明
        st.info("""
        💡 **自动对话说明：**
        - 点击按钮后，四个智能体（旁白、随从、妓女、老鸨）将自动进行多轮对话
        - 每轮对话中，每个角色都会根据当前情况自然地发言
        - 对话会在达到最小轮数后，根据剧情发展自动结束
        - 您无需任何操作，只需等待对话完成即可
        """)
        
        # 显示对话历史
        if st.session_state.conversation_history:
            st.header("📖 对话历史")
            
            for i, entry in enumerate(reversed(st.session_state.conversation_history)):
                # 构建标题，包含轮数信息
                title_parts = [f"对话 {len(st.session_state.conversation_history) - i}"]
                title_parts.append(f"{entry['card']}")
                if "rounds" in entry:
                    title_parts.append(f"({entry['rounds']}轮)")
                title_parts.append(f"({entry['timestamp']})")
                title = ": ".join(title_parts)
                
                with st.expander(title):
                    # 显示对话内容
                    st.markdown("### 📜 对话内容")
                    # 将对话内容按段落分割，更好地显示
                    dialogue_parts = entry["result"].split("\n\n")
                    for part in dialogue_parts:
                        if part.strip():
                            # 检查是否是角色对话
                            if "【" in part and "】" in part:
                                # 提取角色名和对话内容
                                if "【旁白】" in part:
                                    st.markdown(f"🎭 {part}")
                                elif "【随从】" in part:
                                    st.markdown(f"🤵 {part}")
                                elif "【妓女】" in part:
                                    st.markdown(f"💃 {part}")
                                elif "【老鸨】" in part:
                                    st.markdown(f"👩‍💼 {part}")
                                else:
                                    st.markdown(part)
                            else:
                                st.markdown(part)
                    
                    # 显示总结（如果有）
                    if "summary" in entry and entry["summary"]:
                        st.markdown("### 📋 场景总结")
                        st.markdown(entry["summary"])
                    
                    # 显示场景数值变化
                    if "scene_state" in entry:
                        st.markdown("### 📊 场景数值")
                        cols = st.columns(4)
                        scene_values = entry["scene_state"]
                        for idx, (key, value) in enumerate(scene_values.items()):
                            with cols[idx % 4]:
                                if key == "金钱消费":
                                    st.metric(key, f"{value} 金币")
                                else:
                                    st.metric(key, f"{value}/100")
                    
                    # 显示角色状态变化
                    if "characters" in entry:
                        st.markdown("### 👥 角色状态")
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