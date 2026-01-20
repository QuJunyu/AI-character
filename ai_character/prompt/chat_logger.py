# /root/ai_character/prompt/chat_logger.py
import os
import json
from datetime import datetime
# 引用完整配置
from config import CHAT_LOG_PATH, TEXT_CHAT_MODEL_PATH

class ChatLogger:
    """聊天记录管理：自动跨天总结+每日归档"""
    def __init__(self, character_id="furenna"):
        self.character_id = character_id
        self.today = datetime.now().strftime("%Y-%m-%d")
        # 日志保存路径（使用配置中的路径，已自动创建）
        self.today_log_file = os.path.join(CHAT_LOG_PATH, f"{self.character_id}_chat_{self.today}.json")
        # 每日总结路径（使用配置中的聊天日志路径+子目录，已自动创建）
        self.summary_dir = os.path.join(CHAT_LOG_PATH, "daily_summary")

    def _check_date(self):
        """检查是否跨天，跨天自动总结昨日聊天"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.today:
            print(f"📅 跨天啦！自动总结{self.today}的聊天记录...")
            # 总结昨日记录
            self.daily_summary(date=self.today)
            # 更新今日日志文件
            self.today = current_date
            self.today_log_file = os.path.join(CHAT_LOG_PATH, f"{self.character_id}_chat_{self.today}.json")

    def log_chat(self, user_input, character_response):
        """记录聊天（自动检查跨天）"""
        self._check_date()
        # 构建聊天记录项
        chat_item = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_role": "旅行者",
            "user_input": user_input,
            "character_role": "芙宁娜",
            "character_response": character_response
        }
        # 读取现有日志
        if os.path.exists(self.today_log_file) and os.path.getsize(self.today_log_file) > 0:
            with open(self.today_log_file, "r", encoding="utf-8") as f:
                chat_logs = json.load(f)
        else:
            chat_logs = []
        # 追加新记录
        chat_logs.append(chat_item)
        # 保存日志
        with open(self.today_log_file, "w", encoding="utf-8") as f:
            json.dump(chat_logs, f, ensure_ascii=False, indent=2)
        print(f"📝 聊天记录已保存：{self.today_log_file}")

    def daily_summary(self, date=None):
        """生成指定日期的聊天总结（无date则总结今日）"""
        target_date = date if date else self.today
        target_log_file = os.path.join(CHAT_LOG_PATH, f"{self.character_id}_chat_{target_date}.json")
        
        # 检查日志文件是否存在
        if not os.path.exists(target_log_file) or os.path.getsize(target_log_file) == 0:
            print(f"❌ {target_date}无聊天记录，无需总结！")
            return None
        
        # 读取聊天记录
        with open(target_log_file, "r", encoding="utf-8") as f:
            chat_logs = json.load(f)
        
        # 拼接聊天文本
        chat_text = ""
        for item in chat_logs:
            chat_text += f"[{item['timestamp']}] 旅行者：{item['user_input']} | 芙宁娜：{item['character_response']}\n"
        
        # 构建总结提示词
        summary_prompt = f"""
        请总结以下芙宁娜与旅行者的聊天记录，要求：
        1. 核心要点：聊了哪些主要话题（歌剧/甜品/购物等）、芙宁娜的情绪变化；
        2. 格式：50字以内，简洁清晰，无冗余；
        3. 语气：客观中立，符合日常聊天总结。
        聊天记录：
        {chat_text}
        """
        
        try:
            # 调用文本模型生成总结
            import subprocess
            result = subprocess.run(
                [f"{TEXT_CHAT_MODEL_PATH}/infer.py", "--prompt", summary_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            summary_content = result.stdout.strip()
            
            # 保存总结
            summary_file = os.path.join(self.summary_dir, f"{self.character_id}_summary_{target_date}.json")
            summary_data = {
                "date": target_date,
                "chat_count": len(chat_logs),
                "summary": summary_content,
                "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {target_date}聊天总结已保存：{summary_file}")
            print(f"📌 总结内容：{summary_content}")
            return summary_content
        except Exception as e:
            print(f"⚠️ 生成聊天总结失败：{e}")
            return None

    def export_chat_to_producer(self):
        """导出今日聊天记录给制作人（反馈优化用）"""
        self._check_date()
        if not os.path.exists(self.today_log_file) or os.path.getsize(self.today_log_file) == 0:
            print("❌ 今日无聊天记录可导出！")
            return None
        
        # 读取今日日志
        with open(self.today_log_file, "r", encoding="utf-8") as f:
            chat_logs = json.load(f)
        
        # 转换为制作人反馈格式
        export_data = []
        for item in chat_logs:
            export_data.append({
                "user_input": item["user_input"],
                "character_response": item["character_response"],
                "correct_response": ""  # 留空给制作人填写正确回复
            })
        
        # 保存导出文件（使用配置中的制作人反馈路径）
        from config import PRODUCER_FEEDBACK_PATH
        export_file = os.path.join(PRODUCER_FEEDBACK_PATH, f"producer_feedback_{self.today}.json")
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 聊天记录已导出给制作人：{export_file}")
        return export_file