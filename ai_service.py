import json
import boto3

from opencc import OpenCC


MODEL_ID = "amazon.nova-micro-v1:0"

# 簡體 → 台灣繁體
cc = OpenCC("s2twp")


def get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name="us-east-1"
    )


def parse_ai_json(text):
    """
    清理模型可能額外產生的 markdown code block，
    再解析成 JSON。
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


def recommend_courses(goal, courses):
    client = get_bedrock_client()

    course_text = "\n".join(
        [
            (
                f"- course_id={course['id']}; "
                f"name={course['name']}; "
                f"category={course['category']}; "
                f"level={course['level']}"
            )
            for course in courses
        ]
    )

    prompt = f"""
你是一個嚴謹的課程推薦系統。

你的工作不是盡量推薦課程，
而是判斷現有課程是否真的符合使用者的學習目標。

【使用者學習目標】

{goal}

【目前資料庫中的課程】

{course_text}

請遵守以下規則：

1. 只能推薦上方課程清單中實際存在的課程。
2. 不得自行創造任何課程。
3. 必須依照使用者真正想學習的內容判斷相關性。
4. 不可以因為非常間接的關係而勉強推薦。
5. 每門候選課程給予 relevance_score，範圍 0 到 100。
6. 只有高度相關的課程才應給予 70 分以上。
7. 若沒有任何課程達到高度相關程度，recommendations 必須為空陣列。
8. 最多推薦 3 門課程。
9. 推薦原因必須說明「這門課如何直接符合使用者的學習目標」。
10. 所有自然語言文字一律使用繁體中文。
11. 不得輸出 Markdown。
12. 只能輸出合法 JSON。

回傳格式：

{{
  "recommendations": [
    {{
      "course_id": 1,
      "relevance_score": 90,
      "reason": "推薦原因"
    }}
  ]
}}

如果沒有適合課程：

{{
  "recommendations": []
}}
"""

    response = client.converse(
        modelId=MODEL_ID,

        system=[
            {
                "text": (
                    "你是一個保守且嚴謹的課程推薦系統。"
                    "寧可不推薦，也不要推薦與需求無明確關係的課程。"
                )
            }
        ],

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],

        inferenceConfig={
            "maxTokens": 700,
            "temperature": 0.1
        }
    )

    text = response["output"]["message"]["content"][0]["text"]

    ai_result = parse_ai_json(text)

    return validate_recommendations(
        ai_result=ai_result,
        courses=courses
    )


def validate_recommendations(ai_result, courses):
    """
    不直接相信 AI 回傳內容。
    所有推薦都必須經過後端驗證。
    """

    # 建立合法課程 ID 對照表
    valid_courses = {
        int(course["id"]): course
        for course in courses
    }

    raw_recommendations = ai_result.get(
        "recommendations",
        []
    )

    validated = []

    seen_course_ids = set()

    for recommendation in raw_recommendations:

        try:
            course_id = int(
                recommendation.get("course_id")
            )

            score = int(
                recommendation.get(
                    "relevance_score",
                    0
                )
            )

        except (TypeError, ValueError):
            continue

        # AI 幻覺不存在的 course_id
        if course_id not in valid_courses:
            continue

        # 過濾低相關推薦
        if score < 70:
            continue

        # 避免同一課程被推薦兩次
        if course_id in seen_course_ids:
            continue

        course = valid_courses[course_id]

        reason = recommendation.get(
            "reason",
            ""
        ).strip()

        if not reason:
            continue

        # 統一轉成繁體中文
        reason = cc.convert(reason)

        validated.append({
            "course_id": course_id,

            # 課程名稱不相信 AI，
            # 強制使用 RDS 裡的正式名稱
            "course_name": course["name"],

            "category": course["category"],
            "level": course["level"],

            "relevance_score": score,
            "reason": reason
        })

        seen_course_ids.add(course_id)

        if len(validated) >= 3:
            break

    # 依相關程度由高到低
    validated.sort(
        key=lambda item: item["relevance_score"],
        reverse=True
    )

    return {
        "recommendations": validated
    }