# /root/ai_character/voice/__init__.py
# 语音模块包初始化
from .gpt_sovits_tts import GPTSoVITS_TTS
from .speak_finish import SpeakFinish

__all__ = ["GPTSoVITS_TTS", "SpeakFinish"]