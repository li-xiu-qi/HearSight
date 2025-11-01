# 文件组织指南

Backend 采用模块化结构组织 Edge Functions、配置和文档。

## 目录结构

```text
backend/
├── supabase/              # Supabase 配置和函数源码
│   ├── docker-compose.yml # 服务编排
│   ├── deno.json         # Deno 配置
│   ├── import_map.json   # 依赖别名映射
│   ├── migrations/       # 数据库迁移脚本
│   └── volumes/
│       └── functions/
│           ├── hello/    # 健康检查函数
│           ├── main/     # API 路由和 JWT 验证
├── tests/               # Node.js + Vitest 自动化测试
├── docs/                # 文档
└── .env                # 环境变量配置
```

## Edge Functions 组织

### 命名约定

- kebab-case：如 `rag-ask`, `rag-ask-public`
- 函数名应反映功能

### 函数结构

每个函数为独立目录，包含 `index.ts` 入口文件。

### 函数分类

#### main 函数

API 网关，处理路由和 JWT 验证。

#### 业务函数

如 `rag-ask`、`rag-ask-public`，实现具体功能。

#### public 后缀

标识公开接口，无需认证。

## 配置管理

环境变量存储在 `.env` 文件，通过 Docker Compose 注入。

主要配置：

- `SUPABASE_URL`：Supabase 服务地址
- `AIBACKEND_URL`：AIbackend 服务地址
- `JWT_SECRET`：JWT 签名密钥

## 数据库迁移

SQL 初始化脚本存放在 `backend/supabase/migrations/` 目录。

命名格式：`YYYYMMDDHHMMSS_描述.sql`

Supabase 自动按字典序执行这些脚本。

## 测试组织

```text
tests/
├── package.json      # Node.js 依赖
├── vitest.config.js  # Vitest 配置
├── hello.test.js     # 健康检查测试
└── rag.test.js       # RAG 接口测试
```

测试使用 Node.js + Vitest，直接调用运行中的 Supabase API。

## 文档组织

docs/ 目录包含完整的开发文档：

- 快速开始指南
- 架构概述
- API 文档
- 配置指南
- 开发工作流程
- 测试指南
- 数据库管理指南

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [架构概述](backend_架构概述.md)
- [Edge Functions 开发指南](backend_Edge_Functions_开发指南.md)
