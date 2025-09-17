#!/usr/bin/env python3
"""
Unit Tests for Email Scraper
Author: Security Researcher
Date: September 2025
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.scraper import EmailScraper
from utils.proxy_manager import ProxyManager


class TestEmailScraper(unittest.TestCase):
    """Test cases for EmailScraper class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create mock proxy manager
        self.mock_proxy_manager = Mock(spec=ProxyManager)
        self.mock_proxy_manager.has_proxies.return_value = False
        
        self.scraper = EmailScraper(self.mock_proxy_manager)
        
    def tearDown(self):
        """Clean up after each test"""
        if self.scraper:
            self.scraper.close()
            
    def test_scraper_initialization(self):
        """Test scraper initialization"""
        self.assertIsNotNone(self.scraper)
        self.assertEqual(self.scraper.proxy_manager, self.mock_proxy_manager)
        self.assertIsNotNone(self.scraper.session)
        self.assertIsNotNone(self.scraper.user_agents)
        
    def test_session_setup(self):
        """Test session setup with headers"""
        self.scraper.setup_session()
        
        # Check that session has proper headers
        self.assertIn('User-Agent', self.scraper.session.headers)
        self.assertIn('Accept', self.scraper.session.headers)
        self.assertIn('Connection', self.scraper.session.headers)
        
    @patch('utils.scraper.webdriver.Chrome')
    @patch('utils.scraper.ChromeDriverManager')
    def test_selenium_driver_initialization(self, mock_driver_manager, mock_chrome):
        """Test Selenium WebDriver initialization"""
        mock_service = Mock()
        mock_driver_manager.return_value.install.return_value = '/path/to/chromedriver'
        mock_driver_instance = Mock()
        mock_chrome.return_value = mock_driver_instance
        
        with patch('utils.scraper.Service') as mock_service_class:
            mock_service_class.return_value = mock_service
            
            driver = self.scraper.get_selenium_driver()
            
            # Verify Chrome was called with options
            mock_chrome.assert_called_once()
            call_args = mock_chrome.call_args
            self.assertEqual(call_args[1]['service'], mock_service)
            
            # Verify execute_script was called to remove webdriver property
            mock_driver_instance.execute_script.assert_called_once()
            
    def test_platform_search_structure(self):
        """Test that platform search returns proper structure"""
        test_platform = {
            'name': 'Test Platform',
            'url': 'example.com',
            'login_required': False,
            'search_endpoint': '/search',
            'category': 'test'
        }
        
        with patch.object(self.scraper, '_google_site_search') as mock_google_search:
            mock_google_search.return_value = {
                'platform': 'Test Platform',
                'url': 'example.com',
                'status': 'not_found',
                'matches': [],
                'search_method': 'google_site_search',
                'search_time': '2025-09-16T12:00:00'
            }
            
            result = self.scraper.search_email_on_platform('test@example.com', test_platform)
            
            # Check required fields are present
            required_fields = ['platform', 'url', 'status', 'search_time']
            for field in required_fields:
                self.assertIn(field, result)
                
            # Check status is valid
            valid_statuses = ['found', 'not_found', 'potential_match', 'error']
            self.assertIn(result['status'], valid_statuses)
            
    @patch('requests.get')
    def test_google_site_search(self, mock_get):
        """Test Google site search functionality"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = '''
        <html>
            <body>
                <div class="g">
                    <h3>Test Result</h3>
                    <a href="https://example.com/profile">Profile Link</a>
                    <span class="st">Found test@example.com in profile</span>
                </div>
            </body>
        </html>
        '''
        mock_get.return_value = mock_response
        
        test_platform = {
            'name': 'Test Platform',
            'url': 'example.com'
        }
        
        result = self.scraper._google_site_search('test@example.com', test_platform)
        
        self.assertEqual(result['platform'], 'Test Platform')
        self.assertEqual(result['search_method'], 'google_site_search')
        self.assertIn('matches', result)
        
    @patch('requests.get')
    def test_direct_platform_search(self, mock_get):
        """Test direct platform search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'User profile for test@example.com found here'
        mock_get.return_value = mock_response
        
        test_platform = {
            'name': 'Test Platform',
            'url': 'example.com',
            'search_endpoint': '/search',
            'login_required': False
        }
        
        result = self.scraper._direct_platform_search('test@example.com', test_platform)
        
        self.assertEqual(result['platform'], 'Test Platform')
        self.assertEqual(result['search_method'], 'direct_platform_search')
        self.assertIn('status', result)
        
    def test_parse_platform_results(self):
        """Test parsing of platform search results"""
        html_content = '''
        <html>
            <body>
                <div>User: test@example.com</div>
                <p>Contact test@example.com for more info</p>
                <span>Another mention of test@example.com</span>
            </body>
        </html>
        '''
        
        test_platform = {
            'name': 'Test Platform',
            'url': 'example.com'
        }
        
        matches = self.scraper._parse_platform_results(html_content, 'test@example.com', test_platform)
        
        # Should find matches containing the email
        self.assertGreater(len(matches), 0)
        
        # Each match should have required fields
        for match in matches:
            self.assertIn('content', match)
            self.assertIn('confidence', match)
            self.assertIn('source', match)
            
    def test_advanced_google_search(self):
        """Test advanced Google search with variations"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = '''
            <html>
                <body>
                    <div class="g">
                        <h3>User Profile</h3>
                        <a href="https://example.com/user/john">John's Profile</a>
                        <div class="s">Username: john matches test query</div>
                    </div>
                </body>
            </html>
            '''
            mock_get.return_value = mock_response
            
            test_platform = {
                'name': 'Test Platform',
                'url': 'example.com'
            }
            
            result = self.scraper._advanced_google_search('john@example.com', test_platform)
            
            self.assertEqual(result['search_method'], 'advanced_google_search')
            self.assertIn('matches', result)
            
    def test_error_handling(self):
        """Test error handling in scraper methods"""
        test_platform = {
            'name': 'Test Platform',
            'url': 'nonexistent-domain-12345.com',
            'login_required': False,
            'search_endpoint': '/search'
        }
        
        # This should handle the error gracefully
        result = self.scraper.search_email_on_platform('test@example.com', test_platform)
        
        # Should return error status instead of raising exception
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        
    def test_user_agent_rotation(self):
        """Test that user agents are being rotated"""
        initial_ua = self.scraper.session.headers.get('User-Agent')
        
        # Setup session multiple times
        user_agents = []
        for _ in range(10):
            self.scraper.setup_session()
            user_agents.append(self.scraper.session.headers.get('User-Agent'))
            
        # Should have some variation in user agents
        unique_uas = set(user_agents)
        self.assertGreater(len(unique_uas), 1)
        
    def test_proxy_integration(self):
        """Test proxy integration"""
        # Create mock proxy manager with proxies
        mock_proxy_manager = Mock(spec=ProxyManager)
        mock_proxy_manager.has_proxies.return_value = True
        mock_proxy_manager.get_proxy.return_value = {
            'http': 'http://proxy.example.com:8080',
            'https': 'http://proxy.example.com:8080'
        }
        
        scraper_with_proxy = EmailScraper(mock_proxy_manager)
        scraper_with_proxy.setup_session()
        
        # Session should have proxy configured
        self.assertIsNotNone(scraper_with_proxy.session.proxies)
        
        scraper_with_proxy.close()
        
    def test_cleanup_resources(self):
        """Test proper cleanup of resources"""
        # Create scraper with mock driver
        mock_driver = Mock()
        self.scraper.driver = mock_driver
        
        # Close scraper
        self.scraper.close()
        
        # Driver quit should be called
        mock_driver.quit.assert_called_once()
        
    def test_selenium_driver_failure_handling(self):
        """Test handling of Selenium driver failures"""
        with patch('utils.scraper.ChromeDriverManager') as mock_manager:
            # Simulate driver installation failure
            mock_manager.return_value.install.side_effect = Exception("Driver install failed")
            
            driver = self.scraper.get_selenium_driver()
            
            # Should return None on failure
            self.assertIsNone(driver)
            
    def test_empty_search_results(self):
        """Test handling of empty search results"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = '<html><body>No results found</body></html>'
            mock_get.return_value = mock_response
            
            test_platform = {
                'name': 'Empty Platform',
                'url': 'example.com'
            }
            
            result = self.scraper._google_site_search('test@example.com', test_platform)
            
            self.assertEqual(result['status'], 'not_found')
            self.assertEqual(len(result['matches']), 0)
            
    def test_multiple_search_methods(self):
        """Test that multiple search methods are tried"""
        test_platform = {
            'name': 'Test Platform',
            'url': 'example.com',
            'login_required': False,
            'search_endpoint': '/search'
        }
        
        with patch.object(self.scraper, '_google_site_search') as mock_google, \
             patch.object(self.scraper, '_direct_platform_search') as mock_direct, \
             patch.object(self.scraper, '_advanced_google_search') as mock_advanced:
            
            # Make first two methods return no results
            mock_google.return_value = {'matches': [], 'status': 'not_found'}
            mock_direct.return_value = {'matches': [], 'status': 'not_found'}
            mock_advanced.return_value = {'matches': [{'title': 'Found'}], 'status': 'found'}
            
            result = self.scraper.search_email_on_platform('test@example.com', test_platform)
            
            # All three methods should be called
            mock_google.assert_called_once()
            mock_direct.assert_called_once()
            mock_advanced.assert_called_once()
            
    def test_login_required_platforms(self):
        """Test handling of login-required platforms"""
        test_platform = {
            'name': 'Private Platform',
            'url': 'private.com',
            'login_required': True,
            'search_endpoint': '/search'
        }
        
        with patch.object(self.scraper, '_google_site_search') as mock_google, \
             patch.object(self.scraper, '_direct_platform_search') as mock_direct:
            
            mock_google.return_value = {'matches': [], 'status': 'not_found'}
            
            result = self.scraper.search_email_on_platform('test@example.com', test_platform)
            
            # Google search should be called
            mock_google.assert_called_once()
            
            # Direct platform search should NOT be called for login-required platforms
            mock_direct.assert_not_called()


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for scraper functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.scraper = EmailScraper()
        
    def tearDown(self):
        """Clean up after integration tests"""
        if self.scraper:
            self.scraper.close()
            
    @unittest.skip("Integration test - requires internet connection")
    def test_real_google_search(self):
        """Integration test with real Google search (skipped by default)"""
        test_platform = {
            'name': 'GitHub',
            'url': 'github.com'
        }
        
        # Use a well-known email that should have results
        result = self.scraper._google_site_search('noreply@github.com', test_platform)
        
        self.assertIn('status', result)
        self.assertIn('matches', result)
        
    @unittest.skip("Integration test - requires internet connection")  
    def test_real_platform_search(self):
        """Integration test with real platform search (skipped by default)"""
        test_platform = {
            'name': 'Example',
            'url': 'example.com',
            'login_required': False,
            'search_endpoint': '/'
        }
        
        result = self.scraper.search_email_on_platform('test@example.com', test_platform)
        
        # Should complete without errors
        self.assertIn('status', result)
        self.assertIn('platform', result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)