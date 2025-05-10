from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List
import boto3
import os
from datetime import timedelta, datetime
from pydantic import BaseModel
import auth
import crypto
from models import User, File, UserBase
from database import init_db, get_session
import geohash2
from dotenv import load_dotenv
from routes import auth_router, files_router
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from schemas.auth import UserCreate, UserResponse
from schemas.files import FileResponse, FileCreate
import shutil

# Cargar variables de entorno desde .env
load_dotenv()

app = FastAPI()

# Configuración de CORS
origins = [
    "http://localhost:3000",     # React
    "http://localhost:19006",    # Expo
    "http://localhost:19000",    # Expo
    "http://localhost:19001",    # Expo
    "http://localhost:19002",    # Expo
    "exp://localhost:19000",     # Expo
    "exp://localhost:19001",     # Expo
    "exp://localhost:19002",     # Expo
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos al arrancar
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

# Incluir routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(files_router, prefix="/files", tags=["files"])