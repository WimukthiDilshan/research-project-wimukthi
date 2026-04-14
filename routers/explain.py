from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.explanation_models import (
    ExplainRequest,
    ExplainResponse,
    GenerateStudentExplanationsResponse,
)
from models.class_summary_models import ClassRecommendationRequest, ClassRecommendationResponse
from services.explanation_service import build_explanation
from services.class_recommendation_service import generate_class_recommendation
from services.lesson_explanation_generation_service import generate_student_explanations_for_lesson
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


@router.post(
    "/lessons/{lesson_id}/generate-student-explanations",
    response_model=GenerateStudentExplanationsResponse,
)
def generate_lesson_student_explanations(
    lesson_id: int,
    db: Session = Depends(get_db),
) -> GenerateStudentExplanationsResponse:
    return generate_student_explanations_for_lesson(db, lesson_id)


@router.post(
    "/lessons/{lesson_id}/generate-class-recommendation",
    response_model=ClassRecommendationResponse,
)
def generate_lesson_class_recommendation(
    lesson_id: int,
    request: ClassRecommendationRequest,
    db: Session = Depends(get_db),
) -> ClassRecommendationResponse:
    # Real GPT generation will be integrated here later; this path keeps the contract stable.
    class_summary = request.class_summary.model_copy(update={"lesson_id": lesson_id})
    return generate_class_recommendation(db, class_summary)
