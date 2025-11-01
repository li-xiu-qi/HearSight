# 快速开始

Backend 基于 Supabase Edge Functions，通过 Docker Compose 快速启动。

## 启动服务

### 进入目录

```bash
cd backend/supabase
```

### 启动 Supabase

```bash
docker compose up -d
```

等待服务完全启动，约 30 秒。

## 访问服务

启动后可访问：

- Kong API 网关：<http://localhost:8000>
- Supabase Studio：<http://localhost:54323>
- PostgreSQL：localhost:54322

## 验证启动

```bash
curl http://localhost:8000/functions/v1/hello
```

预期返回：

```json
{"message":"Hello from hello!"}
```

## 停止服务

```bash
docker compose down
```

## 下一步

- [架构概述](backend_架构概述.md)
- [可用API指南](backend_可用API指南.md)
- [开发工作流程指南](backend_开发工作流程指南.md)
