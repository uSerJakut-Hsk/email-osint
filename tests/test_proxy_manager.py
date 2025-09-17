#!/usr/bin/env python3
"""
Unit Tests for Proxy Manager
Author: Security Researcher
Date: September 2025
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.proxy_manager import ProxyManager


class TestProxyManager(unittest.TestCase):
    """Test cases for ProxyManager class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create temporary proxy file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("""# Test proxy file
http://proxy1.example.com:8080
http://user:pass@proxy2.example.com:3128
192.168.1.100:8080
proxy3.example.com:3128
# This is a comment
invalid-proxy-line

https://secure-proxy.example.com:8080
""")
        self.temp_file.close()
        
        self.proxy_manager = ProxyManager(self.temp_file.name)
        
    def tearDown(self):
        """Clean up after each test"""
        # Remove temporary file
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
            
    def test_proxy_loading(self):
        """Test loading proxies from file"""
        # Should have loaded several proxies
        self.assertGreater(len(self.proxy_manager.proxies), 0)
        
        # Check that comments and invalid lines were ignored
        proxy_originals = [p['original'] for p in self.proxy_manager.proxies]
        self.assertNotIn('# This is a comment', proxy_originals)
        self.assertNotIn('invalid-proxy-line', proxy_originals)
        
    def test_proxy_parsing(self):
        """Test different proxy format parsing"""
        # Test full URL format
        proxy1 = self.proxy_manager._parse_proxy_line('http://proxy.com:8080')
        self.assertIsNotNone(proxy1)
        self.assertEqual(proxy1['http'], 'http://proxy.com:8080')
        
        # Test IP:PORT format
        proxy2 = self.proxy_manager._parse_proxy_line('192.168.1.1:3128')
        self.assertIsNotNone(proxy2)
        self.assertIn('192.168.1.1:3128', proxy2['http'])
        
        # Test invalid format
        proxy3 = self.proxy_manager._parse_proxy_line('invalid')
        self.assertIsNone(proxy3)
        
    def test_proxy_rotation(self):
        """Test proxy rotation functionality"""
        # Get multiple proxies
        proxies = []
        for _ in range(len(self.proxy_manager.proxies) + 2):
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                proxies.append(proxy)
                
        # Should rotate through available proxies
        if len(self.proxy_manager.proxies) > 1:
            proxy_urls = [p['http'] for p in proxies]
            unique_proxies = set(proxy_urls)
            self.assertGreater(len(unique_proxies), 1)
            
    def test_proxy_failure_handling(self):
        """Test proxy failure marking and removal"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        proxy = self.proxy_manager.proxies[0].copy()
        initial_failures = proxy.get('failures', 0)
        
        # Mark proxy as failed
        self.proxy_manager.mark_proxy_failed(proxy)
        
        # Failure count should increase
        self.assertEqual(proxy['failures'], initial_failures + 1)
        
        # Mark as failed multiple times to trigger removal
        for _ in range(self.proxy_manager.max_retries):
            self.proxy_manager.mark_proxy_failed(proxy)
            
        # Proxy should be in failed list
        self.assertIn(proxy, self.proxy_manager.failed_proxies)
        
    def test_proxy_success_handling(self):
        """Test proxy success marking"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        proxy = self.proxy_manager.proxies[0].copy()
        initial_successes = proxy.get('successes', 0)
        
        # Mark proxy as successful
        self.proxy_manager.mark_proxy_success(proxy, response_time=1.5)
        
        # Success count should increase
        self.assertEqual(proxy['successes'], initial_successes + 1)
        
        # Response time should be recorded
        self.assertEqual(proxy['avg_response_time'], 1.5)
        
        # Should be added to working proxies
        self.assertIn(proxy, self.proxy_manager.working_proxies)
        
    @patch('requests.get')
    def test_proxy_validation(self, mock_get):
        """Test single proxy validation"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        proxy = self.proxy_manager.proxies[0]
        result = self.proxy_manager.validate_proxy(proxy)
        
        # Should return True for successful validation
        self.assertTrue(result)
        
        # Proxy should be marked as working
        self.assertIn(proxy, self.proxy_manager.working_proxies)
        
    @patch('requests.get')
    def test_proxy_validation_failure(self, mock_get):
        """Test proxy validation failure"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        # Mock failed response
        mock_get.side_effect = Exception("Connection failed")
        
        proxy = self.proxy_manager.proxies[0]
        result = self.proxy_manager.validate_proxy(proxy)
        
        # Should return False for failed validation
        self.assertFalse(result)
        
        # Proxy should be marked as failed
        self.assertGreater(proxy['failures'], 0)
        
    def test_proxy_stats(self):
        """Test proxy statistics calculation"""
        stats = self.proxy_manager.get_proxy_stats()
        
        # Should have required fields
        required_fields = ['total_proxies', 'working_proxies', 'failed_proxies', 'success_rate']
        for field in required_fields:
            self.assertIn(field, stats)
            
        # Success rate should be percentage
        self.assertGreaterEqual(stats['success_rate'], 0)
        self.assertLessEqual(stats['success_rate'], 100)
        
    def test_dynamic_proxy_management(self):
        """Test adding and removing proxies dynamically"""
        initial_count = len(self.proxy_manager.proxies)
        
        # Add new proxy
        new_proxy = 'http://new-proxy.com:8080'
        result = self.proxy_manager.add_proxy(new_proxy)
        
        self.assertTrue(result)
        self.assertEqual(len(self.proxy_manager.proxies), initial_count + 1)
        
        # Remove proxy
        result = self.proxy_manager.remove_proxy(new_proxy)
        
        self.assertTrue(result)
        self.assertEqual(len(self.proxy_manager.proxies), initial_count)
        
    def test_best_proxy_selection(self):
        """Test best proxy selection algorithm"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        # Create some working proxies with different performance
        proxy1 = self.proxy_manager.proxies[0].copy()
        proxy2 = self.proxy_manager.proxies[0].copy()  # Copy first proxy for testing
        proxy2['original'] = 'test-proxy-2'
        
        # Set different performance metrics
        self.proxy_manager.mark_proxy_success(proxy1, response_time=2.0)
        self.proxy_manager.mark_proxy_success(proxy2, response_time=1.0)
        
        best_proxy = self.proxy_manager.get_best_proxy()
        
        # Should return the faster proxy
        if best_proxy:
            self.assertLessEqual(best_proxy['avg_response_time'], proxy1['avg_response_time'])
            
    def test_proxy_string_format(self):
        """Test proxy string format for Selenium"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        proxy_string = self.proxy_manager.get_proxy_string()
        
        if proxy_string:
            # Should not contain 'http://' prefix for Selenium
            self.assertNotIn('http://', proxy_string)
            
            # Should contain host:port format
            self.assertIn(':', proxy_string)
            
    def test_cache_cleanup(self):
        """Test cleanup of old performance data"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        proxy = self.proxy_manager.proxies[0]
        
        # Set old last_used time
        proxy['last_used'] = datetime.now() - timedelta(days=10)
        proxy['failures'] = 5
        proxy['successes'] = 3
        
        # Cleanup old data
        self.proxy_manager.cleanup_old_performance_data(days=7)
        
        # Performance counters should be reset
        self.assertEqual(proxy['failures'], 0)
        self.assertEqual(proxy['successes'], 0)
        
    def test_working_proxy_save(self):
        """Test saving working proxies to file"""
        # Add some working proxies
        if self.proxy_manager.proxies:
            proxy = self.proxy_manager.proxies[0]
            self.proxy_manager.mark_proxy_success(proxy, response_time=1.5)
            
        # Save to temporary file
        temp_output = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_output.close()
        
        try:
            result = self.proxy_manager.save_working_proxies(temp_output.name)
            self.assertTrue(result)
            
            # File should exist and have content
            self.assertTrue(os.path.exists(temp_output.name))
            
            with open(temp_output.name, 'r') as f:
                content = f.read()
                self.assertIn('Working proxies', content)
                
        finally:
            try:
                os.unlink(temp_output.name)
            except:
                pass
                
    def test_proxy_connectivity_test(self):
        """Test proxy connectivity testing"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        proxy = self.proxy_manager.proxies[0]
        
        with patch('requests.get') as mock_get:
            # Mock successful connectivity test
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.proxy_manager.test_proxy_connectivity(proxy)
            
            # Should have required fields
            required_fields = ['success', 'response_time', 'status_code']
            for field in required_fields:
                self.assertIn(field, result)
                
    def test_environment_variables(self):
        """Test proxy authentication from environment variables"""
        with patch.dict(os.environ, {'PROXY_AUTH': 'testuser:testpass'}):
            pm = ProxyManager(self.temp_file.name)
            
            # Should have loaded auth from environment
            self.assertEqual(pm.proxy_auth, 'testuser:testpass')
            
    def test_nonexistent_proxy_file(self):
        """Test handling of nonexistent proxy file"""
        nonexistent_file = '/path/that/does/not/exist/proxies.txt'
        pm = ProxyManager(nonexistent_file)
        
        # Should handle gracefully
        self.assertEqual(len(pm.proxies), 0)
        self.assertFalse(pm.has_proxies())
        
    def test_concurrent_proxy_access(self):
        """Test thread-safe proxy access"""
        import threading
        import time
        
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        results = []
        
        def get_proxies():
            for _ in range(10):
                proxy = self.proxy_manager.get_proxy()
                if proxy:
                    results.append(proxy['original'])
                time.sleep(0.01)
                
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_proxies)
            threads.append(thread)
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Should have gotten proxies without errors
        self.assertGreater(len(results), 0)
        
    def test_proxy_reset_functionality(self):
        """Test resetting failed proxies"""
        if not self.proxy_manager.proxies:
            self.skipTest("No proxies loaded for testing")
            
        proxy = self.proxy_manager.proxies[0]
        
        # Mark proxy as failed multiple times
        for _ in range(self.proxy_manager.max_retries + 1):
            self.proxy_manager.mark_proxy_failed(proxy)
            
        # Should be in failed list
        self.assertIn(proxy, self.proxy_manager.failed_proxies)
        
        # Reset failed proxies
        self.proxy_manager.reset_failed_proxies()
        
        # Should no longer be in failed list
        self.assertNotIn(proxy, self.proxy_manager.failed_proxies)
        
        # Counters should be reset
        self.assertEqual(proxy['failures'], 0)
        self.assertEqual(proxy['successes'], 0)


class TestProxyManagerCreation(unittest.TestCase):
    """Test proxy manager creation and default file handling"""
    
    def test_default_proxy_file_creation(self):
        """Test creation of default proxy file"""
        # Use non-existent file path
        test_path = 'test_proxies_temp.txt'
        
        # Ensure file doesn't exist
        if os.path.exists(test_path):
            os.remove(test_path)
            
        try:
            pm = ProxyManager(test_path)
            
            # Default file should be created
            self.assertTrue(os.path.exists(test_path))
            
            # File should have example content
            with open(test_path, 'r') as f:
                content = f.read()
                self.assertIn('Proxy List for Email OSINT Tool', content)
                self.assertIn('Examples:', content)
                
        finally:
            # Clean up
            if os.path.exists(test_path):
                os.remove(test_path)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)