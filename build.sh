#!/usr/bin/env bash
# Скрипт сборки для Render
set -o errexit

pip install --upgrade pip

# CPU-сборка torch: обычный колёсный файл для Linux тянет CUDA-библиотеки
# на несколько гигабайт, а GPU на Render нет
pip install "$(grep -E '^torch==' requirements.txt)" \
    --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Скачиваем веса модели на этапе сборки (в HF_HOME внутри проекта),
# чтобы первый анализ не ждал загрузки
python manage.py shell -c "from articles.ai_detection import get_model; get_model()"
