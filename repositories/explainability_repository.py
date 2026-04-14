from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from repositories.query_utils import fetch_all, insert_record

COGNITIVE_LOAD_LOGS_TABLE = "cognitive_load_logs"
STUDENT_LESSON_EXPLANATIONS_TABLE = "student_lesson_explanations"
CLASS_LESSON_SUMMARY_TABLE = "class_lesson_summary"


def get_cognitive_load_logs_by_student_and_lesson(
    db: Session,
    student_id: int,
    lesson_id: int,
) -> list[dict[str, Any]]:
    query = (
        "SELECT * FROM cognitive_load_logs "
        "WHERE student_id = :student_id AND lesson_id = :lesson_id"
    )
    return fetch_all(
        db,
        query,
        {"student_id": student_id, "lesson_id": lesson_id},
    )


def get_students_by_lesson_id(
    db: Session,
    lesson_id: int,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM cognitive_load_logs WHERE lesson_id = :lesson_id"
    return fetch_all(db, query, {"lesson_id": lesson_id})


def get_lesson_overviews(
    db: Session,
) -> list[dict[str, Any]]:
    query = (
        "SELECT lesson_id, COUNT(DISTINCT student_id) AS total_students "
        "FROM cognitive_load_logs "
        "GROUP BY lesson_id "
        "ORDER BY lesson_id"
    )
    return fetch_all(db, query)


def get_unique_students_by_lesson_id(
    db: Session,
    lesson_id: int,
) -> list[dict[str, Any]]:
    query = (
        "SELECT DISTINCT student_id FROM cognitive_load_logs "
        "WHERE lesson_id = :lesson_id "
        "ORDER BY student_id"
    )
    return fetch_all(db, query, {"lesson_id": lesson_id})


def get_student_lesson_explanations_by_lesson_id(
    db: Session,
    lesson_id: int,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM student_lesson_explanations WHERE lesson_id = :lesson_id"
    return fetch_all(db, query, {"lesson_id": lesson_id})


def save_student_lesson_explanation(
    db: Session,
    payload: Mapping[str, Any],
) -> int | None:
    return insert_record(db, STUDENT_LESSON_EXPLANATIONS_TABLE, payload)


def save_class_lesson_summary(
    db: Session,
    payload: Mapping[str, Any],
) -> int | None:
    return insert_record(db, CLASS_LESSON_SUMMARY_TABLE, payload)
