from app import app


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_get_courses():
    client = app.test_client()

    response = client.get("/courses")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) >= 1


def test_create_enrollment():
    client = app.test_client()

    response = client.post(
        "/enrollments",
        json={
            "student_id": 2,
            "course_id": 3
        }
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["student_id"] == 2
    assert data["course_id"] == 3