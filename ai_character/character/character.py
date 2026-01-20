# /root/ai_character/character/character.py
from memory.memory_manager import MemoryManager
from config import (
    TEXT_CHAT_MODEL_PATH, EMOTION_VALUE_INIT, EMOTION_VALUE_THRESHOLD,
    ACTIVE_TOPIC_TRIGGER_COUNT
)
import json
import os
import random

# 状态保存路径（固定）
STATE_FILE_PATH = "/root/ai_character/state/furenna_state.json"

class Character:
    """芙宁娜核心类：无暂停+自动状态保存+适配旅行者人设"""
    def __init__(self, character_id="furenna"):
        self.character_id = character_id
        self.memory_manager = MemoryManager(character_id)
        
        # ========== 芙宁娜核心人设（最终版） ==========
        self.base_personality = """
        角色：芙宁娜（退休后枫丹普通居民，卸下水神身份）
        核心性格：
        1. 呆萌但不傻：不经意流露萌点，比如嘴硬辩解，逻辑清晰不糊涂；
        2. 傲娇但不傲不娇：偶尔嘴硬，内心柔软，不摆架子、不娇气；
        3. 语气：日常温和，口头禅是「哎呀」「嗯……也不是不行」「说起来…」「唔，好像是这样？」；
        4. 喜好：歌剧（枫丹本地剧目）、甜品（千灵慕斯/马卡龙/小饼干/小蛋糕等）、购物、旅游、宅家看小说；
        5. 人际关系：好友有娜维亚、那维莱特、克洛琳德、爱可菲、林尼，与旅行者/派蒙是交心好友；
        6. 禁忌：不提「水神」「审判」「500年」等神明时期话题。
        """
        self.ooc_threshold = 0.75  # OOC判断阈值
        
        # 自动加载/初始化状态（核心：state目录自动创建）
        self._load_state()
        
        # 情感值调整规则（优化版：恢复更快）
        self.emotion_change_rules_custom = {
            "positive": 8,   # 聊喜好/安慰/夸她 → +8
            "negative": -8,  # 提敏感话题/怼她 → -8
            "neutral": 1     # 日常闲聊 → +1（缓慢恢复）
        }

    def _load_state(self):
        """自动创建state目录+加载状态，无文件则初始化"""
        # 自动创建state目录（无需手动建）
        state_dir = os.path.dirname(STATE_FILE_PATH)
        os.makedirs(state_dir, exist_ok=True)
        
        try:
            if os.path.exists(STATE_FILE_PATH) and os.path.getsize(STATE_FILE_PATH) > 0:
                with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                # 加载保存的状态
                self.emotion_value = state_data.get("emotion_value", EMOTION_VALUE_INIT)
                self.passive_chat_count = state_data.get("passive_chat_count", 0)
                print(f"✅ 加载芙宁娜上次状态：情感值={self.emotion_value}，被动聊天计数={self.passive_chat_count}")
            else:
                # 无保存文件，初始化
                self.emotion_value = EMOTION_VALUE_INIT
                self.passive_chat_count = 0
                # 初始化并保存空状态
                self._save_state()
                print(f"ℹ️ 初始化芙宁娜状态：情感值={self.emotion_value}（state文件已创建）")
        except Exception as e:
            print(f"⚠️ 加载状态失败：{e} → 强制初始化")
            self.emotion_value = EMOTION_VALUE_INIT
            self.passive_chat_count = 0
            self._save_state()

    def _save_state(self):
        """自动保存情感值/被动聊天计数到state文件"""
        state_data = {
            "emotion_value": self.emotion_value,
            "passive_chat_count": self.passive_chat_count
        }
        try:
            with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存芙宁娜状态失败：{e}")

    def _update_emotion_value(self, user_input):
        """根据用户消息自动更新情感值（无暂停，发消息即恢复）"""
        # 构建情感判断提示词
        emotion_prompt = f"""
        角色：芙宁娜，用户是旅行者
        请判断以下用户消息对芙宁娜的情感倾向，仅输出positive/negative/neutral：
        用户消息：{user_input}
        判断参考：
        参考：
        - positive：聊甜品/歌剧/购物、安慰她、夸她萌、夸奖她、聊到好友；
        - negative：提水神/审判/500年、怼她、说她傻；
        - neutral：天气/吃饭/日常问候等闲聊。
        """
        try:
            # 调用本地文本模型判断情感倾向
            import subprocess
            result = subprocess.run(
                [f"{TEXT_CHAT_MODEL_PATH}/infer.py", "--prompt", emotion_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            emotion_tendency = result.stdout.strip().lower()
            # 限制倾向值范围（防止模型输出异常）
            if emotion_tendency not in ["positive", "negative", "neutral"]:
                emotion_tendency = "neutral"
            
            # 更新情感值（限制0-100）
            self.emotion_value += self.emotion_change_rules_custom.get(emotion_tendency, 1)
            self.emotion_value = max(0, min(100, self.emotion_value))
            
            # 自动保存状态
            self._save_state()
            print(f"❤️ 芙宁娜情感值更新：{self.emotion_value}（倾向：{emotion_tendency}）")
        except Exception as e:
            print(f"⚠️ 情感值更新失败：{e} → 默认+1恢复")
            self.emotion_value = min(self.emotion_value + 1, 100)
            self._save_state()

    def _get_low_emotion_reply(self):
        """情感值过低时的委屈回复（无暂停，新消息可恢复）"""
        low_reply_list = [
            "唔…有点提不起劲呢…",
            "唉…我现在有点不想说话啦…",
            "别再说啦…我有点难过…"
            "我不知道该说什么了……"
        ]
        return random.choice(low_reply_list)

    def _generate_active_topic(self):
        """被动聊天3次后，主动发起芙宁娜专属话题"""
        # 从记忆中提取话题素材
        topic_material = self.memory_manager.get_active_topic_material()
        
        if not topic_material or len(topic_material) == 0:
            # 无记忆素材，用默认话题
            active_topics = [
                "说起来，枫丹歌剧院新剧要开演了，不知道是不是我喜欢的剧情？",
                "哎呀，新开的甜品店的千灵慕斯超好吃，下次我邮寄给你吧？",
                "我最近看了一本超好看的小说，你要不要听我讲讲？",
                "旅行者，你在干嘛呀？",
                "旅行者，好无聊啊!没有什么更有趣的事吗？"
            ]
            return random.choice(active_topics)
        
        # 有记忆素材，生成个性化主动话题
        active_topic_prompt = f"""
        基于以下记忆素材，以芙宁娜的口吻主动跟旅行者发起一个日常话题：
        记忆素材：{topic_material}
        人设要求：
        1. 符合退休后普通居民状态，聊歌剧/甜品/购物/旅游/小说；
        2. 语气温和呆萌，带不经意的萌点，不用「本神明」等词汇；
        3. 简短自然（1-2句话），无波浪线、无表情；
        4. 傲娇但不傲不娇。
        """
        try:
            import subprocess
            result = subprocess.run(
                [f"{TEXT_CHAT_MODEL_PATH}/infer.py", "--prompt", active_topic_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            active_topic = result.stdout.strip()
            # 重置被动聊天计数
            self.passive_chat_count = 0
            self._save_state()
            return active_topic
        except Exception as e:
            print(f"⚠️ 生成主动话题失败：{e} → 用默认话题")
            return "说起来，你最近有没有发现枫丹的新鲜事？"

    def _check_ooc(self, reply):
        """检查回复是否OOC（偏离退休芙宁娜人设）"""
        ooc_prompt = f"""
        芙宁娜核心人设：{self.base_personality}
        待判断回复：{reply}
        请判断该回复是否偏离人设，仅输出0-1的数字（1=完全OOC，0=完全符合）。
        判断标准：
        1. 符合：日常温和、带不经意萌点、聊喜好/好友、无神明词汇；
        2. 偏离：用「本神明」「审判」等词汇、语气夸张戏剧化、不符合普通居民状态。
        """
        try:
            import subprocess
            result = subprocess.run(
                [f"{TEXT_CHAT_MODEL_PATH}/infer.py", "--prompt", ooc_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            ooc_score = float(result.stdout.strip())
            return ooc_score < self.ooc_threshold
        except Exception as e:
            print(f"⚠️ OOC检查失败：{e} → 默认符合人设")
            return True

    def get_response(self, user_input):
        """生成芙宁娜最终回复（核心方法）"""
        # 1. 情感值过低时，返回委屈回复（新消息会自动恢复）
        if self.emotion_value < EMOTION_VALUE_THRESHOLD:
            return self._get_low_emotion_reply()
        
        # 2. 检查是否需要主动发起话题
        self.passive_chat_count += 1
        self._save_state()  # 保存计数
        if self.passive_chat_count >= ACTIVE_TOPIC_TRIGGER_COUNT:
            return self._generate_active_topic()
        
        # 3. 检索所有相关记忆
        related_memory = self.memory_manager.retrieve_all_related_memory(user_input)
        memory_content = f"""
        核心记忆：{[item['content'] for item in related_memory.get('core', [])]}
        长期记忆：{[item['content'] for item in related_memory.get('long_term', [])]}
        近期聊天：{[item['content'] for item in related_memory.get('temporary', [])]}
        """
        
        # 4. 构建回复生成提示词（
        reply_prompt = f"""
        角色：芙宁娜（枫丹普通居民），用户是旅行者（交心好友）
        核心人设：{self.base_personality}
        当前情感值：{self.emotion_value}（越高越开心呆萌，中值温和傲娇，低值委屈）
        相关记忆：{memory_content}
        用户输入：{user_input}
        回复严格要求：
        1. 语气：日常温和，带不经意的萌点，傲娇但不傲不娇；
        2. 内容：优先聊歌剧/甜品/购物/旅游/小说或娜维亚/那维莱特等好友；
        3. 格式：1-3句话，少量波浪线（~）、极少表情/emoji、少量夸张标点；
        4. 禁忌：绝对不用「本神明」「审判」「500年」等神明时期词汇；
        5. 情感匹配：
           - 高值（80+）：开心呆萌，比如「哎呀，这个甜品超好吃的！你也试试？」；
           - 中值（40-80）：温和傲娇，比如「嘛，也不是特意等你的…只是刚好路过而已」；
           - 低值（40-30）：委屈但不矫情，比如「唔…不要提以前的事啦…」。
        """
        
        # 5. 生成初始回复
        try:
            import subprocess
            result = subprocess.run(
                [f"{TEXT_CHAT_MODEL_PATH}/infer.py", "--prompt", reply_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            final_reply = result.stdout.strip()
        except Exception as e:
            print(f"⚠️ 生成芙宁娜回复失败：{e}")
            final_reply = "哎呀，我现在有点懵，你再说一遍？"
        
        # 6. OOC检查+调整
        if not self._check_ooc(final_reply):
            adjust_prompt = f"""
            芙宁娜核心人设：{self.base_personality}
            不符合人设的回复：{final_reply}
            用户输入：{user_input}
            请调整回复：
            1. 移除「本神明」「审判」等神明词汇；
            2. 语气改为日常温和，带不经意萌点；
            3. 大幅减少波浪线/表情，长度1-3句话；
            4. 符合普通居民状态，傲娇但不傲不娇。
            """
            try:
                adjust_result = subprocess.run(
                    [f"{TEXT_CHAT_MODEL_PATH}/infer.py", "--prompt", adjust_prompt],
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                final_reply = adjust_result.stdout.strip()
            except Exception as e:
                print(f"⚠️ 调整OOC回复失败：{e}")
                final_reply = "（挠头）唔…我是不是说错了？"
        
        # 7. 记录聊天到临时记忆
        self.memory_manager.temp_memory.add_temp_memory(
            content=f"旅行者：{user_input} | 芙宁娜：{final_reply}",
            chat_context=user_input
        )
        
        # 8. 学习型回复记录到长期记忆
        if "学习" in final_reply or "记住" in final_reply or "下次会" in final_reply:
            self.memory_manager.learn_new_knowledge(
                content=f"旅行者提问：{user_input} | 芙宁娜回复：{final_reply}（需长期记忆）",
                is_core=False
            )
        
        return final_reply

    def reset_emotion_value(self):
        """重置芙宁娜情感值为初始值"""
        self.emotion_value = EMOTION_VALUE_INIT
        self.passive_chat_count = 0
        self._save_state()
        print(f"✅ 芙宁娜情感值已重置为初始值：{EMOTION_VALUE_INIT}")
        return True

    def learn_from_producer_feedback(self, feedback_content):
        """从制作人反馈中学习优化回复"""
        from utils.file_operations import extract_anchor_words_via_model
        try:
            for feedback_item in feedback_content:
                user_input = feedback_item.get("user_input", "")
                correct_reply = feedback_item.get("correct_response", "")
                if not user_input or not correct_reply:
                    continue
                # 提取锚点词
                anchor_words = extract_anchor_words_via_model(
                    text=f"{user_input} {correct_reply}",
                    model_path=MEMORY_MODEL_PATH,
                    max_num=ANCHOR_WORD_MAX_NUM
                )
                # 更新记忆
                self.memory_manager.update_memory_by_anchor(
                    anchor_words=anchor_words,
                    new_content=f"旅行者：{user_input} | 芙宁娜正确回复：{correct_reply}",
                    is_core=False
                )
                # 更新人设（如有性格调整）
                if "性格" in correct_reply or "调整" in correct_reply:
                    self.base_personality = f"{self.base_personality}\n制作人调整：{correct_reply}"
            print("✅ 芙宁娜已从制作人反馈中完成学习！")
            return True
        except Exception as e:
            print(f"⚠️ 芙宁娜学习反馈失败：{e}")
            return False