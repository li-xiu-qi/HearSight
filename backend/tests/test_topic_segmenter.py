"""
最小可运行示例：
1. 使用 audio2text 将指定音频转写并获得分块 segments；
2. 调用 topic_segmenter 进行主题分段；
3. 打印结果 JSON。

说明：
- 尽量使用直接调用方式，不使用 argparse/unittest；
- 交流与注释使用中文；
- 不做过度的 try/except；
- 运行可能耗时较久，请耐心等待。
"""

import json
import os
import sys

# 兼容在 backend/tests 目录下直接运行：将项目根目录加入 sys.path
_THIS_DIR = os.path.dirname(__file__)
# 项目根目录应为 SmartMedia（包含 backend 包），从 backend/tests 上跳两级
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.audio2text.audio2text import audio_to_text
from backend.segmentation.topic_segmenter import segment_text_to_file
from backend.cache.cache_manager import audio_key, get_text, set_text


# 测试音频文件路径（请确保该文件存在）
AUDIO_PATH = (
    r"c:\Users\ke\Documents\projects\python_projects\SmartMedia\backend\tests\datas\大语言模型进化论：从“听懂指令”到“学会思考”，AI如何与人类对齐？.m4a"
)

# 缓存所用的模型名（用于参与 key 计算与标注）
ASR_MODEL_NAME = "funasr-default"


def run():
    """执行一次完整流程：ASR -> 主题分段 -> 打印 JSON 结果。"""
    # 1) 语音转写：先查缓存，未命中再真实识别并写入缓存
    key = audio_key(AUDIO_PATH, model=ASR_MODEL_NAME)
    text = get_text(key)

    if text is None:
        text, _ = audio_to_text(AUDIO_PATH, return_segments=True)
        set_text(key, text, model=ASR_MODEL_NAME, meta={"audio_path": AUDIO_PATH})
    print("text:", text)

    # 2) 基于全文进行主题分块，由大模型返回字符索引，并将结果写入 JSON 文件
    out_path = os.path.join(_PROJECT_ROOT, "backend", "tests", "results", "topic_segments.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    saved = segment_text_to_file(text, out_path, model=None)

    # 3) 简单打印保存路径与内容预览
    print("保存路径:", saved)
    with open(saved, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 打印所有片段的概览信息
    topic_list = data.get("topic_list", [])
    print(f"共分割出 {len(topic_list)} 个主题段落:")
    for i, topic in enumerate(topic_list, 1):
        print(f"{i}. {topic['topic_description']} ({topic['start_char_idx']}-{topic['end_char_idx']})")
    
    # 如果想看完整内容，取消下面的注释
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()

