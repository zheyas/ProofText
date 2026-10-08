FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.hf_cache

RUN useradd --create-home app
WORKDIR /app
RUN chown app:app /app

# CPU-сборка torch: обычный wheel для Linux тянет CUDA-библиотеки
# на несколько гигабайт, а GPU на Render нет
COPY requirements.txt .
RUN pip install "$(grep -E '^torch==' requirements.txt)" \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY --chown=app:app . .
USER app

# Статика и веса модели попадают в образ, чтобы не качать их при старте
RUN python manage.py collectstatic --no-input \
    && python manage.py shell -c \
        "from articles.ai_detection import get_model; get_model()"

EXPOSE 8000
CMD ["./entrypoint.sh"]
