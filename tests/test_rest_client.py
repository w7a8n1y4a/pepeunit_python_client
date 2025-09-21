
import json
import pytest
from unittest.mock import Mock, patch

from pepeunit_client.rest_client import RESTClient, DummyRESTClient
from pepeunit_client.exceptions import PepeunitClientError


class TestRESTClient:
    
    @patch('pepeunit_client.rest_client.REST_AVAILABLE', False)
    def test_rest_not_available(self):
        with pytest.raises(PepeunitClientError, match="httpx is not installed"):
            RESTClient()
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_rest_client_initialization(self, mock_httpx):
        mock_client_instance = Mock()
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient(timeout=60)
        
        assert client.timeout == 60
        mock_httpx.Client.assert_called_with(timeout=60)
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_get_request(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok", "data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        result = client.get("http://test.com/api", headers={"test": "header"})
        
        mock_client_instance.get.assert_called_with("http://test.com/api", headers={"test": "header"})
        assert result == {"status": "ok", "data": "test"}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_get_request_text_response(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("error", "", 0)
        mock_response.text = "plain text response"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        result = client.get("http://test.com/api")
        
        assert result == {"text": "plain text response", "status_code": 200}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_post_request(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"created": True}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        test_data = {"name": "test", "value": 123}
        result = client.post("http://test.com/api", data=test_data, headers={"auth": "token"})
        
        mock_client_instance.post.assert_called_with("http://test.com/api", json=test_data, headers={"auth": "token"})
        assert result == {"created": True}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_put_request(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.put.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        test_data = {"id": 1, "value": "updated"}
        result = client.put("http://test.com/api/1", data=test_data)
        
        mock_client_instance.put.assert_called_with("http://test.com/api/1", json=test_data, headers=None)
        assert result == {"updated": True}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_delete_request(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"deleted": True}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.delete.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        result = client.delete("http://test.com/api/1", headers={"auth": "token"})
        
        mock_client_instance.delete.assert_called_with("http://test.com/api/1", headers={"auth": "token"})
        assert result == {"deleted": True}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_download_file(self, mock_httpx, temp_dir):
        import os
        
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        
        from unittest.mock import MagicMock
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_response
        context_manager.__exit__.return_value = False
        mock_client_instance.stream.return_value = context_manager
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        file_path = os.path.join(temp_dir, "downloaded_file.txt")
        
        client.download_file("http://test.com/file.txt", file_path, headers={"auth": "token"})
        
        mock_client_instance.stream.assert_called_with('GET', "http://test.com/file.txt", headers={"auth": "token"})
        
        assert os.path.exists(file_path)
        
        with open(file_path, 'rb') as f:
            content = f.read()
        assert content == b"chunk1chunk2chunk3"
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_http_error_handling(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        class MockHTTPError(Exception):
            def __init__(self, message, response):
                super().__init__(message)
                self.response = response
        
        http_error = MockHTTPError("404 Not Found", mock_response)
        mock_client_instance.get.side_effect = http_error
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        
        with pytest.raises(PepeunitClientError, match="HTTP error 404"):
            client.get("http://test.com/api")
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_request_error_handling(self, mock_httpx):
        mock_client_instance = Mock()
        
        class MockRequestError(Exception):
            pass
        
        MockRequestError.__name__ = 'httpx.RequestError'
        MockRequestError.__module__ = 'httpx'
        
        request_error = MockRequestError("Connection failed")
        mock_client_instance.get.side_effect = request_error
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        
        with pytest.raises(PepeunitClientError, match="Request error"):
            client.get("http://test.com/api")
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_general_error_handling(self, mock_httpx):
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = Exception("Unexpected error")
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        
        with pytest.raises(PepeunitClientError, match="Unexpected error during GET request"):
            client.get("http://test.com/api")


class TestDummyRESTClient:
    
    def test_dummy_client_methods_raise_errors(self):
        client = DummyRESTClient()
        
        with pytest.raises(PepeunitClientError, match="REST client is not available"):
            client.get("http://test.com")
        
        with pytest.raises(PepeunitClientError, match="REST client is not available"):
            client.post("http://test.com", {"data": "test"})
        
        with pytest.raises(PepeunitClientError, match="REST client is not available"):
            client.put("http://test.com", {"data": "test"})
        
        with pytest.raises(PepeunitClientError, match="REST client is not available"):
            client.delete("http://test.com")
        
        with pytest.raises(PepeunitClientError, match="REST client is not available"):
            client.download_file("http://test.com/file", "/tmp/file")


class TestRESTClientEdgeCases:
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_requests_with_none_data(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        result = client.post("http://test.com/api", data=None, headers=None)
        
        mock_client_instance.post.assert_called_with("http://test.com/api", json=None, headers=None)
        assert result == {"status": "ok"}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_requests_with_empty_headers(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        result = client.get("http://test.com/api", headers={})
        
        mock_client_instance.get.assert_called_with("http://test.com/api", headers={})
        assert result == {"status": "ok"}
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_download_file_io_error(self, mock_httpx, temp_dir):
        import os
        
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_bytes.return_value = [b"test data"]
        
        from unittest.mock import MagicMock
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_response
        context_manager.__exit__.return_value = False
        mock_client_instance.stream.return_value = context_manager
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        
        invalid_path = os.path.join(temp_dir, "nonexistent", "file.txt")
        
        with pytest.raises(PepeunitClientError, match="File writing error"):
            client.download_file("http://test.com/file", invalid_path)
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_client_destruction(self, mock_httpx):
        mock_client_instance = Mock()
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        
        client.__del__()
        
        mock_client_instance.close.assert_called_once()
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_multiple_requests_same_client(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        
        for i in range(5):
            result = client.get(f"http://test.com/api/{i}")
            assert result == {"status": "ok"}
        
        assert mock_client_instance.get.call_count == 5
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_custom_timeout(self, mock_httpx):
        mock_client_instance = Mock()
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient(timeout=120)
        
        assert client.timeout == 120
        mock_httpx.Client.assert_called_with(timeout=120)
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_response_without_json(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)
        mock_response.text = "Success"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        result = client.get("http://test.com/api")
        
        assert result == {"text": "Success", "status_code": 200}


class TestRESTClientParameters:
    
    @patch('pepeunit_client.rest_client.httpx')
    def test_all_http_methods_with_full_parameters(self, mock_httpx):
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"method": "tested"}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.put.return_value = mock_response
        mock_client_instance.delete.return_value = mock_response
        
        mock_httpx.Client.return_value = mock_client_instance
        
        client = RESTClient()
        test_headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        test_data = {"key": "value", "number": 42}
        
        result = client.get("http://test.com/get", headers=test_headers)
        assert result == {"method": "tested"}
        mock_client_instance.get.assert_called_with("http://test.com/get", headers=test_headers)
        
        result = client.post("http://test.com/post", data=test_data, headers=test_headers)
        assert result == {"method": "tested"}
        mock_client_instance.post.assert_called_with("http://test.com/post", json=test_data, headers=test_headers)
        
        result = client.put("http://test.com/put", data=test_data, headers=test_headers)
        assert result == {"method": "tested"}
        mock_client_instance.put.assert_called_with("http://test.com/put", json=test_data, headers=test_headers)
        
        result = client.delete("http://test.com/delete", headers=test_headers)
        assert result == {"method": "tested"}
        mock_client_instance.delete.assert_called_with("http://test.com/delete", headers=test_headers)
