import os
import torch
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import re
from typing import Any, Dict

# 读取全局配置（与 start.py 保持一致）
try:
    from start import load_config  # 使用项目已有的通用配置加载
except Exception:
    # 极简兜底：若无法导入 start.py，则返回空配置
    def load_config() -> Dict[str, Any]:  # type: ignore
        return {}


# 选择设备
device = "cuda" if torch.cuda.is_available() else "cpu"

# 模型：使用内置实现，避免远程 model.py 加载失败
# 优先从 config.yaml 的 audio2text.model 读取；若没有则使用默认值
_cfg = load_config() or {}
_a2t_cfg = (_cfg.get("audio2text") or {}) if isinstance(_cfg, dict) else {}
_model_name = _a2t_cfg.get("model", "iic/SenseVoiceSmall")

model = AutoModel(
    model=_model_name,
    trust_remote_code=False,  # 使用 FunASR 内置实现
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    device=device,
    disable_update=True,
)

def audio_to_text(
    audio_path: str,
    *,
    language: str = "auto",
    use_itn: bool = True,
    batch_size_s: int = 60,
    merge_vad: bool = True,
    merge_length_s: int = 15,
    return_segments: bool = False,
):
    """
    将语音文件转写为文本。

    参数：
    - audio_path: 音频文件绝对路径
    - language: 语言（"auto"/"zn"/"en"/...）
    - use_itn: 文本正规化
    - batch_size_s, merge_vad, merge_length_s: VAD/合并参数
    - return_segments: 若为 True，返回 (text, segments)，segments 为标签解析结果

    返回：
    - str 或 (str, list[dict])
    """
    assert os.path.exists(audio_path), f"文件不存在: {audio_path}"

    res = model.generate(
        input=audio_path,
        cache={},
        language=language,  # "zn", "en", "yue", "ja", "ko", "nospeech"
        use_itn=use_itn,
        batch_size_s=batch_size_s,
        merge_vad=merge_vad,
        merge_length_s=merge_length_s,
    )

    raw = res[0]["text"] if res and len(res) > 0 else ""
    text = rich_transcription_postprocess(raw) if raw else ""
    if return_segments:
        return text, parse_segments(raw)
    return text

def parse_segments(text):
    # 匹配标签和内容
    pattern = re.compile(r'<\|([a-zA-Z]+)\|><\|([A-Z_]+)\|><\|Speech\|><\|([a-zA-Z]+)\|>(.*?)((?=<\|[a-zA-Z]+\|>)|$)', re.DOTALL)
    results = []
    for match in pattern.finditer(text):
        lang = match.group(1)
        emotion = match.group(2)
        speech_type = match.group(3)
        content = match.group(4).strip()
        results.append({
            "lang": lang,
            "emotion": emotion,
            "speech_type": speech_type,
            "content": content
        })
    return results

