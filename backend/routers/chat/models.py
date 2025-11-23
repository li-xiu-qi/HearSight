# -*- coding: utf-8 -*-
"""聊天路由的数据模型"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from typing_extensions import TypedDict

from backend.schemas import Segment, SummaryItem


class SummarizeRequest(TypedDict, total=False):
    """总结请求数据结构"""

    segments: List[Segment]  # 句子片段列表
    api_key: str  # OpenAI API密钥
    base_url: str  # OpenAI API基础URL
    model: str  # 使用的模型


class SummarizeResponse(TypedDict):
    """总结响应数据结构"""

    summaries: List[SummaryItem]  # 总结项列表


class ChatRequest(TypedDict, total=False):
    """聊天请求数据结构"""

    segments: List[Segment]  # 句子片段列表
    question: str  # 问题内容
    api_key: str  # OpenAI API密钥
    base_url: str  # OpenAI API基础URL
    model: str  # 使用的模型
    transcript_ids: Optional[List[int]]  # 可选，转录ID列表，用于知识库检索（支持单视频或多视频）


class ChatResponse(TypedDict):
    """聊天响应数据结构"""

    answer: str  # 回答内容


class SaveSummariesRequest(BaseModel):
    """保存总结的请求体"""

    summaries: List[SummaryItem]


class SaveSummariesResponse(TypedDict):
    """保存总结响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    saved: bool  # 是否已保存
    transcript_id: int  # 转录ID


class GetSummariesResponse(TypedDict):
    """获取总结响应数据结构"""

    summaries: Optional[List[SummaryItem]]  # 总结项列表，可能为None
    has_summaries: bool  # 是否有总结


class ChatMessage(TypedDict):
    """聊天消息数据结构"""

    role: str  # 消息角色 (user/assistant)
    content: str  # 消息内容
    timestamp: Optional[str]  # 时间戳


class SaveChatMessagesRequest(BaseModel):
    """保存聊天消息的请求体"""

    messages: List[Dict]


class SaveChatMessagesResponse(TypedDict):
    """保存聊天消息响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    transcript_id: int  # 转录ID


class GetChatMessagesResponse(TypedDict):
    """获取聊天消息响应数据结构"""

    messages: Optional[List[Dict]]  # 聊天消息列表，可能为None
    has_messages: bool  # 是否有消息


class ClearChatMessagesResponse(TypedDict):
    """清空聊天消息响应数据结构"""

    success: bool  # 是否成功
    message: str  # 响应消息
    transcript_id: int  # 转录ID