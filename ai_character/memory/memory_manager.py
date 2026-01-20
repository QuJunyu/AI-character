# /root/ai_character/memory/memory_manager.py
import os
from .core_memory import CoreMemory
from .long_term_memory import LongTermMemory
from .temporary_memory import TemporaryMemory
from utils.file_operations import extract_anchor_words_via_model
from config import MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM, ACTIVE_TOPIC_MEMORY_TYPES

class MemoryManager:
    """记忆总管理器：锚点检索、全量读取、自动梳理、主动话题素材（移除冲突覆盖）"""
    def __init__(self, character_id="furenna"):
        self.core_memory = CoreMemory(character_id)
        self.long_memory = LongTermMemory(character_id)
        self.temp_memory = TemporaryMemory(character_id)
        self.character_id = character_id

    def retrieve_all_related_memory(self, input_text):
        """
        全量检索所有相关记忆（核心+长期+临时）
        步骤：1. 提取输入锚点词；2. 锚点检索核心/长期记忆；3. 全量取临时记忆
        """
        # 1. 提取输入的锚点词
        input_anchors = extract_anchor_words_via_model(
            input_text, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM
        )
        print(f"输入文本锚点词：{input_anchors}")
        
        # 2. 检索核心记忆（全量匹配锚点）
        core_related = self.core_memory.get_core_memory_by_anchor(input_anchors)
        # 3. 检索长期记忆（全量匹配锚点）
        long_related = self.long_memory.get_long_memory_by_anchor(input_anchors)
        # 4. 获取所有临时记忆
        temp_related = self.temp_memory.get_all_temp_memory()
        
        # 整合记忆（保留全量，便于后续检索）
        all_related_memory = {
            "core": core_related,
            "long_term": long_related,
            "temporary": temp_related,
            "input_anchors": input_anchors  # 记录输入锚点词
        }
        return all_related_memory

    def get_active_topic_material(self):
        """提取主动发起话题的素材（核心+长期记忆）"""
        topic_material = []
        if "core" in ACTIVE_TOPIC_MEMORY_TYPES:
            # 核心记忆取前3条
            core_mem = self.core_memory.memory_data[:3]
            topic_material.extend([item["content"] for item in core_mem])
        if "long_term" in ACTIVE_TOPIC_MEMORY_TYPES:
            # 长期记忆取高访问量素材
            long_mem = self.long_memory.get_active_topic_material()
            topic_material.extend(long_mem)
        # 去重
        return list(set(topic_material))[:3]  # 最多取3条素材

    def learn_new_knowledge(self, content, is_core=False):
        """学习新知识（核心/长期记忆二选一）"""
        if is_core:
            self.core_memory.add_core_memory(content)
        else:
            self.long_memory.add_long_memory(content)

    def update_memory_by_anchor(self, anchor_words, new_content, is_core=False):
        """通过锚点词更新记忆（移除冲突覆盖）"""
        if is_core:
            # 核心记忆直接添加（永久，不覆盖，仅补充）
            self.core_memory.add_core_memory(new_content, anchor_words)
        else:
            self.long_memory.update_long_memory(anchor_words, new_content)

    def optimize_all_memory(self):
        """手动触发所有记忆梳理"""
        self.core_memory.comb_memory()
        self.long_memory.comb_memory()
        self.temp_memory._clean_expired_memory()
        print("所有记忆优化完成！")