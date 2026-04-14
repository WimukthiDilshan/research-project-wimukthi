from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.explanation_models import ExplainRequest, ExplainResponse, ExplanationFactor


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


def _build_factor(rule: FeatureRule, value: float | None, final_cognitive_load: str) -> ExplanationFactor:
    normalized = _normalize_score(value, rule.threshold)
    direction_bias = 1.0 if rule.direction == "higher" else -1.0
    load_bias = {
        "Very Low": -0.6,
        "Low": -0.3,
        "Medium": 0.0,
        "High": 0.4,
        "Very High": 0.7,
    }[final_cognitive_load]
    score = round((normalized * direction_bias) + load_bias, 3)

    if score > 0.25:
        impact = "positive"
    elif score < -0.25:
        impact = "negative"
    else:
        impact = "neutral"

    if value is None:
        reason = f"{rule.explanation} No value was supplied, so this is a placeholder heuristic."
    else:
        reason = f"{rule.explanation} Observed value: {value}."

    return ExplanationFactor(
        feature=rule.feature,
        value=value,
        score=score,
        impact=impact,
        reason=reason,
    )


def _rank_factors(factors: list[ExplanationFactor]) -> list[ExplanationFactor]:
    return sorted(factors, key=lambda factor: abs(factor.score), reverse=True)


def _limit_factors(factors: list[ExplanationFactor], limit: int = 3) -> list[ExplanationFactor]:
    return factors[:limit]


def _build_explanation_text(final_cognitive_load: str, factors: list[ExplanationFactor]) -> str:
    if not factors:
        return f"The learner shows a {final_cognitive_load.lower()} cognitive load profile with limited evidence from the current summary."

    top_features = ", ".join(factor.feature for factor in factors[:3])
    return (
        f"The learner is classified as {final_cognitive_load} based on the summary profile. "
        f"The strongest contributing signals are {top_features}."
    )


def _build_recommendation_text(final_cognitive_load: str, factors: list[ExplanationFactor]) -> str:
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


def build_explanation(request: ExplainRequest) -> ExplainResponse:
    averages = request.summary.averages.model_dump()
    factors = [
        _build_factor(rule, _to_float(averages.get(rule.feature)), request.final_cognitive_load)
        for rule in FEATURE_RULES
    ]

    ranked_shap = _limit_factors(_rank_factors(factors))
    ranked_lime = _limit_factors(sorted(factors, key=lambda factor: (factor.score, factor.feature), reverse=True))

    agreed_features = {factor.feature for factor in ranked_shap} & {factor.feature for factor in ranked_lime}
    agreed_top_factors = [factor for factor in factors if factor.feature in agreed_features]
    agreed_top_factors = _limit_factors(_rank_factors(agreed_top_factors))

    return ExplainResponse(
        shap_top_factors=ranked_shap,
        lime_top_factors=ranked_lime,
        agreed_top_factors=agreed_top_factors,
        explanation_text=_build_explanation_text(request.final_cognitive_load, agreed_top_factors or ranked_shap),
        recommendation_text=_build_recommendation_text(request.final_cognitive_load, agreed_top_factors or ranked_shap),
    )
