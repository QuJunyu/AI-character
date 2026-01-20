# /root/ai_character/emotion/emoji_manager.py
import os
import random
from .emotion_manager import EmotionManager
from config import EMOTION_IMAGE_MAP

class EmojiManager:
    """图片表情包管理（按情绪匹配）"""
    def __init__(self):
        self.emotion_manager = EmotionManager()
        self.emotion_image_map = EMOTION_IMAGE_MAP
        # 预加载各情绪的图片列表
        self.emotion_images = self._load_all_emoji_images()

    def _load_all_emoji_images(self):
        """加载所有情绪对应的图片表情包"""
        emotion_images = {}
        for emotion, path in self.emotion_image_map.items():
            if not os.path.exists(path):
                emotion_images[emotion] = []
                continue
            # 支持的图片格式
            img_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
            images = [
                os.path.join(path, f) for f in os.listdir(path)
                if os.path.splitext(f)[1].lower() in img_ext
            ]
            emotion_images[emotion] = images
        return emotion_images

    def get_emoji_image_by_text(self, text, emotion_value=80):
        """根据文本+情感值获取随机图片表情包路径"""
        # 1. 判断文本情绪
        emotion = self.emotion_manager.judge_emotion(text, emotion_value)
        # 2. 获取该情绪的图片列表
        images = self.emotion_images.get(emotion, [])
        if not images:
            # 无对应图片则用中性
            images = self.emotion_images.get("neutral", [])
        if not images:
            print("无可用的图片表情包！")
            return None
        # 3. 随机选一张
        return random.choice(images)

    def add_emoji_image(self, emotion, image_path):
        """添加图片表情包到指定情绪分类"""
        if emotion not in self.emotion_manager.emotion_list:
            print(f"不支持的情绪类型：{emotion}")
            return False
        # 复制图片到对应路径
        import shutil
        target_path = self.emotion_image_map[emotion]
        try:
            shutil.copy(image_path, target_path)
            # 重新加载图片列表
            self.emotion_images = self._load_all_emoji_images()
            print(f"图片表情包已添加：{image_path} → {target_path}")
            return True
        except Exception as e:
            print(f"添加图片表情包失败：{e}")
            return False