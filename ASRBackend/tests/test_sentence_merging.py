"""测试 DashScope Paraformer-v2 句子合并功能"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ASRBackend.asr_functions.dashscope_paraformer_v2_transcription import (
    _parse_transcription_result,
)
from ASRBackend.asr_functions.segment_normalizer import normalize_segments


def test_sentence_merging():
    """测试句子合并功能"""

    # 模拟真实的 DashScope 转录结果格式（从 transcription_url 获取的 JSON）
    mock_transcription_result = {
        "file_url": "https://example.com/audio.mp3",
        "properties": {
            "audio_format": "aac",
            "channels": [0, 1],
            "original_sampling_rate": 44100,
            "original_duration_in_milliseconds": 119397,
        },
        "transcripts": [
            {
                "channel_id": 0,
                "content_duration_in_milliseconds": 119397,
                "text": "你好，世界！这是一个测试。短句子。",
                "sentences": [
                    {
                        "begin_time": 1000,
                        "end_time": 2000,
                        "text": "你好，",
                        "sentence_id": 0,
                        "words": [
                            {
                                "begin_time": 1000,
                                "end_time": 1500,
                                "text": "你",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 1500,
                                "end_time": 2000,
                                "text": "好",
                                "punctuation": "，",
                            },
                        ],
                    },
                    {
                        "begin_time": 2000,
                        "end_time": 3000,
                        "text": "世界！",
                        "sentence_id": 1,
                        "words": [
                            {
                                "begin_time": 2000,
                                "end_time": 2500,
                                "text": "世",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 2500,
                                "end_time": 3000,
                                "text": "界",
                                "punctuation": "！",
                            },
                        ],
                    },
                    {
                        "begin_time": 3500,
                        "end_time": 5000,
                        "text": "这是一个测试。",
                        "sentence_id": 2,
                        "words": [
                            {
                                "begin_time": 3500,
                                "end_time": 4000,
                                "text": "这",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 4000,
                                "end_time": 4500,
                                "text": "是",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 4500,
                                "end_time": 4800,
                                "text": "一",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 4800,
                                "end_time": 5000,
                                "text": "个",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 5000,
                                "end_time": 5200,
                                "text": "测",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 5200,
                                "end_time": 5400,
                                "text": "试",
                                "punctuation": "。",
                            },
                        ],
                    },
                    {
                        "begin_time": 5500,
                        "end_time": 6000,
                        "text": "短",
                        "sentence_id": 3,
                        "words": [
                            {
                                "begin_time": 5500,
                                "end_time": 6000,
                                "text": "短",
                                "punctuation": "",
                            }
                        ],
                    },
                    {
                        "begin_time": 6000,
                        "end_time": 7000,
                        "text": "句子。",
                        "sentence_id": 4,
                        "words": [
                            {
                                "begin_time": 6000,
                                "end_time": 6500,
                                "text": "句",
                                "punctuation": "",
                            },
                            {
                                "begin_time": 6500,
                                "end_time": 7000,
                                "text": "子",
                                "punctuation": "。",
                            },
                        ],
                    },
                ],
            }
        ],
    }

    print("=== 测试句子合并功能 ===\n")

    # 测试不合并
    segments_no_merge = _parse_transcription_result(
        mock_transcription_result,
    )
    segments_no_merge = normalize_segments(
        segments_no_merge,
        merge_sentences=False,
        merge_short_sentences=False,
    )
    print(f"不合并句子: {len(segments_no_merge)} 个分段")
    for seg in segments_no_merge:
        print(f"  {seg['index']}: {seg['sentence']} (spk_id: {seg['spk_id']})")

    print()

    # 测试合并句子（基于标点）
    segments_merge_sentences = _parse_transcription_result(
        mock_transcription_result,
    )
    segments_merge_sentences = normalize_segments(
        segments_merge_sentences,
        merge_sentences=True,
        merge_short_sentences=False,
    )
    print(f"合并句子（标点）: {len(segments_merge_sentences)} 个分段")
    for seg in segments_merge_sentences:
        print(f"  {seg['index']}: {seg['sentence']} (spk_id: {seg['spk_id']})")

    print()

    # 测试合并短句子
    segments_merge_short = _parse_transcription_result(
        mock_transcription_result,
    )
    segments_merge_short = normalize_segments(
        segments_merge_short,
        merge_sentences=False,
        merge_short_sentences=True,
    )
    print(f"合并短句子: {len(segments_merge_short)} 个分段")
    for seg in segments_merge_short:
        print(f"  {seg['index']}: {seg['sentence']} (spk_id: {seg['spk_id']})")

    print()

    # 测试全部合并
    segments_full_merge = _parse_transcription_result(
        mock_transcription_result,
    )
    segments_full_merge = normalize_segments(
        segments_full_merge,
        merge_sentences=True,
        merge_short_sentences=True,
    )
    print(f"全部合并: {len(segments_full_merge)} 个分段")
    for seg in segments_full_merge:
        print(f"  {seg['index']}: {seg['sentence']} (spk_id: {seg['spk_id']})")

    print("\n✅ 句子合并测试完成")


def test_normalize_result_directly():
    """直接测试 normalize_result 函数"""

    print("=== 直接测试 normalize_result 函数 ===\n")

    # 创建测试数据（模拟解析后的格式）
    test_segments = [
        {
            "index": 1,
            "spk_id": "0",
            "sentence": "你好，",
            "start_time": 1.0,
            "end_time": 2.0,
        },
        {
            "index": 2,
            "spk_id": "0",
            "sentence": "世界！",
            "start_time": 2.0,
            "end_time": 3.0,
        },
        {
            "index": 3,
            "spk_id": "0",
            "sentence": "短",
            "start_time": 3.5,
            "end_time": 4.0,
        },
        {
            "index": 4,
            "spk_id": "0",
            "sentence": "句子。",
            "start_time": 4.0,
            "end_time": 5.0,
        },
    ]

    print("原始分段:")
    for seg in test_segments:
        print(f"  {seg['index']}: {seg['sentence']}")

    print()

    # 测试合并
    merged = normalize_segments(
        test_segments,
        merge_sentences=True,
        merge_short_sentences=True,
    )

    print("合并后:")
    for seg in merged:
        print(f"  {seg['index']}: {seg['sentence']}")

    print("\n✅ normalize_result 测试完成")


if __name__ == "__main__":
    test_sentence_merging()
    print("\n" + "=" * 50 + "\n")
    test_normalize_result_directly()
