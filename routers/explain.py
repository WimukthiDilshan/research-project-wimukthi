from fastapi import APIRouter

from models.explanation_models import ExplainRequest, ExplainResponse
from services.explanation_service import build_explanation

router = APIRouter(tags=["explainability"])


@router.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest) -> ExplainResponse:
    return build_explanation(request)
