"""ASR Router 测试示例

演示如何使用 ASRBackend API 接口：

1. POST /asr/transcribe/bytes - 本地字节流识别
2. POST /asr/transcribe/url - URL 识别
3. POST /asr/transcribe/upload - 文件上传识别
"""

import requests
import tempfile
import os


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


def test_url():
    """测试 URL 转录 API"""
    base_url = "http://localhost:8003"
    url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"

    response = requests.post(f"{base_url}/asr/transcribe/url", data={"url": url})
    print("URL 转录结果:", response.json())


def test_bytes(file_path: str):
    """测试字节流转录 API"""
    base_url = "http://localhost:8003"

    with open(file_path, 'rb') as f:
        files = {"file": f}
        response = requests.post(f"{base_url}/asr/transcribe/bytes", files=files)
    print("字节流转录结果:", response.json())


def test_upload(file_path: str):
    """测试文件上传转录 API"""
    base_url = "http://localhost:8003"

    with open(file_path, 'rb') as f:
        files = {"file": f}
        response = requests.post(f"{base_url}/asr/transcribe/upload", files=files)
    print("文件上传转录结果:", response.json())


def main():
    """主测试函数"""
    print("ASR Router API 测试开始")

    url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
    temp_file_path = None

    try:
        # 下载音频文件
        temp_file_path = download_audio(url)
        print(f"下载测试音频文件到: {temp_file_path}")

        # 测试 URL 转录 API
        test_url()

        # 测试字节流转录 API（本地模式）
        test_bytes(temp_file_path)

        # 测试文件上传转录 API（云端模式）
        test_upload(temp_file_path)

    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        # 删除临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print("临时文件已删除")

    print("测试完成")


if __name__ == "__main__":
    main()
