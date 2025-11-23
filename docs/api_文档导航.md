# API 文档导航

本项目包含两个主要后端的 API 文档：

## Backend API 文档

HearSight 主后端 API，提供媒体处理、转写、总结、翻译和聊天等功能。

- **文档位置**: [backend/docs/api.md](../backend/docs/api.md)
- **服务地址**: `http://localhost:9999`
- **交互式文档**: 启动后端服务后访问 `http://localhost:9999/docs`

主要功能模块：
- 媒体下载：从哔哩哔哩等平台下载视频
- 文件上传：上传本地音视频文件
- 转写管理：管理ASR转写结果
- 翻译服务：将转写内容翻译为多种语言
- 摘要生成：基于内容生成结构化摘要
- 聊天交互：基于转写内容进行问答

## ASR Backend API 文档

HearSight 语音识别后端 API，提供语音转文本功能。

- **文档位置**: [ASRBackend/docs/api.md](../ASRBackend/docs/api.md)
- **服务地址**: `http://localhost:8003`
- **交互式文档**: 启动 ASR 后端服务后访问 `http://localhost:8003/docs`

主要功能模块：
- 音频转文字：将音频文件转换为文本
- URL转录：直接从URL获取音频并转录
- 文件上传转录：上传本地音频文件进行转录

## 快速开始

1. 启动后端服务：`python main.py` (backend/)
2. 启动 ASR 后端服务：`python main.py` (ASRBackend/)
3. 访问交互式 API 文档查看详细接口信息

## 相关文档

- [Backend 数据库设计](../backend/docs/database_schema.md)
- [Backend 聊天系统设计](../backend/docs/chat_system_design.md)
- [ASR 服务设计](../ASRBackend/docs/ASR_服务设计文档.md)