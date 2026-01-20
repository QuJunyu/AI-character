# /root/ai_character/voice/gpt_sovits_tts.py
import os
import subprocess
# 引用完整配置中的路径
from config import GPT_SOVITS_PATH, VOICE_OUTPUT_PATH

class GPTSoVITS_TTS:
    """GPT-SoVITS语音合成：适配已下载的芙宁娜模型"""
    def __init__(self):
        # GPT-SoVITS根目录（使用配置中的路径）
        self.sovits_root = GPT_SOVITS_PATH
        # 已下载的芙宁娜语音模型ID（关键：替换成你的模型实际ID！）
        # 查看你的GPT-SoVITS模型列表：一般在 GPT-SoVITS/voices/ 目录下，ID是数字（比如1/2/3）
        self.furenna_voice_id = 2  # 【必改】替换成你的芙宁娜模型ID
        # 语音输出目录（使用配置中的路径，已自动创建）
        self.output_dir = VOICE_OUTPUT_PATH
        # 芙宁娜语音参数（适配退休后温和语气）
        self.speed = 0.95  # 语速：稍缓（0.8-1.0），日常自然
        self.pitch = 1.0   # 音调：自然（1.0），无神明时期的高扬
        self.volume = 0.9  # 音量：适中

    def generate_voice(self, text):
        """生成芙宁娜的语音（适配已下载模型）"""
        # 生成唯一语音文件名
        timestamp = os.popen('date +%s').read().strip()
        voice_file = os.path.join(self.output_dir, f"furenna_retired_{timestamp}.wav")
        
        # 检查GPT-SoVITS关键文件是否存在（防止路径错误）
        infer_script = os.path.join(self.sovits_root, "infer.py")
        if not os.path.exists(infer_script):
            print(f"❌ GPT-SoVITS路径错误！未找到infer.py：{infer_script}")
            return None
        
        try:
            # 调用GPT-SoVITS生成语音（核心命令：适配已下载模型）
            # 命令说明：--voice_id 是你的芙宁娜模型ID，--text 是要合成的文本
            cmd = [
                "python3", infer_script,
                "--text", text,                  # 要合成的文本（芙宁娜的回复）
                "--voice_id", str(self.furenna_voice_id),  # 你的芙宁娜模型ID
                "--output", voice_file,          # 输出文件路径
                "--speed", str(self.speed),      # 语速
                "--pitch", str(self.pitch),      # 音调
                "--volume", str(self.volume),    # 音量
                "--language", "zh",              # 语言：中文
                "--batch_size", "1",             # 批量大小：1（适配小模型）
                "--split_sentence", "True"       # 分句合成：更自然
            ]
            # 执行命令（隐藏输出，仅报错时显示）
            result = subprocess.run(
                cmd,
                cwd=self.sovits_root,  # 切换到GPT-SoVITS根目录执行
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            # 检查是否生成成功
            if os.path.exists(voice_file) and os.path.getsize(voice_file) > 0:
                print(f"✅ 芙宁娜语音生成成功：{voice_file}")
                return voice_file
            else:
                print(f"❌ 语音生成失败！GPT-SoVITS输出：{result.stderr}")
                return None
        except Exception as e:
            print(f"⚠️ 调用GPT-SoVITS失败：{e}")
            return None

    def play_voice(self, voice_file):
        """播放生成的语音（Linux系统：aplay，Windows：start）"""
        if not os.path.exists(voice_file):
            print(f"❌ 语音文件不存在：{voice_file}")
            return False
        try:
            # Linux系统：用aplay播放
            if os.name == "posix":
                subprocess.run(["aplay", voice_file], capture_output=True)
            # Windows系统：用默认播放器
            elif os.name == "nt":
                os.startfile(voice_file)
            print(f"✅ 已播放芙宁娜语音：{voice_file}")
            return True
        except Exception as e:
            print(f"⚠️ 播放语音失败：{e}")
            return False