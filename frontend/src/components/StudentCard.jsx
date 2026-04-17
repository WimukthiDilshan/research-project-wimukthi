import React from 'react';

function FactorList({ title, factors }) {
  return (
    <div className="factor-block">
      <h4>{title}</h4>
      <ul className="factor-list">
        {/* Display each factor name and score in a compact list. */}
        {factors.map((factor) => (
          <li key={factor.feature}>
            <span className="factor-feature">{factor.feature}</span>
            <span className="factor-score">{factor.score}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function StudentCard({
  explanation,
  highLoadPeriods = [],
  selectedPeriodId = '',
  onSelectPeriod,
  periodExplanation,
}) {
  return (
    <section className="panel">
      {explanation ? (
        <>
          <div className="panel-header">
            <h3>Student Explanation</h3>
            <span className="badge">{explanation.final_cognitive_load ?? 'Unknown'}</span>
          </div>
          <p className="muted">
            Student {explanation.student_id} in lesson {explanation.lesson_id}
          </p>
          <div className="text-block">
            <h4>Explanation</h4>
            <p>{explanation.explanation_text}</p>
          </div>
          <div className="text-block">
            <h4>Recommendation</h4>
            <p>{explanation.recommendation_text}</p>
          </div>
          <div className="factor-grid">
            {/* Keep SHAP, LIME, and overlap factors visually separated. */}
            <FactorList title="SHAP Top Factors" factors={explanation.shap_top_factors ?? []} />
            <FactorList title="LIME Top Factors" factors={explanation.lime_top_factors ?? []} />
            <FactorList title="Agreed Top Factors" factors={explanation.agreed_top_factors ?? []} />
          </div>
        </>
      ) : (
        <>
          <h3>Student Explanation</h3>
          <p className="muted">Base explanation is unavailable, but high-load periods can still be explored.</p>
        </>
      )}

      <div className="text-block">
        <h4>High Cognitive Load Periods</h4>
        {!highLoadPeriods.length ? (
          <p className="muted">No High or Very High periods found for this student.</p>
        ) : (
          <div className="actions-row">
            {highLoadPeriods.map((period) => {
              const label = period.start_time && period.end_time
                ? `${period.dominant_cognitive_load}: ${period.start_time} - ${period.end_time}`
                : `${period.dominant_cognitive_load}: Period ${period.period_id}`;
              return (
                <button
                  key={period.period_id}
                  onClick={() => onSelectPeriod?.(period.period_id)}
                  className={String(selectedPeriodId) === String(period.period_id) ? 'secondary' : ''}
                >
                  {label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {periodExplanation ? (
        <div className="text-block">
          <h4>Selected Period Explanation</h4>
          <p>{periodExplanation.explanation_text}</p>
          <h4>Selected Period Recommendation</h4>
          <p>{periodExplanation.recommendation_text}</p>
          <div className="factor-grid">
            <FactorList title="Period SHAP Top Factors" factors={periodExplanation.shap_top_factors ?? []} />
            <FactorList title="Period LIME Top Factors" factors={periodExplanation.lime_top_factors ?? []} />
            <FactorList title="Period Agreed Top Factors" factors={periodExplanation.agreed_top_factors ?? []} />
          </div>
        </div>
      ) : null}
    </section>
  );
}
