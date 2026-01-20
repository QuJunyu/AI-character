# /root/ai_character/emotion/emotion_manager.py
import os
from config import TEXT_CHAT_MODEL_PATH

class EmotionManager:
    """情绪判断模块（关联情感值）"""
    def __init__(self):
        self.emotion_list = ["happy", "sad", "angry", "surprised", "shy", "neutral"]

    def judge_emotion(self, text, emotion_value=80):
        """
        调用本地模型判断文本情绪
        :param text: 文本内容
        :param emotion_value: 角色当前情感值（影响判断倾向）
        :return: 情绪类型
        """
        import subprocess
        emotion_prompt = f"""
        角色当前情感值：{emotion_value}（0-100，越高越积极）
        请结合情感值判断以下文本的情绪，从列表中选择一个：{','.join(self.emotion_list)}
        文本：{text}
        仅输出情绪名称（如happy），无其他内容。
        """
        try:
            result = subprocess.run(
                [f"{TEXT_CHAT_MODEL_PATH}/infer", "--prompt", emotion_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            emotion = result.stdout.strip()
            return emotion if emotion in self.emotion_list else "neutral"
        except Exception as e:
            print(f"判断情绪失败：{e}")
            return "neutral"