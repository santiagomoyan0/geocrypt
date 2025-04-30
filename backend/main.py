from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import boto3
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from typing import List

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
app = FastAPI()

@app.post("/upload/{geohash}")
async def upload_file(geohash: str, file: UploadFile = File(...)):
    file_id = str(uuid4())
    filename = f"{geohash}/{file_id}_{file.filename}"

    try:
        s3.upload_fileobj(
            Fileobj=file.file,
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        return {"message": "Archivo subido correctamente", "file_id": file_id, "path": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list/{geohash}", response_model=List[str])
def list_files(geohash: str):
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=f"{geohash}/")
        contents = response.get("Contents", [])
        return [obj["Key"] for obj in contents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{geohash}/{filename}")
def download_file(geohash: str, filename: str):
    key = f"{geohash}/{filename}"
    local_filename = f"/tmp/{filename}"

    try:
        s3.download_file(S3_BUCKET_NAME, key, local_filename)
        return FileResponse(local_filename, media_type='application/octet-stream', filename=filename)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")