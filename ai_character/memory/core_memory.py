# /root/ai_character/memory/core_memory.py
import os
from utils.file_operations import (
    save_to_json, load_from_json, get_today_date_str, get_date_diff_days,
    extract_anchor_words_via_model
)
from config import (
    MEMORY_BASE_PATH, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM,
    MEMORY_COMB_DAYS
)

class CoreMemory:
    """核心记忆（永久）：锚点词+链接关系+每3天梳理（移除冲突覆盖）"""
    def __init__(self, character_id="furenna"):
        self.file_path = os.path.join(MEMORY_BASE_PATH, f"{character_id}_core_memory.json")
        self.comb_record_path = os.path.join(MEMORY_BASE_PATH, f"{character_id}_core_comb_record.json")
        self.memory_data = self._load_memory()
        self.comb_record = load_from_json(self.comb_record_path)  # 梳理记录：{"last_comb_date": "2025-10-01"}
        self.check_need_comb()  # 初始化时检查是否需要梳理

    def _load_memory(self):
        """加载核心记忆（结构：[{content, anchor_words, links, create_time, update_time}]）"""
        memory = load_from_json(self.file_path)
        # 兼容旧数据：补充锚点词/链接字段
        for item in memory:
            if "anchor_words" not in item:
                item["anchor_words"] = []
            if "links" not in item:
                item["links"] = []  # 链接的锚点词（如["用户", "生日"]链接到["日期"]）
            if "create_time" not in item:
                item["create_time"] = get_today_date_str()
            if "update_time" not in item:
                item["update_time"] = get_today_date_str()
        return memory

    def add_core_memory(self, content, anchor_words=None):
        """添加核心记忆（自动提取锚点词+建立链接，移除冲突检测）"""
        # 提取锚点词
        anchor_words = anchor_words if anchor_words else extract_anchor_words_via_model(
            content, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM
        )
        # 建立锚点词之间的链接（两两链接）
        links = []
        for i in range(len(anchor_words)):
            for j in range(i+1, len(anchor_words)):
                links.append([anchor_words[i], anchor_words[j]])
        
        memory_item = {
            "content": content,
            "anchor_words": anchor_words,
            "links": links,
            "create_time": get_today_date_str(),
            "update_time": get_today_date_str(),
            "is_core": True
        }
        self.memory_data.append(memory_item)
        save_to_json(self.file_path, self.memory_data)
        return memory_item

    def get_core_memory_by_anchor(self, query_anchors):
        """通过锚点词检索核心记忆（全量匹配+链接拓展）"""
        related_memory = []
        # 1. 先匹配直接锚点词
        for item in self.memory_data:
            if any(anchor in item["anchor_words"] for anchor in query_anchors):
                related_memory.append(item)
                continue
            # 2. 匹配链接的锚点词
            for link in item["links"]:
                if any(anchor in link for anchor in query_anchors):
                    related_memory.append(item)
                    break
        # 去重（按content）
        unique_memory = []
        seen_content = set()
        for item in related_memory:
            if item["content"] not in seen_content:
                seen_content.add(item["content"])
                unique_memory.append(item)
        return unique_memory

    def comb_memory(self):
        """梳理核心记忆：合并重复锚点、优化链接、精简冗余内容"""
        from utils.file_operations import extract_anchor_words_via_model
        # 1. 按锚点词分组
        anchor_groups = {}
        for item in self.memory_data:
            for anchor in item["anchor_words"]:
                if anchor not in anchor_groups:
                    anchor_groups[anchor] = []
                anchor_groups[anchor].append(item)
        
        # 2. 合并同锚点的冗余内容
        new_memory_data = []
        for anchor, items in anchor_groups.items():
            if len(items) <= 1:
                new_memory_data.extend(items)
                continue
            # 合并内容（调用本地模型总结）
            import subprocess
            combine_prompt = f"""
            请合并以下核心记忆内容，保留所有关键信息，精简冗余：
            {[item["content"] for item in items]}
            """
            result = subprocess.run(
                [f"{MEMORY_MODEL_PATH}/infer", "--prompt", combine_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            combined_content = result.stdout.strip()
            # 重新提取锚点词和链接
            combined_anchors = extract_anchor_words_via_model(
                combined_content, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM
            )
            combined_links = []
            for i in range(len(combined_anchors)):
                for j in range(i+1, len(combined_anchors)):
                    combined_links.append([combined_anchors[i], combined_anchors[j]])
            # 生成合并后的记忆项
            combined_item = {
                "content": combined_content,
                "anchor_words": combined_anchors,
                "links": combined_links,
                "create_time": items[0]["create_time"],
                "update_time": get_today_date_str(),
                "is_core": True
            }
            new_memory_data.append(combined_item)
        
        # 3. 去重后保存
        self.memory_data = new_memory_data
        save_to_json(self.file_path, self.memory_data)
        # 4. 记录梳理日期
        self.comb_record = {"last_comb_date": get_today_date_str()}
        save_to_json(self.comb_record_path, self.comb_record)
        print("核心记忆梳理完成！")

    def check_need_comb(self):
        """检查是否需要梳理（每3天一次）"""
        last_comb_date = self.comb_record.get("last_comb_date", "")
        if not last_comb_date:
            # 首次直接梳理
            self.comb_memory()
            return
        # 计算距离上次梳理的天数
        diff_days = get_date_diff_days(last_comb_date, get_today_date_str())
        if diff_days >= MEMORY_COMB_DAYS:
            self.comb_memory()