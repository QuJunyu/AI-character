# /root/ai_character/memory/temporary_memory.py
import os
from datetime import datetime, timedelta
from utils.file_operations import save_to_json, load_from_json, get_today_date_str
from config import MEMORY_BASE_PATH, TEMP_MEMORY_EXPIRE_DAYS

class TemporaryMemory:
    """临时记忆（数天）：无锚点，仅存储近期聊天内容"""
    def __init__(self, character_id="furenna"):
        self.file_path = os.path.join(MEMORY_BASE_PATH, f"{character_id}_temp_memory.json")
        self.memory_data = self._load_memory()
        self._clean_expired_memory()  # 初始化清理过期

    def _load_memory(self):
        """加载临时记忆"""
        return load_from_json(self.file_path)

    def _clean_expired_memory(self):
        """清理过期临时记忆"""
        expire_time = datetime.now() - timedelta(days=TEMP_MEMORY_EXPIRE_DAYS)
        valid_memory = []
        for item in self.memory_data:
            try:
                create_time = datetime.strptime(item["create_time"], "%Y-%m-%d %H:%M:%S")
                if create_time > expire_time:
                    valid_memory.append(item)
            except:
                continue
        self.memory_data = valid_memory
        save_to_json(self.file_path, self.memory_data)

    def add_temp_memory(self, content, chat_context=""):
        """添加临时记忆"""
        memory_item = {
            "content": content,
            "chat_context": chat_context,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory_data.append(memory_item)
        self._clean_expired_memory()  # 添加后清理
        save_to_json(self.file_path, self.memory_data)

    def get_all_temp_memory(self):
        """获取所有有效临时记忆（全量）"""
        self._clean_expired_memory()
        return self.memory_data