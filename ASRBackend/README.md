# HearSight ASR Backend

HearSight 语音识别后端服务，提供高效的音频转文本功能。支持本地模式（基于 FunASR）和云端模式（基于阿里云 DashScope），满足离线和在线不同场景需求。

## 功能特性

核心功能包括音频文件转文本、URL 音频转文本、音频分段处理、语言识别和说话人分离。

支持两种运行模式灵活切换。本地模式完全离线运行，无需网络连接，对隐私性要求高的环境友好。云端模式轻量级部署，无需本地 GPU，支持自动文件上传存储。

支持多种音频格式输入，包括 MP3、WAV、M4A、AAC 等常见格式。

输出结果包含完整文本转录、语言识别、分段信息和时间戳。

## 快速开始

详细配置和启动说明请查看相关文档。

### 基础启动（云端模式）

需要配置环境变量。复制 `.env.example` 为 `.env` 文件并填入 DashScope API Key。

```bash
# 安装依赖
pip install -r requirements-cloud.txt

# 启动服务
python main.py
```

### 本地模式启动

需要额外的 PyTorch 和模型文件支持。

```bash
pip install -r requirements-local.txt
python main.py
```

服务启动后访问 `http://localhost:8003/docs` 查看 API 文档。

## 文档索引

项目文档包含以下部分：

### 配置与启动文档
- [快速配置文档](docs/快速配置.md) - 介绍环境变量设置和依赖安装
- [快速开始文档](docs/快速开始.md) - 包含本地和云端两种模式的启动步骤

### 系统设计文档
- [设计说明文档](docs/设计说明.md) - 详细说明系统架构、数据流和集成关系
- [API文档](docs/api.md) - 详细的API接口说明

### 部署文档
- [Docker部署指南](docs/docker_deployment.md) - 使用Docker部署ASR Backend的详细说明

## 运行模式对比

| 特性 | 本地模式 | 云端模式 |
|------|--------|--------|
| 离线运行 | 支持 | 不支持 |
| 文件上传 | 支持 | 支持 |
| URL 输入 | 支持 | 支持 |
| GPU 要求 | 需要 | 不需要 |
| 响应速度 | 较慢 | 较快 |
| 多语言 | 单语 | 支持 |
| 网络依赖 | 无 | 需要 |

## API 端点

转录接口支持三种方式：

```bash
POST /asr/transcribe/bytes    # 文件字节流识别（本地模式）
POST /asr/transcribe/url      # URL 直接识别（云端模式）
POST /asr/transcribe/upload   # 文件上传到 Supabase 后识别（云端模式）
```

服务信息接口返回当前运行模式和配置信息。

```bash
GET /asr/info
```

健康检查接口验证服务状态。

```bash
GET /health
```

## 项目结构

```
ASRBackend/
├── main.py                           # 应用入口
├── config.py                         # 配置管理
├── providers.py                      # ASR 提供者实现
├── asr_functions/                    # ASR 处理函数
│   ├── asr_sentence_segments.py     # 音频分段处理
│   ├── segment_normalizer.py         # 分段规范化
│   ├── dashscope_paraformer_v2_transcription.py  # DashScope API
│   └── utils/                        # 工具函数
├── routers/                          # API 路由
│   └── asr_router.py                 # ASR 路由实现
├── services/                         # 业务服务层
│   └── asr_service.py                # ASR 业务逻辑
├── supabase_utils/                   # Supabase 文件操作
│   └── supabase_upload.py            # 文件上传实现
├── docs/                             # 文档
│   ├── 快速配置.md                   # 环境配置指南
│   ├── 快速开始.md                   # 启动运行指南
│   ├── docker_deployment.md          # Docker 部署指南
│   └── 设计说明.md                   # 架构设计文档
├── tests/                            # 测试
├── requirements.txt                  # 通用依赖
├── requirements-local.txt            # 本地模式依赖
├── requirements-cloud.txt            # 云端模式依赖
├── Dockerfile                        # 通用 Docker 镜像
├── Dockerfile.local                  # 本地模式 Docker 镜像
├── Dockerfile.cloud                  # 云端模式 Docker 镜像
├── docker-compose.local.yml          # 本地模式 Docker Compose
└── docker-compose.cloud.yml          # 云端模式 Docker Compose
```

## 使用示例

### Python 调用

```python
import requests

# 文件上传方式（本地模式）
url = "http://localhost:8003/asr/transcribe/bytes"
with open("audio.mp3", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    result = response.json()
    print(result)

# URL 方式（云端模式）
url = "http://localhost:8003/asr/transcribe/url"
response = requests.post(
    url,
    data={"url": "https://example.com/audio.wav"}
)
result = response.json()
print(result)

# 文件上传到Supabase方式（云端模式）
url = "http://localhost:8003/asr/transcribe/upload"
with open("audio.mp3", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    result = response.json()
    print(result)
```

### Shell 调用

```bash
# 文件上传（本地模式）
curl -X POST "http://localhost:8003/asr/transcribe/bytes" \
  -F "file=@audio.mp3"

# URL 输入（云端模式）
curl -X POST "http://localhost:8003/asr/transcribe/url" \
  -d "url=https://example.com/audio.wav"

# 文件上传到Supabase（云端模式）
curl -X POST "http://localhost:8003/asr/transcribe/upload" \
  -F "file=@audio.mp3"

# 获取服务信息
curl http://localhost:8003/asr/info

# 健康检查
curl http://localhost:8003/health
```

## 容器化部署

本项目提供了多个 Dockerfile 支持容器部署。

云端模式轻量级镜像。

```bash
docker build -f Dockerfile.cloud -t hearsight-asr-cloud .
docker run -p 8003:8003 \
  -e ASR_MODE=cloud \
  -e DASHSCOPE_API_KEY=your-key \
  hearsight-asr-cloud
```

本地模式完整镜像，体积较大。

```bash
docker build -f Dockerfile.local -t hearsight-asr-local .
docker run -p 8003:8003 \
  -e ASR_MODE=local \
  hearsight-asr-local
```

使用 docker-compose 启动。

```bash
# 使用项目根目录下的docker-compose文件
docker-compose up asr_backend

# 或使用ASRBackend目录下的专属docker-compose文件
cd ASRBackend
docker-compose -f docker-compose.cloud.yml up -d  # 云端模式
docker-compose -f docker-compose.local.yml up -d  # 本地模式
```

有关更详细的 Docker 部署说明，请参阅 [Docker 部署指南](docs/docker_deployment.md)。

## 配置文档

详见 [快速配置文档](docs/快速配置.md)，包含完整的环境变量说明和依赖安装指南。

## 启动指南

详见 [快速开始文档](docs/快速开始.md)，包含本地和云端模式的详细启动步骤。

## 架构设计

详见 [设计说明文档](docs/设计说明.md)，包含系统架构、数据流和模块说明。

## 故障排查

启动服务后访问健康检查接口验证服务状态。

```bash
curl http://localhost:8003/health
```

若需调试，可开启 DEBUG 模式查看详细日志。

```bash
DEBUG=true python main.py
```

更多常见问题解决方案和调试技巧，请参考设计文档中的监控和调试章节。