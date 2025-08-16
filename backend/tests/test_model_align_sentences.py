# coding: utf-8
"""
基于“模型重解码”的句级时间对齐测试脚本（直接运行，无需 argparse）
输出：
- backend/tests/results/model_align/sentence_times.json
- backend/tests/results/model_align/clips/sent_XXX.m4a

依赖：ffmpeg、funasr、torch
"""
import os
import re
import json
import math
import subprocess
from typing import List, Tuple, Dict, Any

import torch
from funasr import AutoModel

# ===== 配置 =====
AUDIO_PATH = r"C:\Users\ke\Documents\projects\python_projects\SmartMedia\backend\tests\datas\大语言模型进化论：从“听懂指令”到“学会思考”，AI如何与人类对齐？.m4a"
BASE_DIR = os.path.dirname(__file__)
RESULT_DIR = os.path.join(BASE_DIR, "results", "model_align")
CLIPS_DIR = os.path.join(RESULT_DIR, "clips")
TMP_DIR = os.path.join(RESULT_DIR, "tmp")

# chunk 相关
MAX_CHUNK_S = 30.0
MERGE_GAP_S = 0.6
OVERLAP_S = 0.8

# 导出与边界
EXPORT_TOP_N = 10
PAD_START_S = 0.10
PAD_END_S = 0.20


# ===== 工具函数 =====
def ensure_dirs():
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)


def ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except FileNotFoundError:
        return False


def split_cn_sentences(text: str) -> List[Tuple[int, int, str]]:
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
    if start < len(text):
        sent = text[start:]
        if sent.strip():
            spans.append((start, len(text), sent))
    return spans


def ms_segments_from_item(item: Dict[str, Any]) -> List[Tuple[int, int]]:
    v = item.get("timestamp")
    segs: List[Tuple[int, int]] = []
    if isinstance(v, list):
        if v and isinstance(v[0], (list, tuple)) and len(v[0]) >= 2:
            for s, e in v:
                s_i, e_i = int(s), int(e)
                if e_i > s_i:
                    segs.append((s_i, e_i))
    return segs


def merge_ms_to_chunks(ms_segs: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
    if not ms_segs:
        return []
    segs = sorted(ms_segs)
    merged: List[Tuple[int, int]] = []
    cur_s, cur_e = segs[0]
    for s, e in segs[1:]:
        if s - cur_e <= int(MERGE_GAP_S * 1000):
            cur_e = max(cur_e, e)
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))

    # 拆分为不超过 MAX_CHUNK_S 的块
    chunks: List[Tuple[float, float]] = []
    max_ms = int(MAX_CHUNK_S * 1000)
    for s, e in merged:
        p = s
        while p < e:
            q = min(e, p + max_ms)
            chunks.append((p / 1000.0, q / 1000.0))
            p = q
    # 注入重叠
    if OVERLAP_S > 0 and len(chunks) > 1:
        out: List[Tuple[float, float]] = []
        for i, (s, e) in enumerate(chunks):
            if i == 0:
                out.append((s, e))
            else:
                ps, pe = out[-1]
                if s < pe:
                    out.append((s, e))
                else:
                    out[-1] = (ps, max(ps, pe - OVERLAP_S))  # 拉长上块的尾部用于重叠
                    out.append((max(ps, s - OVERLAP_S), e))
        chunks = out
    return chunks


def ffmpeg_cut(in_path: str, start_s: float, end_s: float, out_path: str) -> None:
    dur = max(0.0, end_s - start_s)
    if dur <= 0:
        return
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", in_path,
        "-ss", f"{start_s:.3f}", "-t", f"{dur:.3f}",
        "-vn", "-acodec", "aac", "-b:a", "128k",
        out_path,
    ]
    subprocess.run(cmd, check=True)


def longest_common_suffix_prefix(a: str, b: str, max_k: int = 60) -> int:
    k = 0
    la, lb = len(a), len(b)
    while k < max_k and k < la and k < lb:
        if a[la - 1 - k] != b[k]:
            break
        k += 1
    return k


if __name__ == "__main__":
    assert os.path.exists(AUDIO_PATH), f"文件不存在: {AUDIO_PATH}"
    ensure_dirs()
    assert ffmpeg_available(), "未检测到 ffmpeg，请先安装并加入 PATH"

    # 0) 模型加载，与现有配置保持一致
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

    # 1) 全局一次解码，取全文与 VAD 段
    res = model.generate(input=AUDIO_PATH, cache={}, batch_size_s=300)
    item: Dict[str, Any] = res[0] if isinstance(res, list) and res else {}
    full_text: str = item.get("text", "") or ""
    ms_segs = ms_segments_from_item(item)

    # 2) VAD -> chunk（控制单块时长 + 重叠）
    chunks = merge_ms_to_chunks(ms_segs)

    # 3) 逐块重解码
    chunk_units: List[Dict[str, Any]] = []
    for i, (cs, ce) in enumerate(chunks):
        tmp_path = os.path.join(TMP_DIR, f"chunk_{i:03d}.m4a")
        ffmpeg_cut(AUDIO_PATH, cs, ce, tmp_path)
        cres = model.generate(input=tmp_path, cache={}, batch_size_s=300)
        citem: Dict[str, Any] = cres[0] if isinstance(cres, list) and cres else {}
        ctext: str = citem.get("text", "") or ""
        chunk_units.append({"start_s": cs, "end_s": ce, "text": ctext})

    # 4) 构造拼接文本，并记录每块的 concat 索引区间
    concat_text = ""
    concat_ranges: List[Tuple[int, int]] = []
    for u in chunk_units:
        t = u["text"]
        overlap_k = longest_common_suffix_prefix(concat_text[-80:], t[:80], max_k=60) if concat_text and t else 0
        if overlap_k > 0:
            t_eff = t[overlap_k:]
        else:
            t_eff = t
        c_start = len(concat_text)
        concat_text += t_eff
        c_end = len(concat_text)
        concat_ranges.append((c_start, c_end))

    # 5) 分句并定位到 concat_text（优先直接 substring 查找）
    sent_spans = split_cn_sentences(full_text)
    results: List[Dict[str, Any]] = []
    search_pos = 0
    for s_idx, e_idx, sent in sent_spans:
        cs = concat_text.find(sent, search_pos)
        if cs < 0:
            # 回退：用句首锚点（前 8~12 字）做查找
            anchor = sent[:12] if len(sent) >= 12 else sent
            cs = concat_text.find(anchor, max(0, search_pos - 100))
        if cs < 0:
            # 仍失败：使用比例近似（极少发生）
            r = s_idx / max(1, len(full_text))
            cs = int(round(r * len(concat_text)))
        ce = cs + len(sent)
        search_pos = max(search_pos, cs)

        # 6) 将 concat 索引映射到时间：定位落入的块
        def pos_time(p: int) -> float:
            # 找到 p 所在的块范围
            for (c_start, c_end), u in zip(concat_ranges, chunk_units):
                if c_start <= p <= c_end and c_end > c_start:
                    frac = (p - c_start) / (c_end - c_start)
                    return u["start_s"] + frac * (u["end_s"] - u["start_s"])
            # 边界：落在某块之外，做夹逼
            if p < 0:
                return chunk_units[0]["start_s"]
            if p > len(concat_text):
                return chunk_units[-1]["end_s"]
            # 夹在两块之间：取近邻
            best = None
            best_d = 1e18
            for (c_start, c_end), u in zip(concat_ranges, chunk_units):
                if c_end <= c_start:
                    continue
                center = (c_start + c_end) / 2.0
                d = abs(p - center)
                if d < best_d:
                    best_d = d
                    best = u
            if best is None:
                return 0.0
            return 0.5 * (best["start_s"] + best["end_s"])

        st = pos_time(cs)
        ed = pos_time(ce)
        if ed < st:
            ed = st
        results.append({"sentence": sent, "start_s": st, "end_s": ed})

    # 7) 边界修正：单调、不重叠 + padding + 最小时长
    adj: List[Dict[str, Any]] = []
    prev_end = 0.0
    for r in results:
        st = r["start_s"] + PAD_START_S
        ed = r["end_s"] + PAD_END_S
        if st < prev_end:
            st = prev_end
        if ed <= st:
            ed = st + 0.12
        adj.append({"sentence": r["sentence"], "start_s": round(st, 3), "end_s": round(ed, 3), "via": "model_align"})
        prev_end = ed

    # 8) 导出 JSON 与音频切片
    idx_path = os.path.join(RESULT_DIR, "sentence_times.json")
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(adj, f, ensure_ascii=False, indent=2)

    for i, sp in enumerate(adj[:EXPORT_TOP_N]):
        of = os.path.join(CLIPS_DIR, f"sent_{i+1:03d}.m4a")
        ffmpeg_cut(AUDIO_PATH, float(sp["start_s"]), float(sp["end_s"]), of)
        print(f"ok: {of} [{sp['start_s']:.3f}s ~ {sp['end_s']:.3f}s]")

    print(f"索引: {idx_path}")
