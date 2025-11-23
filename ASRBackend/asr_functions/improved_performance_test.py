#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进的本地ASR模型性能测试脚本
该脚本分离模型加载时间和推理时间，提供更准确的性能评估
"""

import time
import os
import sys
import requests
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    # 导入本地ASR相关模块
    from asr_functions.asr_sentence_segments import process as local_asr_process, get_model
    from asr_functions.segment_normalizer import extract_text
    from asr_functions.utils import detect_language
except ImportError as e:
    print(f"导入模块时出错: {e}")
    # 如果相对导入失败，尝试绝对导入
    try:
        from ASRBackend.asr_functions.asr_sentence_segments import process as local_asr_process, get_model
        from ASRBackend.asr_functions.segment_normalizer import extract_text
        from ASRBackend.asr_functions.utils import detect_language
    except ImportError:
        local_asr_process = None
        get_model = None
        extract_text = None
        detect_language = None


def download_sample_audio(url: str, filename: str) -> bool:
    """
    下载示例音频文件
    
    Args:
        url: 音频文件URL
        filename: 保存的文件名
        
    Returns:
        下载是否成功
    """
    try:
        print(f"正在下载示例音频: {url}")
        # 添加请求头以避免406错误
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"示例音频已保存为: {filename}")
        return True
    except Exception as e:
        print(f"下载示例音频失败: {e}")
        return False


def measure_model_loading_time() -> float:
    """
    测量模型加载时间
    
    Returns:
        模型加载时间（秒）
    """
    global get_model
    if get_model is None:
        raise ImportError("无法导入模型加载函数")
    
    # 确保模型未加载
    import asr_functions.asr_sentence_segments as asr_module
    asr_module._model_instance = None
    
    # 测量模型加载时间
    start_time = time.time()
    model = get_model()
    end_time = time.time()
    
    return end_time - start_time


def performance_test_single_file(audio_path: str, iterations: int = 1) -> Dict[str, Any]:
    """
    对单个音频文件进行性能测试（不包含模型加载时间）
    
    Args:
        audio_path: 音频文件路径
        iterations: 重复执行次数，用于测试平均性能
        
    Returns:
        包含性能指标的字典
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    
    if local_asr_process is None:
        raise ImportError("无法导入本地ASR处理模块，请检查依赖是否正确安装")
    
    print(f"开始对文件 {audio_path} 进行性能测试，重复 {iterations} 次")
    
    # 预加载模型
    print("预加载模型...")
    model_loading_time = measure_model_loading_time()
    print(f"模型加载时间: {model_loading_time:.2f} 秒")
    
    # 记录推理时间
    total_inference_time = 0
    results = []
    
    for i in range(iterations):
        print(f"执行第 {i+1}/{iterations} 次推理...")
        start_time = time.time()
        
        try:
            # 执行ASR推理（不包含模型加载时间）
            segments = local_asr_process(audio_path)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            total_inference_time += elapsed_time
            
            if segments:
                text_content = extract_text(segments)
                language = detect_language(text_content)
                
                result = {
                    "segments_count": len(segments),
                    "text_length": len(text_content),
                    "language": language,
                    "inference_time": elapsed_time,
                    "segments": segments
                }
            else:
                result = {
                    "segments_count": 0,
                    "text_length": 0,
                    "language": None,
                    "inference_time": elapsed_time,
                    "segments": [],
                    "error": "未生成有效的转录结果"
                }
                
            results.append(result)
            print(f"第 {i+1} 次推理完成，耗时: {elapsed_time:.2f} 秒")
            
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            total_inference_time += elapsed_time
            
            error_result = {
                "segments_count": 0,
                "text_length": 0,
                "language": None,
                "inference_time": elapsed_time,
                "segments": [],
                "error": str(e)
            }
            results.append(error_result)
            print(f"第 {i+1} 次推理出错: {e}")
    
    # 计算平均性能指标
    avg_inference_time = total_inference_time / iterations
    avg_segments = sum(r["segments_count"] for r in results) / iterations
    avg_text_length = sum(r["text_length"] for r in results) / iterations
    
    # 成功次数
    success_count = sum(1 for r in results if "error" not in r)
    
    performance_metrics = {
        "file_path": audio_path,
        "audio_duration": "约32秒",  # 根据测试音频估算
        "iterations": iterations,
        "successful_runs": success_count,
        "success_rate": success_count / iterations,
        "model_loading_time": model_loading_time,
        "total_inference_time": total_inference_time,
        "average_inference_time": avg_inference_time,
        "average_segments": avg_segments,
        "average_text_length": avg_text_length,
        "real_time_factor": avg_inference_time / 32.0,  # 32秒为音频时长
        "detailed_results": results
    }
    
    return performance_metrics


def print_performance_report(metrics: Dict[str, Any]) -> None:
    """
    打印性能测试报告
    
    Args:
        metrics: 性能指标字典
    """
    print("\n" + "=" * 50)
    print("本地ASR模型性能测试报告")
    print("=" * 50)
    
    print(f"测试文件: {metrics['file_path']}")
    print(f"音频时长: {metrics['audio_duration']}")
    print(f"测试轮次: {metrics['iterations']}")
    print(f"成功次数: {metrics['successful_runs']}")
    print(f"成功率: {metrics['success_rate']*100:.1f}%")
    print(f"模型加载时间: {metrics['model_loading_time']:.2f} 秒")
    print(f"总推理时间: {metrics['total_inference_time']:.2f} 秒")
    print(f"平均推理时间: {metrics['average_inference_time']:.2f} 秒")
    print(f"实时因子(RTF): {metrics['real_time_factor']:.3f}")
    print(f"平均分段数: {metrics['average_segments']:.1f}")
    print(f"平均文本长度: {metrics['average_text_length']:.1f}")
    
    # 显示详细结果
    if metrics["detailed_results"]:
        print("\n详细识别结果:")
        detailed_result = metrics["detailed_results"][0]
        if "segments" in detailed_result and detailed_result["segments"]:
            for i, segment in enumerate(detailed_result["segments"]):
                print(f"[{i+1:2d}] [{segment['start_time']:6.2f}-{segment['end_time']:6.2f}秒] "
                      f"(说话人:{segment['spk_id']}) {segment['sentence']}")


def main():
    print("改进的本地ASR模型性能测试工具")
    print("=" * 50)
    
    # 检查是否安装了必要的依赖
    if local_asr_process is None:
        print("错误: 无法导入本地ASR处理模块，请确保已安装funasr等相关依赖")
        return
    
    # 下载示例音频
    sample_url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
    sample_file = "sample_speech.wav"
    
    if not download_sample_audio(sample_url, sample_file):
        print("无法下载示例音频文件")
        return
    
    try:
        # 执行性能测试
        result = performance_test_single_file(sample_file, iterations=1)
        
        # 打印性能报告
        print_performance_report(result)
        
    except Exception as e:
        print(f"性能测试过程中出现错误: {e}")
    finally:
        # 清理下载的示例文件
        try:
            if os.path.exists(sample_file):
                os.remove(sample_file)
                print(f"\n测试完成，已清理示例文件: {sample_file}")
        except:
            pass


if __name__ == "__main__":
    main()