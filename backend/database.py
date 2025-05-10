from sqlmodel import SQLModel, create_engine, Session
import os

# Configuración de la base de datos SQLite
DATABASE_URL = "sqlite:///./geocrypt.db"
engine = create_engine(
    DATABASE_URL, 
    echo=True,  # Habilitar logs de SQL
    connect_args={"check_same_thread": False}  # Permitir acceso desde múltiples hilos
)

def init_db():
    # Crear todas las tablas si no existen
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session 