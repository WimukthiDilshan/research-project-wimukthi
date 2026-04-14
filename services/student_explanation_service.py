from __future__ import annotations

from sqlalchemy.orm import Session

from models.explanation_models import (
    ExplainRequest,
    ExplainResponse,
    StudentSummaryInput,
    SummaryAverages,
    SummaryCounts,
)
from services.explanation_service import build_explanation
from services.student_summary_service import generate_student_summary


def _normalize_final_cognitive_load(final_cognitive_load: str | None) -> str:
    # Keep the endpoint stable even when a student has no logs yet.
    return final_cognitive_load or "Medium"


def _build_explain_request(student_summary: dict[str, object], final_cognitive_load: str | None) -> ExplainRequest:
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


def generate_student_explanation(
    db: Session,
    student_id: int,
    lesson_id: int,
) -> ExplainResponse:
    student_summary = generate_student_summary(db, student_id, lesson_id)
    explain_request = _build_explain_request(
        student_summary,
        student_summary.get("final_cognitive_load"),
    )
    return build_explanation(explain_request)
