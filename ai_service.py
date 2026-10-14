import json
import boto3


MODEL_ID = "amazon.nova-micro-v1:0"


def get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name="us-east-1"
    )


def recommend_courses(goal, courses):
    client = get_bedrock_client()

    course_text = "\n".join(
        [
            f"- ID: {course['id']}, "
            f"名稱: {course['name']}, "
            f"分類: {course['category']}, "
            f"程度: {course['level']}"
            for course in courses
        ]
    )

    prompt = f"""
你是一個課程推薦助手。

使用者的學習目標：
{goal}

目前可選課程：
{course_text}

請從課程清單中推薦最多 3 門最適合的課程。

請只回傳 JSON，不要加入 Markdown 或其他文字。

格式必須是：
{{
  "recommendations": [
    {{
      "course_id": 1,
      "course_name": "課程名稱",
      "reason": "推薦原因"
    }}
  ]
}}
"""

    response = client.converse(
        modelId=MODEL_ID,
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
            "maxTokens": 600,
            "temperature": 0.2
        }
    )

    text = response["output"]["message"]["content"][0]["text"]

    return json.loads(text)