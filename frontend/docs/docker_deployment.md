# HearSight 前端 Docker 部署指南

本文档详细介绍如何使用 Docker 部署 HearSight 前端应用。

## 📋 前置要求

- Docker 20.10 或更高版本
- Docker Compose 1.29 或更高版本
- 至少 2GB 可用磁盘空间

## 🐳 部署方式

### 方式一：使用项目根目录的 Docker Compose（推荐）

项目根目录提供了完整的 [docker-compose.cloud.yml](../../../docker-compose.cloud.yml) 文件，可以一键启动包括前端在内的所有服务：

```bash
# 在项目根目录执行
docker-compose -f ../docker-compose.cloud.yml up -d --build
```

此方式将同时启动：

- PostgreSQL 数据库
- Redis 服务
- ASR 后端服务
- 主后端服务
- 前端应用

### 方式二：使用前端独立的 Docker Compose

前端目录下提供了独立的 [docker-compose.yml](../docker-compose.yml) 文件，可用于单独部署前端服务：

```bash
# 在 frontend 目录下执行
docker-compose up -d --build
```

注意：使用独立的 docker-compose 文件时，需要确保后端服务已经在运行并且可以通过网络访问。

### 方式三：直接构建和运行 Docker 镜像

#### 1. 构建 Docker 镜像

```bash
# 在 frontend 目录下执行
docker build -t hearsight-frontend .
```

#### 2. 运行容器

```bash
docker run -d \
  --name hearsight-frontend \
  -p 10000:5173 \
  -e BACKEND_HOST=host.docker.internal \
  -e BACKEND_PORT=9999 \
  -e VITE_BACKEND_URL=http://host.docker.internal:9999 \
  hearsight-frontend
```

## ⚙️ 环境变量配置

Docker 部署时可以通过环境变量进行配置：

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `BACKEND_HOST` | `host.docker.internal` | 后端服务主机地址 |
| `BACKEND_PORT` | `9999` | 后端服务端口 |
| `VITE_BACKEND_URL` | `http://host.docker.internal:9999` | 前端应用连接的后端API地址 |
| `VITE_USE_DOCKER` | `false` | 标识是否在Docker环境中运行 |

## 📁 数据卷挂载

前端应用在 Docker 容器中运行时，通常不需要持久化数据。但在开发阶段，可以通过挂载卷实现实时代码更新：

```bash
docker run -d \
  --name hearsight-frontend \
  -p 10000:5173 \
  -v $(pwd):/app \
  -v /app/node_modules \
  hearsight-frontend
```

## 🔍 健康检查

前端应用提供了健康检查端点：

```bash
curl http://localhost:10000/health
```

## 🧪 故障排除

### 1. 前端无法连接后端

确保后端服务正在运行，并且可以通过网络访问。检查以下配置：

- `BACKEND_HOST` 和 `BACKEND_PORT` 环境变量设置正确
- 防火墙规则允许前后端通信
- 在同一台机器上运行时，使用 `host.docker.internal` 作为后端主机地址

### 2. 页面空白或加载错误

检查浏览器控制台是否有错误信息：

```bash
# 查看容器日志
docker logs hearsight-frontend
```

### 3. 构建失败

清理构建缓存并重新构建：

```bash
docker builder prune
docker build -t hearsight-frontend .
```

## 🔄 更新部署

### 更新到最新版本

```bash
# 拉取最新代码
git pull

# 重新构建并启动服务
docker-compose up -d --build
```

## 🗑️ 清理资源

停止并删除容器：

```bash
docker-compose down
```

删除镜像：

```bash
docker rmi hearsight-frontend
```

清理未使用的 Docker 资源：

```bash
docker system prune
```
