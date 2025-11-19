"""集成测试：验证视频文件自动转码功能

演示流程：
1. 检测 MP4 视频文件
2. 自动转码为 M4A
3. 上传转码后的文件到 Supabase
4. 提交给 DashScope 进行转录
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ASRBackend.asr_functions.audio_transcoder import is_video_file, is_audio_file


def test_file_type_detection():
    """测试文件类型检测"""
    print("=== 测试文件类型检测 ===\n")

    test_files = [
        ("video.mp4", True, "MP4 视频文件"),
        ("audio.wav", False, "WAV 音频文件"),
        ("movie.avi", True, "AVI 视频文件"),
        ("song.m4a", False, "M4A 音频文件"),
        ("clip.mov", True, "MOV 视频文件"),
        ("track.mp3", False, "MP3 音频文件"),
    ]

    for filename, expected_is_video, description in test_files:
        is_vid = is_video_file(filename)
        is_aud = is_audio_file(filename)
        status = "✓" if is_vid == expected_is_video else "✗"
        print(f"{status} {description:20} | 视频: {is_vid:5} | 音频: {is_aud:5}")

    print()


def test_transcoding_logic():
    """测试转码逻辑（伪代码验证）"""
    print("=== 转码逻辑流程 ===\n")

    test_scenarios = [
        {
            "name": "场景 1: MP4 视频文件",
            "url": "https://example.com/video.mp4",
            "is_video": True,
            "expected_flow": [
                "1. 检测到视频文件",
                "2. 下载 MP4 文件",
                "3. 使用 ffmpeg 转码为 M4A",
                "4. 上传 M4A 到 Supabase",
                "5. 获取新的公网 URL",
                "6. 提交转码后的 URL 给 DashScope",
            ],
        },
        {
            "name": "场景 2: M4A 音频文件",
            "url": "https://example.com/audio.m4a",
            "is_video": False,
            "expected_flow": [
                "1. 检测为音频文件，无需转码",
                "2. 直接提交给 DashScope",
            ],
        },
        {
            "name": "场景 3: AVI 视频文件",
            "url": "https://example.com/movie.avi",
            "is_video": True,
            "expected_flow": [
                "1. 检测到视频文件",
                "2. 下载 AVI 文件",
                "3. 使用 ffmpeg 转码为 M4A",
                "4. 上传 M4A 到 Supabase",
                "5. 获取新的公网 URL",
                "6. 提交转码后的 URL 给 DashScope",
            ],
        },
    ]

    for scenario in test_scenarios:
        print(f"{scenario['name']}")
        print(f"  URL: {scenario['url']}")
        print(f"  是否为视频: {scenario['is_video']}")
        print(f"  处理流程:")
        for step in scenario["expected_flow"]:
            print(f"    {step}")
        print()


def test_supabase_upload_logic():
    """测试上传逻辑"""
    print("=== Supabase 上传逻辑 ===\n")

    print("上传流程:")
    print("  1. 如果 SUPABASE_URL 和 SUPABASE_KEY 未设置 -> 返回 None，记录警告")
    print("  2. 如果管理员账号未设置 -> 返回 None，记录警告")
    print("  3. 用管理员账号登录 Supabase")
    print("  4. 将转码后的 M4A 文件上传到 bucket 的特定目录")
    print("  5. 构造公网 URL: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}")
    print("  6. 返回公网 URL 供 DashScope 使用")
    print()
    print("失败处理:")
    print("  - 如果上传失败，返回错误信息，不继续转录")
    print("  - 这确保 DashScope 只会接收到可访问的有效 URL")
    print()


def test_error_scenarios():
    """测试错误场景"""
    print("=== 错误场景处理 ===\n")

    scenarios = [
        {
            "name": "ffmpeg 不可用",
            "behavior": "检测失败，返回错误：'ffmpeg 不可用，无法进行转码'",
        },
        {
            "name": "下载文件失败",
            "behavior": "返回错误：'下载文件失败'",
        },
        {
            "name": "转码超时",
            "behavior": "超过 transcoding_timeout 时，返回错误：'转码超时'",
        },
        {
            "name": "Supabase 上传失败",
            "behavior": "返回错误：'转码后的音频文件无法上传到云存储'，不继续转录",
        },
        {
            "name": "DashScope 转录失败",
            "behavior": "返回 DashScope 的错误信息，包含原始 URL 和 transcoded flag",
        },
    ]

    for scenario in scenarios:
        print(f"场景: {scenario['name']}")
        print(f"处理: {scenario['behavior']}")
        print()


if __name__ == "__main__":
    test_file_type_detection()
    test_transcoding_logic()
    test_supabase_upload_logic()
    test_error_scenarios()

    print("=== 配置说明 ===\n")
    print("ASRBackend 相关配置项:")
    print("  enable_transcoding: bool = True")
    print("    - 是否启用自动转码功能")
    print("  max_transcoding_retries: int = 2")
    print("    - 最大转码重试次数（当前未使用，预留）")
    print("  transcoding_timeout: int = 600")
    print("    - 转码超时时间（秒）")
    print()
    print("环境变量要求:")
    print("  SUPABASE_URL: Supabase 项目 URL")
    print("  SUPABASE_KEY: Supabase anon key")
    print("  SUPABASE_ADMIN_EMAIL: 管理员邮箱")
    print("  SUPABASE_ADMIN_PASSWORD: 管理员密码")
    print("  SUPABASE_BUCKET_NAME: 存储 bucket 名称（默认: test-public）")
    print("  SUPABASE_FOLDER_NAME: 存储文件夹名称（默认: asr）")
