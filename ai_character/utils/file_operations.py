# /root/ai_character/utils/file_operations.py
import json
import os
from datetime import datetime

def save_to_json(file_path, data, ensure_ascii=False):
    """保存数据到JSON文件（追加/覆盖）"""
    try:
        # 保证目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # 如果文件存在且非空，读取原有数据
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            # 如果是列表，追加；否则覆盖
            if isinstance(existing_data, list) and isinstance(data, list):
                existing_data.extend(data)
                data = existing_data
            elif isinstance(existing_data, list) and not isinstance(data, list):
                existing_data.append(data)
                data = existing_data
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=2)
        return True
    except Exception as e:
        print(f"保存文件失败：{e}")
        return False

def load_from_json(file_path):
    """从JSON文件加载数据"""
    try:
        if not os.path.exists(file_path):
            return [] if "memory" in file_path or "feedback" in file_path else {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件失败：{e}")
        return [] if "memory" in file_path or "feedback" in file_path else {}

def get_today_date_str():
    """获取今日日期字符串（YYYY-MM-DD）"""
    return datetime.now().strftime("%Y-%m-%d")

def get_date_diff_days(date_str1, date_str2):
    """计算两个日期字符串的天数差（date_str: YYYY-MM-DD）"""
    try:
        date1 = datetime.strptime(date_str1, "%Y-%m-%d")
        date2 = datetime.strptime(date_str2, "%Y-%m-%d")
        return abs((date1 - date2).days)
    except Exception as e:
        print(f"计算日期差失败：{e}")
        return 0

def extract_anchor_words_via_model(text, model_path, max_num=5):
    """调用本地记忆模型提取锚点词（宽泛、不冗余）"""
    import subprocess
    # 提示词：提取宽泛的锚点词，不要过于详细
    anchor_prompt = f"""
    请从以下文本中提取{max_num}个以内的宽泛锚点关键词（用于记忆检索，不要过于详细）：
    文本：{text}
    要求：1. 关键词宽泛（如"用户""生日""日期"，而非"2025年10月1日用户生日"）；
          2. 用英文逗号分隔；
          3. 仅输出关键词，无其他内容。
    """
    try:
        result = subprocess.run(
            [f"{model_path}/infer", "--prompt", anchor_prompt],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        anchor_words = result.stdout.strip().split(",")
        # 清洗锚点词
        anchor_words = [kw.strip() for kw in anchor_words if kw.strip()]
        return anchor_words[:max_num]  # 限制数量，避免冗余
    except Exception as e:
        print(f"提取锚点词失败：{e}")
        # 兜底：简单按空格分割取前max_num个
        return text.split()[:max_num]