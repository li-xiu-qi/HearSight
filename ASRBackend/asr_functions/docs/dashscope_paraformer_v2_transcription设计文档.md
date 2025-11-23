# dashscope_paraformer_v2_transcription 模块设计文档

## 概述

`dashscope_paraformer_v2_transcription.py` 是一个用于云端语音识别（ASR）的模块，基于阿里云 DashScope API 的 Paraformer-v2 模型实现。该模块提供异步音频转录功能，支持多语言识别，并能处理长时间音频文件。

## 功能特性

- 基于阿里云 DashScope API 实现云端语音识别
- 支持异步转录处理，适合处理大文件
- 支持多语言识别
- 自动处理任务状态轮询
- 结果规范化处理
- 详细的错误处理机制

## 输入输出说明

### 主要入口函数

```python
def transcribe_audio_from_url(
    url: str,
    model: str = MODEL_NAME,
    language_hints: Optional[List[str]] = None,
    timeout: int = 600,
) -> Optional[Dict]
```

#### 参数说明

- `url`: 音频文件的 URL 地址
- `model`: 使用的转录模型，默认为 "paraformer-v2"
- `language_hints`: 语言提示列表，默认为 ["zh", "en"]
- `timeout`: 等待超时时间（秒），默认为 600 秒

#### 返回值

返回一个包含识别结果的字典，结构如下：

成功时：
```json
{
  "filename": "原始文件名",
  "text": "完整的识别文本",
  "language": "检测到的语言",
  "segments": [
    {
      "spk_id": "说话人ID",
      "sentence": "识别的句子",
      "start_time": 起始时间（毫秒）,
      "end_time": 结束时间（毫秒）
    }
  ],
  "status": "success",
  "task_id": "任务ID"
}
```

失败时：
```json
{
  "status": "error",
  "error": "错误描述",
  "...": "其他错误相关信息"
}
```

### 辅助函数

#### `initialize_dashscope_client(api_key: str) -> None`

初始化 DashScope 客户端，设置 API 密钥。

#### `async_transcribe_audio(file_urls: List[str], model: str = MODEL_NAME, language_hints: Optional[List[str]] = None) -> Optional[str]`

提交异步转录任务，返回任务 ID。

#### `get_transcription_status(task_id: str, wait_timeout: int = 0) -> Optional[Dict]`

获取转录任务的状态。

#### `_parse_transcription_result(result: Dict) -> Optional[List[Dict]]`

解析 DashScope 转录结果为标准格式。

## 工作流程

1. 初始化 DashScope 客户端
2. 提交异步转录任务
3. 轮询任务状态直到完成或超时
4. 获取转录结果
5. 解析并规范化识别结果
6. 检测文本语言
7. 返回标准化的结果

## 依赖项

- dashscope: 阿里云 DashScope SDK
- requests: 用于获取转录结果
- segment_normalizer: 用于结果规范化处理
- utils: 用于语言检测

## 异常处理

模块具有完善的异常处理机制：

- 网络异常处理
- API 调用失败处理
- 超时处理
- 结果解析异常处理
- 任务失败状态处理

所有异常都会被捕获并转化为标准错误响应格式返回。