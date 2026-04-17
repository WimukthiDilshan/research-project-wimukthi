from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.explanation_models import (
    ExplainRequest,
    ExplainResponse,
    GeneratedStudentExplanation,
    StudentSummaryInput,
    SummaryAverages,
    SummaryCounts,
)
from models.api_response_models import StudentExplanationData
from repositories.explainability_repository import (
    get_cognitive_load_logs_by_student_and_lesson,
    get_students_by_lesson_id,
    save_student_lesson_explanation,
)
from services.explanation_service import build_explanation
from services.student_summary_service import generate_student_summary


def _normalize_final_cognitive_load(final_cognitive_load: str | None) -> str:
    """Keep the endpoint stable even when a student has no logs yet."""
    return final_cognitive_load or "Medium"


def _build_explain_request(student_summary: dict[str, object], final_cognitive_load: str | None) -> ExplainRequest:
    """Transform a raw student summary dictionary into the explain API request model."""
    summary_payload = student_summary.get("summary", {})
    averages_payload = summary_payload.get("averages", {}) if isinstance(summary_payload, dict) else {}
    counts_payload = summary_payload.get("counts", {}) if isinstance(summary_payload, dict) else {}

    return ExplainRequest(
        summary=StudentSummaryInput(
            averages=SummaryAverages.model_validate(averages_payload),
            counts=SummaryCounts.model_validate(counts_payload),
        ),
        final_cognitive_load=_normalize_final_cognitive_load(final_cognitive_load),
    )


def _flatten_averages(averages: SummaryAverages) -> dict[str, float | None]:
    """Convert the averages model into a plain dictionary for persistence."""
    return averages.model_dump()


def _serialize_factors(factors: list[object]) -> str:
    """Serialize explanation factors to JSON for database storage."""
    return json.dumps([factor.model_dump() for factor in factors], ensure_ascii=False)


def _build_save_payload(
    student_id: int,
    lesson_id: int,
    final_cognitive_load: str,
    counts: SummaryCounts,
    averages: SummaryAverages,
    explanation: ExplainResponse,
) -> dict[str, object]:
    """Shape the student explanation payload to the existing table columns."""
    flattened_averages = _flatten_averages(averages)
    flattened_counts = counts.model_dump(by_alias=True)
    payload: dict[str, object] = {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "final_cognitive_load": final_cognitive_load,
        "explanation_text": explanation.explanation_text,
        "recommendation_text": explanation.recommendation_text,
        "very_low_count": flattened_counts.get("Very Low", 0),
        "low_count": flattened_counts.get("Low", 0),
        "medium_count": flattened_counts.get("Medium", 0),
        "high_count": flattened_counts.get("High", 0),
        "very_high_count": flattened_counts.get("Very High", 0),
        "shap_top_factors_json": _serialize_factors(explanation.shap_top_factors),
        "lime_top_factors_json": _serialize_factors(explanation.lime_top_factors),
        "agreed_top_factors_json": _serialize_factors(explanation.agreed_top_factors),
    }
    payload.update(flattened_averages)
    return payload


def generate_student_explanation_record(
    db: Session,
    student_id: int,
    lesson_id: int,
) -> GeneratedStudentExplanation:
    """Build, explain, and persist one student's lesson explanation."""
    # 1) Aggregate this student's logs into summary averages/counts.
    student_summary = generate_student_summary(db, student_id, lesson_id)
    # 2) Use lesson rows as SHAP/LIME background distribution.
    background_rows = get_students_by_lesson_id(db, lesson_id)
    explain_request = _build_explain_request(
        student_summary,
        student_summary.get("final_cognitive_load"),
    )
    # 3) Compute SHAP/LIME and explanation text.
    explanation = build_explanation(explain_request, background_rows=background_rows)
    # 4) Persist generated result for later class-level aggregation and dashboard reuse.
    saved_row_id = save_student_lesson_explanation(
        db,
        _build_save_payload(
            student_id=student_id,
            lesson_id=lesson_id,
            final_cognitive_load=explain_request.final_cognitive_load,
            counts=explain_request.summary.counts,
            averages=explain_request.summary.averages,
            explanation=explanation,
        ),
    )

    return GeneratedStudentExplanation(
        student_id=student_id,
        lesson_id=lesson_id,
        final_cognitive_load=explain_request.final_cognitive_load,
        averages=explain_request.summary.averages,
        shap_top_factors=explanation.shap_top_factors,
        lime_top_factors=explanation.lime_top_factors,
        agreed_top_factors=explanation.agreed_top_factors,
        explanation_text=explanation.explanation_text,
        recommendation_text=explanation.recommendation_text,
        saved_row_id=saved_row_id,
    )


def generate_student_explanation_preview(
    db: Session,
    student_id: int,
    lesson_id: int,
) -> StudentExplanationData:
    """Build a read-only explanation response for the frontend."""
    rows = get_cognitive_load_logs_by_student_and_lesson(db, student_id, lesson_id)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "No cognitive load logs found for the requested student and lesson.",
                "data": None,
                "errors": [f"student_id={student_id}, lesson_id={lesson_id} not found"],
            },
        )

    student_summary = generate_student_summary(db, student_id, lesson_id)
    background_rows = get_students_by_lesson_id(db, lesson_id)
    explain_request = _build_explain_request(
        student_summary,
        student_summary.get("final_cognitive_load"),
    )
    explanation = build_explanation(explain_request, background_rows=background_rows)

    return StudentExplanationData(
        student_id=student_id,
        lesson_id=lesson_id,
        summary=explain_request.summary,
        final_cognitive_load=explain_request.final_cognitive_load,
        shap_top_factors=explanation.shap_top_factors,
        lime_top_factors=explanation.lime_top_factors,
        agreed_top_factors=explanation.agreed_top_factors,
        explanation_text=explanation.explanation_text,
        recommendation_text=explanation.recommendation_text,
    )


def generate_student_explanation(
    db: Session,
    student_id: int,
    lesson_id: int,
) -> ExplainResponse:
    """Return the raw explain response without saving it."""
    student_summary = generate_student_summary(db, student_id, lesson_id)
    # Same background strategy as preview/save paths for consistent explanations.
    background_rows = get_students_by_lesson_id(db, lesson_id)
    explain_request = _build_explain_request(
        student_summary,
        student_summary.get("final_cognitive_load"),
    )
    return build_explanation(explain_request, background_rows=background_rows)
