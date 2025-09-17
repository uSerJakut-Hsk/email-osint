"""
Unit tests for the ProxyManager utility module
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, mock_open
import requests
import tempfile
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.proxy_manager import ProxyManager


class TestProxyManager:
    
    @pytest.fixture
    def temp_proxy_file(self):
        """Create a temporary proxy file for testing"""
        content = """# Test proxy file
http://proxy1.example.com:8080
192.168.1.100:3128
http://user:pass@proxy2.example.com:8080
socks5://proxy3.example.com:1080
invalid-proxy-format
# Comment line
203.0.113.1:8080
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def proxy_manager(self, temp_proxy_file):
        """Create a ProxyManager instance with test file"""
        return ProxyManager(proxy_file=temp_proxy_file, timeout=5)
    
    @pytest.fixture
    def proxy_manager_no_file(self):
        """Create a ProxyManager instance with non-existent file"""
        return ProxyManager(proxy_file="non_existent_file.txt", timeout=5)
    
    def test_proxy_manager_initialization(self, proxy_manager):
        """Test ProxyManager initialization"""
        assert proxy_manager.timeout == 5
        assert len(proxy_manager.proxies) > 0
        assert isinstance(proxy_manager.working_proxies, list)
        assert isinstance(proxy_manager.failed_proxies, set)
    
    def test_proxy_manager_no_file(self, proxy_manager_no_file):
        """Test ProxyManager with non-existent file"""
        assert len(proxy_manager_no_file.proxies) == 0
        assert len(proxy_manager_no_file.working_proxies) == 0
    
    def test_load_proxies(self, proxy_manager):
        """Test loading proxies from file"""
        # Should load valid proxies and skip invalid ones
        assert len(proxy_manager.proxies) == 4  # 4 valid proxies in test file
        
        valid_proxies = [
            "http://proxy1.example.com:8080",
            "192.168.1.100:3128", 
            "http://user:pass@proxy2.example.com:8080",
            "socks5://proxy3.example.com:1080"
        ]
        
        for proxy in valid_proxies:
            assert proxy in proxy_manager.proxies
            
        # Invalid proxy should not be loaded
        assert "invalid-proxy-format" not in proxy_manager.proxies
    
    @pytest.mark.parametrize("proxy,expected", [
        ("http://proxy.example.com:8080", True),
        ("https://proxy.example.com:8080", True), 
        ("socks5://proxy.example.com:1080", True),
        ("192.168.1.1:3128", True),
        ("proxy.com:80", True),
        ("invalid-proxy", False),
        ("http://", False),
        ("", False),
        ("proxy:abc", False),  # invalid port
        ("proxy:-1", False),   # invalid port
        ("proxy:99999", False) # invalid port
    ])
    def test_is_valid_proxy_format(self, proxy_manager, proxy, expected):
        """Test proxy format validation"""
        result = proxy_manager._is_valid_proxy_format(proxy)
        assert result == expected
    
    def test_get_proxy_with_working_proxies(self, proxy_manager):
        """Test getting proxy when working proxies available"""
        proxy_manager.working_proxies = ["http://working.proxy.com:8080"]
        
        proxy_dict = proxy_manager.get_proxy()
        
        assert proxy_dict is not None
        assert 'http' in proxy_dict
        assert 'https' in proxy_dict
        assert proxy_dict['http'] == "http://working.proxy.com:8080"
    
    def test_get_proxy_no_working_proxies(self, proxy_manager):
        """Test getting proxy when no working proxies available"""
        proxy_manager.working_proxies = []
        proxy_manager.failed_proxies = set()
        
        proxy_dict = proxy_manager.get_proxy()
        
        assert proxy_dict is not None
        # Should get a proxy from the main list
        assert 'http' in proxy_dict
        assert 'https' in proxy_dict
    
    def test_get_proxy_all_failed(self, proxy_manager):
        """Test getting proxy when all proxies have failed"""
        proxy_manager.working_proxies = []
        proxy_manager.failed_proxies = set(proxy_manager.proxies)
        
        proxy_dict = proxy_manager.get_proxy()
        
        # Should reset failed proxies and return one
        assert proxy_dict is not None
        assert len(proxy_manager.failed_proxies) == 0
    
    def test_get_proxy_no_proxies(self, proxy_manager_no_file):
        """Test getting proxy when no proxies available"""
        proxy_dict = proxy_manager_no_file.get_proxy()
        assert proxy_dict is None
    
    def test_format_proxy_dict_full_url(self, proxy_manager):
        """Test formatting proxy with full URL"""
        proxy_url = "http://proxy.example.com:8080"
        result = proxy_manager._format_proxy_dict(proxy_url)
        
        expected = {
            'http': proxy_url,
            'https': proxy_url
        }
        assert result == expected
    
    def test_format_proxy_dict_ip_port(self, proxy_manager):
        """Test formatting proxy with IP:PORT format"""
        proxy_url = "192.168.1.1:8080"
        result = proxy_manager._format_proxy_dict(proxy_url)
        
        expected = {
            'http': "http://192.168.1.1:8080",
            'https': "http://192.168.1.1:8080"
        }
        assert result == expected
    
    @patch('utils.proxy_manager.requests.get')
    def test_validate_proxy_success(self, mock_get, proxy_manager):
        """Test successful proxy validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        is_working, response_time = proxy_manager.validate_proxy("http://proxy.example.com:8080")
        
        assert is_working is True
        assert response_time > 0
        mock_get.assert_called()
    
    @patch('utils.proxy_manager.requests.get')
    def test_validate_proxy_failure(self, mock_get, proxy_manager):
        """Test failed proxy validation"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        is_working, response_time = proxy_manager.validate_proxy("http://proxy.example.com:8080")
        
        assert is_working is False
        assert response_time == 0.0
    
    @patch('utils.proxy_manager.requests.get')
    def test_validate_proxy_http_error(self, mock_get, proxy_manager):
        """Test proxy validation with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        is_working, response_time = proxy_manager.validate_proxy("http://proxy.example.com:8080")
        
        assert is_working is False
        assert response_time == 0.0
    
    def test_mark_proxy_failed(self, proxy_manager):
        """Test marking proxy as failed"""
        proxy_url = "http://proxy.example.com:8080"
        proxy_manager.working_proxies = [proxy_url]
        
        proxy_manager.mark_proxy_failed(proxy_url)
        
        assert proxy_url in proxy_manager.failed_proxies
        assert proxy_url not in proxy_manager.working_proxies
    
    def test_get_proxy_stats(self, proxy_manager):
        """Test getting proxy statistics"""
        proxy_manager.working_proxies = ["proxy1", "proxy2"]
        proxy_manager.failed_proxies = {"proxy3"}
        
        stats = proxy_manager.get_proxy_stats()
        
        assert stats["total_proxies"] == len(proxy_manager.proxies)
        assert stats["working_proxies"] == 2
        assert stats["failed_proxies"] == 1
        assert stats["available_proxies"] == len(proxy_manager.proxies) - 1
    
    def test_reset_failed_proxies(self, proxy_manager):
        """Test resetting failed proxies"""
        proxy_manager.failed_proxies = {"proxy1", "proxy2", "proxy3"}
        
        proxy_manager.reset_failed_proxies()
        
        assert len(proxy_manager.failed_proxies) == 0
    
    def test_add_proxy_valid(self, proxy_manager):
        """Test adding valid proxy"""
        new_proxy = "http://new.proxy.com:8080"
        original_count = len(proxy_manager.proxies)
        
        result = proxy_manager.add_proxy(new_proxy)
        
        assert result is True
        assert new_proxy in proxy_manager.proxies
        assert len(proxy_manager.proxies) == original_count + 1
    
    def test_add_proxy_invalid(self, proxy_manager):
        """Test adding invalid proxy"""
        invalid_proxy = "invalid-proxy-format"
        original_count = len(proxy_manager.proxies)
        
        result = proxy_manager.add_proxy(invalid_proxy)
        
        assert result is False
        assert invalid_proxy not in proxy_manager.proxies
        assert len(proxy_manager.proxies) == original_count
    
    def test_add_proxy_duplicate(self, proxy_manager):
        """Test adding duplicate proxy"""
        existing_proxy = proxy_manager.proxies[0] if proxy_manager.proxies else "http://test.com:8080"
        if not proxy_manager.proxies:
            proxy_manager.proxies.append(existing_proxy)
        
        original_count = len(proxy_manager.proxies)
        
        result = proxy_manager.add_proxy(existing_proxy)
        
        assert result is False
        assert len(proxy_manager.proxies) == original_count
    
    def test_remove_proxy_existing(self, proxy_manager):
        """Test removing existing proxy"""
        if not proxy_manager.proxies:
            proxy_manager.proxies.append("http://test.com:8080")
        
        proxy_to_remove = proxy_manager.proxies[0]
        original_count = len(proxy_manager.proxies)
        
        result = proxy_manager.remove_proxy(proxy_to_remove)
        
        assert result is True
        assert proxy_to_remove not in proxy_manager.proxies
        assert len(proxy_manager.proxies) == original_count - 1
    
    def test_remove_proxy_nonexistent(self, proxy_manager):
        """Test removing non-existent proxy"""
        nonexistent_proxy = "http://nonexistent.proxy.com:8080"
        original_count = len(proxy_manager.proxies)
        
        result = proxy_manager.remove_proxy(nonexistent_proxy)
        
        assert result is False
        assert len(proxy_manager.proxies) == original_count
    
    def test_save_proxies(self, proxy_manager):
        """Test saving proxies to file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_filename = f.name
        
        try:
            proxy_manager.working_proxies = [proxy_manager.proxies[0]] if proxy_manager.proxies else []
            proxy_manager.failed_proxies = {proxy_manager.proxies[1]} if len(proxy_manager.proxies) > 1 else set()
            
            proxy_manager.save_proxies(temp_filename)
            
            # Check file was created and has content
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert "# Proxy list for OSINT Email Tool" in content
                for proxy in proxy_manager.proxies:
                    assert proxy in content
                    
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    @patch('utils.proxy_manager.requests.get')
    def test_test_proxy_connectivity_success(self, mock_get, proxy_manager):
        """Test proxy connectivity test success"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"origin": "203.0.113.1"}
        mock_get.return_value = mock_response
        
        result = proxy_manager.test_proxy_connectivity("http://proxy.example.com:8080")
        
        assert result["is_working"] is True
        assert result["ip_address"] == "203.0.113.1"
        assert result["response_time"] > 0
        assert result["error"] is None
    
    @patch('utils.proxy_manager.requests.get')
    def test_test_proxy_connectivity_failure(self, mock_get, proxy_manager):
        """Test proxy connectivity test failure"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = proxy_manager.test_proxy_connectivity("http://proxy.example.com:8080")
        
        assert result["is_working"] is False
        assert result["error"] == "Connection failed"
    
    def test_get_best_proxies(self, proxy_manager):
        """Test getting best performing proxies"""
        proxy_manager.working_proxies = ["proxy1", "proxy2", "proxy3", "proxy4"]
        
        best_proxies = proxy_manager.get_best_proxies(count=2)
        
        assert len(best_proxies) == 2
        for proxy in best_proxies:
            assert proxy in proxy_manager.working_proxies
    
    def test_get_best_proxies_no_working(self, proxy_manager):
        """Test getting best proxies when none are working"""
        proxy_manager.working_proxies = []
        
        best_proxies = proxy_manager.get_best_proxies(count=5)
        
        assert len(best_proxies) == 0
    
    def test_is_proxy_available_true(self, proxy_manager):
        """Test proxy availability check when proxies available"""
        proxy_manager.failed_proxies = set()
        
        result = proxy_manager.is_proxy_available()
        
        assert result is (len(proxy_manager.proxies) > 0)
    
    def test_is_proxy_available_false(self, proxy_manager):
        """Test proxy availability check when no proxies available"""
        proxy_manager.failed_proxies = set(proxy_manager.proxies)
        
        result = proxy_manager.is_proxy_available()
        
        assert result is False


class TestProxyManagerIntegration:
    """Integration tests for ProxyManager"""
    
    def test_full_proxy_lifecycle(self):
        """Test complete proxy management lifecycle"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("192.168.1.1:8080\nhttp://proxy.example.com:8080\n")
            f.flush()
            temp_file = f.name
        
        try:
            # Initialize manager
            pm = ProxyManager(proxy_file=temp_file, timeout=1)
            
            # Test initial state
            assert len(pm.proxies) == 2
            assert pm.is_proxy_available()
            
            # Add new proxy
            pm.add_proxy("http://new.proxy.com:8080")
            assert len(pm.proxies) == 3
            
            # Mark one as failed
            pm.mark_proxy_failed(pm.proxies[0])
            assert len(pm.failed_proxies) == 1
            
            # Get stats
            stats = pm.get_proxy_stats()
            assert stats["total_proxies"] == 3
            assert stats["failed_proxies"] == 1
            
            # Reset failures
            pm.reset_failed_proxies()
            assert len(pm.failed_proxies) == 0
            
            # Remove proxy
            pm.remove_proxy(pm.proxies[0])
            assert len(pm.proxies) == 2
            
        finally:
            os.unlink(temp_file)
    
    def test_thread_safety(self, proxy_manager):
        """Test thread safety of proxy operations"""
        import threading
        import time
        
        results = []
        
        def get_proxy_worker():
            for _ in range(10):
                proxy = proxy_manager.get_proxy()
                results.append(proxy)
                time.sleep(0.01)
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_proxy_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 30  # 3 threads * 10 requests each
        # All results should be valid proxy dicts or None
        for result in results:
            if result is not None:
                assert 'http' in result
                assert 'https' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])