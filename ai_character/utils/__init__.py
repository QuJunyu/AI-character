# /root/ai_character/utils/__init__.py
# 工具模块包初始化
from .file_operations import (
    save_to_json, load_from_json, get_today_date_str,
    get_date_diff_days, extract_anchor_words_via_model
)

__all__ = [
    "save_to_json", "load_from_json", "get_today_date_str",
    "get_date_diff_days", "extract_anchor_words_via_model"
]