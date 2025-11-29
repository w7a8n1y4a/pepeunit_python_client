import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AesGcmCipher:
    
    def aes_gcm_encode(self, data: str, key: str) -> str:
        """
        data: any python str
        key: (base64 str) 16, 24, 32 bytes sync encrypt key
        return: (base64 str - nonce).(base64 str - encrypted data).(base64 str - tag)
        """

        key = base64.b64decode(key.encode())
        nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
        aesgcm = AESGCM(key)

        cipher = aesgcm.encrypt(nonce, data.encode(), None)  # Encrypt data

        return f"{base64.b64encode(nonce).decode()}.{base64.b64encode(cipher).decode()}"
    
    def aes_gcm_decode(self, data: str, key: str) -> str:
        """
        data: (base64 str - nonce).(base64 str - encrypted data)
        key: (base64 str) 16, 24, 32 bytes sync encrypt key
        return: decode python str
        """

        key = base64.b64decode(key.encode())
        nonce, cipher = data.split(".")
        nonce = base64.b64decode(nonce.encode())
        cipher = base64.b64decode(cipher.encode())

        aesgcm = AESGCM(key)

        return aesgcm.decrypt(nonce, cipher, None).decode("utf-8")
