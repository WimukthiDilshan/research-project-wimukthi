from __future__ import annotations

import json
from collections import Counter
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.class_summary_models import ClassSummary, CommonFactor, CognitiveLoadCounts
from repositories.explainability_repository import get_student_lesson_explanations_by_lesson_id

COGNITIVE_LOAD_ORDER = ["Very Low", "Low", "Medium", "High", "Very High"]
FACTOR_FIELDS = ["shap_top_factors", "lime_top_factors", "agreed_top_factors"]


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            return None
    return None


def _parse_json_payload(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    return []


def _extract_label(row: dict[str, Any]) -> str | None:
    value = row.get("final_cognitive_load")
    if isinstance(value, str):
        normalized = value.strip()
        if normalized in COGNITIVE_LOAD_ORDER:
            return normalized
    return None


def _dominant_label(counts: dict[str, int]) -> str | None:
    max_count = max(counts.values()) if counts else 0
    if max_count <= 0:
        return None
    for label in COGNITIVE_LOAD_ORDER:
        if counts.get(label, 0) == max_count:
            return label
    return None


def _count_cognitive_loads(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in COGNITIVE_LOAD_ORDER}
    for row in rows:
        label = _extract_label(row)
        if label is not None:
            counts[label] += 1
    return counts


def _aggregate_common_factors(rows: list[dict[str, Any]]) -> list[CommonFactor]:
    factor_counts: Counter[str] = Counter()

    for row in rows:
        per_student_features: set[str] = set()
        for field_name in FACTOR_FIELDS:
            for factor in _parse_json_payload(row.get(field_name)):
                feature = factor.get("feature")
                if isinstance(feature, str) and feature.strip():
                    per_student_features.add(feature.strip())
        factor_counts.update(per_student_features)

    ranked = sorted(factor_counts.items(), key=lambda item: (-item[1], item[0]))
    return [CommonFactor(feature=feature, frequency=frequency) for feature, frequency in ranked[:5]]


def generate_class_summary(
    db: Session,
    lesson_id: int,
) -> ClassSummary:
    rows = get_student_lesson_explanations_by_lesson_id(db, lesson_id)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "No saved student explanations found for the requested lesson.",
                "data": None,
                "errors": [f"lesson_id={lesson_id} not found"],
            },
        )
    counts = _count_cognitive_loads(rows)
    return ClassSummary(
        lesson_id=lesson_id,
        total_students=len(rows),
        cognitive_load_counts=CognitiveLoadCounts.model_validate(counts),
        dominant_cognitive_load=_dominant_label(counts),
        common_factors=_aggregate_common_factors(rows),
    )
