# docker/Dockerfile
FROM python:3.10-alpine

WORKDIR /app

# Instalar dependências do sistema necessárias para OpenCV e compilação
RUN apk update && apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    postgresql-dev \
    python3-dev \
    ffmpeg \
    ffmpeg-dev \
    jpeg-dev \
    zlib-dev \
    libpng-dev \
    openblas-dev \
    libffi-dev \
    cmake \
    make \
    linux-headers \
    && pip install --upgrade pip

# Instalar UV
# RUN pip install --no-cache-dir uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar arquivos de dependências
COPY pyproject.toml uv.lock .

# Instalar dependências usando UV
RUN uv sync --frozen --no-cache

# Copiar o restante do código
COPY . .

# Criar diretórios necessários
RUN mkdir -p uploads outputs

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:$PATH"

# O comando será definido no docker-compose.yml
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]