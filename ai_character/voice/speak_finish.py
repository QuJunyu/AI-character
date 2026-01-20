# /root/ai_character/voice/speak_finish.py
from memory.memory_manager import MemoryManager
from .gpt_sovits_tts import GPTSoVITS_TTS

class SpeakFinish:
    """语音回复模块：锚点记忆驱动"""
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.tts = GPTSoVITS_TTS()

    def process_voice_response(self, user_input):
        """处理语音回复（锚点记忆+生成语音）"""
        # 1. 角色生成文本回复
        from character.character import Character
        character = Character()
        text_response = character.get_response(user_input)
        # 2. 生成语音
        voice_file = self.tts.generate_voice(text_response)
        # 3. 播放语音（可选）
        if voice_file:
            self.tts.play_voice(voice_file)
        return {
            "text_response": text_response,
            "voice_file": voice_file,
            "input_anchors": self.memory_manager.retrieve_all_related_memory(user_input)["input_anchors"]
        }