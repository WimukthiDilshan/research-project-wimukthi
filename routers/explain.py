from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from config.database import get_db
from models.api_response_models import (
    ApiResponse,
    LessonOverviewList,
    LessonStudentsData,
    StudentExplanationData,
)
from models.class_summary_models import ClassRecommendationRequest, ClassRecommendationResponse, ClassSummary
from models.explanation_models import (
    ExplainRequest,
    ExplainResponse,
    GenerateStudentExplanationsResponse,
)
from services.explanation_service import build_explanation
from services.class_summary_service import generate_class_summary
from services.class_recommendation_service import generate_class_recommendation
from services.lesson_explanation_generation_service import generate_student_explanations_for_lesson
from services.lesson_lookup_service import list_lessons, list_students_for_lesson
from services.student_explanation_service import generate_student_explanation_preview

router = APIRouter(tags=["explainability"])


def _ok(message: str, data: object | None = None) -> dict[str, object | None]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": [],
    }


@router.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest) -> ExplainResponse:
    return build_explanation(request)


@router.get("/lessons", response_model=ApiResponse[LessonOverviewList])
def get_lessons(db: Session = Depends(get_db)) -> dict[str, object | None]:
    lessons = list_lessons(db)
    return _ok("Lessons retrieved successfully.", {"lessons": lessons})


@router.get("/lessons/{lesson_id}/students", response_model=ApiResponse[LessonStudentsData])
def get_lesson_students(
    lesson_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> dict[str, object | None]:
    students = list_students_for_lesson(db, lesson_id)
    return _ok("Lesson students retrieved successfully.", students)


@router.get(
    "/students/{student_id}/lessons/{lesson_id}/explanation",
    response_model=ApiResponse[StudentExplanationData],
)
def get_student_lesson_explanation(
    student_id: int = Path(..., gt=0),
    lesson_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> dict[str, object | None]:
    explanation = generate_student_explanation_preview(db, student_id, lesson_id)
    return _ok("Student explanation retrieved successfully.", explanation)


@router.get("/lessons/{lesson_id}/class-summary", response_model=ApiResponse[ClassSummary])
def get_lesson_class_summary(
    lesson_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> dict[str, object | None]:
    summary = generate_class_summary(db, lesson_id)
    return _ok("Class summary retrieved successfully.", summary)


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
