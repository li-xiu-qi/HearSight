#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地ASR模型推理性能测试示例
该脚本用于测试本地ASR模型的性能水平，包括准确性和处理速度
"""

import asyncio
import time
import os
import sys
import requests
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    # 导入本地ASR相关模块
    from asr_functions.asr_sentence_segments import process as local_asr_process
    from asr_functions.segment_normalizer import extract_text
    from asr_functions.utils import detect_language
except ImportError as e:
    print(f"导入模块时出错: {e}")
    # 如果相对导入失败，尝试绝对导入
    try:
        from ASRBackend.asr_functions.asr_sentence_segments import process as local_asr_process
        from ASRBackend.asr_functions.segment_normalizer import extract_text
        from ASRBackend.asr_functions.utils import detect_language
    except ImportError:
        local_asr_process = None
        extract_text = None
        detect_language = None


def performance_test_single_file(audio_path: str, iterations: int = 1) -> Dict[str, Any]:
    """
    对单个音频文件进行性能测试
    
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
    
    # 记录总时间
    total_time = 0
    results = []
    
    for i in range(iterations):
        print(f"执行第 {i+1}/{iterations} 次推理...")
        start_time = time.time()
        
        try:
            # 执行ASR推理
            segments = local_asr_process(audio_path)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            total_time += elapsed_time
            
            if segments:
                text_content = extract_text(segments)
                language = detect_language(text_content)
                
                result = {
                    "segments_count": len(segments),
                    "text_length": len(text_content),
                    "language": language,
                    "processing_time": elapsed_time,
                    "segments": segments
                }
            else:
                result = {
                    "segments_count": 0,
                    "text_length": 0,
                    "language": None,
                    "processing_time": elapsed_time,
                    "segments": [],
                    "error": "未生成有效的转录结果"
                }
                
            results.append(result)
            print(f"第 {i+1} 次推理完成，耗时: {elapsed_time:.2f} 秒")
            
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            total_time += elapsed_time
            
            error_result = {
                "segments_count": 0,
                "text_length": 0,
                "language": None,
                "processing_time": elapsed_time,
                "segments": [],
                "error": str(e)
            }
            results.append(error_result)
            print(f"第 {i+1} 次推理出错: {e}")
    
    # 计算平均性能指标
    avg_time = total_time / iterations
    avg_segments = sum(r["segments_count"] for r in results) / iterations
    avg_text_length = sum(r["text_length"] for r in results) / iterations
    
    # 成功次数
    success_count = sum(1 for r in results if "error" not in r)
    
    performance_metrics = {
        "file_path": audio_path,
        "iterations": iterations,
        "successful_runs": success_count,
        "success_rate": success_count / iterations,
        "total_time": total_time,
        "average_time": avg_time,
        "average_segments": avg_segments,
        "average_text_length": avg_text_length,
        "detailed_results": results
    }
    
    print(f"\n性能测试总结:")
    print(f"  文件: {audio_path}")
    print(f"  总执行次数: {iterations}")
    print(f"  成功次数: {success_count}")
    print(f"  成功率: {success_count/iterations*100:.1f}%")
    print(f"  总耗时: {total_time:.2f} 秒")
    print(f"  平均耗时: {avg_time:.2f} 秒")
    print(f"  平均分段数: {avg_segments:.1f}")
    print(f"  平均文本长度: {avg_text_length:.1f}")
    
    return performance_metrics


def benchmark_different_sizes(audio_paths: list) -> Dict[str, Any]:
    """
    对不同大小的音频文件进行基准测试
    
    Args:
        audio_paths: 音频文件路径列表
        
    Returns:
        包含所有测试结果的字典
    """
    print("开始对不同大小的音频文件进行基准测试...")
    
    all_results = {}
    
    for audio_path in audio_paths:
        try:
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            print(f"\n测试文件: {audio_path} (大小: {file_size:.2f} MB)")
            
            result = performance_test_single_file(audio_path, iterations=1)
            all_results[audio_path] = {
                "file_size_mb": file_size,
                "performance": result
            }
            
        except Exception as e:
            print(f"测试文件 {audio_path} 时出错: {e}")
            all_results[audio_path] = {
                "file_size_mb": 0,
                "error": str(e)
            }
    
    return all_results


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


def create_test_audio(duration=5):
    """
    创建一个测试用的音频文件
    """
    try:
        import numpy as np
        from scipy.io.wavfile import write
        
        # 生成一个简单的测试音频信号
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A音符频率
        waveform = np.sin(2 * np.pi * frequency * t)
        
        # 添加一些语音模拟信号
        speech_freq = 1000
        speech_wave = 0.5 * np.sin(2 * np.pi * speech_freq * t)
        combined_wave = (waveform + speech_wave) / 2
        
        # 保存为WAV文件
        test_filename = f"test_audio_{duration}s.wav"
        write(test_filename, sample_rate, combined_wave.astype(np.float32))
        print(f"测试音频文件已创建: {test_filename}")
        return test_filename
    except ImportError:
        print("警告: 无法创建测试音频文件，缺少numpy或scipy库")
        return None
    except Exception as e:
        print(f"创建测试音频文件时出错: {e}")
        return None


def transcribe_file(audio_path: str) -> Dict[str, Any]:
    """
    转录音频文件，返回标准格式的结果
    
    Args:
        audio_path: 音频文件路径
        
    Returns:
        标准格式的转录结果
    """
    try:
        segments = local_asr_process(audio_path)
        if segments:
            text_content = extract_text(segments)
            language = detect_language(text_content)
            
            return {
                "text": text_content,
                "language": language,
                "segments": segments,
                "status": "success",
                "filename": os.path.basename(audio_path)
            }
        else:
            return {
                "status": "error",
                "error": "未生成有效的转录结果",
                "filename": os.path.basename(audio_path)
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "filename": os.path.basename(audio_path)
        }


def transcribe_bytes(audio_data: bytes, filename: str = "temp.wav") -> Dict[str, Any]:
    """
    转录字节数据，返回标准格式的结果
    
    Args:
        audio_data: 音频字节数据
        filename: 临时文件名
        
    Returns:
        标准格式的转录结果
    """
    # 创建临时文件
    temp_file = f"temp_{int(time.time())}_{filename}"
    
    try:
        # 写入临时文件
        with open(temp_file, "wb") as f:
            f.write(audio_data)
        
        # 调用文件转录函数
        result = transcribe_file(temp_file)
        result["filename"] = filename
        return result
        
    finally:
        # 删除临时文件
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass


if __name__ == "__main__":
    # 使用示例
    print("本地ASR模型推理性能测试工具")
    print("=" * 50)
    
    # 检查是否安装了必要的依赖
    if local_asr_process is None:
        print("错误: 无法导入本地ASR处理模块，请确保已安装funasr等相关依赖")
        sys.exit(1)
    
    # 如果提供了命令行参数，则使用参数作为音频文件路径
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if os.path.exists(audio_file):
            print(f"\n使用提供的音频文件进行测试: {audio_file}")
            try:
                result = performance_test_single_file(audio_file, iterations=1)
            except Exception as e:
                print(f"性能测试过程中出现错误: {e}")
        else:
            print(f"错误: 找不到指定的音频文件: {audio_file}")
    else:
        # 没有提供文件，下载示例音频进行测试
        print("\n未提供音频文件，将下载示例音频进行测试...")
        sample_url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
        sample_file = "sample_speech.wav"
        
        # 下载示例音频
        if download_sample_audio(sample_url, sample_file):
            try:
                print(f"\n使用下载的示例音频文件进行测试: {sample_file}")
                result = performance_test_single_file(sample_file, iterations=1)
                
                # 显示详细结果
                if result and "detailed_results" in result and result["detailed_results"]:
                    detailed_result = result["detailed_results"][0]
                    if "segments" in detailed_result and detailed_result["segments"]:
                        print("\n识别结果详情:")
                        for i, segment in enumerate(detailed_result["segments"]):
                            print(f"[{i+1:2d}] [{segment['start_time']:6.2f}-{segment['end_time']:6.2f}秒] "
                                  f"(说话人:{segment['spk_id']}) {segment['sentence']}")
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
        else:
            print("无法下载示例音频文件")
            print("\n使用说明:")
            print("1. 准备一个音频文件（如 test.wav）")
            print("2. 运行命令: python local_asr_example.py test.wav")
            print("3. 查看输出的性能测试结果")