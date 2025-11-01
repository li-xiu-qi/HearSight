# Edge Functions 开发指南

Backend 主要开发 Edge Functions，少数情况需要编写 SQL。

## Edge Functions 开发

### 函数位置

所有 Edge Functions 源码位于 `backend/supabase/volumes/functions/` 目录。

现有函数：

- `hello/` - 健康检查
- `main/` - API 路由与 JWT 验证

### 创建新函数

1. 在 `functions/` 下创建新目录，如 `my-function/`
2. 创建 `index.ts` 入口文件
3. 导出 `serve` 函数

### 函数示例

```typescript
import { serve } from "https://deno.land/std@0.177.1/http/server.ts"

serve(async (req) => {
  return new Response("Hello!")
})
```

### 本地开发

启动 Supabase 后，修改函数代码会自动重载。查看日志：

```bash
cd backend/supabase
docker compose logs -f
```

## SQL 查询

Backend 中的数据查询主要通过 Edge Functions 使用 Supabase 客户端进行，不需要直接编写 SQL 查询语句。

### 查询方式

在 Edge Functions 中使用 Supabase JavaScript/TypeScript 客户端进行数据操作：

```typescript
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
)

// 查询数据
const { data, error } = await supabase
  .from("users")
  .select("*")
  .eq("status", "active")

// 插入数据
const { data, error } = await supabase
  .from("users")
  .insert([{ name: "John", email: "john@example.com" }])

// 更新数据
const { data, error } = await supabase
  .from("users")
  .update({ name: "John Doe" })
  .eq("id", userId)

// 删除数据
const { data, error } = await supabase
  .from("users")
  .delete()
  .eq("id", userId)
```

### 优势

- **类型安全**：TypeScript 提供类型检查
- **自动优化**：Supabase 客户端自动优化查询
- **安全**：内置 SQL 注入防护
- **易维护**：代码而非字符串，易于重构

### 复杂查询

对于复杂查询，可以使用 Supabase 的高级查询功能：

```typescript
// 联表查询
const { data, error } = await supabase
  .from("posts")
  .select(`
    *,
    author:users(name, avatar),
    comments:comments(content, created_at)
  `)

// 聚合查询
const { data, error } = await supabase
  .from("orders")
  .select("status, count")
  .select("status")
```

### 查看数据库

通过 Supabase Studio 或命令行查看数据：

```bash
docker exec -it supabase-db psql -U postgres -d postgres
```

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
- [可用API指南](backend_可用API指南.md)
- [测试指南](backend_测试指南.md)
- [数据库管理指南](backend_数据库管理指南.md)
