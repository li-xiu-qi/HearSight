# Supabase 配置

这个目录包含了Supabase自托管服务的配置和启动文件。

## 文件说明

- `.env`: 环境变量配置文件，包含数据库密码、JWT密钥等敏感信息
- `supabase-docker-compose.yml`: Docker Compose配置文件，用于启动Supabase服务栈
- `volumes.example/`: 示例卷目录，包含Supabase服务所需的持久化数据目录结构（包括api、db、functions、logs、pooler等子目录）。当 Supabase 服务启动失败（通常由于配置文件缺失）时，可复制此目录为 `volumes` 并根据需要修改其中的配置。

## 重要提醒

在使用前，请务必修改`.env`文件中的默认密码和密钥，特别是：

- `POSTGRES_PASSWORD`: 数据库密码
- `JWT_SECRET`: JWT签名密钥（至少32字符）
- `SERVICE_ROLE_KEY`: 服务角色密钥
- `DASHBOARD_USERNAME` 和 `DASHBOARD_PASSWORD`: 管理面板登录凭据

如果 Supabase 服务启动失败（通常由于 volumes 目录或配置文件缺失），请复制`volumes.example`目录并重命名为`volumes`，以创建Supabase服务的持久化数据目录。

## 设置步骤

1. 修改 `.env` 文件中的默认密码和密钥。

2. （可选）如果 Supabase 服务启动失败，可复制 `volumes.example` 目录并重命名为 `volumes`：

   - Linux/Mac：

     ```bash
     cp -r volumes.example volumes
     ```

   - Windows (cmd)：

     ```cmd
     xcopy volumes.example volumes /E /I /H
     ```

在backend/supabase目录下运行：

```bash
docker compose -f docker-compose.yml up -d
```

服务启动后，可以通过以下地址访问：

- Supabase Studio: <http://localhost:3000>
- API Gateway: <http://localhost:8000>
- 数据库: localhost:5432

## 停止服务

```bash
docker compose -f docker-compose.yml down
```

## 注意事项

- 确保Docker和Docker Compose已安装
- 首次启动可能需要一些时间来初始化数据库
- 生产环境使用前，请更换所有默认的密钥和密码

## 代码检查

Supabase Edge Functions 使用 TypeScript 开发，基于 Deno 运行时。推荐使用 Deno 内置工具进行代码检查：

### 代码质量检查

```bash
# 检查所有边缘函数代码
deno lint volumes/functions/

# 检查特定函数
deno lint volumes/functions/rag-ask-public/
```

### 代码格式化

```bash
# 自动格式化代码
deno fmt volumes/functions/

# 检查格式（不修改文件）
deno fmt --check volumes/functions/
```

### 类型检查

```bash
# 检查 TypeScript 类型
deno check volumes/functions/
```

### 配置说明

- `deno.json`: 包含 lint、fmt 和编译选项配置
- 建议在开发时定期运行上述命令，确保代码质量

## 故障排除

### Docker 挂载错误

如果遇到以下错误：

```text
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error mounting "/path/to/your/volumes/logs/vector.yml" to rootfs at "/etc/vector/vector.yml": mount src=/path/to/your/volumes/logs/vector.yml, dst=/etc/vector/vector.yml, dstFd=/proc/thread-self/fd/8, flags=0x5000: not a directory: unknown: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type
```

**原因**：Docker Desktop 的缓存或文件共享状态出现问题，导致挂载失败。

**解决方案**：
运行 `docker system prune` 清理 Docker 缓存，然后重新启动服务：

```bash
docker system prune
docker compose -f supabase-docker-compose.yml up -d --build
```

## 参考文档

- [Supabase官方文档](https://supabase.com/docs)
