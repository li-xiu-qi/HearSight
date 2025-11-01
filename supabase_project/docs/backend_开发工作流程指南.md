# 开发工作流程指南

Backend 采用标准的开发工作流，包括代码开发、测试、提交和部署。

## Git 工作流

### 提交前

运行测试确保功能正常：

```bash
cd backend/tests
npm test
```

运行 lefthook 代码检查：

```bash
# 运行所有检查
lefthook run pre-commit

# 或只运行 backend 相关的检查
lefthook run pre-commit --only backend-tests-lint
lefthook run pre-commit --only backend-supabase-format
lefthook run pre-commit --only backend-supabase-lint
```

更多信息请查看根目录的 [LEFTHOOK_SETUP.md](../../LEFTHOOK_SETUP.md)。

### 提交代码

```bash
git add .
git commit -m "feat: 功能描述"
git push origin dev
```

### 提交信息规范

- `feat: 新功能` - 新增 Edge Function 或功能
- `fix: 缺陷修复` - 修复已有函数
- `refactor: 代码重构` - 重构现有代码
- `docs: 文档更新` - 文档变更
- `chore: 构建变更` - 配置、依赖等变更

## 调试技巧

### 查看日志

```bash
docker compose logs -f kong
docker compose logs -f db
```

### 手动测试

```bash
curl http://localhost:8000/functions/v1/hello
```

### 常见问题

- **函数无响应**：检查 Docker 容器状态，运行 `docker compose ps`
- **认证失败**：验证 JWT token 和环境变量配置
- **数据库连接失败**：检查 PostgreSQL 容器是否启动

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [Edge Functions 开发指南](backend_Edge_Functions_开发指南.md)
- [可用API指南](backend_可用API指南.md)
- [测试指南](backend_测试指南.md)
