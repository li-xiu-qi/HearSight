# Lefthook 使用指南

## 📖 概述

Lefthook 是一个快速且强大的 Git hooks 管理器，用于在提交代码前自动运行代码质量检查、格式化和测试。本项目使用 Lefthook 来确保代码质量和一致性。

## 🚀 快速开始

### 安装 Lefthook

#### 全局安装

```bash
npm install -g @arkweid/lefthook
```

#### 项目级安装

```bash
npm install lefthook --save-dev
```

### 初始化配置

在项目根目录运行：

```bash
lefthook install
```

这会在 `.git/hooks/` 目录中创建相应的 Git hooks.

## 📋 配置说明

项目的 Lefthook 配置位于 `lefthook.yml` 文件中，包含以下检查：

### 前端检查 (frontend/)

#### frontend-format

- **作用**：自动格式化前端代码
- **触发文件**：`frontend/**/*.{ts,tsx,js,jsx,json,css,scss,html}`
- **执行命令**：Prettier 格式化
- **跳过条件**：merge commits

#### frontend-lint

- **作用**：前端代码检查和类型检查
- **触发文件**：`frontend/**/*.{ts,tsx,js,jsx}`
- **执行命令**：ESLint 检查 + TypeScript 类型检查
- **跳过条件**：merge commits

### 后端检查 (backend/)

#### backend-format

- **作用**：Python 代码格式化
- **触发文件**：`backend/**/*.py`
- **执行命令**：Black 格式化 + isort 导入排序
- **跳过条件**：merge commits

#### backend-lint

- **作用**：Python 代码质量检查
- **触发文件**：`backend/**/*.py`
- **执行命令**：Pylint 代码检查
- **跳过条件**：merge commits

### Supabase 项目检查 (supabase_project/)

#### supabase-format

- **作用**：Supabase 项目代码格式化
- **触发文件**：`supabase_project/**/*.ts`
- **执行命令**：Prettier 格式化
- **跳过条件**：merge commits

#### supabase-lint

- **作用**：Supabase 项目代码检查
- **触发文件**：`supabase_project/**/*.ts`
- **执行命令**：ESLint 检查
- **跳过条件**：merge commits

## 🛠️ 开发环境配置

### Python 开发依赖

为确保 Python 代码检查正常工作，需要安装以下依赖：

```bash
pip install black isort pylint
```

或者添加到 `requirements.txt`：

```txt
black
isort
pylint
```

### 前端开发依赖

确保前端项目已安装相关依赖：

```bash
cd frontend
npm install
```

### Supabase 项目依赖

如果 `supabase_project` 有独立的 `package.json`：

```bash
cd supabase_project
npm install
```

## 📝 使用方法

### 自动检查

一旦配置完成，每次 `git commit` 时会自动运行相关检查：

```bash
git add .
git commit -m "feat: add new feature"
# Lefthook 会自动运行相关检查
```

### 手动运行检查

#### 运行所有 pre-commit 检查

```bash
lefthook run pre-commit
```

#### 运行特定检查

```bash
lefthook run frontend-lint
lefthook run backend-format
lefthook run supabase-lint
```

#### 仅检查暂存的文件

```bash
lefthook run pre-commit --force
```

### 跳过检查

在紧急情况下可以跳过检查：

```bash
git commit -m "fix: urgent fix" --no-verify
```

## 🔧 配置自定义

### 修改检查规则

编辑 `lefthook.yml` 文件来自定义检查规则：

```yaml
pre-commit:
  commands:
    custom-check:
      glob: "src/**/*.{js,ts}"
      run: bash -c "npm run custom-lint"
```

### 添加新检查

在 `lefthook.yml` 中添加新的命令块：

```yaml
pre-commit:
  commands:
    new-check:
      glob: "new-folder/**/*.ext"
      run: bash -c "your-command-here"
      skip: [merge-commit]
```

### 常见问题

#### 1. Lefthook 未运行

**问题**：提交时没有触发检查

**解决**：

- 确认已运行 `lefthook install`
- 检查 `.git/hooks/` 目录是否存在 lefthook 文件

#### 2. Python 工具未找到

**问题**：`black`、`isort` 或 `pylint` 命令未找到

**解决**：

```bash
pip install black isort pylint
```

#### 3. 前端工具未找到

**问题**：`npx prettier` 或 `npm run lint` 失败

**解决**：

```bash
cd frontend
npm install
```

#### 4. 权限问题 (Windows)

**问题**：Git hooks 没有执行权限

**解决**：

```bash
git config core.hooksPath .git/hooks
```

### 检查 Lefthook 状态

```bash
lefthook version
lefthook dump
```

### 重新安装 hooks

```bash
lefthook uninstall
lefthook install
```

## 📚 相关链接

- [Lefthook 官方文档](https://github.com/evilmartians/lefthook)
- [Prettier 文档](https://prettier.io/)
- [ESLint 文档](https://eslint.org/)
- [Black 代码格式化](https://black.readthedocs.io/)
- [isort 导入排序](https://pycqa.github.io/isort/)
- [Pylint 代码检查](https://pylint.readthedocs.io/)

## 🤝 贡献指南

提交代码前请确保：

1. 本地运行 `lefthook run pre-commit` 通过所有检查
2. 如果添加新代码，请确保相关检查规则覆盖新文件
3. 更新此文档以反映配置变更
