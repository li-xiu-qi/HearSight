FROM node:18-alpine AS build
WORKDIR /app
# 使用国内 npm 镜像以加速依赖安装
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com
COPY frontend/package.json frontend/package-lock.json* ./
COPY frontend/tsconfig.json frontend/vite.config.ts ./
RUN npm ci --legacy-peer-deps || npm install
COPY frontend/ ./
RUN npm run build
FROM nginx:stable-alpine AS runtime
WORKDIR /app
# copy built static files to nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html
# copy nginx config template
COPY frontend/nginx.conf.template /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
