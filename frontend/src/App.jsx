import React, { useEffect, useState } from 'react';
import ClassSummary from './components/ClassSummary';
import StudentCard from './components/StudentCard';
import {
  fetchClassSummary,
  fetchLessonStudents,
  fetchLessons,
  fetchStudentExplanation,
  generateClassRecommendation,
  generateStudentExplanations,
} from './api/client';

export default function App() {
  const [lessons, setLessons] = useState([]);
  const [selectedLessonId, setSelectedLessonId] = useState('');
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [studentExplanation, setStudentExplanation] = useState(null);
  const [classSummary, setClassSummary] = useState(null);
  const [classRecommendation, setClassRecommendation] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // Load lesson options once when the dashboard starts.
    loadLessons();
  }, []);

  useEffect(() => {
    // Refresh lesson-level data whenever the selected lesson changes.
    if (!selectedLessonId) {
      setStudents([]);
      setSelectedStudentId('');
      setStudentExplanation(null);
      setClassSummary(null);
      setClassRecommendation('');
      return;
    }

    loadLessonData(selectedLessonId);
  }, [selectedLessonId]);

  useEffect(() => {
    // Keep the student explanation panel in sync with the selected student.
    if (!selectedLessonId || !selectedStudentId) {
      setStudentExplanation(null);
      return;
    }

    loadStudentExplanation(selectedStudentId, selectedLessonId);
  }, [selectedLessonId, selectedStudentId]);

  async function loadLessons() {
    // Populate the lesson selector from the API.
    try {
      setError('');
      const payload = await fetchLessons();
      setLessons(payload.lessons ?? []);
      if (!selectedLessonId && payload.lessons?.length) {
        setSelectedLessonId(String(payload.lessons[0].lesson_id));
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadLessonData(lessonId) {
    // Load the student list and class summary in parallel for the chosen lesson.
    try {
      setLoading(true);
      setError('');
      const [studentsPayload, summaryPayload] = await Promise.all([
        fetchLessonStudents(lessonId),
        fetchClassSummary(lessonId),
      ]);
      setStudents(studentsPayload.students ?? []);
      setClassSummary(summaryPayload);
      setClassRecommendation(summaryPayload?.next_lesson_recommendation ?? '');
      const nextStudentId = studentsPayload.students?.[0]?.student_id;
      setSelectedStudentId(nextStudentId ? String(nextStudentId) : '');
    } catch (err) {
      setError(err.message);
      setStudents([]);
      setClassSummary(null);
      setSelectedStudentId('');
    } finally {
      setLoading(false);
    }
  }

  async function loadStudentExplanation(studentId, lessonId) {
    // Fetch the currently selected student's explanation from the backend.
    try {
      setError('');
      const payload = await fetchStudentExplanation(studentId, lessonId);
      setStudentExplanation(payload);
    } catch (err) {
      setError(err.message);
      setStudentExplanation(null);
    }
  }

  async function handleGenerateStudentExplanations() {
    // Ask the backend to generate and save explanation rows for the lesson.
    if (!selectedLessonId) return;
    try {
      setLoading(true);
      setError('');
      const payload = await generateStudentExplanations(selectedLessonId);
      setStatusMessage(`Generated explanations for ${payload.count} students.`);
      await Promise.all([loadLessonData(selectedLessonId), loadLessons()]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefreshClassSummary() {
    // Reload the class summary so the dashboard reflects saved rows.
    if (!selectedLessonId) return;
    try {
      setLoading(true);
      setError('');
      const payload = await fetchClassSummary(selectedLessonId);
      setClassSummary(payload);
      setClassRecommendation(payload?.next_lesson_recommendation ?? '');
      setStatusMessage('Class summary refreshed.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateRecommendation() {
    // Generate the class-level next lesson recommendation from the saved summary.
    if (!selectedLessonId || !classSummary) return;
    try {
      setLoading(true);
      setError('');
      const payload = await generateClassRecommendation(selectedLessonId, classSummary);
      setClassRecommendation(payload.next_lesson_recommendation);
      setStatusMessage('Class recommendation generated.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Teacher Dashboard</p>
          <h1>Lesson explainability console</h1>
          <p className="hero-copy">
            Review student cognitive load, inspect explanations, and generate class-level guidance.
          </p>
        </div>
        <div className="actions-row">
          <button onClick={handleGenerateStudentExplanations} disabled={!selectedLessonId || loading}>
            Generate student explanations
          </button>
          <button onClick={handleRefreshClassSummary} disabled={!selectedLessonId || loading} className="secondary">
            Generate class summary
          </button>
          <button onClick={handleGenerateRecommendation} disabled={!selectedLessonId || !classSummary || loading} className="secondary">
            Generate recommendation
          </button>
        </div>
      </header>

      <section className="toolbar">
        <label>
          Lesson
          <select value={selectedLessonId} onChange={(event) => setSelectedLessonId(event.target.value)}>
            <option value="">Select a lesson</option>
            {lessons.map((lesson) => (
              <option key={lesson.lesson_id} value={lesson.lesson_id}>
                Lesson {lesson.lesson_id} ({lesson.total_students} students)
              </option>
            ))}
          </select>
        </label>

        <label>
          Student
          <select
            value={selectedStudentId}
            onChange={(event) => setSelectedStudentId(event.target.value)}
            disabled={!students.length}
          >
            <option value="">Select a student</option>
            {students.map((student) => (
              <option key={student.student_id} value={student.student_id}>
                Student {student.student_id}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? <div className="alert error">{error}</div> : null}
      {statusMessage ? <div className="alert success">{statusMessage}</div> : null}

      <main className="dashboard-grid">
        <StudentCard explanation={studentExplanation} />
        <ClassSummary summary={classSummary} recommendation={classRecommendation} />
      </main>

      {loading ? <p className="loading-text">Loading...</p> : null}
    </div>
  );
}
