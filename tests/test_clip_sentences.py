# coding: utf-8
import os
import re
import json
import subprocess
from typing import List, Tuple, Dict, Any

import torch
from funasr import AutoModel

# ===== 配置 =====
AUDIO_PATH = r"./datas/test.mp4"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")
CLIPS_DIR = os.path.join(OUTPUT_DIR, "clips")
MAX_SENTENCES = 10  # 仅截取前 N 句，避免过多文件
# 轻微校正：整体将句子开始略微延后、结束再多延后一点，减少句首夹带与句尾缺失
PADDING_START_MS = 0  # 毫秒
PADDING_END_MS = 0    # 毫秒

# ===== 工具函数 =====
def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)


def ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except FileNotFoundError:
        return False


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
    思路：仅按“有声累计时长”线性分配（忽略静音间隔）。
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


def clip_with_ffmpeg(in_path: str, start_s: float, end_s: float, out_path: str) -> None:
    duration = max(0.0, end_s - start_s)
    if duration <= 0.0:
        return
    # 更精确的切割：将 -ss 放到 -i 之后，并用 -t 指定时长（解码级寻址，牺牲速度换精度）
    # 为了更高的兼容性，采用重编码（aac）而不是 -c copy
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", in_path,
        "-ss", f"{start_s:.3f}", "-t", f"{duration:.3f}",
        "-vn", "-acodec", "aac", "-b:a", "128k",
        out_path,
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    assert os.path.exists(AUDIO_PATH), f"文件不存在: {AUDIO_PATH}"
    ensure_dirs()

    if not ffmpeg_available():
        raise RuntimeError("未检测到 ffmpeg，请先在系统中安装 ffmpeg 并确保其在 PATH 中可用。")

    # 1) 语音转写（与现有配置保持一致）
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

    res = model.generate(input=AUDIO_PATH, cache={}, batch_size_s=300)
    item: Dict[str, Any] = res[0] if isinstance(res, list) and res else {}
    text: str = item.get("text", "") or ""
    timestamps: List[List[int]] = item.get("timestamp", []) or []

    # 2) 计算句子时间（快速近似）
    sentence_spans = sentences_with_times(text, timestamps)

    # 2.1) 轻微校正边界，避免：
    #  - 句尾缺少最后几个字（统一延长句尾）
    #  - 下一句包含上一句的一部分（统一将句首略微延后，并与上一句不重叠）
    adjusted_spans: List[Dict[str, Any]] = []
    prev_end = 0
    for sp in sentence_spans:
        st = int(sp.get("start_ms", 0)) + PADDING_START_MS
        ed = int(sp.get("end_ms", st)) + PADDING_END_MS
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

    # 保存索引
    idx_path = os.path.join(OUTPUT_DIR, "paraformer_sentence_times.json")
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(adjusted_spans, f, ensure_ascii=False, indent=2)

    # 3) 截取前 MAX_SENTENCES 句音频，保存到 clips/
    for i, sp in enumerate(adjusted_spans[:MAX_SENTENCES]):
        st_ms = int(sp["start_ms"]) if isinstance(sp.get("start_ms"), (int, float)) else 0
        ed_ms = int(sp["end_ms"]) if isinstance(sp.get("end_ms"), (int, float)) else st_ms
        # 转换为秒用于ffmpeg
        st_s = st_ms / 1000.0
        ed_s = ed_ms / 1000.0
        out_file = os.path.join(CLIPS_DIR, f"sent_{i+1:03d}.m4a")
        try:
            clip_with_ffmpeg(AUDIO_PATH, st_s, ed_s, out_file)
            print(f"ok: {out_file} [{st_ms}ms ~ {ed_ms}ms]")
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg 失败: {out_file} - {e}")

    print(f"索引: {idx_path}")
    print(f"音频片段输出目录: {CLIPS_DIR}")
