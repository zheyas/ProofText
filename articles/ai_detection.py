# articles/ai_detection.py
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def get_model():
    """
    Загружает токенизатор и модель при первом обращении,
    а не при старте сервера: torch и веса занимают много памяти.
    """
    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer)

    tokenizer = AutoTokenizer.from_pretrained(settings.AI_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        settings.AI_MODEL_NAME
    )
    # В model.safetensors у roberta-base-openai-detector веса не выровнены,
    # и на arm64 (Apple Silicon) torch падает с Bus error —
    # копируем их из mmap в обычную память
    for param in model.parameters():
        param.data = param.data.clone()
    model.eval()
    return tokenizer, model


def _ai_label_index(model) -> int:
    # У roberta-base-openai-detector метки {0: "Fake", 1: "Real"}
    for index, label in model.config.id2label.items():
        if str(label).lower() == "fake":
            return int(index)
    return 1


def detect_ai(text: str) -> float:
    """
    Использует RoBERTa для определения вероятности AI-генерации текста.
    Возвращает число от 0 до 100.
    """
    import torch

    tokenizer, model = get_model()
    inputs = tokenizer(text, return_tensors="pt",
                       truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1).squeeze().tolist()

    ai_probability = probs[_ai_label_index(model)]
    return round(ai_probability * 100, 2)
