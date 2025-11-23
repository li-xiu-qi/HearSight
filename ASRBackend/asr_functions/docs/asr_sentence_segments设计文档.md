# asr_sentence_segments 模块设计文档

## 概述

`asr_sentence_segments.py` 是一个用于本地语音识别（ASR）的核心处理模块，基于 FunASR 库实现。该模块负责处理音频文件并将其转换为带时间戳的文本片段，支持本地文件和远程 URL 地址的音频处理。

## 功能特性

- 支持本地音频文件和远程 URL 音频处理
- 自动下载远程音频文件至临时目录
- 使用 FunASR 进行语音识别
- 支持说话人分离
- 支持句子合并和规范化处理
- 自动清理临时文件

## 输入输出说明

### 主要入口函数

```python
def process(
    audio_path: str,
    merge_sentences: bool = True,
    merge_short_sentences: bool = True,
    batch_size_s: int = 300,
    hotword: str = "Obsidian"
) -> List[Dict]
```

#### 参数说明

- `audio_path`: 音频文件路径或 URL 地址
- `merge_sentences`: 是否合并句子（默认: True）
- `merge_short_sentences`: 是否合并短句（默认: True）
- `batch_size_s`: 批处理大小（秒）（默认: 300）
- `hotword`: 热词（默认: "Obsidian"）

#### 返回值

返回一个包含识别结果的字典列表，每个字典包含以下字段：

- `spk_id`: 说话人 ID
- `sentence`: 识别的文本内容
- `start_time`: 句子开始时间（毫秒）
- `end_time`: 句子结束时间（毫秒）

### 辅助函数

#### `is_url(path: str) -> bool`

判断给定路径是否为 URL。

#### `download_audio(url: str, max_size: int = 100 * 1024 * 1024) -> str`

下载远程音频文件到本地临时目录。

#### `get_model()`

获取或加载 ASR 模型（单例模式）。

## 工作流程

1. 判断输入路径是本地文件还是 URL
2. 如果是 URL，则下载到临时文件
3. 加载 ASR 模型（如果尚未加载）
4. 使用 FunASR 处理音频文件
5. 解析并规范化识别结果
6. 清理临时文件
7. 返回标准化的结果列表

## 依赖项

- funasr: 主要的 ASR 处理库
- requests: 用于下载远程音频文件
- segment_normalizer: 用于结果规范化处理

## 异常处理

模块会在以下情况下抛出异常或返回空列表：
- 音频文件不存在或无法访问
- 模型加载失败
- ASR 处理过程中发生错误
- 网络连接问题导致下载失败

所有异常都会被捕获并记录日志，函数通常会返回空列表而不是传播异常。