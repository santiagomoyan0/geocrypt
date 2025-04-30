import pytest
from main import app
import tempfile
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.fixture
def test_file():
    # Crear un archivo temporal para las pruebas
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        return tmp.name

def test_upload_file(test_file):
    geohash = "u33d8"  # Un geohash de ejemplo
    with open(test_file, "rb") as f:
        response = client.post(
            f"/upload/{geohash}",
            files={"file": ("test.txt", f, "text/plain")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "path" in data
    assert data["message"] == "Archivo subido correctamente"

def test_list_files():
    geohash = "u33d8"
    response = client.get(f"/list/{geohash}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_download_file():
    geohash = "u33d8"
    # Primero necesitamos subir un archivo para poder descargarlo
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        with open(tmp.name, "rb") as f:
            upload_response = client.post(
                f"/upload/{geohash}",
                files={"file": ("test.txt", f, "text/plain")}
            )
    
    if upload_response.status_code == 200:
        file_id = upload_response.json()["file_id"]
        response = client.get(f"/download/{geohash}/{file_id}_test.txt")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream" 