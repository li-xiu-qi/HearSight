# ASR Backend Docker 部署指南

本文档介绍如何使用 Docker 部署 ASR Backend 服务。

## 概述

ASR Backend 提供了两种 Docker 镜像构建方式：

- **云端模式**: 使用 [Dockerfile.cloud](../Dockerfile.cloud) 构建轻量级镜像，依赖阿里云 DashScope API
- **本地模式**: 使用 [Dockerfile.local](../Dockerfile.local) 构建完整镜像，包含本地 FunASR 模型

## 构建镜像

### 云端模式镜像

```bash
# 在 ASRBackend 目录下执行
docker build -f Dockerfile.cloud -t hearsight-asr-cloud .
```

### 本地模式镜像

```bash
# 在 ASRBackend 目录下执行
docker build -f Dockerfile.local -t hearsight-asr-local .
```

## 运行容器

### 云端模式容器

```bash
docker run -d \
  --name asr-backend-cloud \
  -p 8003:8003 \
  -e ASR_MODE=cloud \
  -e DASHSCOPE_API_KEY=your-api-key \
  hearsight-asr-cloud
```

### 本地模式容器

```bash
docker run -d \
  --name asr-backend-local \
  -p 8003:8003 \
  -e ASR_MODE=local \
  hearsight-asr-local
```

## Docker Compose 部署

项目提供了两个专门用于 ASR Backend 的 Docker Compose 配置文件：

### 云端环境部署

使用 [docker-compose.cloud.yml](../docker-compose.cloud.yml) 部署云端模式：

```bash
# 在 ASRBackend 目录下执行
docker-compose -f docker-compose.cloud.yml up -d
```

### 本地环境部署

使用 [docker-compose.local.yml](../docker-compose.local.yml) 部署本地模式：

```bash
# 在 ASRBackend 目录下执行
docker-compose -f docker-compose.local.yml up -d
```

在 Docker Compose 配置中，ASR Backend 服务定义如下：

### 云端模式配置 (docker-compose.cloud.yml)

```yaml
version: '3.8'

services:
  asr-backend:
    build:
      context: .
      dockerfile: Dockerfile.cloud
    container_name: hearsight-asr-backend-cloud
    restart: unless-stopped
    env_file: .env
    ports:
      - "${ASR_BACKEND_PORT:-8003}:8003"
    environment:
      - ASR_MODE=cloud
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 本地模式配置 (docker-compose.local.yml)

```yaml
version: '3.8'

services:
  asr-backend:
    build:
      context: .
      dockerfile: Dockerfile.local
    container_name: hearsight-asr-backend-local
    restart: unless-stopped
    env_file: .env
    ports:
      - "${ASR_BACKEND_PORT:-8003}:8003"
    environment:
      - ASR_MODE=local
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 环境变量配置

Docker 环境中支持以下环境变量：

### 基础配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ASR_MODE` | 运行模式，可选 `local` 或 `cloud` | `cloud` |
| `PORT` | 服务端口 | `8003` |
| `DEBUG` | 调试模式 | `false` |

### 云端模式配置

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key | 是 |
| `DASHSCOPE_MODEL` | DashScope 模型 | 否，默认 `paraformer-v2` |
| `DASHSCOPE_LANGUAGE_HINTS` | 语言提示 | 否，默认 `zh,en` |
| `SUPABASE_URL` | Supabase URL | 否，文件上传时必需 |
| `SUPABASE_KEY` | Supabase API Key | 否，文件上传时必需 |
| `SUPABASE_BUCKET_NAME` | Supabase 存储桶名称 | 否，默认 `test-public` |
| `SUPABASE_FOLDER_NAME` | Supabase 文件夹名称 | 否，默认 `asr` |

### 本地模式配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LOCAL_MODEL_NAME` | FunASR 模型名称 | `paraformer-zh` |
| `LOCAL_MODEL_REVISION` | FunASR 模型版本 | `v2.0.4` |
| `LOCAL_VAD_MODEL` | VAD 模型名称 | `fsmn-vad` |
| `LOCAL_VAD_MODEL_REVISION` | VAD 模型版本 | `v2.0.4` |
| `LOCAL_PUNC_MODEL` | 标点模型名称 | `ct-punc-c` |
| `LOCAL_PUNC_MODEL_REVISION` | 标点模型版本 | `v2.0.4` |
| `LOCAL_SPK_MODEL` | 说话人模型名称 | `cam++` |

## 健康检查

容器内置健康检查，通过访问 `/health` 端点验证服务状态：

```bash
curl http://localhost:8003/health
```

预期响应：

```json
{
  "status": "healthy",
  "service": "ASR Backend",
  "mode": "cloud"
}
```

## 故障排查

### 查看日志

```bash
# 查看容器日志
docker logs asr-backend-cloud

# 实时查看日志
docker logs -f asr-backend-cloud
```

### 常见问题

1. **端口冲突**：修改 `-p` 参数映射到其他端口
2. **API Key 无效**：检查 `DASHSCOPE_API_KEY` 环境变量是否正确设置
3. **模型加载失败**（本地模式）：检查网络连接和存储空间
4. **文件上传失败**：检查 Supabase 相关配置是否正确

### 进入容器调试

```bash
docker exec -it asr-backend-cloud /bin/bash
```