#!/usr/bin/env python3
"""
完整的随从选择系统演示
展示了新的游戏机制：随从选择、数值评估、游戏进度控制
"""

import asyncio
import json
from sultans_game.models import GameState, SceneState, GamePhase, FollowerChoice, GameResult
from sultans_game.agents.agent_manager import AgentManager
from sultans_game.agents.agent_coordinator import AgentCoordinator


class FollowerChoiceSystemDemo:
    """随从选择系统完整演示"""
    
    def __init__(self):
        # 创建游戏状态
        self.game_state = GameState(
            current_scene=SceneState(
                location="奢华妓院",
                characters_present=["随从", "妓女", "老鸨"],
                atmosphere="暧昧",
                time_of_day="夜晚"
            )
        )
        
        # 设置智能体管理器
        self.agent_manager = AgentManager()
        self.agent_manager.set_game_state(self.game_state)
        self.agent_manager.setup_scene("brothel")
        
        # 创建协调器
        self.agent_coordinator = AgentCoordinator()
        
        # 游戏状态
        self.round_count = 0
        
    async def run_complete_demo(self):
        """运行完整演示"""
        print("🎮 苏丹的游戏 - 随从选择系统完整演示")
        print("=" * 60)
        
        # 1. 初始化游戏
        await self._initialize_game()
        
        # 2. 运行游戏循环
        await self._run_game_loop()
        
        # 3. 显示最终结果
        await self._show_final_results()
    
    async def _initialize_game(self):
        """初始化游戏"""
        print("\n📋 初始化游戏状态...")
        print(f"当前阶段: {self.game_state.current_phase.value}")
        print(f"最大轮数: {self.game_state.max_follower_rounds}")
        print(f"初始场景数值: {self.game_state.current_scene.scene_values}")
        
        # 设置一个目标任务
        print("\n🎯 任务目标：获取敏感情报")
        print("- 暧昧度需要达到 60+")
        print("- 危险度保持在 80 以下")
        print("- 最多 5 轮随从行动")
        
    async def _run_game_loop(self):
        """运行游戏主循环"""
        print("\n🔄 开始游戏循环...")
        
        while not self.game_state.check_game_end_conditions():
            self.round_count += 1
            print(f"\n{'='*20} 第 {self.round_count} 轮 {'='*20}")
            
            # 自由聊天阶段
            await self._free_chat_phase()
            
            # 检查是否应该触发随从选择
            if self._should_trigger_follower_choice():
                await self._follower_choice_phase()
            
            # 检查游戏结束条件
            if self.game_state.check_game_end_conditions():
                break
                
            # 防止无限循环
            if self.round_count >= 10:
                print("⏰ 达到最大循环次数，强制结束")
                break
    
    async def _free_chat_phase(self):
        """自由聊天阶段"""
        print("\n💬 自由聊天阶段")
        
        # 模拟一些角色对话
        dialogues = [
            ("旁白", "夜色渐深，妓院中传来悠扬的琴声..."),
            ("妓女", "公子第一次来我们这儿吧？"),
            ("随从", "我在观察四周的情况..."),
            ("老鸨", "贵客请坐，我们这里什么都有。")
        ]
        
        selected_dialogue = dialogues[self.round_count % len(dialogues)]
        speaker, content = selected_dialogue
        
        print(f"🗣️  {speaker}: {content}")
        
        # 添加到对话历史
        self.game_state.current_scene.add_conversation(speaker, content)
        
        # 简单的数值变化
        if "观察" in content:
            self.game_state.current_scene.update_scene_value("紧张度", 5)
        elif "琴声" in content:
            self.game_state.current_scene.update_scene_value("暧昧度", 8)
        
        print(f"📊 当前数值: {self.game_state.current_scene.scene_values}")
    
    def _should_trigger_follower_choice(self) -> bool:
        """判断是否应该触发随从选择"""
        # 每2轮触发一次随从选择
        if self.round_count % 2 == 0:
            return True
        
        # 或者根据数值触发
        values = self.game_state.current_scene.scene_values
        if values.get("暧昧度", 0) > 20 and self.game_state.follower_rounds_used < self.game_state.max_follower_rounds:
            return True
            
        return False
    
    async def _follower_choice_phase(self):
        """随从选择阶段"""
        print("\n🎯 进入随从选择阶段")
        
        # 开始随从选择阶段
        self.game_state.start_follower_choice_phase()
        
        # 生成选择项
        choices = await self._generate_follower_choices()
        
        # 显示选择项
        print("📋 可选行动:")
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice.content}")
            print(f"   风险等级: {choice.risk_level}/5")
            print(f"   预期效果: {choice.expected_values}")
            print(f"   提示: {choice.description}")
            print()
        
        # 模拟用户选择（这里随机选择第2个）
        selected_choice = choices[1] if len(choices) >= 2 else choices[0]
        print(f"✅ 随从选择了: {selected_choice.content}")
        
        # 处理选择结果
        await self._process_choice_result(selected_choice)
        
        # 结束随从选择阶段
        self.game_state.end_follower_choice_phase(selected_choice.choice_id)
    
    async def _generate_follower_choices(self) -> list[FollowerChoice]:
        """生成随从选择项"""
        import uuid
        
        # 根据当前情况生成不同的选择
        current_values = self.game_state.current_scene.scene_values
        
        if current_values.get("暧昧度", 0) < 30:
            # 早期阶段的选择
            choices = [
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="主动与妓女搭话，套取信息",
                    risk_level=3,
                    expected_values={"暧昧度": 15, "危险度": 10},
                    description="有效果但有暴露风险"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="假装喝醉，在角落偷听",
                    risk_level=2,
                    expected_values={"紧张度": 10, "危险度": 5},
                    description="较安全但信息有限"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="观察老鸨的行为模式",
                    risk_level=1,
                    expected_values={"紧张度": 8},
                    description="最安全但进展缓慢"
                )
            ]
        else:
            # 后期阶段的选择
            choices = [
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="直接询问敏感话题",
                    risk_level=5,
                    expected_values={"暧昧度": 25, "危险度": 30},
                    description="高风险高回报"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="通过暗示引导话题",
                    risk_level=3,
                    expected_values={"暧昧度": 18, "危险度": 12},
                    description="平衡的选择"
                ),
                FollowerChoice(
                    choice_id=str(uuid.uuid4())[:8],
                    content="保持现状，等待时机",
                    risk_level=1,
                    expected_values={"紧张度": -5},
                    description="保守策略"
                )
            ]
        
        return choices
    
    async def _process_choice_result(self, choice: FollowerChoice):
        """处理选择结果"""
        print(f"\n⚙️  处理选择结果...")
        
        # 应用数值变化
        for value_name, change in choice.expected_values.items():
            old_value = self.game_state.current_scene.scene_values.get(value_name, 0)
            self.game_state.current_scene.update_scene_value(value_name, change)
            new_value = self.game_state.current_scene.scene_values.get(value_name, 0)
            print(f"📈 {value_name}: {old_value} → {new_value} ({change:+d})")
        
        # 评估选择质量
        quality_score = await self._evaluate_choice_quality(choice)
        print(f"🎯 选择质量评分: {quality_score}/10")
        
        # 生成后续反应
        await self._generate_npc_reactions(choice, quality_score)
    
    async def _evaluate_choice_quality(self, choice: FollowerChoice) -> int:
        """评估选择质量"""
        # 简单的质量评估逻辑
        score = 5  # 基础分
        
        # 根据风险和回报调整
        if choice.risk_level <= 2:
            score += 2  # 安全选择加分
        elif choice.risk_level >= 4:
            score += 3  # 冒险选择在某些情况下加分
        
        # 根据当前情况调整
        current_danger = self.game_state.current_scene.scene_values.get("危险度", 0)
        if current_danger > 60 and choice.risk_level <= 2:
            score += 2  # 高危情况下选择安全行动加分
        
        return min(score, 10)
    
    async def _generate_npc_reactions(self, choice: FollowerChoice, quality_score: int):
        """生成NPC反应"""
        print("\n🎭 NPC反应:")
        
        if quality_score >= 8:
            reactions = [
                "妓女对你投来赞赏的目光",
                "老鸨露出满意的微笑",
                "其他客人没有注意到异常"
            ]
        elif quality_score >= 6:
            reactions = [
                "妓女似乎有所察觉但没说什么",
                "老鸨眯起了眼睛",
                "气氛变得微妙"
            ]
        else:
            reactions = [
                "妓女脸上闪过疑惑",
                "老鸨的表情变得警惕",
                "你感到一些不友善的目光"
            ]
        
        for reaction in reactions:
            print(f"👁️  {reaction}")
    
    async def _show_final_results(self):
        """显示最终结果"""
        print("\n" + "="*60)
        print("🏁 游戏结束")
        
        # 计算最终结果
        final_result = self.game_state.calculate_final_result()
        final_score = self.game_state.calculate_final_score()
        
        print(f"\n📊 最终统计:")
        print(f"游戏结果: {final_result.value}")
        print(f"最终得分: {final_score}")
        print(f"使用轮数: {self.game_state.follower_rounds_used}/{self.game_state.max_follower_rounds}")
        print(f"最终数值: {self.game_state.current_scene.scene_values}")
        
        # 显示详细分析
        self._analyze_performance()
    
    def _analyze_performance(self):
        """分析游戏表现"""
        print(f"\n📈 表现分析:")
        
        values = self.game_state.current_scene.scene_values
        
        if values.get("暧昧度", 0) >= 60:
            print("✅ 成功建立足够的信任关系")
        else:
            print("❌ 信任关系建立不足")
        
        if values.get("危险度", 0) < 80:
            print("✅ 成功保持低调，避免暴露")
        else:
            print("⚠️ 行动过于危险，引起怀疑")
        
        efficiency = (self.game_state.max_follower_rounds - self.game_state.follower_rounds_used) / self.game_state.max_follower_rounds
        print(f"⚡ 效率评级: {efficiency:.1%}")
        
        if self.game_state.game_result == GameResult.SUCCESS:
            print("🎉 任务成功完成！随从成功获取了所需情报。")
        elif self.game_state.game_result == GameResult.FAILURE:
            print("💀 任务失败！随从被发现并面临危险。")
        else:
            print("😐 任务结果平平，没有明显的成功或失败。")


async def main():
    """主函数"""
    demo = FollowerChoiceSystemDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main()) 