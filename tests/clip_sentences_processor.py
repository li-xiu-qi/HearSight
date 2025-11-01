# coding: utf-8
import os
import re
import json
import subprocess
from typing import List, Tuple, Dict, Any, Optional

import torch
from funasr import AutoModel


def load_model() -> AutoModel:
    """
    加载 Paraformer 语音识别模型（含 VAD / 标点）。
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModel(
        model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        model_revision="v2.0.4",
        vad_model="fsmn-vad",
        vad_model_revision="v2.0.4",
        punc_model="ct-punc-c",
        punc_model_revision="v2.0.4",
        device=device,
        disable_update=True,
    )
    return model


def split_cn_sentences(text: str) -> List[Tuple[int, int, str]]:
    """
    简单中文分句，返回 [(start_idx, end_idx, sentence)]，end_idx 不含。保留句末标点。
    标点集：。！？；（可按需扩展）
    """
    if not text:
        return []
    spans: List[Tuple[int, int, str]] = []
    start = 0
    for m in re.finditer(r"[。！？；]", text):
        end = m.end()
        sent = text[start:end]
        if sent.strip():
            spans.append((start, end, sent))
        start = end
    if start < len(text):  # 末尾残句
        sent = text[start:]
        if sent.strip():
            spans.append((start, len(text), sent))
    return spans


def map_charpos_to_time_ms(pos: int, text_len: int, seg_ms: List[Tuple[int, int]]) -> int:
    """
    将字符位置 pos (0..text_len) 映射到时间(ms)。
    思路：仅按"有声累计时长"线性分配（忽略静音间隔）。
    """
    if text_len <= 0 or not seg_ms:
        return 0
    total_voiced = sum(e - s for s, e in seg_ms)
    if total_voiced <= 0:
        return seg_ms[0][0]

    target = total_voiced * (pos / text_len)  # 目标有声累计时长
    acc = 0.0
    for s, e in seg_ms:
        dur = e - s
        if dur <= 0:
            continue
        if acc + dur >= target:
            inside = target - acc
            return int(round(s + inside))
        acc += dur
    return seg_ms[-1][1]


def sentences_with_times(text: str, timestamps_ms: List[List[int]]) -> List[Dict[str, Any]]:
    """
    输入：整段 text 与 VAD 窗口 timestamps_ms -> 近似句子时间范围（毫秒）
    输出：[{sentence, start_ms, end_ms}]
    """
    seg_ms = [(int(s), int(e)) for s, e in timestamps_ms if isinstance(s, (int, float)) and isinstance(e, (int, float))]
    seg_ms = [(s, e) for s, e in seg_ms if e > s]
    if not text or not seg_ms:
        return []

    sents = split_cn_sentences(text)
    n = len(text)
    out: List[Dict[str, Any]] = []
    for s_idx, e_idx, sent in sents:
        st_ms = map_charpos_to_time_ms(s_idx, n, seg_ms)
        ed_ms = map_charpos_to_time_ms(e_idx, n, seg_ms)
        if ed_ms < st_ms:
            ed_ms = st_ms
        out.append({
            "sentence": sent,
            "start_ms": st_ms,
            "end_ms": ed_ms,
        })
    return out


def process(audio_path: str, padding_start_ms: int = 0, padding_end_ms: int = 0) -> List[Dict]:
    """
    处理音频并返回标准化列表：
    list[dict(index, spk_id, sentence, start_time, end_time)]
    
    example:
    [
        {
            "index": 1,
            "spk_id": "1",
            "sentence": "你好，世界！",
            "start_time": 0.0,     # 单位为：ms
            "end_time": 1000.0     # 单位为：ms
        }
    ]
    
    Args:
        audio_path: 音频文件路径
        padding_start_ms: 句子开始时补充的毫秒数
        padding_end_ms: 句子结束时补充的毫秒数
    
    Returns:
        标准化的句子列表，每个元素包含句子索引、说话人ID、文本和时间范围
    """
    # 1) 加载模型并生成
    model = load_model()
    res = model.generate(input=audio_path, cache={}, batch_size_s=300)
    
    # 2) 提取文本和时间戳
    item: Dict[str, Any] = res[0] if isinstance(res, list) and res else {}
    text: str = item.get("text", "") or ""
    timestamps: List[List[int]] = item.get("timestamp", []) or []
    
    # 3) 计算句子时间（快速近似）
    sentence_spans = sentences_with_times(text, timestamps)
    
    # 4) 轻微校正边界
    adjusted_spans: List[Dict[str, Any]] = []
    prev_end = 0
    for sp in sentence_spans:
        st = int(sp.get("start_ms", 0)) + padding_start_ms
        ed = int(sp.get("end_ms", st)) + padding_end_ms
        # 不与上一句重叠：强制单调不减
        if st < prev_end:
            st = prev_end
        # 至少保留最小时长，避免 0 长或负长
        if ed <= st:
            ed = st + 100  # 至少100ms
        adjusted_spans.append({
            "sentence": sp.get("sentence", ""),
            "start_ms": st,
            "end_ms": ed,
        })
        prev_end = ed
    
    # 5) 转换为标准格式
    results: List[Dict] = []
    for idx, sp in enumerate(adjusted_spans, start=1):
        results.append({
            "index": idx,
            "spk_id": "1",
            "sentence": sp.get("sentence", ""),
            "start_time": float(sp.get("start_ms", 0)),  # 单位：ms
            "end_time": float(sp.get("end_ms", 0)),      # 单位：ms
        })
    
    return results
