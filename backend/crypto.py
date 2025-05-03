from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import geohash2

def derive_key_from_location(latitude: float, longitude: float) -> bytes:
    """Deriva una clave AES de 32 bytes a partir de la ubicación."""
    gh = geohash2.encode(latitude, longitude, precision=12)
    # Usar el geohash como semilla para generar una clave de 32 bytes
    key = gh.encode('utf-8') * (32 // len(gh) + 1)
    return key[:32]

def encrypt_file(content: bytes, latitude: float, longitude: float) -> bytes:
    """Cifra el contenido del archivo usando AES en modo GCM."""
    key = derive_key_from_location(latitude, longitude)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(content)
    
    # Combinar nonce, tag y texto cifrado
    return cipher.nonce + tag + ciphertext

def decrypt_file(encrypted_content: bytes, latitude: float, longitude: float) -> bytes:
    """Descifra el contenido del archivo usando AES en modo GCM."""
    key = derive_key_from_location(latitude, longitude)
    
    # Separar nonce, tag y texto cifrado
    nonce = encrypted_content[:16]
    tag = encrypted_content[16:32]
    ciphertext = encrypted_content[32:]
    
    # Crear cipher con el nonce original
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    
    # Descifrar y verificar
    return cipher.decrypt_and_verify(ciphertext, tag) 