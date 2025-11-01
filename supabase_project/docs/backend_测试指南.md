# 测试指南

supabase_project 的测试和代码检查使用 lefthook 进行统一管理。

## 本地脚本

### 手动运行检查

```bash
cd supabase_project/tests
npm run lint       # 运行 ESLint 检查
npm run lint:fix   # 自动修复代码格式
```

## Git 提交检查

git 提交时会自动通过 lefthook 进行代码检查。

更多信息请查看根目录的 [Lefthook 使用指南](../../docs/lefthook-usage-guide.md)。

## 测试架构

```text
tests/
├── package.json       # Node.js 依赖
├── vitest.config.js   # Vitest 配置
├── hello.test.js      # 健康检查测试

```

## 快速开始

### 启动 Supabase 服务

```bash
cd supabase_project/supabase
docker compose up -d
```

等待服务完全启动，约 30 秒。

### 安装测试依赖

```bash
cd supabase_project/tests
npm install
```

### 运行测试

```bash
npm test
```

输出示例：

```text
✓ tests/hello.test.js (2)


Test Files  1 passed (3)
     Tests  1 passed (5)
```

**注意**：需要启动 AIbackend 服务才能通过 RAG 和 SQL 接口测试。

## 测试策略

### 测试范围

- ✅ 基本响应：验证 HTTP 状态码
- ✅ 认证机制：验证 token 验证流程
- ⚠️ 复杂逻辑：不需要测试详细业务逻辑

### 测试类型

- **快速测试**：验证 API 端点可用性
- **集成测试**：验证 Supabase Auth 与 Edge Functions 集成
- **错误处理**：验证异常情况响应

## 测试用例

### hello 函数

验证 hello 函数返回 200 状态码。

## 调试技巧

### 查看服务日志

```bash
cd backend/supabase
docker compose logs -f
```

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [可用API指南](backend_可用API指南.md)
- [Docker 部署指南](backend_Docker_部署指南.md)
