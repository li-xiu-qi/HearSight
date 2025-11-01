# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
from funasr import AutoModel
import sys
import json
import os
import unicodedata


def detect_language(text: str) -> str:
    """
    检测文本主要语言，支持中文和英文。
    如果中文字符比例 > 70%，返回 'zh'，否则返回 'en'。
    """
    if not text:
        return 'en'  # 默认英文
    
    chinese_count = 0
    total_count = 0
    for char in text:
        if char.isspace():
            continue
        total_count += 1
        if unicodedata.category(char).startswith('Lo') or '\u4e00' <= char <= '\u9fff':
            chinese_count += 1
    
    if total_count == 0:
        return 'en'
    
    chinese_ratio = chinese_count / total_count
    return 'zh' if chinese_ratio > 0.7 else 'en'


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


def normalize_result(res: List[Dict], merge_sentences: bool = True, merge_short_sentences: bool = True) -> List[Dict]:
    """
    将 funASR 的推理结果 res 规范化为
    list[dict(index, spk_id, sentence, start_time, end_time)].

    说明：
    - 许多返回中为：res = [{'key': ..., 'text': '全文', 'timestamp': [[s,e], ...], ...}]
    - 仅在存在逐句字段 `sentence_info` 时返回对应的句级结果；否则返回空列表。
    - spk_id：若返回包含 'spk' 或 'spk_id' 字段，尝试读取；否则为 None。
    - merge_sentences：是否通过标点符号合并句子，默认 True。
    - merge_short_sentences：是否合并少于4个字的句子到下一句，默认 True。
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

    if not merge_sentences:
        return results

    # 检测主要语言
    full_text = " ".join([r["sentence"] for r in results])
    language = detect_language(full_text)
    
    # 根据语言设置合并标点
    if language == 'zh':
        merge_punctuations = ["，", "；", "：","、",",", ";", ":"]
    else:  # en
        merge_punctuations = ["，", "；", "：","、",",", ";", ":"]

    # 合并句子逻辑
    merged_results: List[Dict] = []
    i = 0
    while i < len(results):
        current = results[i]
        merged = False
        
        # 首先检查是否需要合并：句子以指定标点结尾，且非空
        if any(current["sentence"].endswith(punc) for punc in merge_punctuations) and i + 1 < len(results):
            next_item = results[i + 1]
            # 仅在说话人相同且下一个句子非空时合并
            if current["spk_id"] == next_item["spk_id"] and next_item["sentence"].strip():
                # 合并句子和时间戳
                merged_sentence = current["sentence"] + next_item["sentence"]
                merged_end_time = next_item["end_time"]
                current["sentence"] = merged_sentence
                current["end_time"] = merged_end_time
                merged_results.append(current)
                # 跳过下一个句子
                i += 2
                merged = True
        
        # 如果上面没有合并，检查是否需要合并短句子（少于4个字）
        if not merged and merge_short_sentences and i + 1 < len(results):
            # 计算句子长度（不含标点和空格）
            sent_length = len(current["sentence"].strip())
            if sent_length < 4:
                next_item = results[i + 1]
                if current["spk_id"] == next_item["spk_id"] and next_item["sentence"].strip():
                    # 合并句子（添加空格）和时间戳
                    merged_sentence = current["sentence"] + " " + next_item["sentence"]
                    merged_end_time = next_item["end_time"]
                    current["sentence"] = merged_sentence
                    current["end_time"] = merged_end_time
                    merged_results.append(current)
                    # 跳过下一个句子
                    i += 2
                    merged = True
        
        if not merged:
            merged_results.append(current)
            i += 1

    # 重新调整索引
    for idx, item in enumerate(merged_results, start=1):
        item["index"] = idx

    return merged_results


def process(audio_path: str, merge_sentences: bool = True, merge_short_sentences: bool = True) -> List[Dict]:
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
    merge_sentences: 是否合并句子，默认 True。
    merge_short_sentences: 是否合并少于4个字的句子到下一句，默认 True。
    """
    model = load_model()
    res = model.generate(
        input=audio_path,
        batch_size_s=300,
        hotword="魔搭",
    )
    return normalize_result(res, merge_sentences, merge_short_sentences)

