import os
import boto3


from dotenv import load_dotenv
import os

load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")


def load_file_s3(OUTPUT_NAME , ACCESS_KEY=ACCESS_KEY, SECRET_KEY=SECRET_KEY, BUCKET_NAME=BUCKET_NAME, ContentType="video/mp4"):
    session = boto3.session.Session()
    s3 = session.client(
        service_name="s3",
        endpoint_url="https://storage.yandexcloud.net",
        region_name="ru-central1",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )

    s3.upload_file(
        Filename=OUTPUT_NAME,
        Bucket=BUCKET_NAME,
        Key=f"videos/{OUTPUT_NAME}",
        ExtraArgs={
            "ACL": "public-read",
            "ContentType": ContentType,
        },
    )
    
    url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": f"videos/{OUTPUT_NAME}"},
            # ExpiresIn=3600  # сек
        )
    return url