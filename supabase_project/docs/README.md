# Backend 文档

Backend 是 AIASys 的 API 网关层，基于 Supabase Edge Functions。

## 快速导航

### 新用户入门

1. [快速开始](backend_快速开始指南.md) - 5 分钟启动 Backend 服务
2. [架构概述](backend_架构概述.md) - 了解 Backend 的整体设计

### 开发相关

- [开发工作流程指南](backend_开发工作流程指南.md) - Git 工作流和调试技巧
- [Edge Functions 开发指南](backend_Edge_Functions_开发指南.md) - 如何开发 Edge Functions 和 SQL
- [可用API指南](backend_可用API指南.md) - API 端点文档
- [数据库管理指南](backend_数据库管理指南.md) - 数据库表结构和迁移脚本

### 配置与部署

- [配置指南](backend_配置指南.md) - Supabase 环境变量配置
- [Docker 部署指南](backend_Docker_部署指南.md) - Docker 容器部署和故障排除

### 参考资料

- [文件组织指南](backend_文件组织指南.md) - 项目目录结构说明
- [测试指南](backend_测试指南.md) - 如何运行和编写测试

## 核心概念

### Edge Functions

Backend 的所有 API 都通过 Supabase Edge Functions（Deno 运行时）实现，位于 `backend/supabase/volumes/functions/` 目录。

### 数据库

使用 PostgreSQL 数据库存储应用数据，迁移脚本放在 `backend/supabase/migrations/` 目录。

### 测试

使用 Node.js + Vitest 进行自动化测试，测试文件位于 `backend/tests/` 目录。

## 常见任务

### 启动开发环境

→ 阅读[快速开始](backend_快速开始指南.md)

### 创建新的 API 接口

→ 阅读[Edge Functions 开发指南](backend_Edge_Functions_开发指南.md)

### 查看可用的 API 端点

→ 阅读[可用API指南](backend_可用API指南.md)

### 运行测试

→ 阅读[测试指南](backend_测试指南.md)

### 配置环境变量

→ 阅读[配置指南](backend_配置指南.md)

### 创建数据库表

→ 阅读[Edge Functions 开发指南](backend_Edge_Functions_开发指南.md)中的 SQL 部分或[数据库管理指南](backend_数据库管理指南.md)
