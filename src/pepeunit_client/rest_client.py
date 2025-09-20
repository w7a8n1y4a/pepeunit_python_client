import json
from typing import Any, Dict, List, Optional, Union

import httpx

from .interfaces import RESTClientInterface


class RESTClient(RESTClientInterface):
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        follow_redirects: bool = True,
        limits: Optional[httpx.Limits] = None
    ) -> None:
        self.base_url = base_url.rstrip('/') if base_url else None
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.follow_redirects = follow_redirects
        
        self._default_headers = headers or {}
        self._limits = limits or httpx.Limits(max_keepalive_connections=20, max_connections=100)
        
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._default_headers,
                verify=self.verify_ssl,
                follow_redirects=self.follow_redirects,
                limits=self._limits
            )
        return self._client
    
    def _build_url(self, url: str) -> str:
        if self.base_url and not url.startswith(('http://', 'https://')):
            return f"{self.base_url}/{url.lstrip('/')}"
        return url
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        if headers is None:
            return self._default_headers.copy()
        
        merged_headers = self._default_headers.copy()
        merged_headers.update(headers)
        return merged_headers
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return {
                    'status_code': response.status_code,
                    'text': response.text,
                    'headers': dict(response.headers)
                }
        except (json.JSONDecodeError, ValueError):
            return {
                'status_code': response.status_code,
                'text': response.text,
                'headers': dict(response.headers),
                'error': 'Invalid JSON response'
            }
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            client = self._get_client()
            full_url = self._build_url(url)
            prepared_headers = self._prepare_headers(headers)
            
            response = client.get(
                full_url,
                headers=prepared_headers,
                params=params
            )
            
            result = self._handle_response(response)
            result['success'] = response.is_success
            return result
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timeout',
                'status_code': 408
            }
        except httpx.ConnectError:
            return {
                'success': False,
                'error': 'Connection error',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            client = self._get_client()
            full_url = self._build_url(url)
            prepared_headers = self._prepare_headers(headers)
            
            if json_data is not None:
                prepared_headers.setdefault('Content-Type', 'application/json')
                response = client.post(
                    full_url,
                    json=json_data,
                    headers=prepared_headers,
                    params=params
                )
            else:
                response = client.post(
                    full_url,
                    data=data,
                    headers=prepared_headers,
                    params=params
                )
            
            result = self._handle_response(response)
            result['success'] = response.is_success
            return result
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timeout',
                'status_code': 408
            }
        except httpx.ConnectError:
            return {
                'success': False,
                'error': 'Connection error',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            client = self._get_client()
            full_url = self._build_url(url)
            prepared_headers = self._prepare_headers(headers)
            
            if json_data is not None:
                prepared_headers.setdefault('Content-Type', 'application/json')
                response = client.put(
                    full_url,
                    json=json_data,
                    headers=prepared_headers,
                    params=params
                )
            else:
                response = client.put(
                    full_url,
                    data=data,
                    headers=prepared_headers,
                    params=params
                )
            
            result = self._handle_response(response)
            result['success'] = response.is_success
            return result
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timeout',
                'status_code': 408
            }
        except httpx.ConnectError:
            return {
                'success': False,
                'error': 'Connection error',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            client = self._get_client()
            full_url = self._build_url(url)
            prepared_headers = self._prepare_headers(headers)
            
            response = client.delete(
                full_url,
                headers=prepared_headers,
                params=params
            )
            
            result = self._handle_response(response)
            result['success'] = response.is_success
            return result
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timeout',
                'status_code': 408
            }
        except httpx.ConnectError:
            return {
                'success': False,
                'error': 'Connection error',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def patch(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            client = self._get_client()
            full_url = self._build_url(url)
            prepared_headers = self._prepare_headers(headers)
            
            if json_data is not None:
                prepared_headers.setdefault('Content-Type', 'application/json')
                response = client.patch(
                    full_url,
                    json=json_data,
                    headers=prepared_headers,
                    params=params
                )
            else:
                response = client.patch(
                    full_url,
                    data=data,
                    headers=prepared_headers,
                    params=params
                )
            
            result = self._handle_response(response)
            result['success'] = response.is_success
            return result
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timeout',
                'status_code': 408
            }
        except httpx.ConnectError:
            return {
                'success': False,
                'error': 'Connection error',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def set_default_headers(self, headers: Dict[str, str]) -> None:
        self._default_headers.update(headers)
        if self._client:
            self._client.headers.update(headers)
    
    def add_default_header(self, key: str, value: str) -> None:
        self._default_headers[key] = value
        if self._client:
            self._client.headers[key] = value
    
    def remove_default_header(self, key: str) -> None:
        self._default_headers.pop(key, None)
        if self._client:
            self._client.headers.pop(key, None)
    
    def get_client_info(self) -> Dict[str, Any]:
        return {
            'base_url': self.base_url,
            'timeout': self.timeout,
            'verify_ssl': self.verify_ssl,
            'follow_redirects': self.follow_redirects,
            'default_headers': self._default_headers.copy(),
            'limits': {
                'max_keepalive_connections': self._limits.max_keepalive_connections,
                'max_connections': self._limits.max_connections
            }
        }
    
    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
