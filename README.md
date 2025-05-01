# GeoCrypt - Sistema de Almacenamiento Basado en Geohash

Sistema de almacenamiento de archivos que utiliza geohashes para organizar y acceder a archivos basados en su ubicación geográfica.

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Cuenta de AWS con acceso a S3
- Credenciales de AWS (Access Key ID y Secret Access Key)

## Configuración del Entorno

1. **Crear y activar el entorno virtual**:
```bash
# Crear el entorno virtual
python -m venv env

# Activar el entorno virtual
# En Linux/Mac:
source env/bin/activate
# En Windows:
.\env\Scripts\activate
```

2. **Instalar dependencias**:
```bash
# Navegar al directorio backend
cd backend

# Instalar las dependencias
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:
Crear un archivo `.env` en el directorio `backend` con el siguiente contenido:
```env
AWS_ACCESS_KEY_ID=tu_access_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_access_key
AWS_REGION=tu_region  # ej: us-east-1
S3_BUCKET_NAME=nombre_de_tu_bucket
```

## Ejecutar la Aplicación

1. **Iniciar el servidor**:
```bash
# Asegúrate de estar en el directorio backend
cd backend

# Iniciar el servidor con uvicorn
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

## Ejecutar Tests

```bash
# Asegúrate de estar en el directorio backend
cd backend

# Ejecutar todos los tests
pytest test_main.py -v
```

## Endpoints de la API

### 1. Subir Archivo
```http
POST /upload/{geohash}
```
- **Body**: form-data
  - Key: `file`
  - Value: Seleccionar archivo
  - Type: File

Ejemplo con Insomnia/Postman:
- URL: `http://localhost:8000/upload/u33d8`
- Método: POST
- Body: form-data
  - Key: `file`
  - Value: [Seleccionar archivo]
  - Type: File

### 2. Listar Archivos
```http
GET /list/{geohash}
```
Ejemplo:
- URL: `http://localhost:8000/list/u33d8`
- Método: GET

### 3. Descargar Archivo
```http
GET /download/{geohash}/{filename}
```
Ejemplo:
- URL: `http://localhost:8000/download/u33d8/nombre_del_archivo`
- Método: GET

## Ejemplos de Geohashes

- Madrid, España: `u33d8`
- San Rafael, Mendoza: `6g3qj`

## Notas Importantes

1. Asegúrate de que el bucket de S3 exista y sea accesible
2. Las credenciales de AWS deben tener los permisos necesarios para S3
3. El archivo `.env` debe estar en el directorio `backend`
4. Los tests requieren una conexión activa a AWS S3

## Solución de Problemas

1. **Error de conexión a AWS**:
   - Verificar las credenciales en `.env`
   - Confirmar que el bucket existe
   - Verificar los permisos de IAM

2. **Error en los tests**:
   - Asegurarse de que el entorno virtual está activado
   - Verificar que todas las dependencias están instaladas
   - Confirmar que las variables de entorno están configuradas

3. **Error al iniciar uvicorn**:
   - Verificar que estás en el directorio correcto
   - Confirmar que el archivo `main.py` existe
   - Asegurarse de que todas las dependencias están instaladas 