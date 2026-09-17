FROM python:3.13-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY install.sh .
COPY pyproject.toml .
COPY uv.lock .

COPY src src

RUN uv sync --frozen --no-cache

ENV OPENAI_API_KEY="" GRADIO_PORT="5000" PATH="${PATH};/root/.local/bin"

EXPOSE ${GRADIO_PORT}

SHELL [ "/bin/sh", "-c" ]
ENTRYPOINT uv run agents-on-k8s
