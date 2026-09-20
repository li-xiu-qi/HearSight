# API 文档导航

本项目有两类后端接口：主 API（全栈应用的 API 路由）与语音识别服务 API。

## 主 API（Next.js 全栈应用）

原独立后端已并入 Next.js 应用，接口即 `next-app/src/app/api/` 下的路由文件，请求路径与旧版一致（`/api/...`）。

- **服务地址**: `http://localhost:9187`（由 `scripts/start-local.sh` 启动，端口可配）
- **交互式文档**: 不再提供自动生成的文档页，按下方模块直接查对应路由文件

主要功能模块（括号内为路由文件位置）：

- 文件上传与媒体管理：`api/upload/route.ts`、`api/upload/rename/route.ts`、`api/transcripts/route.ts`、`api/transcripts/[id]/route.ts`
- 进度推送：`api/progress/task/[jobId]/route.ts`、`api/progress/download/[jobId]/route.ts`、`api/progress/stream-all/route.ts`
- 摘要与翻译：`api/summarize/route.ts`、`api/transcripts/[id]/summaries/route.ts`、`api/transcripts/[id]/translate/route.ts`、`api/transcripts/[id]/translate/stream/route.ts`
- 问答：`api/chat/stream/route.ts`、`api/chat/streaming/route.ts`、`api/chat/[taskId]/stream/route.ts`、`api/chat-sessions/route.ts`、`api/transcripts/[id]/chat-messages/route.ts`
- 媒体下载与静态资源：`api/download/route.ts`、`api/static/[...path]/route.ts`、`api/thumbnails/[id]/route.ts`

注意流式问答用的是自定义行协议（`[chunk]...[/chunk]` / `[done][/done]` / `[error]...[/error]`），不是标准 SSE。

## ASR Backend API 文档

HearSight 语音识别服务 API，提供语音转文本功能，本地 FunASR 与云端两种模式。

- **文档位置**: [ASRBackend/docs/api.md](../ASRBackend/docs/api.md)
- **服务地址**: `http://localhost:8003`
- **交互式文档**: 启动 ASR 服务后访问 `http://localhost:8003/docs`

主要功能模块：
- 音频转文字：将音频文件转换为文本
- URL 转录：直接从 URL 获取音频并转录
- 文件上传转录：上传本地音频文件进行转录

## 相关文档

- [ASR 服务设计](../ASRBackend/docs/ASR_服务设计文档.md)
- [ASR 快速开始](../ASRBackend/docs/快速开始.md)
- [项目结构](项目结构.md)
- [快速开始](快速开始.md)
