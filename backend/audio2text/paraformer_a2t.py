import os
from typing import Any, Dict, List, Optional, TypedDict

import torch
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

# 读取全局配置（与 start.py 保持一致）
try:
    from start import load_config  # 使用项目已有的通用配置加载
except Exception:
    # 极简兜底：若无法导入 start.py，则返回空配置
    def load_config() -> Dict[str, Any]:  # type: ignore
        return {}


class Segment(TypedDict):
    start: float
    end: float
    text: str


# 选择设备
_device = "cuda" if torch.cuda.is_available() else "cpu"

# 模型：Paraformer 长音频（集成 VAD + 标点 + 时间戳）
# 允许通过 config.yaml 的 audio2text_paraformer.model 覆盖
_cfg = load_config() or {}
_para_cfg = (_cfg.get("audio2text_paraformer") or {}) if isinstance(_cfg, dict) else {}
_model_name = _para_cfg.get(
    "model",
    # 文档给出的模型标识
    "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
)

_model_revision = _para_cfg.get("model_revision", "v2.0.4")
_vad_model = _para_cfg.get("vad_model", "fsmn-vad")
_vad_revision = _para_cfg.get("vad_model_revision", "v2.0.4")
_punc_model = _para_cfg.get("punc_model", "ct-punc-c")
_punc_revision = _para_cfg.get("punc_model_revision", "v2.0.4")

model = AutoModel(
    model=_model_name,
    model_revision=_model_revision,
    vad_model=_vad_model,
    vad_model_revision=_vad_revision,
    punc_model=_punc_model,
    punc_model_revision=_punc_revision,
    device=_device,
    disable_update=True,
)


def _extract_segments(item: Dict[str, Any]) -> List[Segment]:
    """
    从 funasr 返回的单条结果里尽力提取段级时间戳。
    优先级：
    - item["segments"]: [{"start": float, "end": float, "text": str}, ...]
    - 其次尝试 item["timestamp"] 若为上述结构（某些版本可能为 [{start,end,text}...]）
    若无法提取，则返回空列表。
    """
    segs: List[Segment] = []

    v = item.get("segments")
    if isinstance(v, list) and v and isinstance(v[0], dict):
        ok = all(
            ("start" in s and "end" in s and "text" in s) for s in v  # type: ignore
        )
        if ok:
            for s in v:  # type: ignore
                try:
                    segs.append(
                        Segment(start=float(s["start"]), end=float(s["end"]), text=str(s["text"]))
                    )
                except Exception:
                    # 跳过异常段
                    pass
            return segs

    v = item.get("timestamp")
    if isinstance(v, list) and v and isinstance(v[0], dict):
        ok = all(("start" in s and "end" in s) for s in v)  # type: ignore
        if ok:
            # 若每个时间戳条目没有 text，则回退为整条 item 的文本
            whole_text = str(item.get("text", ""))
            for s in v:  # type: ignore
                text_piece = s.get("text", whole_text)
                try:
                    segs.append(
                        Segment(start=float(s["start"]), end=float(s["end"]), text=str(text_piece))
                    )
                except Exception:
                    pass
            return segs

    return segs


def to_second_index(segments: List[Segment]) -> Dict[int, str]:
    """
    将 [{start, end, text}] 聚合为按秒的字典：{second: text_concat}
    同一秒内若有多个片段，按出现顺序拼接并去重简单规整。
    """
    idx: Dict[int, List[str]] = {}
    for seg in segments:
        s = max(0, int(seg["start"]))
        e = max(s, int(seg["end"]))
        # 覆盖到 [s, e] 的每一秒
        for sec in range(s, e + 1):
            idx.setdefault(sec, [])
            idx[sec].append(seg["text"])  # 保持原顺序

    # 合并并做一点点重复规整
    out: Dict[int, str] = {}
    for sec, parts in idx.items():
        cleaned: List[str] = []
        last = None
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if p != last:
                cleaned.append(p)
                last = p
        out[sec] = " ".join(cleaned)
    return out


def paraformer_audio_to_text(
    audio_path: str,
    *,
    batch_size_s: int = 300,
    return_segments: bool = True,
) -> Any:
    """
    使用 Paraformer 长音频模型进行转写。

    参数：
    - audio_path: 音频文件绝对路径（16k）
    - batch_size_s: 批处理窗口，长音频建议大些
    - return_segments: 返回 (text, segments, per_second)

    返回：
    - 若 return_segments=True: (text: str, segments: List[Segment], per_second: Dict[int, str])
    - 否则：text: str
    """
    assert os.path.exists(audio_path), f"文件不存在: {audio_path}"

    res = model.generate(
        input=audio_path,
        cache={},
        batch_size_s=batch_size_s,
    )

    item = res[0] if res and len(res) > 0 else {}
    raw_text = str(item.get("text", ""))
    text = rich_transcription_postprocess(raw_text) if raw_text else ""

    if not return_segments:
        return text

    segments = _extract_segments(item)
    per_second = to_second_index(segments) if segments else {}
    return text, segments, per_second
