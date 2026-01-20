# /root/ai_character/prompt/producer_feedback.py
import os
import json
from config import CHAT_LOG_PATH

class ProducerFeedback:
    """制作人反馈加载：读取反馈文件并返回结构化数据"""
    def __init__(self, character_id="furenna"):
        self.character_id = character_id
        self.feedback_dir = CHAT_LOG_PATH

    def load_producer_feedback_file(self, feedback_file_path):
        """加载指定路径的制作人反馈文件"""
        # 检查文件是否存在
        if not os.path.exists(feedback_file_path):
            print(f"❌ 反馈文件不存在：{feedback_file_path}")
            return None
        # 读取反馈文件
        try:
            with open(feedback_file_path, "r", encoding="utf-8") as f:
                feedback_content = json.load(f)
            # 验证格式
            for item in feedback_content:
                if not all(key in item for key in ["user_input", "character_response", "correct_response"]):
                    print(f"⚠️ 反馈项格式错误：{item} → 跳过")
                    feedback_content.remove(item)
            print(f"✅ 成功加载{len(feedback_content)}条制作人反馈！")
            return feedback_content
        except Exception as e:
            print(f"⚠️ 加载反馈文件失败：{e}")
            return None