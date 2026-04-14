from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from config.settings import settings
from models.class_summary_models import ClassSummary, ClassRecommendationResponse
from repositories.explainability_repository import save_class_lesson_summary


def _has_gpt_api_key() -> bool:
    return bool(settings.GPT_API_KEY and settings.GPT_API_KEY.strip())


def _build_gpt_placeholder_recommendation(class_summary: ClassSummary) -> str:
    # Real GPT recommendation generation will be integrated here later.
    dominant = class_summary.dominant_cognitive_load or "unknown"
    common_features = ", ".join(item.feature for item in class_summary.common_factors[:3]) or "limited signals"
    return (
        f"[GPT placeholder] For lesson {class_summary.lesson_id}, the next lesson should adapt to {dominant.lower()} cognitive load. "
        f"The future GPT call will consider features such as {common_features}."
    )


def _build_deterministic_recommendation(class_summary: ClassSummary) -> str:
    dominant = class_summary.dominant_cognitive_load or "Medium"
    if dominant in {"High", "Very High"}:
        base_text = "Reduce complexity in the next lesson, add shorter sections, and include more guided practice."
    elif dominant == "Medium":
        base_text = "Keep the next lesson balanced and add small comprehension checks."
    else:
        base_text = "Advance gradually and keep the next lesson concise while reinforcing key ideas."

    common_features = ", ".join(item.feature for item in class_summary.common_factors[:3])
    if common_features:
        return f"{base_text} Common signals to address: {common_features}."
    return base_text


def _build_next_lesson_recommendation(class_summary: ClassSummary) -> str:
    if _has_gpt_api_key():
        return _build_gpt_placeholder_recommendation(class_summary)
    return _build_deterministic_recommendation(class_summary)


def _serialize_summary(class_summary: ClassSummary) -> dict[str, Any]:
    return class_summary.model_dump(by_alias=True)


def _build_save_payload(
    class_summary: ClassSummary,
    next_lesson_recommendation: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "lesson_id": class_summary.lesson_id,
        "total_students": class_summary.total_students,
        "cognitive_load_counts": json.dumps(class_summary.cognitive_load_counts.model_dump(by_alias=True), ensure_ascii=False),
        "dominant_cognitive_load": class_summary.dominant_cognitive_load,
        "common_factors": json.dumps([item.model_dump() for item in class_summary.common_factors], ensure_ascii=False),
        "next_lesson_recommendation": next_lesson_recommendation,
        "class_summary": json.dumps(_serialize_summary(class_summary), ensure_ascii=False),
    }
    # The class_lesson_summary table is kept schema-stable; this payload is shaped for future persistence mapping.
    return payload


def generate_class_recommendation(
    db: Session,
    class_summary: ClassSummary,
) -> ClassRecommendationResponse:
    recommendation = _build_next_lesson_recommendation(class_summary)
    saved_row_id = save_class_lesson_summary(
        db,
        _build_save_payload(class_summary, recommendation),
    )
    return ClassRecommendationResponse(
        lesson_id=class_summary.lesson_id,
        next_lesson_recommendation=recommendation,
        saved_row_id=saved_row_id,
    )
