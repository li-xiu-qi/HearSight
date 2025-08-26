Docker 使用说明
=================

本文件简要说明如何用 Docker 与 docker-compose 在本项目中运行、开发与调试后端（FastAPI）与前端（构建后静态文件由 nginx 提供）。

快速约定
- 项目根目录：包含 `docker-compose.yml`、`Dockerfile.backend`、`frontend/Dockerfile`。
- 默认端口（可通过环境变量覆盖）：
	- 后端（容器内）: 8000
	- 后端（宿主映射，默认）: 9999 （由 `docker-compose.yml` 的 `${BACKEND_PORT:-9999}:8000` 控制）
	- 前端（宿主映射）: 10000 （由 `${FRONTEND_PORT:-10000}:80` 控制）

快速开始（使用 docker-compose）
--------------------------------

1. 构建并启动（前台）：

```cmd
docker-compose up --build
```

2. 在后台运行：

```cmd
docker-compose up --build -d
```

3. 停止并移除容器：

```cmd
docker-compose down
```

验证服务是否就绪
- 前端（静态页面）：打开 http://localhost:10000
- 后端（API）：

```cmd
curl -i http://localhost:9999/docs
curl -i http://localhost:9999/api/transcripts?limit=1
```

注意：如果你在 `docker-compose.yml` 中覆盖了环境变量（例如在 `.env` 中设置了 `BACKEND_PORT` 或 `FRONTEND_PORT`），请相应修改以上端口。

开发模式（本地开发，不使用 nginx）
----------------------------------

本项目前端使用 Vite，开发时建议直接在宿主机运行 Vite dev server，它会使用 `frontend/vite.config.ts` 中的 proxy 将 `/api` 请求转发到后端（便于热重载与快速调试）。

前端开发运行：

```cmd
cd frontend
npm install
npm run dev
```

默认情况下 Vite 会在一个端口（通常 5173/3000）启动，并代理 `/api` 到后端开发地址；查看终端输出获得实际端口。

生产/Compose 模式（build 后静态文件）
----------------------------------

构建后的前端静态文件会被 `frontend/Dockerfile` 的 runtime 阶段复制到 nginx，并使用 `frontend/nginx.conf.template` 中的反向代理将 `/api` 转发到 `http://backend:8000`（容器网络内部地址）。因此在 docker-compose 中运行时，nginx 会负责把浏览器对 `/api/*` 的请求转发到后端容器。

在容器内调试后端（推荐做法）
--------------------------------

如果需要在容器中进行 Python 调试（例如使用 VSCode attach 调试），建议使用一个 `docker-compose.override.yml` 来临时替换部分服务配置，而不是修改主 `docker-compose.yml`。示例 `docker-compose.override.yml`：

```yaml
services:
	backend:
		ports:
			- "5678:5678"   # debugpy 端口
		volumes:
			- ./:/app        # 源码挂载为可写，以启用 --reload
		command: >
			sh -c "pip install debugpy && python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

使用方法：

```cmd
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

然后在 VSCode 中使用下列 `launch.json` 附加配置：

```json
{
	"name": "Python: Attach (debugpy)",
	"type": "python",
	"request": "attach",
	"connect": { "host": "localhost", "port": 5678 },
	"pathMappings": [ { "localRoot": "${workspaceFolder}", "remoteRoot": "/app" } ]
}
```

或直接在宿主机用 curl 测试后端 API：

```cmd
curl -i http://localhost:9999/api/transcripts?limit=1
```

常见问题与提示
- 我们的 `docker-compose.yml` 默认把源码挂载为只读 (`./:/app:ro`)。如果你要在容器内做开发（自动重载、临时安装包、调试），需要用 override 文件把挂载改为可写（上面 override 示例已演示）。
- Vite 的 dev proxy 仅在 `npm run dev` 时生效，build 后静态文件需要由 nginx 或其他反向代理来处理 `/api` 转发。
- 如果前端在容器中访问后端出现 404，请确认：
	1. nginx 配置是否保留了 `/api` 前缀（`proxy_pass` 末尾不要带 `/`，我们已将模板改为 `proxy_pass http://backend:8000;`）；
	2. frontend 的 `BACKEND_HOST`/`BACKEND_PORT` 环境变量在容器内是否指向 `backend:8000`（`docker-compose.yml` 已用 `${BACKEND_PORT:-8000}` 默认）；

如果需要我可以：
- 帮你添加 `docker-compose.override.yml` 文件并运行一次 compose 来验证；
- 或者在当前环境里执行 `docker-compose up --build` 并贴出 curl 输出以便确认服务是否正常。

-- 结束

