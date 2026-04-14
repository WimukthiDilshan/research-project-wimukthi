from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.explanation_models import ExplainRequest, ExplainResponse
from services.explanation_service import build_explanation
from services.student_explanation_service import generate_student_explanation

router = APIRouter(tags=["explainability"])


@router.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest) -> ExplainResponse:
    return build_explanation(request)


@router.get(
    "/students/{student_id}/lessons/{lesson_id}/explanation",
    response_model=ExplainResponse,
)
def get_student_lesson_explanation(
    student_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
) -> ExplainResponse:
    return generate_student_explanation(db, student_id, lesson_id)
