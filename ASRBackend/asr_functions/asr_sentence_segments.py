"""语音识别句子分段处理模块"""

import os
import tempfile
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

try:
    from funasr import AutoModel
except ImportError:
    AutoModel = None

from .segment_normalizer import normalize_segments
from .utils import detect_language

# 全局模型缓存
_model_instance = None


def get_model():
    """获取或加载 ASR 模型（单例模式）"""
    global _model_instance
    if _model_instance is None:
        if AutoModel is None:
            raise ImportError("funasr 未安装。请安装本地版本依赖")
        print("加载 ASR 模型...")
        _model_instance = AutoModel(
            model="paraformer-zh",
            model_revision="v2.0.4",
            vad_model="fsmn-vad",
            vad_model_revision="v2.0.4",
            punc_model="ct-punc-c",
            punc_model_revision="v2.0.4",
            spk_model="cam++",
        )
        print("ASR 模型加载完成")
    return _model_instance


def is_url(path: str) -> bool:
    """准确判断是否为 URL"""
    if path.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
        return True
    try:
        result = urlparse(path)
        return bool(result.scheme and result.netloc)
    except:
        return False


def download_audio(url: str, max_size: int = 100 * 1024 * 1024) -> str:
    """下载音频文件到临时位置

    Args:
        url: 音频文件 URL
        max_size: 最大文件大小（字节），默认 100MB

    Returns:
        临时文件路径

    Raises:
        ValueError: 文件过大或下载失败
    """
    try:
        # 检查文件大小
        head_response = requests.head(url, timeout=10)
        if head_response.status_code == 200:
            content_length = head_response.headers.get('content-length')
            if content_length and int(content_length) > max_size:
                raise ValueError(f"文件过大: {int(content_length)} bytes > {max_size} bytes")

        # 下载文件
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        filename = os.path.basename(urlparse(url).path) or "temp_audio.mp3"
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(filename)[1]
        )
        temp_file_path = temp_file.name
        temp_file.close()

        downloaded_size = 0
        with open(temp_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                downloaded_size += len(chunk)
                if downloaded_size > max_size:
                    os.unlink(temp_file_path)
                    raise ValueError(f"下载文件过大: {downloaded_size} bytes")
                f.write(chunk)

        print(f"音频下载完成: {temp_file_path}")
        return temp_file_path

    except Exception as e:
        raise ValueError(f"下载音频失败: {e}")


def _extract_segments_from_result(
    res: List[Dict],
    merge_sentences: bool = True,
    merge_short_sentences: bool = True,
) -> List[Dict]:
    """从 funASR 推理结果中提取并规范化分段信息

    Args:
        res: funASR 推理结果
        merge_sentences: 是否合并句子
        merge_short_sentences: 是否合并短句子

    Returns:
        标准分段列表
    """
    if not res:
        return []

    try:
        item = res[0]
        sentence_info = item.get("sentence_info")
        if sentence_info is None:
            raise ValueError("ASR 结果格式错误，缺少 sentence_info 字段")

        # 获取默认说话人 ID
        spk_default: Optional[str] = None
        if "spk_id" in item and item["spk_id"] is not None:
            spk_default = str(item["spk_id"])
        elif "spk" in item and item["spk"] is not None:
            spk_default = str(item["spk"])

        results: List[Dict] = []
        for s in sentence_info:
            sent_text = (s.get("text") or "").strip()
            if not sent_text:  # 跳过空句子
                continue

            try:
                st = float(s.get("start", 0.0))
            except (ValueError, TypeError):
                st = 0.0

            try:
                ed = float(s.get("end", st))
            except (ValueError, TypeError):
                ed = st

            spk_local = s.get("spk_id", s.get("spk", None))
            spk_val = str(spk_local) if spk_local is not None else spk_default

            results.append({
                "spk_id": spk_val,
                "sentence": sent_text,
                "start_time": float(st),
                "end_time": float(ed),
            })

        return normalize_segments(results, merge_sentences, merge_short_sentences)

    except Exception as e:
        print(f"提取分段信息失败: {e}")
        return []


def process(
    audio_path: str,
    merge_sentences: bool = True,
    merge_short_sentences: bool = True,
    batch_size_s: int = 300,
    hotword: str = "Obsidian"
) -> List[Dict]:
    """处理音频并返回标准化列表

    Args:
        audio_path: 音频文件路径或 URL
        merge_sentences: 是否合并句子
        merge_short_sentences: 是否合并少于4个字的句子到下一句
        batch_size_s: 批处理大小（秒）
        hotword: 热词

    Returns:
        list[dict(index, spk_id, sentence, start_time, end_time)]
    """
    temp_file_path = None

    try:
        actual_path = audio_path

        # 处理 URL
        if is_url(audio_path):
            print(f"下载音频文件: {audio_path}")
            temp_file_path = download_audio(audio_path)
            actual_path = temp_file_path

        # 检查文件是否存在
        if not os.path.exists(actual_path):
            raise FileNotFoundError(f"音频文件不存在: {actual_path}")

        # 获取模型（缓存）
        model = get_model()

        # 执行推理
        print(f"开始 ASR 推理: {actual_path}")
        res = model.generate(
            input=actual_path,
            batch_size_s=batch_size_s,
            hotword=hotword,
        )

        if not res:
            print("ASR 推理结果为空")
            return []

        # 提取和规范化结果
        segments = _extract_segments_from_result(
            res, merge_sentences, merge_short_sentences
        )

        print(f"ASR 处理完成，共 {len(segments)} 个分段")
        return segments

    except Exception as e:
        print(f"ASR 处理失败: {e}")
        return []

    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"临时文件已清理: {temp_file_path}")
            except Exception as e:
                print(f"清理临时文件失败: {e}")
