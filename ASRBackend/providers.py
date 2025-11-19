"""ASR 提供者工厂模块

定义抽象的 ASR 提供者接口和具体实现，支持本地和云端两种模式。
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import sys
import os

# 添加项目根目录到 Python 路径（开发环境）
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ASRBackend.config import settings
except ImportError:
    # 相对导入（生产环境）
    from .config import settings


class ASRProvider(ABC):
    """ASR 提供者抽象基类"""

    @abstractmethod
    async def transcribe_file(self, audio_path: str) -> Dict[str, Any]:
        """转录本地音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            转录结果字典
        """
        pass

    @abstractmethod
    async def transcribe_url(self, url: str) -> Dict[str, Any]:
        """转录 URL 音频文件

        Args:
            url: 音频文件 URL

        Returns:
            转录结果字典
        """
        pass

    @abstractmethod
    async def transcribe_bytes(
        self, audio_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """转录二进制音频数据

        Args:
            audio_data: 音频二进制数据
            filename: 文件名

        Returns:
            转录结果字典
        """
        pass


class LocalASRProvider(ASRProvider):
    """本地 ASR 提供者（使用 FunASR）"""

    def __init__(self):
        """初始化本地 ASR 提供者"""
        self._initialized = False
        self._process = None

    async def _ensure_initialized(self) -> None:
        """确保本地模型已加载"""
        if not self._initialized:
            # 动态导入本地模块以避免启用云端模式时的依赖问题
            from .asr_functions.asr_sentence_segments import process
            from .asr_functions.segment_normalizer import extract_text
            from .asr_functions.utils import detect_language

            self._process = process
            self._extract_text = extract_text
            self._detect_language = detect_language
            self._initialized = True

    async def transcribe_file(self, audio_path: str) -> Dict[str, Any]:
        """转录本地音频文件"""
        await self._ensure_initialized()

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._process, audio_path
            )

            if not result:
                return {"status": "error", "error": "无法处理的音频格式"}

            text_content = self._extract_text(result)
            language = self._detect_language(text_content)

            return {
                "text": text_content,
                "language": language,
                "segments": result,
                "status": "success",
            }
        except Exception as e:
            return {
                "error": f"语音识别失败: {str(e)}",
                "status": "error",
            }

    async def transcribe_url(self, url: str) -> Dict[str, Any]:
        """转录 URL 音频文件"""
        return await self.transcribe_file(url)

    async def transcribe_bytes(
        self, audio_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """转录二进制音频数据"""
        import os
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(filename)[1]
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                result = await self.transcribe_file(temp_file_path)
                result["filename"] = filename
                return result
            finally:
                os.unlink(temp_file_path)

        except Exception as e:
            return {
                "filename": filename,
                "error": f"语音识别失败: {str(e)}",
                "status": "error",
            }


class CloudASRProvider(ASRProvider):
    """云端 ASR 提供者（使用 DashScope）"""

    def __init__(self):
        """初始化云端 ASR 提供者"""
        self._initialized = False
        self._transcribe_audio = None
        self._extract_text = None
        self._detect_language = None

    async def _ensure_initialized(self) -> None:
        """确保云端 API 已初始化"""
        if not self._initialized:
            # 动态导入云端模块
            from .asr_functions.dashscope_paraformer_v2_transcription import (
                initialize_dashscope_client,
                transcribe_audio_from_url,
            )
            from .asr_functions.segment_normalizer import extract_text
            from .asr_functions.utils import detect_language

            if settings.dashscope_api_key:
                initialize_dashscope_client(settings.dashscope_api_key)

            self._transcribe_audio = transcribe_audio_from_url
            self._extract_text = extract_text
            self._detect_language = detect_language
            self._initialized = True

    async def transcribe_file(self, audio_path: str) -> Dict[str, Any]:
        """云端模式不支持本地文件"""
        return {
            "status": "error",
            "error": "云端模式不支持本地文件，请使用 URL 或二进制数据",
        }

    async def transcribe_url(self, url: str) -> Dict[str, Any]:
        """转录 URL 音频文件"""
        await self._ensure_initialized()

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._transcribe_audio,
                url,
                settings.dashscope_model,
                settings.dashscope_language_hints.split(","),
                600,
            )
            # 如果下游函数返回带有 status=error 的 dict，直接返回错误信息
            if isinstance(result, dict) and result.get("status") == "error":
                return result

            if isinstance(result, dict) and result.get("status") == "success":
                segments = result.get("segments")
                text_content = result.get("text") or self._extract_text(segments or [])
                language = result.get("language") or self._detect_language(text_content)
                return {
                    "text": text_content,
                    "language": language,
                    "segments": segments,
                    "status": "success",
                }

            return {"status": "error", "error": "转录失败"}

        except Exception as e:
            return {
                "error": f"语音识别失败: {str(e)}",
                "status": "error",
            }

    async def transcribe_bytes(
        self, audio_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """云端模式需要先上传到 URL"""
        return {
            "filename": filename,
            "status": "error",
            "error": "云端模式需要音频 URL，如需上传二进制文件，请先上传到云存储后提供 URL",
        }


class ASRProviderFactory:
    """ASR 提供者工厂类"""

    _provider: Optional[ASRProvider] = None

    @classmethod
    def get_provider(cls) -> ASRProvider:
        """获取当前配置的 ASR 提供者实例"""
        if cls._provider is None:
            if settings.is_cloud_mode():
                cls._provider = CloudASRProvider()
            else:
                cls._provider = LocalASRProvider()

        return cls._provider

    @classmethod
    def reset_provider(cls) -> None:
        """重置提供者（用于测试）"""
        cls._provider = None
