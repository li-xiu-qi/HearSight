# 架构概述

Backend 基于 Supabase Edge Functions，通过 TypeScript/Deno 实现无服务器 API 网关，与 AIbackend 集成提供 RAG 问答服务。

## 整体架构

```text
backend/
├── supabase/                    # Supabase 自托管配置
│   ├── docker-compose.yml      # 服务编排配置
│   ├── deno.json               # Deno 运行时配置
│   ├── import_map.json         # 依赖别名映射
│   └── volumes/
│       └── functions/          # Edge Functions 源码
│           ├── hello/          # 健康检查
│           ├── main/           # API 路由与 JWT 验证
├── tests/                      # Node.js + Vitest 自动化测试
└── docs/                       # 文档
```

## 核心组件

### Edge Functions

所有 API 通过 Deno 运行时的 Edge Functions 实现，使用 TypeScript 开发。

#### hello 函数

健康检查端点，用于验证服务运行状态。

#### main 函数

API 网关与路由入口，负责：

- 请求路由和分发
- JWT 令牌验证（可配置）
- 转发到对应业务函数

### Supabase 服务

- **Kong API 网关**：负责路由 HTTP 请求到 Edge Functions
- **Supabase Auth**：管理用户认证与 JWT 令牌
- **PostgreSQL**：应用数据存储
- **Supabase Storage**：文件存储服务

## 与 AIbackend 的集成

Edge Functions 通过 HTTP 调用与 AIbackend 通信，基于环境变量 `AIBACKEND_URL` 配置。

集成模式：

- **认证集成**：`rag-ask` 调用 AIbackend 的 `/rag/ask` 接口
- **公开集成**：`rag-ask-public` 调用 AIbackend 的 `/rag/ask-public` 接口

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [可用API指南](backend_可用API指南.md)
- [Edge Functions 开发指南](backend_Edge_Functions_开发指南.md)
- [Docker 部署指南](backend_Docker_部署指南.md)
- [配置指南](backend_配置指南.md)
