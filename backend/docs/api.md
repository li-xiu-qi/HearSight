# HearSight Backend API 文档

## 概述

HearSight Backend 提供媒体处理、转写、总结、翻译和聊天等功能的 RESTful API。

## 基础信息

- **基础 URL**: `http://localhost:9999`
- **认证**: 无需认证
- **数据格式**: JSON

## API 接口列表

### 媒体下载

#### POST /api/download

启动视频下载任务（异步处理）。

**请求体**:
```json
{
  "url": "string",  // 下载URL（必需）
  "out_dir": "string",  // 输出目录（可选）
  "job_id": "integer"  // 任务ID（必需）
}
```

**响应**:
```json
{
  "status": "started",
  "job_id": 123,
  "task_id": "string",
  "message": "任务已提交，后台异步处理中"
}
```

### 文件上传

#### POST /api/upload

上传视频或音频文件。

**请求体**: multipart/form-data
- `file`: 文件（支持 .mp4, .avi, .mov, .mkv, .flv, .wmv, .webm, .mp3, .wav, .m4a, .aac, .flac, .ogg, .wma）

**响应**:
```json
{
  "success": true,
  "message": "文件上传成功,正在处理中",
  "data": {
    "path": "string",
    "basename": "string",
    "static_url": "string",
    "size": 123456,
    "is_audio": false,
    "job_id": "string",
    "placeholder_url": "string"  // 音频文件可选
  }
}
```

#### POST /api/upload/rename

重命名已上传的文件。

**请求体**:
```json
{
  "old_filename": "string",
  "new_filename": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "文件重命名成功",
  "data": {
    "old_filename": "string",
    "new_filename": "string",
    "static_url": "string",
    "placeholder_url": "string"
  }
}
```

### 转写记录管理

#### GET /api/transcripts

列出已转写的媒体列表（按id倒序）。

**查询参数**:
- `limit`: 返回数量（默认50）
- `offset`: 偏移量（默认0）

**响应**:
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "audio_path": "string",
      "video_path": "string",
      "created_at": "2023-01-01T00:00:00",
      "segment_count": 10
    }
  ]
}
```

#### GET /api/transcripts/{transcript_id}

获取指定转写记录的详情（包含 segments）。

**响应**:
```json
{
  "id": 1,
  "media_path": "string",
  "created_at": "2023-01-01T00:00:00",
  "segments": [
    {
      "index": 0,
      "spk_id": "string",
      "sentence": "string",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ],
  "media_type": "video",
  "summaries": [],
  "translations": {}
}
```

#### DELETE /api/transcripts/{transcript_id}

删除指定的转写记录及其对应的视频文件。该操作会同时删除视频文件和数据库记录，不可恢复。

**响应**:
```json
{
  "success": true,
  "message": "string",
  "transcript_id": 1
}
```

### 翻译功能

#### POST /api/transcripts/{transcript_id}/translate

翻译转写内容。后台异步翻译，使用轮询查询进度。

**请求体**:
```json
{
  "target_language": "zh",
  "confirmed": true,
  "max_tokens": 4096,
  "source_lang_name": "string",
  "target_lang_name": "string",
  "force_retranslate": false
}
```

**响应**:
```json
{
  "status": "started",
  "transcript_id": 1
}
```

#### GET /api/transcripts/{transcript_id}/translate-progress

获取翻译进度。

**响应**:
```json
{
  "status": "translating",
  "progress": 50,
  "translated_count": 5,
  "total_count": 10,
  "message": "string"
}
```

#### GET /api/transcripts/{transcript_id}/translations

获取已保存的翻译结果。

**响应**:
```json
{
  "translations": {
    "zh": [
      {
        "index": 0,
        "sentence": "string",
        "start_time": 0.0,
        "end_time": 5.0
      }
    ]
  },
  "has_translations": true
}
```

### 总结功能

#### POST /api/summarize

基于句级片段一次性生成总结。

**请求体**:
```json
{
  "segments": [
    {
      "index": 0,
      "sentence": "string",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ],
  "api_key": "string",
  "base_url": "string",
  "model": "string"
}
```

**响应**:
```json
{
  "summaries": [
    {
      "topic": "string",
      "summary": "string",
      "start_time": 0.0,
      "end_time": 10.0
    }
  ]
}
```

#### POST /api/transcripts/{transcript_id}/summaries

保存生成的总结到数据库。

**请求体**:
```json
{
  "summaries": [
    {
      "topic": "string",
      "summary": "string",
      "start_time": 0.0,
      "end_time": 10.0
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "message": "总结已保存",
  "saved": true,
  "transcript_id": 1
}
```

#### GET /api/transcripts/{transcript_id}/summaries

获取已保存的总结。

**响应**:
```json
{
  "summaries": [
    {
      "topic": "string",
      "summary": "string",
      "start_time": 0.0,
      "end_time": 10.0
    }
  ],
  "has_summaries": true
}
```

### 聊天功能

#### POST /api/chat

基于分句内容进行问答。

**请求体**:
```json
{
  "segments": [
    {
      "index": 0,
      "sentence": "string",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ],
  "question": "string",
  "api_key": "string",
  "base_url": "string",
  "model": "string"
}
```

**响应**:
```json
{
  "answer": "string"
}
```

#### POST /api/transcripts/{transcript_id}/chat-messages

保存chat消息到数据库。

**请求体**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string",
      "timestamp": "string"
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "message": "chat消息已保存",
  "transcript_id": 1
}
```

#### GET /api/transcripts/{transcript_id}/chat-messages

获取已保存的chat消息。

**响应**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string",
      "timestamp": "string"
    }
  ],
  "has_messages": true
}
```

#### DELETE /api/transcripts/{transcript_id}/chat-messages

清空chat消息。

**响应**:
```json
{
  "success": true,
  "message": "chat消息已清空",
  "transcript_id": 1
}
```

### 进度查询

#### GET /api/progress/stream-all

SSE 推送全部进度事件（订阅 Redis pubsub channel `progress_channel`）。

客户端可订阅该路由来接收系统中所有任务的进度更新，从而替代轮询。

**响应**: Server-Sent Events 流

### 缩略图

#### GET /api/thumbnails/{transcript_id}

获取视频缩略图。

**查询参数**:
- `start_time`: 开始时间（毫秒）
- `end_time`: 结束时间（毫秒）
- `width`: 缩略图宽度（默认320）

**响应**:
```json
{
  "success": true,
  "data": "data:image/jpeg;base64,/9j/4AAQ..."
}
```