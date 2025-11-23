"""记忆管理器"""

from typing import List, Dict, Any
from backend.config import settings
from backend.startup import get_llm_router


class MemoryManager:
    """对话记忆管理器

    负责监控对话上下文长度，自动进行记忆总结，避免超出LLM上下文限制。
    """

    def __init__(self, context_limit: int = None):
        """
        初始化记忆管理器

        参数:
            context_limit: 上下文长度限制，默认使用settings.llm_context_length
        """
        self.context_limit = context_limit or settings.llm_context_length or 8000
        self.conversation_summary = ""  # 对话总结
        self.message_buffer: List[Dict[str, str]] = []  # 消息缓冲区
        self.llm_router = get_llm_router()

    async def summarize_memory(self) -> str:
        """
        生成记忆总结

        使用增量总结策略，基于当前摘要和新对话内容生成更新后的摘要。

        返回:
            新的对话摘要
        """
        # 获取需要总结的消息（除了系统消息）
        dialogue_messages = [msg for msg in self.message_buffer if msg["role"] != "system"]

        if not dialogue_messages:
            return self.conversation_summary

        # 构建对话内容文本
        dialogue_content = ""
        for msg in dialogue_messages:
            role = "用户" if msg["role"] == "user" else "助手"
            dialogue_content += f"{role}：{msg['content']}\n\n"

        # 使用增量总结提示词
        if self.conversation_summary:
            # 有现有摘要时的增量总结
            prompt = f"""请逐步总结提供的对话内容，将其补充到之前的摘要中并返回一个新的摘要。

示例：
当前摘要：
用户询问了人工智能的发展现状。

新的对话内容：
用户：人工智能在医疗领域有哪些应用？
助手：人工智能在医疗领域可以帮助诊断疾病、分析医学影像、药物研发等方面。

新摘要：
用户询问了人工智能的发展现状和医疗应用，AI在医疗领域可以帮助诊断疾病、分析医学影像和药物研发。

当前摘要：
{self.conversation_summary}

新的对话内容：
{dialogue_content}

新摘要："""
        else:
            # 首次总结时的处理
            prompt = f"""请总结以下对话内容，提取关键信息并生成简洁的摘要。

对话内容：
{dialogue_content}

要求：
1. 总结对话的主要话题和结论
2. 保留重要的事实和观点
3. 保持摘要简洁明了
4. 突出对话的核心内容

摘要："""

        try:
            response = self.llm_router.completion(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            new_summary = response.choices[0].message.content.strip()

            # 更新摘要
            self.conversation_summary = new_summary

            # 压缩消息缓冲区，保留系统消息和最近几条消息
            self._compress_message_buffer()

            return new_summary

        except Exception as e:
            # 总结失败时，使用简单的压缩策略
            self._compress_message_buffer()
            return f"对话历史已压缩（总结失败：{str(e)}）"

    def _compress_message_buffer(self) -> None:
        """
        压缩消息缓冲区，保留系统消息和最近的对话轮次

        策略：
        - 保留所有系统消息
        - 保留最近5轮对话（10条消息：5个用户问题 + 5个助手回复）
        - 确保至少保留最近的用户问题
        """
        system_messages = [msg for msg in self.message_buffer if msg["role"] == "system"]
        non_system_messages = [msg for msg in self.message_buffer if msg["role"] != "system"]

        # 保留最近5轮对话（10条消息：5个用户问题 + 5个助手回复）
        # 但至少要保留最近的用户问题
        recent_messages = non_system_messages[-10:]  # 最近10条消息

        # 确保至少有最近的用户问题
        user_messages = [msg for msg in recent_messages if msg["role"] == "user"]
        if not user_messages:
            # 如果没有用户消息，保留最近的一条非系统消息（通常是用户问题）
            recent_messages = non_system_messages[-1:] if non_system_messages else []

        self.message_buffer = system_messages + recent_messages

    def add_message(self, message: Dict[str, str]) -> None:
        """
        添加新消息到缓冲区

        参数:
            message: 消息字典，包含role和content
        """
        self.message_buffer.append(message)

    def should_summarize(self) -> bool:
        """
        检查是否需要总结记忆

        返回:
            是否需要总结
        """
        # 计算当前消息总长度
        total_length = self._calculate_total_length()

        # 当长度超过80%的阈值时触发总结
        threshold = int(self.context_limit * 0.8)
        return total_length > threshold

    def get_context_messages(self) -> List[Dict[str, str]]:
        """
        获取当前上下文消息

        如果有总结，则返回系统提示+总结+最新消息
        否则返回所有消息

        返回:
            上下文消息列表
        """
        if self.conversation_summary:
            # 有总结时，只返回系统消息和当前问题
            system_messages = [msg for msg in self.message_buffer if msg["role"] == "system"]
            user_messages = [msg for msg in self.message_buffer if msg["role"] == "user"]

            if system_messages and user_messages:
                # 更新系统消息包含总结
                updated_system = system_messages[0].copy()
                updated_system["content"] = updated_system["content"] + f"\n\n对话历史总结：\n{self.conversation_summary}"

                return [updated_system, user_messages[-1]]  # 只保留最新的用户问题

        return self.message_buffer

    def _calculate_total_length(self) -> int:
        """
        计算消息缓冲区中所有消息的总长度

        返回:
            总字符数
        """
        total = 0
        for message in self.message_buffer:
            total += len(message.get("content", ""))
        return total

    def reset_memory(self) -> None:
        """重置记忆，清空总结和消息缓冲区"""
        self.conversation_summary = ""
        self.message_buffer = []