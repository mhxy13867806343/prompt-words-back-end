# 提示词管理系统

基于 FastAPI + SQLAlchemy (PostgreSQL) + Redis 的提示词分享平台

## 功能特性

- 用户注册/登录（JWT Token 30天有效期）
- 邮箱绑定与验证码（Redis 5分钟有效期）
- 找回密码（需绑定邮箱）
- 提示词创建/编辑/删除（软删除）
- 点赞/收藏功能（不能操作自己的内容）
- 浏览记录（限IP统计）
- 个人中心（我的提示词/收藏/点赞列表）
- 全局统计（总数量/浏览量）
- 分页查询

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy (异步)
- PostgreSQL
- Redis
- JWT 认证

## 安装

1. 安装依赖：
```bash
# 方式一：使用 uv（推荐）
# 安装 uv（macOS/Linux）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 创建并同步虚拟环境到 .venv
uv sync

# 方式二：使用 pip
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入数据库和邮箱配置
```

3. 启动服务：
```bash
# 使用 uv 运行（自动启用 .venv）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 或使用系统 Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动后访问：http://localhost:8000/docs

## 数据库表结构

- users: 用户表
- prompts: 提示词表
- prompt_views: 浏览记录
- prompt_likes: 点赞记录
- prompt_favorites: 收藏记录

## API 响应格式

```json
{
  "code": 200,
  "data": {},
  "msg": "成功"
}
```

字段名采用驼峰命名（camelCase）返回给前端。

## 使用 Docker

```bash
# 构建镜像
docker build -t prompt-words-back-end .

# 运行容器（加载环境变量并映射端口）
docker run --rm -p 8000:8000 --env-file .env prompt-words-back-end
```

环境变量示例：
- `DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname`
- `REDIS_URL=redis://host:6379/0`
- `SECRET_KEY=your-secret`
- 邮件相关：`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD`、`SMTP_FROM`

## 开发辅助

```bash
# 代码风格检查（需 uv 已同步 dev 依赖）
uv run ruff check .

# 运行简单 API 测试脚本
uv run python test_api.py
```

## 前端对接

- 仓库：`https://github.com/mhxy13867806343/prompt-words-front-end`
- 接口前缀：同时支持 `/{...}` 与 `/api/{...}`，推荐使用 `/api`
- Vite 代理示例（将 `/api` 指向后端 `http://localhost:8000`）：
  ```ts
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
  ```

兼容路由：
- `GET /api/auth/user`
- `POST /api/prompts/:id/like`，`DELETE /api/prompts/:id/like`
- `POST /api/prompts/:id/collect`，`DELETE /api/prompts/:id/collect`
- `GET /api/prompts/my`、`GET /api/prompts/my/likes`、`GET /api/prompts/my/collects`
- `GET /api/prompts/statistics`（等价 `GET /api/prompts/stats/global`）
