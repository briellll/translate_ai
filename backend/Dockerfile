FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry --no-cache-dir

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main --no-interaction --no-ansi

COPY backend/ ./backend/

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
