# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
from funasr import AutoModel
import sys
import json
import os


def load_model() -> AutoModel:
    """
    加载 Paraformer 语音识别模型（含 VAD / 标点 / 说话人分离）。
    """
    model = AutoModel(
        model="paraformer-zh",
        model_revision="v2.0.4",
        vad_model="fsmn-vad",
        vad_model_revision="v2.0.4",
        punc_model="ct-punc-c",
        punc_model_revision="v2.0.4",
        spk_model="cam++",
        # spk_model_revision="v2.0.2",
    )
    return model


def normalize_result(res: List[Dict]) -> List[Dict]:
    """
    将 funASR 的推理结果 res 规范化为
    list[dict(index, spk_id, sentence, start_time, end_time)].

    说明：
    - 许多返回中为：res = [{'key': ..., 'text': '全文', 'timestamp': [[s,e], ...], ...}]
    - 仅在存在逐句字段 `sentence_info` 时返回对应的句级结果；否则返回空列表。
    - spk_id：若返回包含 'spk' 或 'spk_id' 字段，尝试读取；否则为 None。
    """
    if not res:
        return []

    item = res[0]
    # 保存下识别结果
    os.makedirs("results", exist_ok=True)
    # 优先读取逐句字段 sentence_info
    sentence_info = item.get("sentence_info")
    if sentence_info is None:
        raise ValueError("无法处理的 ASR 结果格式，缺少 sentence_info 字段")
    # 若句级没写 spk，则使用整体的 spk/spk_id 作为默认
    spk_default: Optional[str] = None
    if "spk_id" in item and item["spk_id"] is not None:
        spk_default = str(item["spk_id"]) 
    elif "spk" in item and item["spk"] is not None:
        spk_default = str(item["spk"]) 

    results: List[Dict] = []
    for idx, s in enumerate(sentence_info, start=1):
        sent_text = (s.get("text") or "").strip()
        try:
            st = float(s.get("start", 0.0))
        except Exception:
            st = 0.0
        try:
            ed = float(s.get("end", st))
        except Exception:
            ed = st
        spk_local = s.get("spk_id", s.get("spk", None))
        spk_val = str(spk_local) if spk_local is not None else spk_default
        results.append({
            "index": idx,
            "spk_id": spk_val,
            "sentence": sent_text,
            "start_time": float(st),
            "end_time": float(ed),
        })

    return results



def process(audio_path: str) -> List[Dict]:
    """
    处理音频并返回标准化列表：
    list[dict(index, spk_id, sentence, start_time, end_time)]
    example:
    [
        {
            "index": 1,
            "spk_id": "1",
            "sentence": "你好，世界！",
            "start_time": 0.0, # 单位为：ms
            "end_time": 1.0 # 单位为：ms
        }
    ]
    """
    model = load_model()
    res = model.generate(
        input=audio_path,
        batch_size_s=300,
        hotword="魔搭",
    )
    return normalize_result(res)

