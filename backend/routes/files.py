from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form, status
from sqlmodel import Session, select
from typing import List
import os
import geohash2
from models import User, File
from database import get_session
import auth
import crypto
from schemas.files import FileResponse, FileCreate
from services.s3_service import S3Service

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
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
        gh = geohash2.encode(latitude, longitude, precision=7)
        print(f"Geohash generado: {gh}")
        
        # Subir a S3
        s3_key = f"{current_user.username}/{gh}/{file.filename}"
        print(f"Intentando subir a S3: {s3_key}")
        
        if not await S3Service.upload_file(encrypted_content, s3_key):
            # En caso de error, simular el almacenamiento localmente
            os.makedirs("uploads", exist_ok=True)
            local_path = os.path.join("uploads", s3_key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(encrypted_content)
            print(f"Archivo guardado localmente en: {local_path}")
        
        # Guardar en la base de datos
        db_file = File(
            filename=file.filename,
            s3_key=s3_key,
            geohash=gh,
            user_id=current_user.id,
            size=len(content),
            content_type=file.content_type or "application/octet-stream"
        )
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
        
        return {"message": "File uploaded successfully", "file_id": db_file.id}
    except Exception as e:
        print(f"Error general: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {str(e)}"
        )

@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    geohash: str,
    current_user: User = Depends(auth.get_current_user),
    save_path: str = "downloads",
    session: Session = Depends(get_session)
):
    # Obtener el archivo de la base de datos
    file = session.exec(select(File).where(File.id == file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Verificar acceso
    if file.user_id != current_user.id and file.geohash != geohash:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Intentar descargar de S3
        encrypted_content = await S3Service.download_file(file.s3_key)
    except Exception as e:
        print(f"Error al descargar de S3: {str(e)}")
        # Si falla S3, intentar leer del almacenamiento local
        local_path = os.path.join("uploads", file.s3_key)
        try:
            with open(local_path, "rb") as f:
                encrypted_content = f.read()
        except Exception as local_error:
            raise HTTPException(
                status_code=500,
                detail="No se pudo recuperar el archivo ni de S3 ni del almacenamiento local"
            )
    
    # Descifrar el archivo
    try:
        lat, lon, me1, me2 = geohash2.decode_exactly(geohash)
        decrypted_content = crypto.decrypt_file(encrypted_content, float(lat), float(lon))
        
        # Guardar el archivo descifrado
        os.makedirs(save_path, exist_ok=True)
        output_file_path = os.path.join(save_path, file.filename)
        with open(output_file_path, "wb") as output_file:
            output_file.write(decrypted_content)
        
        return {"message": "File downloaded and decrypted successfully", "path": output_file_path}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al descifrar el archivo: {str(e)}"
        )

@router.get("/", response_model=List[FileResponse])
def list_files(
    current_user: User = Depends(auth.get_current_user),
    session: Session = Depends(get_session)
):
    files = session.exec(
        select(File).where(File.user_id == current_user.id)
    ).all()
    return files

@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: int,
    current_user: User = Depends(auth.get_current_user),
    session: Session = Depends(get_session)
):
    file = session.exec(
        select(File).where(
            File.id == file_id,
            File.user_id == current_user.id
        )
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(auth.get_current_user),
    session: Session = Depends(get_session)
):
    file = session.exec(
        select(File).where(
            File.id == file_id,
            File.user_id == current_user.id
        )
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Eliminar de S3
    await S3Service.delete_file(file.s3_key)
    
    # Eliminar de la base de datos
    session.delete(file)
    session.commit()
    
    return {"message": "File deleted successfully"} 