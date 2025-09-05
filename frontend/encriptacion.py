from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64

# Parámetros globales
SALT_SIZE = 16
KEY_SIZE = 32
NONCE_SIZE = 16
ITERACIONES = 100_000

def cifrar(texto_plano, password):
    salt = get_random_bytes(SALT_SIZE)
    key = PBKDF2(password, salt, dkLen=KEY_SIZE, count=ITERACIONES)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(texto_plano.encode('utf-8'))

    # Empaquetamos salt + nonce + tag + ciphertext
    datos = salt + cipher.nonce + tag + ciphertext
    return base64.b64encode(datos).decode('utf-8')


def descifrar(texto_cifrado_b64, password):
    datos = base64.b64decode(texto_cifrado_b64.encode('utf-8'))

    salt = datos[:SALT_SIZE]
    nonce = datos[SALT_SIZE:SALT_SIZE+NONCE_SIZE]
    tag = datos[SALT_SIZE+NONCE_SIZE:SALT_SIZE+NONCE_SIZE+16]
    ciphertext = datos[SALT_SIZE+NONCE_SIZE+16:]

    key = PBKDF2(password, salt, dkLen=KEY_SIZE, count=ITERACIONES)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    texto_plano = cipher.decrypt_and_verify(ciphertext, tag)

    return texto_plano.decode('utf-8')


def test():
    clave_original = "SPqGfxsIk4OkUD2mKptJfGWxz-2bhjlcAIT0zAWfVACV5df3Hu5uz4ndVBfA7tws"
    password = "rgusdjzo;v;laoeq3t8w9 e0g7054w8h tn78w09tp82u0 n3"

    # Encriptar
    cifrado = cifrar(clave_original, password)
    print("Texto cifrado:", cifrado)

    # Desencriptar
    descifrado = descifrar(cifrado, password)
    print("Texto descifrado:", descifrado)


# if __name__ == "__main__":
#     test()