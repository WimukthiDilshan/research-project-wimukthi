const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

async function request(path, options = {}) {
  // Centralize API calls so the dashboard keeps one consistent JSON contract.
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message = payload?.message || payload?.detail?.message || 'Request failed.';
    const errors = payload?.errors ?? [];
    throw new Error(errors.length ? `${message} ${errors.join(', ')}` : message);
  }

  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    return payload.data;
  }

  return payload;
}

export async function fetchLessons() {
  // Load all lessons for the lesson selector.
  return request('/lessons');
}

export async function fetchLessonStudents(lessonId) {
  // Load the students for one lesson.
  return request(`/lessons/${lessonId}/students`);
}

export async function fetchStudentExplanation(studentId, lessonId) {
  // Load the explanation view for one student in one lesson.
  return request(`/students/${studentId}/lessons/${lessonId}/explanation`);
}

export async function fetchHighLoadPeriods(studentId, lessonId) {
  // Load high-load periods for one student in one lesson.
  return request(`/students/${studentId}/lessons/${lessonId}/high-load-periods`);
}

export async function fetchHighLoadPeriodExplanation(studentId, lessonId, periodId) {
  // Load period-level explanation for one selected high-load period.
  return request(`/students/${studentId}/lessons/${lessonId}/high-load-periods/${periodId}/explanation`);
}

export async function fetchClassSummary(lessonId) {
  // Load the class summary for one lesson.
  return request(`/lessons/${lessonId}/class-summary`);
}

export async function generateStudentExplanations(lessonId) {
  // Trigger backend generation for all student explanations in a lesson.
  return request(`/lessons/${lessonId}/generate-student-explanations`, {
    method: 'POST',
  });
}

export async function generateClassRecommendation(lessonId, classSummary) {
  // Trigger backend generation for the class-level recommendation.
  return request(`/lessons/${lessonId}/generate-class-recommendation`, {
    method: 'POST',
    body: JSON.stringify({ class_summary: classSummary }),
  });
}
