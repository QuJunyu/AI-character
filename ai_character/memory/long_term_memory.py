# /root/ai_character/memory/long_term_memory.py
import os
from utils.file_operations import (
    save_to_json, load_from_json, get_today_date_str, get_date_diff_days,
    extract_anchor_words_via_model
)
from config import (
    MEMORY_BASE_PATH, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM,
    MEMORY_COMB_DAYS
)

class LongTermMemory:
    """长期记忆（数月）：锚点词+链接关系+每3天梳理（移除冲突覆盖）"""
    def __init__(self, character_id="furenna"):
        self.file_path = os.path.join(MEMORY_BASE_PATH, f"{character_id}_long_memory.json")
        self.comb_record_path = os.path.join(MEMORY_BASE_PATH, f"{character_id}_long_comb_record.json")
        self.memory_data = self._load_memory()
        self.comb_record = load_from_json(self.comb_record_path)
        self.check_need_comb()  # 初始化时检查是否需要梳理

    def _load_memory(self):
        """加载长期记忆（同核心记忆结构）"""
        memory = load_from_json(self.file_path)
        # 兼容旧数据
        for item in memory:
            if "anchor_words" not in item:
                item["anchor_words"] = []
            if "links" not in item:
                item["links"] = []
            if "create_time" not in item:
                item["create_time"] = get_today_date_str()
            if "update_time" not in item:
                item["update_time"] = get_today_date_str()
            if "expire_date" not in item:
                # 长期记忆默认保存6个月
                from datetime import datetime, timedelta
                expire_date = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
                item["expire_date"] = expire_date
        return memory

    def add_long_memory(self, content, anchor_words=None):
        """添加长期记忆（自动提取锚点词+建立链接，移除冲突检测）"""
        # 提取锚点词
        anchor_words = anchor_words if anchor_words else extract_anchor_words_via_model(
            content, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM
        )
        # 建立锚点链接
        links = []
        for i in range(len(anchor_words)):
            for j in range(i+1, len(anchor_words)):
                links.append([anchor_words[i], anchor_words[j]])
        # 计算过期日期（6个月后）
        from datetime import datetime, timedelta
        expire_date = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        
        memory_item = {
            "content": content,
            "anchor_words": anchor_words,
            "links": links,
            "create_time": get_today_date_str(),
            "update_time": get_today_date_str(),
            "expire_date": expire_date,
            "access_count": 0
        }
        self.memory_data.append(memory_item)
        save_to_json(self.file_path, self.memory_data)
        return memory_item

    def update_long_memory(self, anchor_words, new_content):
        """通过锚点词更新长期记忆（移除冲突检测）"""
        from utils.file_operations import extract_anchor_words_via_model
        # 查找匹配的记忆项
        matched_items = self.get_long_memory_by_anchor(anchor_words)
        if not matched_items:
            # 无匹配则新增
            return self.add_long_memory(new_content, anchor_words)
        # 合并更新
        combined_content = f"{[item['content'] for item in matched_items]} + 新内容：{new_content}"
        new_anchors = extract_anchor_words_via_model(
            combined_content, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM
        )
        new_links = []
        for i in range(len(new_anchors)):
            for j in range(i+1, len(new_anchors)):
                new_links.append([new_anchors[i], new_anchors[j]])
        # 更新第一个匹配项，删除其他项
        first_item = matched_items[0]
        first_item["content"] = combined_content
        first_item["anchor_words"] = new_anchors
        first_item["links"] = new_links
        first_item["update_time"] = get_today_date_str()
        first_item["access_count"] += 1
        # 过滤掉其他匹配项
        self.memory_data = [item for item in self.memory_data if item not in matched_items[1:]]
        # 替换第一个项
        for idx, item in enumerate(self.memory_data):
            if item == first_item:
                self.memory_data[idx] = first_item
                break
        save_to_json(self.file_path, self.memory_data)
        return True

    def get_long_memory_by_anchor(self, query_anchors):
        """通过锚点词检索长期记忆（全量+链接拓展）"""
        related_memory = []
        # 先过滤过期记忆
        valid_memory = [
            item for item in self.memory_data
            if get_date_diff_days(item["expire_date"], get_today_date_str()) > 0
        ]
        # 匹配锚点词/链接
        for item in valid_memory:
            if any(anchor in item["anchor_words"] for anchor in query_anchors):
                related_memory.append(item)
                item["access_count"] += 1
                continue
            for link in item["links"]:
                if any(anchor in link for anchor in query_anchors):
                    related_memory.append(item)
                    item["access_count"] += 1
                    break
        # 去重
        unique_memory = []
        seen_content = set()
        for item in related_memory:
            if item["content"] not in seen_content:
                seen_content.add(item["content"])
                unique_memory.append(item)
        # 保存访问次数更新
        save_to_json(self.file_path, self.memory_data)
        return unique_memory

    def get_active_topic_material(self):
        """提取主动发起话题的素材（高访问量记忆）"""
        # 过滤过期记忆
        valid_memory = [
            item for item in self.memory_data
            if get_date_diff_days(item["expire_date"], get_today_date_str()) > 0
        ]
        # 按访问次数排序，取前3条
        valid_memory.sort(key=lambda x: x["access_count"], reverse=True)
        return [item["content"] for item in valid_memory[:3]]

    def comb_memory(self):
        """梳理长期记忆：合并重复锚点、清理过期、优化链接"""
        from utils.file_operations import extract_anchor_words_via_model
        # 1. 清理过期记忆
        valid_memory = [
            item for item in self.memory_data
            if get_date_diff_days(item["expire_date"], get_today_date_str()) > 0
        ]
        # 2. 按锚点分组合并
        anchor_groups = {}
        for item in valid_memory:
            for anchor in item["anchor_words"]:
                if anchor not in anchor_groups:
                    anchor_groups[anchor] = []
                anchor_groups[anchor].append(item)
        # 3. 合并同锚点内容
        new_memory_data = []
        for anchor, items in anchor_groups.items():
            if len(items) <= 1:
                new_memory_data.extend(items)
                continue
            # 调用模型合并
            import subprocess
            combine_prompt = f"""
            请合并以下长期记忆内容，保留关键信息，精简冗余：
            {[item["content"] for item in items]}
            """
            result = subprocess.run(
                [f"{MEMORY_MODEL_PATH}/infer", "--prompt", combine_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            combined_content = result.stdout.strip()
            # 重新提取锚点和链接
            combined_anchors = extract_anchor_words_via_model(
                combined_content, MEMORY_MODEL_PATH, ANCHOR_WORD_MAX_NUM
            )
            combined_links = []
            for i in range(len(combined_anchors)):
                for j in range(i+1, len(combined_anchors)):
                    combined_links.append([combined_anchors[i], combined_anchors[j]])
            # 生成合并项
            combined_item = {
                "content": combined_content,
                "anchor_words": combined_anchors,
                "links": combined_links,
                "create_time": items[0]["create_time"],
                "update_time": get_today_date_str(),
                "expire_date": items[0]["expire_date"],
                "access_count": sum([item["access_count"] for item in items])
            }
            new_memory_data.append(combined_item)
        # 4. 保存
        self.memory_data = new_memory_data
        save_to_json(self.file_path, self.memory_data)
        # 5. 记录梳理日期
        self.comb_record = {"last_comb_date": get_today_date_str()}
        save_to_json(self.comb_record_path, self.comb_record)
        print("长期记忆梳理完成！")

    def check_need_comb(self):
        """检查是否需要梳理（每3天一次）"""
        last_comb_date = self.comb_record.get("last_comb_date", "")
        if not last_comb_date:
            self.comb_memory()
            return
        diff_days = get_date_diff_days(last_comb_date, get_today_date_str())
        if diff_days >= MEMORY_COMB_DAYS:
            self.comb_memory()