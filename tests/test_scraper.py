"""
Unit tests for the EmailScraper utility module
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.scraper import EmailScraper
from utils.proxy_manager import ProxyManager


class TestEmailScraper:
    
    @pytest.fixture
    def scraper(self):
        """Create a scraper instance for testing"""
        return EmailScraper()
    
    @pytest.fixture
    def scraper_with_proxy(self):
        """Create a scraper instance with proxy manager"""
        proxy_manager = Mock(spec=ProxyManager)
        proxy_manager.get_proxy.return_value = {'http': 'http://proxy:8080'}
        return EmailScraper(proxy_manager=proxy_manager)
    
    @pytest.fixture
    def sample_platform(self):
        """Sample platform configuration"""
        return {
            "name": "Test Platform",
            "url": "example.com",
            "login_required": False,
            "search_endpoint": "/search",
            "category": "test"
        }
    
    def test_scraper_initialization(self, scraper):
        """Test scraper initialization"""
        assert scraper is not None
        assert scraper.session is not None
        assert len(scraper.user_agents) > 0
        assert 'Mozilla/5.0' in scraper.user_agents[0]
    
    def test_scraper_with_proxy_initialization(self, scraper_with_proxy):
        """Test scraper initialization with proxy"""
        assert scraper_with_proxy.proxy_manager is not None
        scraper_with_proxy.proxy_manager.get_proxy.assert_called_once()
    
    def test_setup_session(self, scraper):
        """Test session setup"""
        assert 'User-Agent' in scraper.session.headers
        assert 'Accept' in scraper.session.headers
        assert scraper.session.headers['DNT'] == '1'
    
    @patch('utils.scraper.requests.Session.get')
    def test_search_google_platform_success(self, mock_get, scraper, sample_platform):
        """Test successful Google platform search"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><div class="result">test@example.com found</div></html>'
        mock_get.return_value = mock_response
        
        platform = {
            "name": "Google Search",
            "url": "google.com/search",
            "login_required": False,
            "search_endpoint": "",
            "category": "web_search"
        }
        
        result = scraper.search_email_on_platform("test@example.com", platform)
        
        assert result['status'] == 'found'
        assert result['platform'] == 'Google Search'
        assert 'search_url' in result['details']
        mock_get.assert_called_once()
    
    @patch('utils.scraper.requests.Session.get')
    def test_search_public_platform_success(self, mock_get, scraper, sample_platform):
        """Test successful public platform search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><p>User profile: test@example.com</p></html>'
        mock_get.return_value = mock_response
        
        result = scraper.search_email_on_platform("test@example.com", sample_platform)
        
        assert result['status'] == 'found'
        assert result['platform'] == 'Test Platform'
        assert len(result['matches']) > 0
        mock_get.assert_called_once()
    
    @patch('utils.scraper.requests.Session.get')
    def test_search_platform_not_found(self, mock_get, scraper, sample_platform):
        """Test platform search with no results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><p>No results found</p></html>'
        mock_get.return_value = mock_response
        
        result = scraper.search_email_on_platform("test@example.com", sample_platform)
        
        assert result['status'] == 'not_found'
        assert result['platform'] == 'Test Platform'
        mock_get.assert_called_once()
    
    @patch('utils.scraper.requests.Session.get')
    def test_search_platform_error(self, mock_get, scraper, sample_platform):
        """Test platform search with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = scraper.search_email_on_platform("test@example.com", sample_platform)
        
        assert result['status'] == 'error'
        assert 'HTTP 404' in result['error']
        mock_get.assert_called_once()
    
    @patch('utils.scraper.requests.Session.get')
    def test_search_platform_exception(self, mock_get, scraper, sample_platform):
        """Test platform search with exception"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = scraper.search_email_on_platform("test@example.com", sample_platform)
        
        assert result['status'] == 'error'
        assert 'Connection failed' in result['error']
        mock_get.assert_called_once()
    
    def test_has_search_results_with_results(self, scraper):
        """Test _has_search_results method with actual results"""
        html = '<html><div class="result">test@example.com profile</div></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = scraper._has_search_results(soup, "test@example.com")
        assert result is True
    
    def test_has_search_results_no_results(self, scraper):
        """Test _has_search_results method with no results"""
        html = '<html><p>No results found for your search</p></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = scraper._has_search_results(soup, "test@example.com")
        assert result is False
    
    def test_contains_email_true(self, scraper):
        """Test _contains_email method when email is present"""
        html = '<html><p>Contact us at test@example.com</p></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = scraper._contains_email(soup, "test@example.com")
        assert result is True
    
    def test_contains_email_false(self, scraper):
        """Test _contains_email method when email is not present"""
        html = '<html><p>No email addresses here</p></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = scraper._contains_email(soup, "test@example.com")
        assert result is False
    
    def test_extract_google_results(self, scraper):
        """Test extracting Google search results"""
        html = '''
        <html>
            <div class="g">
                <h3>User Profile</h3>
                <a href="https://example.com/profile">Example Profile</a>
                <span>Profile for test@example.com with additional info</span>
            </div>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        matches = scraper._extract_google_results(soup, "test@example.com")
        
        assert len(matches) > 0
        assert 'title' in matches[0]
        assert 'url' in matches[0]
        assert 'snippet' in matches[0]
    
    def test_extract_email_contexts(self, scraper):
        """Test extracting email contexts from page"""
        html = '''
        <html>
            <p>Please contact our support team at test@example.com for assistance</p>
            <div>User test@example.com has been registered successfully</div>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        contexts = scraper._extract_email_contexts(soup, "test@example.com")
        
        assert len(contexts) > 0
        assert 'context' in contexts[0]
        assert 'test@example.com' in contexts[0]['context']
    
    def test_rotate_user_agent(self, scraper):
        """Test user agent rotation"""
        original_ua = scraper.session.headers.get('User-Agent')
        scraper.rotate_user_agent()
        new_ua = scraper.session.headers.get('User-Agent')
        
        assert new_ua in scraper.user_agents
        # Might be the same if randomly selected the same one
        # assert new_ua != original_ua  # Not always true due to randomness
    
    def test_reset_session(self, scraper):
        """Test session reset"""
        original_session = scraper.session
        scraper.reset_session()
        
        assert scraper.session != original_session
        assert 'User-Agent' in scraper.session.headers
    
    @patch('utils.scraper.webdriver.Chrome')
    def test_search_with_selenium_success(self, mock_chrome, scraper, sample_platform):
        """Test Selenium search success"""
        mock_driver = Mock()
        mock_driver.page_source = 'Page content with test@example.com'
        mock_driver.current_url = 'https://example.com'
        mock_chrome.return_value = mock_driver
        
        result = scraper.search_with_selenium("test@example.com", sample_platform)
        
        assert result['status'] == 'found'
        assert result['details']['method'] == 'selenium'
        mock_driver.quit.assert_called_once()
    
    @patch('utils.scraper.webdriver.Chrome')
    def test_search_with_selenium_not_found(self, mock_chrome, scraper, sample_platform):
        """Test Selenium search not found"""
        mock_driver = Mock()
        mock_driver.page_source = 'Page content without email'
        mock_chrome.return_value = mock_driver
        
        result = scraper.search_with_selenium("test@example.com", sample_platform)
        
        assert result['status'] == 'not_found'
        mock_driver.quit.assert_called_once()
    
    @patch('utils.scraper.webdriver.Chrome')
    def test_search_with_selenium_exception(self, mock_chrome, scraper, sample_platform):
        """Test Selenium search with exception"""
        mock_chrome.side_effect = Exception("WebDriver error")
        
        result = scraper.search_with_selenium("test@example.com", sample_platform)
        
        assert result['status'] == 'error'
        assert 'WebDriver error' in result['error']
    
    def test_search_login_required_platform(self, scraper):
        """Test search on login-required platform"""
        platform = {
            "name": "Login Required Platform",
            "url": "loginrequired.com",
            "login_required": True,
            "search_endpoint": "/search",
            "category": "marketplace"
        }
        
        with patch('utils.scraper.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'<html><div class="result">Found via Google</div></html>'
            mock_get.return_value = mock_response
            
            result = scraper.search_email_on_platform("test@example.com", platform)
            
            assert result['platform'] == 'Login Required Platform'
            # Should use Google search for login-required platforms
            assert 'site:loginrequired.com' in mock_get.call_args[0][0]


class TestEmailScraperIntegration:
    """Integration tests for EmailScraper"""
    
    @pytest.fixture
    def scraper(self):
        return EmailScraper()
    
    def test_user_agent_list_validity(self, scraper):
        """Test that all user agents are valid"""
        for ua in scraper.user_agents:
            assert isinstance(ua, str)
            assert len(ua) > 0
            assert 'Mozilla' in ua
    
    def test_session_headers_complete(self, scraper):
        """Test that session has all required headers"""
        required_headers = [
            'User-Agent', 'Accept', 'Accept-Language',
            'Accept-Encoding', 'DNT', 'Connection'
        ]
        
        for header in required_headers:
            assert header in scraper.session.headers
    
    def test_platform_search_result_structure(self, scraper, sample_platform):
        """Test that search results have required structure"""
        with patch('utils.scraper.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'<html><p>test content</p></html>'
            mock_get.return_value = mock_response
            
            result = scraper.search_email_on_platform("test@example.com", sample_platform)
            
            # Check required fields
            required_fields = [
                'platform', 'url', 'email', 'timestamp',
                'status', 'details', 'matches'
            ]
            
            for field in required_fields:
                assert field in result
            
            assert isinstance(result['matches'], list)
            assert isinstance(result['details'], dict)
    
    @pytest.mark.parametrize("email,expected", [
        ("test@example.com", True),
        ("invalid-email", False),
        ("", False),
        (None, False)
    ])
    def test_email_validation_in_search(self, scraper, sample_platform, email, expected):
        """Test email validation within search process"""
        if not expected:
            # Invalid emails should not cause crashes
            result = scraper.search_email_on_platform(email, sample_platform)
            assert 'error' in result or result['status'] == 'error'
        else:
            with patch('utils.scraper.requests.Session.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'<html></html>'
                mock_get.return_value = mock_response
                
                result = scraper.search_email_on_platform(email, sample_platform)
                assert result['email'] == email


if __name__ == '__main__':
    pytest.main([__file__, '-v'])