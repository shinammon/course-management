import os

from flask import Blueprint, jsonify, request
from data import courses, students, enrollments
from db import get_db_connection

api = Blueprint("api", __name__)


@api.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


@api.route("/courses", methods=["GET"])
def get_courses():
    use_rds = os.getenv("USE_RDS", "false").lower() == "true"

    if not use_rds:
        return jsonify(courses)

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, category, level
                FROM courses
                ORDER BY id
            """)

            result = cursor.fetchall()

        return jsonify(result)

    finally:
        connection.close()

@api.route("/students", methods=["GET"])
def get_students():
    return jsonify(students)


@api.route("/enrollments", methods=["GET"])
def get_enrollments():
    return jsonify(enrollments)


@api.route("/enrollments", methods=["POST"])
def create_enrollment():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    student_id = data.get("student_id")
    course_id = data.get("course_id")

    if not student_id or not course_id:
        return jsonify({
            "error": "student_id and course_id are required"
        }), 400

    new_enrollment = {
        "id": len(enrollments) + 1,
        "student_id": student_id,
        "course_id": course_id
    }

    enrollments.append(new_enrollment)

    return jsonify(new_enrollment), 201


@api.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    goal = data.get("goal", "")

    return jsonify({
        "goal": goal,
        "recommendations": [
            {
                "course_id": 2,
                "course_name": "Docker 容器化實戰",
                "reason": "適合想學習部署與容器化技術的學員"
            },
            {
                "course_id": 3,
                "course_name": "AWS 雲端部署入門",
                "reason": "適合想學習 AWS 與雲端部署流程的學員"
            }
        ]
    })