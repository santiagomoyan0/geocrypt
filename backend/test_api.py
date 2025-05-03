import requests
import os
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "email": "test@example.com",
    "password": "testpassword123"
}

def test_registration():
    print("\n=== Probando registro de usuario ===")
    try:
        response = requests.post(f"{BASE_URL}/register", json=TEST_USER)
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            print(f"Response JSON: {response.json()}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error durante el registro: {str(e)}")
        return None

def test_login():
    print("\n=== Probando login ===")
    try:
        response = requests.post(
            f"{BASE_URL}/token",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            print(f"Response JSON: {response.json()}")
            return response.json()["access_token"]
        return None
    except Exception as e:
        print(f"Error durante el login: {str(e)}")
        return None

def test_upload_file(token, file_path, latitude, longitude):
    print("\n=== Probando subida de archivo ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {
                "latitude": latitude,
                "longitude": longitude
            }
            response = requests.post(
                f"{BASE_URL}/upload",
                headers=headers,
                files=files,
                data=data
            )
        
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            print(f"Response JSON: {response.json()}")
            return response.json()
        return None
    except Exception as e:
        print(f"Error durante la subida: {str(e)}")
        return None

def test_list_files(token):
    print("\n=== Probando listado de archivos ===")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/files", headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            print(f"Response JSON: {response.json()}")
            return response.json()
        return None
    except Exception as e:
        print(f"Error durante el listado: {str(e)}")
        return None

def test_download_file(token, file_id, latitude, longitude):
    print("\n=== Probando descarga de archivo ===")
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "latitude": latitude,
        "longitude": longitude
    }
    try:
        response = requests.get(
            f"{BASE_URL}/download/{file_id}",
            headers=headers,
            params=params
        )
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            # Guardar el archivo descargado
            filename = response.headers.get("content-disposition", "").split("filename=")[-1]
            with open(f"downloaded_{filename}", "wb") as f:
                f.write(response.content)
            print(f"Archivo guardado como: downloaded_{filename}")
        
        return response.status_code
    except Exception as e:
        print(f"Error durante la descarga: {str(e)}")
        return None

if __name__ == "__main__":
    # Crear un archivo de prueba
    test_file_path = "test_file.txt"
    with open(test_file_path, "w") as f:
        f.write("Este es un archivo de prueba para GeoCrypt")
    
    try:
        # Probar registro
        user_data = test_registration()
        if not user_data:
            print("Error en el registro. Abortando pruebas.")
            exit(1)
        
        # Probar login
        token = test_login()
        if not token:
            print("Error en el login. Abortando pruebas.")
            exit(1)
        
        # Probar subida de archivo
        upload_result = test_upload_file(
            token=token,
            file_path=test_file_path,
            latitude=40.4168,  # Madrid
            longitude=-3.7038
        )
        if not upload_result:
            print("Error en la subida. Abortando pruebas.")
            exit(1)
        
        # Probar listado de archivos
        files = test_list_files(token)
        if not files:
            print("Error en el listado. Abortando pruebas.")
            exit(1)
        
        if files:
            # Probar descarga del primer archivo
            test_download_file(
                token=token,
                file_id=files[0]["id"],
                latitude=40.4168,
                longitude=-3.7038
            )
    
    finally:
        # Limpiar archivo de prueba
        if os.path.exists(test_file_path):
            os.remove(test_file_path) 