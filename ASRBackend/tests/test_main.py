"""测试 ASR Backend API"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ASRBackend.config import settings
from ASRBackend.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "ASR Backend"


def test_get_asr_info():
    """测试 ASR 信息接口"""
    response = client.get("/asr/info")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "debug" in data
    assert "description" in data
    assert data["mode"] == settings.asr_mode


def test_transcribe_audio_url():
    """测试 URL 转录接口（支持所有模式）"""
    test_url = "https://example.com/audio.wav"

    mock_result = {
        "filename": "audio.wav",
        "text": "这是 URL 测试文本",
        "language": "zh",
        "segments": [
            {
                "index": 1,
                "spk_id": "0",
                "sentence": "这是 URL 测试文本",
                "start_time": 0.0,
                "end_time": 2.0,
            }
        ],
        "status": "success",
    }

    with patch(
        "ASRBackend.services.asr_service.ASRService.transcribe_audio_from_url"
    ) as mock_transcribe:
        mock_transcribe.return_value = mock_result

        response = client.post(
            "/asr/transcribe",
            data={"url": test_url},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == mock_result

        mock_transcribe.assert_called_once_with(test_url)


def test_transcribe_no_params():
    """测试缺少参数的情况"""
    response = client.post("/asr/transcribe")

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "必须提供" in data["detail"]


def test_transcribe_both_params():
    """测试同时提供文件和 URL 的情况"""
    mock_audio_data = b"fake audio data"
    test_url = "https://example.com/audio.wav"

    response = client.post(
        "/asr/transcribe",
        files={"file": ("test.wav", mock_audio_data, "audio/wav")},
        data={"url": test_url},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "不能同时提供" in data["detail"]
