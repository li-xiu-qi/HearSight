"""ASR Service 测试示例

演示如何使用 ASRBackend.services.asr_service.ASRService 的各种方法：

1. transcribe_from_bytes() - 从字节流进行本地识别
2. transcribe_from_url() - 从 URL 进行识别
3. transcribe_from_file_with_upload() - 上传文件到 Supabase 后进行云端识别
"""

import os
import sys
import asyncio
import requests
import tempfile

# 添加项目根目录到路径（HearSight目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ASRBackend.config import settings
from ASRBackend.services.asr_service import ASRService


def download_audio(url: str) -> str:
    """下载音频文件到临时目录"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.write(response.content)
    temp_file.close()

    return temp_file.name


async def test_url():
    """测试 URL 转录"""
    url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
    result = await ASRService.transcribe_from_url(url)
    print("URL 转录结果:", result)


async def test_bytes(audio_data: bytes):
    """测试字节流转录"""
    result = await ASRService.transcribe_from_bytes(audio_data, "test.wav")
    print("字节流转录结果:", result)


async def test_upload(audio_data: bytes):
    """测试文件上传转录"""
    result = await ASRService.transcribe_from_file_with_upload(audio_data, "test.wav")
    print("文件上传转录结果:", result)


async def main():
    """主测试函数"""
    print("ASR Service 测试开始")

    url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
    audio_data = None
    temp_file_path = None

    try:
        # 下载音频文件一次
        temp_file_path = download_audio(url)
        print(f"下载测试音频文件到: {temp_file_path}")

        # 读取文件内容
        with open(temp_file_path, 'rb') as f:
            audio_data = f.read()

        # 测试 URL 转录
        await test_url()

        # 测试字节流转录（本地模式）
        if settings.is_local_mode():
            await test_bytes(audio_data)

        # 测试文件上传转录（云端模式）
        if settings.is_cloud_mode():
            await test_upload(audio_data)

    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        # 删除临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print("临时文件已删除")

    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())
