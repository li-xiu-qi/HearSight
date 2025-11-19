import json
import os
import sys

"""语音识别句子分段处理模块"""

import json
import os
import unicodedata
from typing import Dict, List, Optional

from funasr import AutoModel

if __name__ == "__main__":
    def load_model() -> AutoModel:
        """加载 Paraformer 语音识别模型（含 VAD / 标点 / 说话人分离）"""
        model = AutoModel(
            model="paraformer-zh",
            model_revision="v2.0.4",
            vad_model="fsmn-vad",
            vad_model_revision="v2.0.4",
            punc_model="ct-punc-c",
            punc_model_revision="v2.0.4",
            spk_model="cam++",
        )
        return model


    def process(
        audio_path: str, merge_sentences: bool = True, merge_short_sentences: bool = True
    ) -> List[Dict]:
        """处理音频并返回标准化列表

        Args:
            audio_path: 音频文件路径
            merge_sentences: 是否合并句子
            merge_short_sentences: 是否合并少于4个字的句子到下一句

        Returns:
            list[dict(index, spk_id, sentence, start_time, end_time)]

        Example:
            [
                {
                    "index": 1,
                    "spk_id": "1",
                    "sentence": "你好，世界！",
                    "start_time": 0.0,
                    "end_time": 1.0
                }
            ]
        """
        model = load_model()
        res = model.generate(
            input=audio_path,
            batch_size_s=300,
            hotword="Obsidian",
        )
        return res


    # 使用与现有测试一致的数据路径（可按需修改为你的绝对路径）
    audio_path = r"./test_datas/test_output.wav"

    # 调用转写函数
    segments = process(audio_path)


    # 如需保存解析结果
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    with open(
        os.path.join(output_dir, "test_paraformer_a2t_segments.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)


    """
    输出结果格式说明：
    test_paraformer_a2t_segments.json 文件包含音频转录的段落级结果，数据结构为数组，每个元素是一个对象，包含以下字段：

    - `key`：字符串，表示段落标识，如"test_output"。
    - `text`：字符串，转录的完整文本内容。
    - `timestamp`：数组，包含多个子数组，每个子数组为 [start_time, end_time]，表示该段文本对应的时间戳（毫秒）。
    - `sentence_info`：数组，每个元素是一个句子对象，包含：
    - `text`：字符串，句子文本。
    - `start`：整数，句子开始时间（毫秒）。
    - `end`：整数，句子结束时间（毫秒）。
    - `timestamp`：数组，该句子的详细时间戳列表，每个子数组为 [start, end]。
    - `spk`：整数，说话人ID。

    示例结构：
    [
        {
            "key": "test_output",
            "text": "转录文本内容...",
            "timestamp": [
                [1200, 1740],
                [1740, 1860],
                ...
            ],
            "sentence_info": [
                {
                    "text": "句子文本",
                    "start": 1200,
                    "end": 3100,
                    "timestamp": [
                        [1200, 1740],
                        ...
                    ],
                    "spk": 0
                },
                ...
            ]
        }
    ]

    此格式基于 funasr 模型的输出，经过标准化处理，便于后续分析和使用。
    """
