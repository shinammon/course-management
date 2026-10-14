import boto3


BUCKET_NAME = "course-management-assets-800460064208"


def get_s3_client():
    return boto3.client(
        "s3",
        region_name="us-east-1"
    )


def generate_image_url(image_key):
    if not image_key:
        return None

    s3 = get_s3_client()

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": image_key
        },
        ExpiresIn=3600
    )