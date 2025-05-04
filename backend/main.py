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
from models import User, FileModel, UserBase
from database import init_db, get_session
import geohash2
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = FastAPI()

# Inicializar la base de datos al arrancar
@app.on_event("startup")
def on_startup():
    init_db()

# Configuración de S3
try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    print("Cliente S3 creado exitosamente")
except Exception as e:
    print(f"Error al crear cliente S3: {str(e)}")
    raise

BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
if not BUCKET_NAME:
    print("ADVERTENCIA: AWS_BUCKET_NAME no está configurado en las variables de entorno")
    BUCKET_NAME = "geocrypt-files"  # Valor por defecto para pruebas
    print(f"Usando bucket por defecto: {BUCKET_NAME}")

# Verificar acceso a S3
try:
    s3.head_bucket(Bucket=BUCKET_NAME)
    print(f"Acceso al bucket {BUCKET_NAME} verificado")
except Exception as e:
    print(f"Error al verificar acceso al bucket: {str(e)}")
    print("ADVERTENCIA: No se pudo verificar el acceso al bucket S3")

# Schemas para las respuestas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FileResponse(BaseModel):
    id: int
    filename: str
    geohash: str
    created_at: datetime

# Endpoints de autenticación
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, session: Session = Depends(get_session)):
    # Verificar si el username ya existe
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Verificar si el email ya existe
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoints de archivos
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    current_user: User = Depends(auth.get_current_user),
    session: Session = Depends(get_session)
):
    try:
        # Leer el contenido del archivo
        content = await file.read()
        print(f"Contenido del archivo leído: {len(content)} bytes")
        
        # Cifrar el archivo
        encrypted_content = crypto.encrypt_file(content, latitude, longitude)
        print(f"Contenido cifrado: {len(encrypted_content)} bytes")
        
        # Generar geohash
        gh = geohash2.encode(latitude, longitude, precision=8)
        print(f"Geohash generado: {gh}")
        
        # Verificar configuración de S3
        if not BUCKET_NAME:
            print("Error: AWS_BUCKET_NAME no está configurado")
            raise HTTPException(
                status_code=500,
                detail="AWS_BUCKET_NAME no está configurado en las variables de entorno"
            )
        
        # Subir a S3
        s3_key = f"{current_user.username}/{gh}/{file.filename}"
        print(f"Intentando subir a S3: {s3_key}")
        try:
            # Intentar subir a S3
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=encrypted_content
            )
            print("Archivo subido exitosamente a S3")
        except Exception as e:
            print(f"Error al subir a S3: {str(e)}")
            print("Simulando almacenamiento local para pruebas")
            # En caso de error, simular el almacenamiento localmente
            os.makedirs("uploads", exist_ok=True)
            local_path = os.path.join("uploads", s3_key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(encrypted_content)
            print(f"Archivo guardado localmente en: {local_path}")
        
        # Obtener el tipo de contenido del archivo
        content_type = file.content_type or "application/octet-stream"
        print(f"Tipo de contenido: {content_type}")
        
        # Guardar en la base de datos
        db_file = FileModel(
            filename=file.filename,
            s3_key=s3_key,
            geohash=gh,
            user_id=current_user.id,
            size=len(content),
            content_type=content_type
        )
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
        print(f"Archivo guardado en la base de datos con ID: {db_file.id}")
        
        return {"message": "File uploaded successfully", "file_id": db_file.id}
    except Exception as e:
        print(f"Error general: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {str(e)}"
        )

@app.get("/download/{file_id}")
async def download_file(
    file_id: int,
    geohash: str,
    current_user: User = Depends(auth.get_current_user),
    session: Session = Depends(get_session)
):
    # Obtener el archivo de la base de datos
    file = session.exec(select(FileModel).where(FileModel.id == file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verificar acceso
    if file.user_id != current_user.id and file.geohash != geohash:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Intentar descargar de S3 primero
        print(f"Intentando descargar de S3: {file.s3_key}")
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file.s3_key)
        encrypted_content = response['Body'].read()
        print("Archivo descargado exitosamente de S3")
    except Exception as e:
        print(f"Error al descargar de S3: {str(e)}")
        print("Intentando leer desde almacenamiento local")
        # Si falla S3, intentar leer del almacenamiento local
        local_path = os.path.join("uploads", file.s3_key)
        try:
            with open(local_path, "rb") as f:
                encrypted_content = f.read()
            print(f"Archivo leído exitosamente desde: {local_path}")
        except Exception as local_error:
            print(f"Error al leer archivo local: {str(local_error)}")
            raise HTTPException(
                status_code=500,
                detail="No se pudo recuperar el archivo ni de S3 ni del almacenamiento local"
            )
    
    # Descifrar el archivo
    try:
        # Decodificar el geohash para obtener las coordenadas
        lat, lon = geohash2.decode(geohash)
        # Asegurarnos de que las coordenadas sean números flotantes
        lat = float(lat)
        lon = float(lon)
        print(f"Geohash recibido: {geohash}")
        print(f"Coordenadas decodificadas: lat={lat}, lon={lon}")
        print(f"Geohash del archivo en BD: {file.geohash}")
        print(f"Tamaño del contenido cifrado: {len(encrypted_content)} bytes")
        decrypted_content = crypto.decrypt_file(encrypted_content, lat, lon)
        print(f"Archivo descifrado exitosamente: {len(decrypted_content)} bytes")
    except Exception as e:
        print(f"Error al descifrar archivo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al descifrar el archivo: {str(e)}"
        )
    
    return {
        "filename": file.filename,
        "content": decrypted_content,
        "content_type": file.content_type
    }

@app.get("/files", response_model=List[FileResponse])
def list_files(
    current_user: User = Depends(auth.get_current_user),
    session: Session = Depends(get_session)
):
    files = session.exec(select(FileModel).where(FileModel.user_id == current_user.id)).all()
    return files