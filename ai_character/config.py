# /root/ai_character/main.py
import os
from character.character import Character
from prompt.chat_logger import ChatLogger
from prompt.producer_feedback import ProducerFeedback
from voice.speak_finish import SpeakFinish
from emotion.emoji_manager import EmojiManager
from memory.memory_manager import MemoryManager
# 引用完整配置中的情感值阈值
from config import EMOTION_VALUE_THRESHOLD

def main():
    """芙宁娜与旅行者聊天主程序：无暂停+一直运行+自动总结"""
    # 初始化核心模块
    character_id = "furenna"
    furenna = Character(character_id)
    chat_logger = ChatLogger(character_id)
    producer_feedback = ProducerFeedback(character_id)
    speak_finish = SpeakFinish()
    emoji_manager = EmojiManager()
    memory_manager = MemoryManager(character_id)

    # 欢迎语
    print("="*70)
    print("芙宁娜与旅行者的日常聊天")
    print("📌 核心特性：")
    print("  1. 不关闭终端则一直聊，情感值低时发消息自动恢复；")
    print("  2. 跨天自动总结聊天记录，支持手动总结（/summary）；")
    print("  3. 状态自动保存，重启终端可恢复上次情感值；")
    print("  4. 语音合成适配已下载的芙宁娜模型。")
    print("📌 指令说明：")
    print("  /export      → 导出今日聊天记录给制作人；")
    print("  /feedback 路径 → 加载制作人反馈（示例：/feedback /root/xxx.json）；")
    print("  /optimize    → 优化芙宁娜的记忆；")
    print("  /reset_emotion → 重置芙宁娜情感值；")
    print("  /summary [日期] → 手动总结聊天（示例：/summary 2025-10-01）；")
    print("  /exit        → 退出程序（自动保存所有数据）。")
    print(f"❤️ 初始状态：芙宁娜情感值={furenna.emotion_value}，低阈值={EMOTION_VALUE_THRESHOLD}")
    print("="*70)

    # 无限循环：不输入/exit则一直运行
    while True:
        # 获取用户输入（旅行者）
        user_input = input("\n旅行者：").strip()
        
        # 退出指令：保存所有数据后退出
        if user_input.lower() == "exit":
            print("\n📌 程序退出中，正在保存所有数据...")
            # 1. 优化记忆
            memory_manager.optimize_all_memory()
            # 2. 保存芙宁娜状态
            furenna._save_state()
            # 3. 总结今日聊天
            chat_logger.daily_summary()
            print("✅ 记忆/状态/聊天总结已全部保存！")
            print("👋 再见啦～下次启动可直接恢复聊天状态～")
            break

        # 处理特殊指令
        if user_input.startswith("/export"):
            chat_logger.export_chat_to_producer()
            continue
        
        if user_input.startswith("/feedback"):
            # 解析反馈文件路径
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("❌ 指令格式错误！示例：/feedback /root/ai_character/producer_feedback/producer_feedback_2025-10-01.json")
                continue
            feedback_file = parts[1]
            # 加载并学习反馈
            feedback_content = producer_feedback.load_producer_feedback_file(feedback_file)
            if feedback_content:
                furenna.learn_from_producer_feedback(feedback_content)
            else:
                print("❌ 加载制作人反馈失败！请检查文件路径是否正确。")
            continue
        
        if user_input.startswith("/optimize"):
            print("🔧 正在优化芙宁娜的记忆...")
            memory_manager.optimize_all_memory()
            print("✅ 芙宁娜记忆优化完成！")
            continue
        
        if user_input.startswith("/reset_emotion"):
            furenna.reset_emotion_value()
            print(f"✅ 芙宁娜情感值已重置为初始值：{furenna.emotion_value}")
            continue
        
        if user_input.startswith("/summary"):
            # 解析总结日期
            parts = user_input.split(maxsplit=1)
            target_date = parts[1] if len(parts) > 1 else None
            chat_logger.daily_summary(target_date)
            continue

        # ========== 核心聊天流程 ==========
        # 1. 先更新情感值（发消息即恢复，无暂停）
        furenna._update_emotion_value(user_input)
        # 2. 生成芙宁娜回复
        furenna_reply = furenna.get_response(user_input)
        # 3. 生成表情包（可选，使用配置中的表情包路径）
        emoji_image = emoji_manager.get_emoji_image_by_text(furenna_reply, furenna.emotion_value)
        emoji_tip = f"\n📸 匹配表情包：{emoji_image}" if emoji_image else ""
        # 4. 生成语音（可选）
        voice_result = speak_finish.process_voice_response(user_input, furenna_reply)
        voice_tip = f"\n🎵 语音文件：{voice_result['voice_file']}" if voice_result['voice_file'] else ""
        # 5. 输出回复
        emotion_tip = f"\n❤️ 芙宁娜当前情感值：{furenna.emotion_value}"
        print(f"\n芙宁娜：{furenna_reply}{emoji_tip}{voice_tip}{emotion_tip}")
        # 6. 记录聊天（自动检查跨天总结）
        chat_logger.log_chat(user_input, furenna_reply)

if __name__ == "__main__":
    # 确保工作目录正确
    os.chdir("/root/ai_character")
    main()