# API 文档导航

本项目包含两个主要后端的 API 文档：

## Backend API 文档

HearSight 主后端 API，提供媒体处理、转写、总结、翻译和聊天等功能。

- **文档位置**: [backend/docs/api.md](backend/docs/api.md)
- **服务地址**: `http://localhost:9999`
- **交互式文档**: 启动后端服务后访问 `http://localhost:9999/docs`

## ASR Backend API 文档

HearSight 语音识别后端 API，提供语音转文本功能。

- **文档位置**: [ASRBackend/docs/api.md](ASRBackend/docs/api.md)
- **服务地址**: `http://localhost:8003`
- **交互式文档**: 启动 ASR 后端服务后访问 `http://localhost:8003/docs`

## 快速开始

1. 启动后端服务：`python main.py` (backend/)
2. 启动 ASR 后端服务：`python main.py` (ASRBackend/)
3. 访问交互式 API 文档查看详细接口信息
