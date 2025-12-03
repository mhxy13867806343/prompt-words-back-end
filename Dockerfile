# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv（轻量级 Python 包管理器）
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

# 先拷贝依赖声明文件用于缓存
COPY pyproject.toml ./
# 如果存在锁文件，可一并拷贝提升一致性
# COPY uv.lock ./

# 安装依赖到本地虚拟环境 .venv
RUN uv sync --frozen --no-dev

# 拷贝项目源代码
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

