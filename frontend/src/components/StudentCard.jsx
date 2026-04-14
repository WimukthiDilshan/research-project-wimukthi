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

export default function StudentCard({ explanation }) {
  if (!explanation) {
    return (
      <section className="panel">
        <h3>Student Explanation</h3>
        <p className="muted">Select a student to view their explanation.</p>
      </section>
    );
  }

  return (
    <section className="panel">
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
    </section>
  );
}
