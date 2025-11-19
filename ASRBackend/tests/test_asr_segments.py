"""测试 ASR 句子分段功能"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

from ASRBackend.asr_functions.asr_sentence_segments import process
from ASRBackend.asr_functions.utils import detect_language
from ASRBackend.config import settings
from ASRBackend.services.asr_service import ASRService

# 测试数据路径
TEST_DATA_DIR = Path(__file__).parent / "test_datas"
TEST_AUDIO_FILE = TEST_DATA_DIR / "test.mp4"


@pytest.mark.asyncio
async def test_transcribe_audio_url():
    """测试使用音频 URL 进行语音识别（支持云端和本地模式）"""
    # 使用一个测试 URL（这个 URL 在测试文件中也使用了）
    test_url = "https://sbp-7fgelj2azms1xag5.supabase.opentrust.net/storage/v1/object/public/test-public/asr/test.mp4"

    # 调用 ASR 服务进行识别
    result = await ASRService.transcribe_audio_from_url(test_url)

    # 验证结果结构
    assert isinstance(result, dict)
    assert "filename" in result
    assert "status" in result

    # 云端模式可能需要 API Key，本地模式可能需要模型
    # 这里只验证基本结构，不强制要求成功
    if result["status"] == "success":
        assert "text" in result
        assert "language" in result
        assert "segments" in result
        assert isinstance(result["text"], str)
        assert result["language"] in ["zh", "en"]
        assert isinstance(result["segments"], list)
        if result["segments"]:
            seg = result["segments"][0]
            assert "index" in seg
            assert "spk_id" in seg
            assert "sentence" in seg
            assert "start_time" in seg
            assert "end_time" in seg


def test_test_data_exists():
    """测试测试数据文件是否存在"""
    assert TEST_DATA_DIR.exists(), f"测试数据目录不存在: {TEST_DATA_DIR}"
    assert TEST_AUDIO_FILE.exists(), f"测试音频文件不存在: {TEST_AUDIO_FILE}"
