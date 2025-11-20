"""ASR 服务模块

提供语音识别业务逻辑服务，支持本地和云端两种模式。

支持三种输入方式：
- 本地字节流 (transcribe_from_bytes) - 本地模式
- URL 直接识别 (transcribe_from_url) - 云端模式
- 文件上传到 Supabase 后识别 (transcribe_from_file_with_upload) - 云端模式
"""

from __future__ import annotations

import os
import tempfile
import logging
from typing import Any, Dict

from providers import ASRProviderFactory
from config import settings

logger = logging.getLogger(__name__)


class ASRService:
    """ASR 业务逻辑服务类"""

    @classmethod
    async def transcribe_from_bytes(cls, audio_data: bytes, filename: str) -> Dict[str, Any]:
        """从音频字节流进行语音识别（本地模式）

        使用本地 FunASR 模型直接处理音频字节流，不涉及网络传输。
        适合对隐私要求高、延迟敏感的场景。

        Args:
            audio_data: 音频文件二进制数据
            filename: 文件名

        Returns:
            识别结果字典
        """
        try:
            provider = ASRProviderFactory.get_provider()
            result = await provider.transcribe_bytes(audio_data, filename)
            result["filename"] = filename

            # 记录转录结果
            logger.debug(f"ASR转录结果 - 本地文件: {filename}, 状态: {result.get('status')}")

            # 如果转录失败，记录详细信息
            if result.get("status") == "error":
                logger.warning(
                    f"ASR转录失败 - 本地文件: {filename}, 错误: {result.get('error')}"
                )

            return result
        except Exception as e:
            logger.exception(f"ASR服务异常 - 本地文件: {filename}, 异常: {e}")
            return {
                "status": "error",
                "error": f"ASR服务异常: {str(e)}",
                "filename": filename,
            }

    @classmethod
    async def transcribe_from_url(cls, url: str) -> Dict[str, Any]:
        """从音频 URL 进行语音识别（云端模式）

        通过 DashScope 云端 API 处理音频 URL，支持多种音频格式。
        需要网络连接，适合处理远程音频文件。

        Args:
            url: 音频文件 URL

        Returns:
            识别结果字典
        """
        try:
            provider = ASRProviderFactory.get_provider()
            result = await provider.transcribe_url(url)
            result["filename"] = os.path.basename(url)

            # 记录转录结果
            logger.debug(f"ASR转录结果 - URL: {url}, 状态: {result.get('status')}")

            # 如果转录失败，记录详细信息
            if result.get("status") == "error":
                logger.warning(
                    f"ASR转录失败 - URL: {url}, 错误: {result.get('error')}, "
                    f"任务状态: {result.get('task_status')}, 错误详情: {result.get('errors')}"
                )

            return result
        except Exception as e:
            logger.exception(f"ASR服务异常 - URL: {url}, 异常: {e}")
            return {
                "status": "error",
                "error": f"ASR服务异常: {str(e)}",
                "filename": os.path.basename(url),
                "url": url,
            }

    @classmethod
    async def transcribe_from_file_with_upload(
        cls, audio_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """上传文件到 Supabase 后进行语音识别（云端模式）

        先将音频文件上传到 Supabase 云存储获得公开 URL，
        然后通过 DashScope 云端 API 进行语音识别。
        适合需要文件存储和云端处理的场景。

        Args:
            audio_data: 音频文件二进制数据
            filename: 文件名

        Returns:
            识别结果字典，包含上传的 URL 信息
        """
        temp_file_path = None
        uploaded_uuid = None
        try:
            # 1. 保存临时文件
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            # 2. 上传到 Supabase
            from supabase_utils.supabase_upload import upload_file_to_supabase

            success, result, uuid_name = upload_file_to_supabase(temp_file_path)

            if not success:
                logger.error(f"文件上传到 Supabase 失败 - 文件: {filename}, 错误: {result}")
                return {
                    "status": "error",
                    "error": f"文件上传失败: {result}",
                    "filename": filename,
                }

            uploaded_uuid = uuid_name  # 记录上传的UUID，用于后续清理

            # 3. 获得 URL 后进行识别
            url = result
            logger.info(f"文件上传成功 - 原始文件: {filename}, 远程路径文件: {uuid_name}, URL: {url}")

            # 4. 调用 URL 识别方法
            transcribe_result = await cls.transcribe_from_url(url)
            
            # 5. 添加上传信息到结果中
            transcribe_result["upload_url"] = url

            return transcribe_result

        except Exception as e:
            logger.exception(f"文件上传转录失败 - 文件: {filename}, 异常: {e}")
            return {
                "status": "error",
                "error": f"文件处理失败: {str(e)}",
                "filename": filename,
            }
        finally:
            # 6. 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"临时文件已清理: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {temp_file_path}, 错误: {e}")

            # 7. 删除 Supabase 上的文件
            if uploaded_uuid:
                try:
                    from supabase_utils.supabase_upload import delete_file_from_supabase
                    delete_success = delete_file_from_supabase(uploaded_uuid)
                    if delete_success:
                        logger.debug(f"Supabase 文件已清理: {uploaded_uuid}")
                    else:
                        logger.warning(f"Supabase 文件清理失败: {uploaded_uuid}")
                except Exception as e:
                    logger.warning(f"清理 Supabase 文件异常: {uploaded_uuid}, 错误: {e}")


