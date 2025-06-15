from crewai.tools import tool
from typing import Dict, Any, Optional, List
import json
import random

from .models import GameState, Character, SceneState, Card

# 全局游戏状态存储
_game_state_store: Optional[GameState] = None

def set_game_state(game_state: GameState):
    """设置全局游戏状态"""
    global _game_state_store
    _game_state_store = game_state

def get_game_state() -> Optional[GameState]:
    """获取全局游戏状态"""
    return _game_state_store

@tool("关系管理工具")
def relationship_tool(character_name: str, target_name: str, relationship_change: int, reason: str = "") -> str:
    """管理角色之间的关系变化，包括好感度、敌意等
    
    Args:
        character_name: 角色名称
        target_name: 目标角色名称
        relationship_change: 关系变化值，-100到100之间
        reason: 关系变化的原因
        
    Returns:
        关系变化结果的JSON字符串
    """
    game_state = get_game_state()
    if not game_state:
        return json.dumps({"error": "游戏状态未初始化"}, ensure_ascii=False)
    
    if character_name not in game_state.characters:
        return json.dumps({"error": f"角色 {character_name} 不存在"}, ensure_ascii=False)
    
    character = game_state.characters[character_name]
    
    # 更新关系
    if target_name not in character.relationships:
        character.relationships[target_name] = 0
    
    old_relationship = character.relationships[target_name]
    character.relationships[target_name] = max(-100, min(100, 
        character.relationships[target_name] + relationship_change))
    
    new_relationship = character.relationships[target_name]
    
    result = {
        "character": character_name,
        "target": target_name,
        "old_relationship": old_relationship,
        "new_relationship": new_relationship,
        "change": relationship_change,
        "reason": reason,
        "relationship_level": _get_relationship_level(new_relationship)
    }
    
    return json.dumps(result, ensure_ascii=False)

@tool("场景数值管理工具")
def scene_value_tool(value_type: str, change_amount: int, reason: str = "") -> str:
    """管理场景的各种数值变化
    
    Args:
        value_type: 数值类型（紧张度、暧昧度、危险度、金钱消费）
        change_amount: 变化量
        reason: 变化原因
        
    Returns:
        场景数值变化结果的JSON字符串
    """
    game_state = get_game_state()
    if not game_state:
        return json.dumps({"error": "游戏状态未初始化"}, ensure_ascii=False)
    
    scene = game_state.current_scene
    valid_types = ["紧张度", "暧昧度", "危险度", "金钱消费"]
    
    if value_type not in valid_types:
        return json.dumps({"error": f"无效的数值类型: {value_type}"}, ensure_ascii=False)
    
    # 获取当前值
    current_value = scene.scene_values.get(value_type, 0)
    
    # 更新值
    new_value = max(0, min(100, current_value + change_amount))
    scene.scene_values[value_type] = new_value
    
    result = {
        "value_type": value_type,
        "old_value": current_value,
        "new_value": new_value,
        "change": change_amount,
        "reason": reason
    }
    
    return json.dumps(result, ensure_ascii=False)

@tool("骰子检定工具")
def dice_roll_tool(character_name: str, attribute: str, difficulty: int = 10, bonus: int = 0) -> str:
    """进行骰子检定
    
    Args:
        character_name: 角色名称
        attribute: 属性名称（魅力、智慧、体魄、战斗、社交、隐匿）
        difficulty: 难度值（默认10）
        bonus: 额外加成
        
    Returns:
        检定结果的JSON字符串
    """
    game_state = get_game_state()
    if not game_state:
        return json.dumps({"error": "游戏状态未初始化"}, ensure_ascii=False)
    
    if character_name not in game_state.characters:
        return json.dumps({"error": f"角色 {character_name} 不存在"}, ensure_ascii=False)
    
    character = game_state.characters[character_name]
    
    # 获取属性值
    attribute_value = getattr(character, attribute.lower(), 0)
    
    # 投骰子
    dice_result = random.randint(1, 20)
    total = dice_result + attribute_value + bonus
    
    success = total >= difficulty
    
    result = {
        "character": character_name,
        "attribute": attribute,
        "attribute_value": attribute_value,
        "dice_result": dice_result,
        "bonus": bonus,
        "total": total,
        "difficulty": difficulty,
        "success": success,
        "margin": total - difficulty
    }
    
    return json.dumps(result, ensure_ascii=False)

@tool("卡牌使用工具")
def card_usage_tool(card_id: str, action: str, target: str = "") -> str:
    """使用卡牌或采取行动
    
    Args:
        card_id: 卡牌ID
        action: 行动类型（使用、放弃、保留）
        target: 目标角色或对象
        
    Returns:
        卡牌使用结果的JSON字符串
    """
    game_state = get_game_state()
    if not game_state:
        return json.dumps({"error": "游戏状态未初始化"}, ensure_ascii=False)
    
    # 查找卡牌
    card = None
    for c in game_state.active_cards:
        if c.card_id == card_id:
            card = c
            break
    
    if not card:
        return json.dumps({"error": f"未找到卡牌 {card_id}"}, ensure_ascii=False)
    
    result = {
        "card_id": card_id,
        "card_title": card.title,
        "action": action,
        "target": target,
        "success": False,
        "consequences": []
    }
    
    if action == "使用":
        # 模拟卡牌使用结果
        success_chance = random.randint(1, 100)
        if success_chance > 30:  # 70%成功率
            result["success"] = True
            result["consequences"] = [
                f"成功执行了{card.title}",
                f"获得了{card.rewards}奖励"
            ]
            
            # 从活动卡牌中移除
            game_state.active_cards.remove(card)
        else:
            result["consequences"] = [
                f"执行{card.title}失败",
                "可能产生负面后果"
            ]
    
    elif action == "放弃":
        game_state.active_cards.remove(card)
        result["consequences"] = [f"放弃了{card.title}"]
    
    return json.dumps(result, ensure_ascii=False)

@tool("对话记录工具")
def dialogue_recorder_tool(speaker: str, content: str, emotion: str = "中性", importance: int = 1) -> str:
    """记录重要对话内容
    
    Args:
        speaker: 发言者
        content: 对话内容
        emotion: 情绪状态
        importance: 重要程度（1-5）
        
    Returns:
        记录结果的JSON字符串
    """
    game_state = get_game_state()
    if not game_state:
        return json.dumps({"error": "游戏状态未初始化"}, ensure_ascii=False)
    
    dialogue_entry = {
        "speaker": speaker,
        "content": content,
        "emotion": emotion,
        "importance": importance,
        "timestamp": len(game_state.dialogue_history) + 1
    }
    
    game_state.dialogue_history.append(dialogue_entry)
    
    result = {
        "recorded": True,
        "entry": dialogue_entry,
        "total_entries": len(game_state.dialogue_history)
    }
    
    return json.dumps(result, ensure_ascii=False)

@tool("场景控制工具")
def scene_control_tool(action: str, parameter: str = "", value: str = "") -> str:
    """控制场景变化和事件
    
    Args:
        action: 行动类型（改变氛围、触发事件、转换场景、改变数值）
        parameter: 参数名称（对于改变数值：紧张度、暧昧度、危险度、金钱消费）
        value: 参数值（对于改变数值：数值变化量）
        
    Returns:
        场景控制结果的JSON字符串
    """
    game_state = get_game_state()
    if not game_state:
        return json.dumps({"error": "游戏状态未初始化"}, ensure_ascii=False)
    
    scene = game_state.current_scene
    result = {
        "action": action,
        "parameter": parameter,
        "value": value,
        "success": True,
        "changes": []
    }
    
    if action == "改变氛围":
        old_atmosphere = scene.atmosphere
        scene.atmosphere = value
        result["changes"].append(f"氛围从'{old_atmosphere}'变为'{value}'")
    
    elif action == "改变数值":
        # 处理场景数值变化
        valid_types = ["紧张度", "暧昧度", "危险度", "金钱消费"]
        if parameter in valid_types:
            try:
                change_amount = int(value)
                current_value = scene.scene_values.get(parameter, 0)
                new_value = max(0, min(100, current_value + change_amount))
                scene.scene_values[parameter] = new_value
                result["changes"].append(f"{parameter}从{current_value}变为{new_value}（变化{change_amount}）")
            except ValueError:
                result["success"] = False
                result["changes"].append(f"无效的数值变化量: {value}")
        else:
            result["success"] = False
            result["changes"].append(f"无效的场景数值类型: {parameter}")
    
    elif action == "触发事件":
        event = {
            "type": parameter,
            "description": value,
            "timestamp": len(game_state.dialogue_history) + 1
        }
        if not hasattr(scene, 'events'):
            scene.events = []
        scene.events.append(event)
        result["changes"].append(f"触发了事件: {value}")
    
    elif action == "转换场景":
        # 这里可以添加场景转换逻辑
        result["changes"].append(f"准备转换到场景: {value}")
    
    return json.dumps(result, ensure_ascii=False)

def _get_relationship_level(value: int) -> str:
    """获取关系等级描述"""
    if value >= 80:
        return "深爱"
    elif value >= 60:
        return "喜爱"
    elif value >= 40:
        return "好感"
    elif value >= 20:
        return "友好"
    elif value >= -20:
        return "中性"
    elif value >= -40:
        return "冷淡"
    elif value >= -60:
        return "厌恶"
    elif value >= -80:
        return "仇恨"
    else:
        return "深仇"

class GameToolsManager:
    """游戏工具管理器"""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        # 设置全局游戏状态
        set_game_state(game_state)
    
    def get_all_tools(self) -> List:
        """获取所有工具"""
        return [
            relationship_tool,
            scene_value_tool,
            dice_roll_tool,
            card_usage_tool,
            dialogue_recorder_tool,
            scene_control_tool
        ]
    
    def get_tools_by_agent_type(self, agent_type: str) -> List:
        """根据智能体类型获取相应工具"""
        if agent_type == "follower":
            return [card_usage_tool, dice_roll_tool, dialogue_recorder_tool]
        elif agent_type == "courtesan":
            return [relationship_tool, scene_value_tool, dialogue_recorder_tool]
        elif agent_type == "madam":
            return [relationship_tool, scene_value_tool, scene_control_tool]
        elif agent_type == "narrator":
            return [scene_control_tool, dialogue_recorder_tool, dice_roll_tool]
        else:
            return self.get_all_tools()