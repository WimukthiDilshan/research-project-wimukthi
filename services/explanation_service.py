from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.explanation_models import ExplainRequest, ExplainResponse, ExplanationFactor
from config.settings import settings


@dataclass(frozen=True)
class FeatureRule:
    feature: str
    threshold: float
    direction: str
    explanation: str
    recommendation: str


FEATURE_RULES: list[FeatureRule] = [
    FeatureRule("avg_pause_frequency", 0.6, "higher", "Frequent pauses suggest friction or uncertainty.", "Break content into smaller sections and add quick checkpoints."),
    FeatureRule("avg_navigation_count_video", 0.6, "higher", "Repeated navigation in video often reflects replaying or searching.", "Add chapter markers and concise summaries."),
    FeatureRule("avg_rewatch_segments", 0.5, "higher", "Rewatching segments can indicate unclear explanation or difficult concepts.", "Highlight key moments and simplify the most difficult parts."),
    FeatureRule("avg_playback_rate_change", 0.4, "higher", "Playback changes often show the student is adjusting pace to manage difficulty.", "Provide adaptive pacing suggestions and optional slower narration."),
    FeatureRule("avg_idle_duration_video", 0.5, "higher", "Idle time during video suggests disengagement or load overload.", "Use shorter video segments and add interactive prompts."),
    FeatureRule("avg_time_on_content", 0.6, "higher", "Long time on content can mean deeper engagement or extra effort.", "Confirm comprehension with lightweight checks before moving on."),
    FeatureRule("avg_navigation_count_adaptation", 0.5, "higher", "More navigation in adaptation content suggests the learner is exploring alternatives.", "Make adaptation steps more linear and explicit."),
    FeatureRule("avg_revisit_frequency", 0.5, "higher", "Frequent revisits indicate uncertainty or review behavior.", "Add a short recap and stronger progress cues."),
    FeatureRule("avg_idle_duration_adaptation", 0.5, "higher", "Idle time in adaptation steps points to hesitation or decision fatigue.", "Reduce branching options and provide clearer recommendations."),
    FeatureRule("avg_quiz_response_time", 0.6, "higher", "Long quiz response time often indicates slow recall or uncertainty.", "Offer practice questions and immediate feedback."),
    FeatureRule("avg_error_rate", 0.7, "higher", "High error rate is a direct signal of confusion or workload strain.", "Simplify tasks and surface the relevant prerequisite material."),
]

FINAL_LOAD_PRIORITY = ["Very Low", "Low", "Medium", "High", "Very High"]

LOAD_BIAS = {
    "Very Low": -0.6,
    "Low": -0.3,
    "Medium": 0.0,
    "High": 0.4,
    "Very High": 0.7,
}


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _normalize_score(value: float | None, threshold: float) -> float:
    if value is None:
        return 0.0
    ratio = value / threshold if threshold else value
    return max(min(ratio - 1.0, 2.0), -2.0)


def _impact_from_score(score: float) -> str:
    if score > 0.25:
        return "positive"
    if score < -0.25:
        return "negative"
    return "neutral"


def _build_reason(rule: FeatureRule, value: float | None, source: str) -> str:
    if value is None:
        return f"{rule.explanation} No value was supplied, so this is a placeholder {source} heuristic."
    return f"{rule.explanation} Observed value: {value}."


def _shap_style_score(rule: FeatureRule, value: float | None, final_cognitive_load: str) -> float:
    normalized = _normalize_score(value, rule.threshold)
    direction_bias = 1.0 if rule.direction == "higher" else -1.0
    load_bias = LOAD_BIAS[final_cognitive_load]
    return round((normalized * direction_bias) + load_bias, 3)


def _lime_style_score(rule: FeatureRule, value: float | None, final_cognitive_load: str) -> float:
    if value is None:
        return round(LOAD_BIAS[final_cognitive_load] * 0.5, 3)

    midpoint = rule.threshold * 1.15
    deviation = value - midpoint
    direction_bias = 1.0 if rule.direction == "higher" else -1.0
    stability_bias = 0.15 if rule.feature in {"avg_time_on_content", "avg_quiz_response_time"} else 0.0
    load_bias = LOAD_BIAS[final_cognitive_load] * 0.35
    return round((deviation * direction_bias) + load_bias + stability_bias, 3)


def _build_shap_factor(rule: FeatureRule, value: float | None, final_cognitive_load: str) -> ExplanationFactor:
    score = _shap_style_score(rule, value, final_cognitive_load)
    return ExplanationFactor(
        feature=rule.feature,
        value=value,
        score=score,
        impact=_impact_from_score(score),
        reason=_build_reason(rule, value, "SHAP-like"),
    )


def _build_lime_factor(rule: FeatureRule, value: float | None, final_cognitive_load: str) -> ExplanationFactor:
    score = _lime_style_score(rule, value, final_cognitive_load)
    return ExplanationFactor(
        feature=rule.feature,
        value=value,
        score=score,
        impact=_impact_from_score(score),
        reason=_build_reason(rule, value, "LIME-like"),
    )


def _rank_factors(factors: list[ExplanationFactor]) -> list[ExplanationFactor]:
    return sorted(factors, key=lambda factor: abs(factor.score), reverse=True)


def _limit_factors(factors: list[ExplanationFactor], limit: int = 3) -> list[ExplanationFactor]:
    return factors[:limit]


def _top_feature_names(factors: list[ExplanationFactor]) -> list[str]:
    return [factor.feature for factor in factors]


def _resolve_agreed_top_factors(
    shap_top_factors: list[ExplanationFactor],
    lime_top_factors: list[ExplanationFactor],
) -> list[ExplanationFactor]:
    agreed_features = set(_top_feature_names(shap_top_factors)) & set(_top_feature_names(lime_top_factors))
    if not agreed_features:
        # Placeholder fallback until real SHAP/LIME are integrated and can produce a shared ranking.
        return shap_top_factors[:2] if shap_top_factors else lime_top_factors[:2]

    overlap_candidates = [factor for factor in shap_top_factors if factor.feature in agreed_features]
    return _limit_factors(_rank_factors(overlap_candidates))


def _has_gpt_api_key() -> bool:
    return bool(settings.GPT_API_KEY and settings.GPT_API_KEY.strip())


def _build_gpt_placeholder_explanation_text(
    final_cognitive_load: str,
    factors: list[ExplanationFactor],
) -> str:
    # Real GPT generation will be integrated here later.
    factor_names = ", ".join(factor.feature for factor in factors[:3]) if factors else "limited signals"
    return (
        f"[GPT placeholder] The learner is classified as {final_cognitive_load}. "
        f"This branch will eventually call GPT using factors such as {factor_names}."
    )


def _build_gpt_placeholder_recommendation_text(
    final_cognitive_load: str,
    factors: list[ExplanationFactor],
) -> str:
    # Real GPT recommendation generation will be integrated here later.
    factor_names = ", ".join(factor.feature for factor in factors[:2]) if factors else "limited signals"
    return (
        f"[GPT placeholder] Recommend tailoring instruction for {final_cognitive_load.lower()} load. "
        f"The future GPT call will use signals like {factor_names}."
    )


def _build_deterministic_explanation_text(final_cognitive_load: str, factors: list[ExplanationFactor]) -> str:
    if not factors:
        return f"The learner shows a {final_cognitive_load.lower()} cognitive load profile with limited evidence from the current summary."

    top_features = ", ".join(factor.feature for factor in factors[:3])
    return (
        f"The learner is classified as {final_cognitive_load} based on the summary profile. "
        f"The strongest contributing signals are {top_features}."
    )


def _build_deterministic_recommendation_text(final_cognitive_load: str, factors: list[ExplanationFactor]) -> str:
    if not factors:
        return "Collect more interaction data and re-evaluate the learner profile before making instructional changes."

    factor_reasons = "; ".join(factor.reason for factor in factors[:2])
    if final_cognitive_load in {"High", "Very High"}:
        return (
            f"Prioritize simpler content, shorter segments, and immediate feedback. {factor_reasons}"
        )
    if final_cognitive_load == "Medium":
        return f"Maintain the current pace but add small scaffolds and confidence checks. {factor_reasons}"
    return f"Keep the experience concise and monitor for changes in effort or confusion. {factor_reasons}"


def _build_explanation_text(final_cognitive_load: str, factors: list[ExplanationFactor]) -> str:
    if _has_gpt_api_key():
        return _build_gpt_placeholder_explanation_text(final_cognitive_load, factors)
    return _build_deterministic_explanation_text(final_cognitive_load, factors)


def _build_recommendation_text(final_cognitive_load: str, factors: list[ExplanationFactor]) -> str:
    if _has_gpt_api_key():
        return _build_gpt_placeholder_recommendation_text(final_cognitive_load, factors)
    return _build_deterministic_recommendation_text(final_cognitive_load, factors)


def build_explanation(request: ExplainRequest) -> ExplainResponse:
    averages = request.summary.averages.model_dump()
    # Real SHAP scoring will be integrated here later.
    shap_factors = [
        _build_shap_factor(rule, _to_float(averages.get(rule.feature)), request.final_cognitive_load)
        for rule in FEATURE_RULES
    ]
    # Real LIME scoring will be integrated here later.
    lime_factors = [
        _build_lime_factor(rule, _to_float(averages.get(rule.feature)), request.final_cognitive_load)
        for rule in FEATURE_RULES
    ]

    ranked_shap = _limit_factors(_rank_factors(shap_factors))
    ranked_lime = _limit_factors(_rank_factors(lime_factors))
    agreed_top_factors = _resolve_agreed_top_factors(ranked_shap, ranked_lime)

    return ExplainResponse(
        shap_top_factors=ranked_shap,
        lime_top_factors=ranked_lime,
        agreed_top_factors=agreed_top_factors,
        explanation_text=_build_explanation_text(request.final_cognitive_load, agreed_top_factors or ranked_shap),
        recommendation_text=_build_recommendation_text(request.final_cognitive_load, agreed_top_factors or ranked_shap),
    )
