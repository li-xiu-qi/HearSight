# HearSight ASR Backend API 文档

## 概述

HearSight ASR Backend 提供语音识别功能的 RESTful API，支持本地和云端两种模式。

## 基础信息

- **基础 URL**: `http://localhost:8003`
- **认证**: 无需认证
- **数据格式**: JSON

## API 接口列表

### 健康检查

#### GET /health

健康检查接口，返回服务状态和运行模式。

**响应**:
```json
{
  "status": "healthy",
  "service": "ASR Backend",
  "mode": "cloud"
}
```

### 语音识别

#### POST /asr/transcribe/bytes

从音频字节流进行语音识别（本地模式）。

直接上传音频文件，使用本地 FunASR 模型进行识别。适合对隐私要求高、延迟敏感的场景。

**请求体**: multipart/form-data
- `file`: 音频文件（支持 .wav, .mp3, .m4a, .flac, .ogg）

**响应**:
成功响应:
```json
{
  "status": "success",
  "text": "识别的完整文本内容",
  "language": "检测到的语言代码，如zh、en等",
  "segments": [
    {
      "index": 0,
      "spk_id": "说话人ID",
      "sentence": "识别的句子内容",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ],
  "filename": "原始文件名"
}
```

错误响应:
```json
{
  "status": "error",
  "error": "错误描述信息",
  "filename": "原始文件名"
}
```

#### POST /asr/transcribe/url

从音频 URL 进行语音识别（云端模式）。

提供音频文件 URL，通过 DashScope 云端 API 进行识别。需要网络连接，适合处理远程音频文件。

**请求体**: form-data
- `url`: 音频文件 URL

**响应**:
成功响应:
```json
{
  "status": "success",
  "text": "识别的完整文本内容",
  "language": "检测到的语言代码，如zh、en等",
  "segments": [
    {
      "index": 0,
      "spk_id": "说话人ID",
      "sentence": "识别的句子内容",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ],
  "filename": "从URL中提取的文件名",
  "url": "原始请求的URL"
}
```

错误响应:
```json
{
  "status": "error",
  "error": "错误描述信息",
  "filename": "从URL中提取的文件名",
  "url": "原始请求的URL"
}
```

#### POST /asr/transcribe/upload

上传文件到 Supabase 后进行语音识别（云端模式）。

先将音频文件上传到 Supabase 云存储获得公开 URL，然后通过 DashScope 云端 API 进行语音识别。适合需要文件存储和云端处理的场景。

**请求体**: multipart/form-data
- `file`: 音频文件（支持 .wav, .mp3, .m4a, .flac, .ogg）

**响应**:
成功响应:
```json
{
  "status": "success",
  "text": "识别的完整文本内容",
  "language": "检测到的语言代码，如zh、en等",
  "segments": [
    {
      "index": 0,
      "spk_id": "说话人ID",
      "sentence": "识别的句子内容",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ],
  "filename": "原始文件名",
  "upload_url": "上传到Supabase后的公开访问URL"
}
```

错误响应:
```json
{
  "status": "error",
  "error": "错误描述信息",
  "filename": "原始文件名"
}
```