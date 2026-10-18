import os

from flask import Blueprint, jsonify, request
from data import courses, students, enrollments
from db import get_db_connection
from ai_service import recommend_courses
from s3_service import generate_image_url
from botocore.exceptions import NoCredentialsError

api = Blueprint("api", __name__)


@api.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })

@api.route("/courses", methods=["GET"])
def get_courses():
    use_rds = os.getenv(
        "USE_RDS",
        "false"
    ).lower() == "true"

    if use_rds:
        connection = get_db_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        id,
                        name,
                        category,
                        level,
                        image_key
                    FROM courses
                    ORDER BY id
                """)

                course_list = cursor.fetchall()

        finally:
            connection.close()

    else:
        course_list = courses

    result = []

    for course in course_list:
        item = dict(course)

        image_key = item.get("image_key")

        if image_key:
            try:
                item["image_url"] = generate_image_url(
                    image_key
                )

            except NoCredentialsError:
                # CI / 無 AWS 登入的本機環境
                # 不讓 S3 credentials 影響課程 API
                item["image_url"] = None
        else:
            item["image_url"] = None

        result.append(item)

    return jsonify(result)

@api.route("/students", methods=["GET"])
def get_students():
    use_rds = os.getenv("USE_RDS", "false").lower() == "true"

    if not use_rds:
        return jsonify(students)

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email
                FROM students
                ORDER BY id
            """)

            result = cursor.fetchall()

        return jsonify(result)

    finally:
        connection.close()

@api.route("/enrollments", methods=["GET"])
def get_enrollments():
    use_rds = os.getenv("USE_RDS", "false").lower() == "true"

    if not use_rds:
        return jsonify(enrollments)

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    e.id,
                    e.student_id,
                    s.name AS student_name,
                    e.course_id,
                    c.name AS course_name,
                    e.created_at
                FROM enrollments e
                JOIN students s
                    ON e.student_id = s.id
                JOIN courses c
                    ON e.course_id = c.id
                ORDER BY e.id
            """)

            result = cursor.fetchall()

        return jsonify(result)

    finally:
        connection.close()

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

    use_rds = os.getenv("USE_RDS", "false").lower() == "true"

    # 本機 / CI 使用 mock data
    if not use_rds:
        new_enrollment = {
            "id": len(enrollments) + 1,
            "student_id": student_id,
            "course_id": course_id
        }

        enrollments.append(new_enrollment)

        return jsonify(new_enrollment), 201

    # AWS 正式環境使用 RDS
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO enrollments (student_id, course_id)
                VALUES (%s, %s)
                """,
                (student_id, course_id)
            )

            connection.commit()

            new_id = cursor.lastrowid

        return jsonify({
            "id": new_id,
            "student_id": student_id,
            "course_id": course_id
        }), 201

    except Exception as e:
        connection.rollback()

        return jsonify({
            "error": str(e)
        }), 400

    finally:
        connection.close()

@api.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    goal = data.get("goal", "").strip()

    if not goal:
        return jsonify({
            "error": "goal is required"
        }), 400

    use_rds = os.getenv(
        "USE_RDS",
        "false"
    ).lower() == "true"

    if use_rds:
        connection = get_db_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        id,
                        name,
                        category,
                        level
                    FROM courses
                    ORDER BY id
                """)

                course_list = cursor.fetchall()

        finally:
            connection.close()

    else:
        course_list = courses

    try:
        result = recommend_courses(
            goal=goal,
            courses=course_list
        )

        return jsonify({
            "goal": goal,
            "recommendations":
                result["recommendations"]
        })

    except Exception as e:
        return jsonify({
            "error":
                "AI recommendation failed",
            "detail":
                str(e)
        }), 500