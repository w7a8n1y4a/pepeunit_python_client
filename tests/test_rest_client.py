import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from pepeunit_client.rest_client import RESTClient
from pepeunit_client.interfaces import RESTClientInterface


class TestRESTClient:
    
    def test_implements_interface(self):
        assert issubclass(RESTClient, RESTClientInterface)
    
    def test_init_with_defaults(self):
        client = RESTClient()
        assert client.base_url is None
        assert client.timeout == 30.0
        assert client.verify_ssl is True
        assert client.follow_redirects is True
        assert client._default_headers == {}
        assert client._client is None
    
    def test_init_with_custom_params(self):
        client = RESTClient(
            base_url="https://api.example.com",
            timeout=60.0,
            headers={"Authorization": "Bearer token"},
            verify_ssl=False,
            follow_redirects=False
        )
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60.0
        assert client.verify_ssl is False
        assert client.follow_redirects is False
        assert client._default_headers == {"Authorization": "Bearer token"}
    
    def test_build_url_with_base_url(self):
        client = RESTClient(base_url="https://api.example.com")
        assert client._build_url("users") == "https://api.example.com/users"
        assert client._build_url("/users") == "https://api.example.com/users"
        assert client._build_url("https://other.com/users") == "https://other.com/users"
    
    def test_build_url_without_base_url(self):
        client = RESTClient()
        assert client._build_url("https://api.example.com/users") == "https://api.example.com/users"
        assert client._build_url("users") == "users"
    
    def test_prepare_headers(self):
        client = RESTClient(headers={"Content-Type": "application/json"})
        
        # Test with no additional headers
        headers = client._prepare_headers()
        assert headers == {"Content-Type": "application/json"}
        
        # Test with additional headers
        additional_headers = {"Authorization": "Bearer token"}
        headers = client._prepare_headers(additional_headers)
        expected = {"Content-Type": "application/json", "Authorization": "Bearer token"}
        assert headers == expected
    
    def test_handle_response_json(self):
        client = RESTClient()
        
        # Mock response with JSON content
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"key": "value"}
        mock_response.status_code = 200
        
        result = client._handle_response(mock_response)
        assert result == {"key": "value"}
    
    def test_handle_response_text(self):
        client = RESTClient()
        
        # Mock response with text content
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Hello World"
        mock_response.status_code = 200
        
        result = client._handle_response(mock_response)
        expected = {
            "status_code": 200,
            "text": "Hello World",
            "headers": {"content-type": "text/plain"}
        }
        assert result == expected
    
    def test_handle_response_invalid_json(self):
        client = RESTClient()
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON"
        mock_response.status_code = 200
        
        result = client._handle_response(mock_response)
        expected = {
            "status_code": 200,
            "text": "Invalid JSON",
            "headers": {"content-type": "application/json"},
            "error": "Invalid JSON response"
        }
        assert result == expected
    
    @patch('httpx.Client')
    def test_get_success(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": "test"}
        mock_client.get.return_value = mock_response
        
        result = client.get("/users")
        
        assert result["success"] is True
        assert result["data"] == "test"
        mock_client.get.assert_called_once()
    
    @patch('httpx.Client')
    def test_get_with_params(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": "test"}
        mock_client.get.return_value = mock_response
        
        result = client.get("/users", params={"page": 1, "limit": 10})
        
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"] == {"page": 1, "limit": 10}
    
    @patch('httpx.Client')
    def test_get_timeout_error(self, mock_client_class):
        client = RESTClient()
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        
        result = client.get("https://api.example.com/users")
        
        assert result["success"] is False
        assert result["error"] == "Request timeout"
        assert result["status_code"] == 408
    
    @patch('httpx.Client')
    def test_get_connection_error(self, mock_client_class):
        client = RESTClient()
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get.side_effect = httpx.ConnectError("Connection failed")
        
        result = client.get("https://api.example.com/users")
        
        assert result["success"] is False
        assert result["error"] == "Connection error"
        assert result["status_code"] == 0
    
    @patch('httpx.Client')
    def test_post_json_success(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"id": 123}
        mock_client.post.return_value = mock_response
        
        data = {"name": "John", "email": "john@example.com"}
        result = client.post("/users", json_data=data)
        
        assert result["success"] is True
        assert result["id"] == 123
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["json"] == data
        assert "Content-Type" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
    
    @patch('httpx.Client')
    def test_post_form_data(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"status": "ok"}
        mock_client.post.return_value = mock_response
        
        data = {"name": "John", "email": "john@example.com"}
        result = client.post("/users", data=data)
        
        assert result["success"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["data"] == data
    
    @patch('httpx.Client')
    def test_put_success(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"updated": True}
        mock_client.put.return_value = mock_response
        
        data = {"name": "John Updated"}
        result = client.put("/users/1", json_data=data)
        
        assert result["success"] is True
        assert result["updated"] is True
        mock_client.put.assert_called_once()
    
    @patch('httpx.Client')
    def test_delete_success(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"deleted": True}
        mock_client.delete.return_value = mock_response
        
        result = client.delete("/users/1")
        
        assert result["success"] is True
        assert result["deleted"] is True
        mock_client.delete.assert_called_once()
    
    @patch('httpx.Client')
    def test_patch_success(self, mock_client_class):
        client = RESTClient(base_url="https://api.example.com")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"patched": True}
        mock_client.patch.return_value = mock_response
        
        data = {"name": "John Patched"}
        result = client.patch("/users/1", json_data=data)
        
        assert result["success"] is True
        assert result["patched"] is True
        mock_client.patch.assert_called_once()
    
    def test_set_default_headers(self):
        client = RESTClient()
        client._client = Mock()
        
        new_headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        client.set_default_headers(new_headers)
        
        assert client._default_headers == new_headers
        client._client.headers.update.assert_called_once_with(new_headers)
    
    def test_add_default_header(self):
        client = RESTClient()
        mock_client = Mock()
        mock_client.headers = {}
        client._client = mock_client
        
        client.add_default_header("Authorization", "Bearer token")
        
        assert client._default_headers["Authorization"] == "Bearer token"
        assert mock_client.headers["Authorization"] == "Bearer token"
    
    def test_remove_default_header(self):
        client = RESTClient(headers={"Authorization": "Bearer token"})
        mock_client = Mock()
        mock_client.headers = {"Authorization": "Bearer token"}
        client._client = mock_client
        
        client.remove_default_header("Authorization")
        
        assert "Authorization" not in client._default_headers
        assert "Authorization" not in mock_client.headers
    
    def test_get_client_info(self):
        client = RESTClient(
            base_url="https://api.example.com",
            timeout=60.0,
            headers={"Authorization": "Bearer token"}
        )
        
        info = client.get_client_info()
        
        assert info["base_url"] == "https://api.example.com"
        assert info["timeout"] == 60.0
        assert info["verify_ssl"] is True
        assert info["follow_redirects"] is True
        assert info["default_headers"] == {"Authorization": "Bearer token"}
        assert "limits" in info
    
    def test_close(self):
        client = RESTClient()
        mock_client = Mock()
        client._client = mock_client
        
        client.close()
        
        mock_client.close.assert_called_once()
        assert client._client is None
    
    def test_context_manager(self):
        client = RESTClient()
        
        with patch.object(client, 'close') as mock_close:
            with client as ctx_client:
                assert ctx_client is client
            mock_close.assert_called_once()
    
    def test_exception_handling_in_methods(self):
        client = RESTClient()
        
        with patch.object(client, '_get_client', side_effect=Exception("Client error")):
            result = client.get("/test")
            
            assert result["success"] is False
            assert result["error"] == "Client error"
            assert result["status_code"] == 0
