import ai_service
from app import app


TEST_COURSES = [
    {
        "id": 1,
        "name": "Python 基礎程式設計",
        "category": "Programming",
        "level": "Beginner"
    },
    {
        "id": 2,
        "name": "Docker 容器化實戰",
        "category": "DevOps",
        "level": "Intermediate"
    },
    {
        "id": 3,
        "name": "AWS 雲端部署入門",
        "category": "Cloud",
        "level": "Intermediate"
    },
    {
        "id": 4,
        "name": "Amazon RDS 實戰",
        "category": "Database",
        "level": "Intermediate"
    }
]


def test_validate_recommendations_filters_invalid_course_id():
    ai_result = {
        "recommendations": [
            {
                "course_id": 999,
                "relevance_score": 95,
                "reason": "很適合"
            }
        ]
    }

    result = ai_service.validate_recommendations(
        ai_result,
        TEST_COURSES
    )

    assert result["recommendations"] == []


def test_validate_recommendations_filters_low_score():
    ai_result = {
        "recommendations": [
            {
                "course_id": 3,
                "relevance_score": 69,
                "reason": "有一些相關"
            }
        ]
    }

    result = ai_service.validate_recommendations(
        ai_result,
        TEST_COURSES
    )

    assert result["recommendations"] == []


def test_validate_recommendations_removes_duplicates():
    ai_result = {
        "recommendations": [
            {
                "course_id": 3,
                "relevance_score": 95,
                "reason": "直接符合 AWS 學習目標"
            },
            {
                "course_id": 3,
                "relevance_score": 90,
                "reason": "重複推薦同一門課"
            }
        ]
    }

    result = ai_service.validate_recommendations(
        ai_result,
        TEST_COURSES
    )

    recommendations = result["recommendations"]

    assert len(recommendations) == 1
    assert recommendations[0]["course_id"] == 3


def test_validate_recommendations_max_three_courses():
    ai_result = {
        "recommendations": [
            {
                "course_id": 1,
                "relevance_score": 90,
                "reason": "相關"
            },
            {
                "course_id": 2,
                "relevance_score": 85,
                "reason": "相關"
            },
            {
                "course_id": 3,
                "relevance_score": 80,
                "reason": "相關"
            },
            {
                "course_id": 4,
                "relevance_score": 75,
                "reason": "相關"
            }
        ]
    }

    result = ai_service.validate_recommendations(
        ai_result,
        TEST_COURSES
    )

    assert len(result["recommendations"]) == 3


def test_recommend_api_with_mock_ai(monkeypatch):
    def fake_recommend_courses(goal, courses):
        return {
            "recommendations": [
                {
                    "course_id": 3,
                    "course_name": "AWS 雲端部署入門",
                    "category": "Cloud",
                    "level": "Intermediate",
                    "relevance_score": 95,
                    "reason": "直接符合 AWS 雲端部署的學習目標"
                }
            ]
        }

    # routes.py 裡 import recommend_courses 的情況，
    # 這裡要 patch routes.recommend_courses
    monkeypatch.setattr(
        "routes.recommend_courses",
        fake_recommend_courses
    )

    client = app.test_client()

    response = client.post(
        "/recommend",
        json={
            "goal": "我想學 AWS 雲端部署"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["goal"] == "我想學 AWS 雲端部署"
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["course_id"] == 3
    assert data["recommendations"][0]["relevance_score"] == 95

def test_recommend_requires_request_body():
    client = app.test_client()

    response = client.post(
        "/recommend",
        json={}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Request body is required"


def test_recommend_requires_goal():
    client = app.test_client()

    response = client.post(
        "/recommend",
        json={
            "goal": ""
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "goal is required"