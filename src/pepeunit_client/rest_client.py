import json
from typing import Any, Dict, Optional

from .interfaces import RESTClientInterface
from .exceptions import PepeunitClientError


try:
    import httpx
    REST_AVAILABLE = True
except ImportError:
    REST_AVAILABLE = False


class RESTClient(RESTClientInterface):
    """Реализация REST клиента на основе httpx"""
    
    def __init__(self, timeout: int = 30):
        if not REST_AVAILABLE:
            raise PepeunitClientError("httpx is not installed. Install with: pip install 'pepeunit-client[rest]'")
        
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
    
    def __del__(self):
        """Закрытие клиента при удалении объекта"""
        if hasattr(self, 'client'):
            self.client.close()
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET запрос"""
        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            
            # Пытаемся разобрать как JSON, если не получается - возвращаем текст
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": response.text, "status_code": response.status_code}
                
        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                raise PepeunitClientError(f"HTTP error {e.response.status_code}: {e.response.text}")
            elif 'httpx' in str(type(e)) and 'RequestError' in str(type(e)):
                raise PepeunitClientError(f"Request error: {e}")
            else:
                raise PepeunitClientError(f"Unexpected error during GET request: {e}")
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """POST запрос"""
        try:
            response = self.client.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": response.text, "status_code": response.status_code}
                
        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                raise PepeunitClientError(f"HTTP error {e.response.status_code}: {e.response.text}")
            elif 'httpx' in str(type(e)) and 'RequestError' in str(type(e)):
                raise PepeunitClientError(f"Request error: {e}")
            else:
                raise PepeunitClientError(f"Unexpected error during POST request: {e}")
    
    def put(self, url: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """PUT запрос"""
        try:
            response = self.client.put(url, json=data, headers=headers)
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": response.text, "status_code": response.status_code}
                
        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                raise PepeunitClientError(f"HTTP error {e.response.status_code}: {e.response.text}")
            elif 'httpx' in str(type(e)) and 'RequestError' in str(type(e)):
                raise PepeunitClientError(f"Request error: {e}")
            else:
                raise PepeunitClientError(f"Unexpected error during PUT request: {e}")
    
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """DELETE запрос"""
        try:
            response = self.client.delete(url, headers=headers)
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": response.text, "status_code": response.status_code}
                
        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                raise PepeunitClientError(f"HTTP error {e.response.status_code}: {e.response.text}")
            elif 'httpx' in str(type(e)) and 'RequestError' in str(type(e)):
                raise PepeunitClientError(f"Request error: {e}")
            else:
                raise PepeunitClientError(f"Unexpected error during DELETE request: {e}")
    
    def download_file(self, url: str, file_path: str, 
                     headers: Optional[Dict[str, str]] = None) -> None:
        """Скачивание файла"""
        try:
            with self.client.stream('GET', url, headers=headers) as response:
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                        
        except IOError as e:
            raise PepeunitClientError(f"File writing error: {e}")
        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                raise PepeunitClientError(f"HTTP error {e.response.status_code}: {e.response.text}")
            elif 'httpx' in str(type(e)) and 'RequestError' in str(type(e)):
                raise PepeunitClientError(f"Request error: {e}")
            else:
                raise PepeunitClientError(f"Unexpected error during file download: {e}")


class DummyRESTClient(RESTClientInterface):
    """Заглушка REST клиента для случаев, когда REST не используется"""
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        raise PepeunitClientError("REST client is not available. Install httpx to use REST functionality.")
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        raise PepeunitClientError("REST client is not available. Install httpx to use REST functionality.")
    
    def put(self, url: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        raise PepeunitClientError("REST client is not available. Install httpx to use REST functionality.")
    
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        raise PepeunitClientError("REST client is not available. Install httpx to use REST functionality.")
    
    def download_file(self, url: str, file_path: str, 
                     headers: Optional[Dict[str, str]] = None) -> None:
        raise PepeunitClientError("REST client is not available. Install httpx to use REST functionality.")
