import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AesGcmCipher:
    
    def aes_gcm_encode(self, data: str, key: str) -> str:
        """Encrypt text using a Base64-encoded AES key and return the encoded nonce and ciphertext."""

        key = base64.b64decode(key.encode())
        nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
        aesgcm = AESGCM(key)

        cipher = aesgcm.encrypt(nonce, data.encode(), None)  # Encrypt data

        return f"{base64.b64encode(nonce).decode()}.{base64.b64encode(cipher).decode()}"
    
    def aes_gcm_decode(self, data: str, key: str) -> str:
        """Decrypt the encoded nonce and ciphertext using a Base64-encoded AES key."""

        key = base64.b64decode(key.encode())
        nonce, cipher = data.split(".")
        nonce = base64.b64decode(nonce.encode())
        cipher = base64.b64decode(cipher.encode())

        aesgcm = AESGCM(key)

        return aesgcm.decrypt(nonce, cipher, None).decode("utf-8")
