# Docker 部署指南

Backend 基于 Supabase 自托管方案，通过 Docker Compose 部署。

## 快速启动

### 启动服务

```bash
cd backend/supabase
docker compose up -d
```

### 服务访问

启动完成后可访问：

- Kong API 网关：<http://localhost:8000>
- Supabase Studio：<http://localhost:54323>
- PostgreSQL：localhost:54322

### 验证启动

```bash
# 检查容器状态
docker compose ps

# 测试 API
curl http://localhost:8000/functions/v1/hello
```

### 停止服务

```bash
docker compose down
```

## 环境配置

创建 `backend/supabase/.env` 配置环境变量：

```bash
# 数据库
POSTGRES_PASSWORD=postgres

# JWT
JWT_SECRET=your_secret_key

# AIbackend 集成
AIBACKEND_URL=http://host.docker.internal:8001
```

## Docker 服务

### 主要服务

Supabase 包含以下核心服务：

- **PostgreSQL**：数据库存储
- **Kong**：API 网关和路由
- **Supabase Auth**：用户认证
- **Supabase Studio**：管理界面

### 容器管理

```bash
# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 清除数据并重新启动
docker compose down -v
docker compose up -d
```

## 部署验证

### 检查服务

```bash
# 查看容器状态
docker compose ps

# 查看服务日志
docker compose logs
```

### 测试连接

```bash
# 测试 API 网关
curl http://localhost:8000/functions/v1/hello

# 测试数据库
docker exec <db_container> pg_isready -U postgres
```

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [配置指南](backend_配置指南.md)
- [可用API指南](backend_可用API指南.md)
