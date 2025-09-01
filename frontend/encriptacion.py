from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import os

from dotenv import load_dotenv

# Función para generar una clave a partir de una contraseña
def generar_clave(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

# Cifrar
def cifrar(texto: str, password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)  # Sal aleatoria
    clave = generar_clave(password, salt)
    fernet = Fernet(clave)
    texto_cifrado = fernet.encrypt(texto.encode())
    return texto_cifrado, salt

# Descifrar
def descifrar(texto_cifrado: bytes, password: str, salt: bytes) -> str:
    clave = generar_clave(password, salt)
    fernet = Fernet(clave)
    return fernet.decrypt(texto_cifrado).decode()


def cifrar_api_key():
    load_dotenv(".env")

    api_key = os.getenv("GENIUS_TOKEN")
    password = os.getenv("KEY_PASSWORD")

    texto_cifrado, salt = cifrar(api_key, password)

    texto_cifrado_str = base64.b64encode(texto_cifrado).decode('ascii')
    salt_str = base64.b64encode(salt).decode('ascii')

    print("Sal:", salt_str)
    print("Texto cifrado:", texto_cifrado_str)

    texto_descifrado = descifrar(texto_cifrado, password, salt)
    print("Texto descifrado:", texto_descifrado)


def descifrar_api_key(texto_b64, password, sal_b64):
    texto = base64.b64decode(texto_b64.encode('ascii'))
    sal = base64.b64decode(sal_b64.encode('ascii'))
    key = descifrar(texto, password, sal)
    return key


if __name__ == "__main__":
    # cifrar_api_key()
    descifrar_api_key()

    
