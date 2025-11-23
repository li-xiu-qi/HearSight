# ASR Router 设计文档

## 概述

`asr_router.py` 是 HearSight 项目中 ASRBackend 模块的路由模块，负责提供语音识别（ASR）相关的 API 接口。该模块基于 FastAPI 框架实现，支持本地和云端两种运行模式，以适应不同的部署环境和需求。

模块提供三个明确的 API 端点，对应三种不同的语音识别场景：

- **本地字节流识别** (`/asr/transcribe/bytes`)：直接处理上传的音频文件
- **URL 识别** (`/asr/transcribe/url`)：处理远程音频文件 URL
- **文件上传识别** (`/asr/transcribe/upload`)：上传文件到 Supabase 后进行识别

## 架构

### 依赖关系

- **FastAPI**: 用于构建 RESTful API 接口
- **ASRService**: 核心业务逻辑服务，处理实际的语音识别任务
- **Settings**: 配置管理模块，用于获取运行模式和模型配置
- **Supabase**: 云端模式下用于文件存储的后端服务

### 运行模式

模块支持两种运行模式，通过 `settings.asr_mode` 配置：

1. **本地模式 (local)**: 使用 FunASR 本地模型进行语音识别
   - 支持输入方式：文件上传（字节流）
   - 文件直接在本地进行处理，无需网络传输

2. **云端模式 (cloud)**: 使用阿里云 DashScope API 进行语音识别
   - 支持输入方式：URL 识别、文件上传（自动上传到 Supabase）
   - 通过网络 API 进行识别，支持远程文件处理

## API 接口详解

### POST /asr/transcribe/bytes

从音频字节流进行语音识别（本地模式）。

直接上传音频文件，使用本地 FunASR 模型进行识别。适合对隐私要求高、延迟敏感的场景。

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `file` | UploadFile | 是 | 音频文件。支持格式：wav, mp3, m4a, flac, ogg |

#### 响应内容

##### 成功响应 (status=200)

```json
{
  "status": "success",
  "text": "识别的文本内容",
  "language": "zh",
  "segments": [
    {
      "index": 0,
      "spk_id": "说话人ID",
      "sentence": "识别的句子",
      "start_time": 起始时间（毫秒）,
      "end_time": 结束时间（毫秒）
    }
  ],
  "filename": "audio.wav"
}
```

##### 错误响应

| HTTP 状态 | 错误条件 |
|----------|---------|
| 400 | 文件格式不支持 |
| 500 | 服务器内部错误 |

```json
{
  "detail": "不支持的文件格式。支持的格式：wav, mp3, m4a, flac, ogg"
}
```

#### 处理流程

```text
1. 文件格式校验（wav, mp3, m4a, flac, ogg）
2. 读取文件内容为字节流
3. ASRService.transcribe_from_bytes(audio_data, filename)
   └─ LocalASRProvider.transcribe_bytes()
4. 返回识别结果
```

### POST /asr/transcribe/url

从音频 URL 进行语音识别（云端模式）。

提供音频文件 URL，通过 DashScope 云端 API 进行识别。需要网络连接，适合处理远程音频文件。

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `url` | str | 是 | 音频文件 URL，必须以 http:// 或 https:// 开头 |

#### 响应内容

##### 成功响应 (status=200)

```json
{
  "status": "success",
  "text": "识别的文本内容",
  "language": "zh",
  "segments": [
    {
      "index": 0,
      "spk_id": "说话人ID",
      "sentence": "识别的句子",
      "start_time": 起始时间（毫秒）,
      "end_time": 结束时间（毫秒）
    }
  ],
  "filename": "audio.mp3"
}
```

##### 错误响应

| HTTP 状态 | 错误条件 |
|----------|---------|
| 400 | URL 格式无效 |
| 500 | 服务器内部错误 |

```json
{
  "detail": "URL 必须以 http:// 或 https:// 开头"
}
```

#### 处理流程

```text
1. URL 格式校验（http/https 开头）
2. ASRService.transcribe_from_url(url)
   └─ CloudASRProvider.transcribe_url()
3. 返回识别结果
```

### POST /asr/transcribe/upload

上传文件到 Supabase 后进行语音识别（云端模式）。

先将音频文件上传到 Supabase 云存储获得公开 URL，然后通过 DashScope 云端 API 进行语音识别。适合需要文件存储和云端处理的场景。

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `file` | UploadFile | 是 | 音频文件。支持格式：wav, mp3, m4a, flac, ogg |

#### 响应内容

##### 成功响应 (status=200)

```json
{
  "status": "success",
  "text": "识别的文本内容",
  "language": "zh",
  "segments": [
    {
      "index": 0,
      "spk_id": "说话人ID",
      "sentence": "识别的句子",
      "start_time": 起始时间（毫秒）,
      "end_time": 结束时间（毫秒）
    }
  ],
  "filename": "a1b2c3d4e5f6.wav",
  "upload_url": "https://xxx.supabase.co/storage/v1/object/public/..."
}
```

#### 处理流程

```text
1. 文件格式校验（wav, mp3, m4a, flac, ogg）
2. 读取文件内容为字节流
3. ASRService.transcribe_from_file_with_upload(audio_data, filename)
   3.1. 创建临时文件
   3.2. 上传到 Supabase，返回公开 URL
   3.3. ASRService.transcribe_from_url(public_url)
   3.4. 添加上传信息到结果
   3.5. 清理本地临时文件
   3.6. 清理 Supabase 临时文件
4. 返回识别结果（包含上传 URL）
```

## 使用示例

### Python 客户端示例

#### 本地字节流识别

```python
import requests

url = "http://localhost:8000/asr/transcribe/bytes"
files = {"file": open("audio.wav", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

#### URL 识别

```python
import requests

url = "http://localhost:8000/asr/transcribe/url"
data = {"url": "https://example.com/audio.mp3"}
response = requests.post(url, data=data)
print(response.json())
```

#### 文件上传识别

```python
import requests

url = "http://localhost:8000/asr/transcribe/upload"
files = {"file": open("audio.mp3", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### cURL 示例

#### 本地字节流识别

```bash
curl -X POST "http://localhost:8000/asr/transcribe/bytes" \
     -F "file=@audio.wav"
```

#### URL 识别

```bash
curl -X POST "http://localhost:8000/asr/transcribe/url" \
     -F "url=https://example.com/audio.mp3"
```

#### 文件上传识别

```bash
curl -X POST "http://localhost:8000/asr/transcribe/upload" \
     -F "file=@audio.mp3"
```

## 服务层架构（ASRService）

### 核心方法

#### transcribe_from_bytes (本地模式)

从音频字节流进行识别（本地模式）。

- **适用场景**: 本地模式，隐私敏感，无网络依赖
- **处理流程**: 直接调用本地 FunASR 模型
- **返回内容**: 标准识别结果（text, language, segments）

#### transcribe_from_url (云端模式)

从 URL 进行识别（云端模式）。

- **适用场景**: 云端模式，处理远程音频文件
- **处理流程**: 调用 DashScope API 处理 URL
- **返回内容**: 标准识别结果

#### transcribe_from_file_with_upload (云端模式)

上传文件到 Supabase 后进行识别（云端模式）。

- **适用场景**: 云端模式，需要文件存储
- **处理流程**:
  1. 保存临时文件
  2. 上传到 Supabase 获得公开 URL
  3. 调用 URL 识别
  4. 添加上传信息到结果
  5. 清理临时文件
  6. 清理 Supabase 临时文件
- **返回内容**: 标准识别结果 + 上传信息（upload_url）

## 配置要求

### 通用配置

```python
asr_mode = "local"  # 或 "cloud"
app_name = "ASR Backend"
debug = False
```

### 本地模式配置

```python
local_model_name = "paraformer-v2-zh"
local_vad_model = "fsmn-vad-zh"
local_punc_model = "ct-punc-v3"
```

### 云端模式配置

```python
dashscope_api_key = "your-api-key"
dashscope_model = "paraformer-v2"
dashscope_language_hints = "zh,en"

# Supabase 配置（文件上传必需）
supabase_url = "https://xxx.supabase.co"
supabase_key = "your-api-key"
supabase_bucket_name = "audio-storage"
supabase_folder_name = "uploads"
```