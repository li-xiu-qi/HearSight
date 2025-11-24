# HearSight 前端 API 文档

本文档描述了前端应用与后端服务之间的 API 接口调用。

## 概述

前端通过 HTTP RESTful API 与后端服务进行通信。所有 API 调用都通过 [services/](../src/services/) 目录下的服务模块进行封装。

## 基础配置

### Base URL

API 请求的基础 URL 可以通过环境变量 `VITE_BACKEND_URL` 配置，默认为 `http://localhost:9999`。

### 认证

目前 API 调用不需要额外的认证头，所有认证由后端处理。

## API 模块

### 1. 下载服务 (downloadService)

#### 创建下载任务

```http
POST /api/download
```

**请求体:**
```json
{
  "url": "string",           // 下载URL（必需）
  "job_id": "number",        // 任务ID（必需）
  "sessdata": "string",      // B站SESSDATA（可选）
  "playlist": "boolean",     // 是否下载播放列表（可选，默认false）
  "quality": "string",       // 视频质量（可选，默认"best"）
  "workers": "number"        // 下载线程数（可选，默认1）
}
```

**响应:**
```json
{
  "status": "started",
  "job_id": "number",
  "task_id": "string",
  "message": "string"
}
```

#### 查询下载进度

```http
GET /api/download/{job_id}
```

**响应:**
```json
{
  "job_id": "string",
  "status": "string",
  "progress": "number",
  "message": "string"
}
```

### 2. 转写服务 (transcriptService)

#### 获取转写记录列表

```http
GET /api/transcripts
```

**响应:**
```json
[
  {
    "id": "string",
    "title": "string",
    "created_at": "string",
    "duration": "number",
    "status": "string"
  }
]
```

#### 获取转写记录详情

```http
GET /api/transcripts/{id}
```

**响应:**
```json
{
  "id": "string",
  "title": "string",
  "created_at": "string",
  "duration": "number",
  "status": "string",
  "segments": [
    {
      "id": "string",
      "start": "number",
      "end": "number",
      "text": "string"
    }
  ],
  "full_text": "string"
}
```

#### 删除转写记录

```http
DELETE /api/transcripts/{id}
```

**响应:**
```json
{
  "message": "string"
}
```

### 3. 翻译服务 (translateService)

#### 创建翻译任务

```http
POST /transcripts/{transcript_id}/translate
```

**请求体:**
```json
{
  "target_lang_code": "string",      // 目标语言代码（默认"zh"）
  "source_lang_code": "string",      // 源语言代码（可选）
  "confirmed": "boolean",            // 是否确认（默认true）
  "max_tokens": "number",            // 最大token数（默认4096）
  "source_lang_display_name": "string", // 源语言显示名称（可选）
  "target_lang_display_name": "string", // 目标语言显示名称（可选）
  "force_retranslate": "boolean"     // 强制重新翻译（默认false）
}
```

**响应:**
```json
{
  "status": "string",
  "transcript_id": "number"
}
```

#### 获取翻译结果

```http
GET /transcripts/{transcript_id}/translations
```

**响应:**
```json
{
  "translations": {
    "language_code": [
      // 翻译后的片段数组
    ]
  },
  "has_translations": "boolean"
}
```

### 4. 摘要服务 (summaryService)

#### 生成摘要

```http
POST /api/summaries
```

**请求体:**
```json
{
  "transcript_id": "string",
  "length": "string" // "short", "medium", "long"
}
```

**响应:**
```json
{
  "summary_id": "string",
  "content": "string",
  "created_at": "string"
}
```

#### 获取摘要列表

```http
GET /api/summaries?transcript_id={transcript_id}
```

**响应:**
```json
[
  {
    "summary_id": "string",
    "content": "string",
    "created_at": "string",
    "length": "string"
  }
]
```

### 5. 聊天服务 (chatService)

#### 创建聊天会话

```http
POST /api/chat/sessions
```

**请求体:**
```json
{
  "title": "string"
}
```

**响应:**
```json
{
  "session_id": "string",
  "title": "string",
  "created_at": "string"
}
```

#### 获取聊天会话列表

```http
GET /api/chat/sessions
```

**响应:**
```json
[
  {
    "session_id": "string",
    "title": "string",
    "created_at": "string",
    "updated_at": "string"
  }
]
```

#### 发送聊天消息

```http
POST /api/chat/sessions/{session_id}/messages
```

**请求体:**
```json
{
  "content": "string",
  "transcript_ids": ["string"]
}
```

**响应:**
```json
{
  "message_id": "string",
  "role": "string", // "user" or "assistant"
  "content": "string",
  "timestamp": "string"
}
```

#### 获取聊天消息历史

```http
GET /api/chat/sessions/{session_id}/messages
```

**响应:**
```json
[
  {
    "message_id": "string",
    "role": "string",
    "content": "string",
    "timestamp": "string"
  }
]
```

### 6. 缩略图服务 (thumbnailService)

#### 获取缩略图

```http
GET /api/thumbnails/{transcript_id}
```

**响应:**
```json
{
  "thumbnails": [
    {
      "timestamp": "number",
      "url": "string"
    }
  ]
}
```

### 7. 上传服务 (uploadService)

#### 上传文件

```http
POST /api/upload
Content-Type: multipart/form-data
```

**请求体:**
```
file: (binary)
```

**响应:**
```json
{
  "job_id": "string"
}
```

#### 查询上传进度

```http
GET /api/upload/{job_id}
```

**响应:**
```json
{
  "job_id": "string",
  "status": "string",
  "progress": "number",
  "message": "string"
}
```

### 8. 进度服务 (progressService)

#### 查询任务进度

```http
GET /api/progress/{job_id}
```

**响应:**
```json
{
  "job_id": "string",
  "status": "string",
  "progress": "number",
  "message": "string"
}
```

## 错误处理

所有 API 错误都会返回以下格式的响应：

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object"
  }
}
```

常见的错误码：
- `400`: 请求参数错误
- `404`: 资源未找到
- `500`: 服务器内部错误

## 数据模型

### Transcript (转写记录)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 转写记录ID |
| title | string | 标题 |
| created_at | string | 创建时间 |
| duration | number | 时长（秒） |
| status | string | 状态 |

### Segment (片段)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 片段ID |
| start | number | 开始时间（秒） |
| end | number | 结束时间（秒） |
| text | string | 文本内容 |

### Summary (摘要)

| 字段 | 类型 | 描述 |
|------|------|------|
| summary_id | string | 摘要ID |
| content | string | 摘要内容 |
| created_at | string | 创建时间 |
| length | string | 长度类型 |

### ChatSession (聊天会话)

| 字段 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话ID |
| title | string | 标题 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### ChatMessage (聊天消息)

| 字段 | 类型 | 描述 |
|------|------|------|
| message_id | string | 消息ID |
| role | string | 角色（user/assistant） |
| content | string | 内容 |
| timestamp | string | 时间戳 |