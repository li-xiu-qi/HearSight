FROM node:18-alpine AS build
WORKDIR /app
# 使用国内 npm 镜像以加速依赖安装
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com
COPY frontend/package.json frontend/package-lock.json* ./
COPY frontend/tsconfig.json frontend/vite.config.ts ./
RUN npm ci --legacy-peer-deps || npm install
COPY frontend/ ./
RUN npm run build
FROM node:18-alpine AS runtime
WORKDIR /app
# copy built static files
COPY --from=build /app/dist ./dist
# install a small static server
RUN npm install -g serve
ENV PORT=80
EXPOSE 80
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:$PORT"]
