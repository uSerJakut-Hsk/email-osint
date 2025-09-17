"""
Email Scraper Utility Module
Handles web scraping operations for email OSINT searches
"""

import requests
import time
import logging
from typing import Dict, Optional, List
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class EmailScraper:
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.setup_session()
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
    def setup_session(self):
        """Setup requests session with headers and proxy"""
        self.session.headers.update({
            'User-Agent': self.user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        if self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                self.session.proxies.update(proxy)
                
    def search_email_on_platform(self, email: str, platform: Dict) -> Dict:
        """
        Search for email on a specific platform
        
        Args:
            email: Email to search for
            platform: Platform configuration dictionary
            
        Returns:
            Dictionary with search results
        """
        platform_name = platform.get('name', 'Unknown')
        platform_url = platform.get('url', '')
        
        logging.info(f"Searching {platform_name} ({platform_url}) for {email}")
        
        result = {
            "platform": platform_name,
            "url": platform_url,
            "email": email,
            "timestamp": time.time(),
            "status": "not_found",
            "details": {},
            "matches": []
        }
        
        try:
            # Different search strategies based on platform type
            if 'google.com' in platform_url:
                return self._search_google_platform(email, platform, result)
            elif platform.get('login_required', False):
                return self._search_login_required_platform(email, platform, result)
            else:
                return self._search_public_platform(email, platform, result)
                
        except Exception as e:
            logging.error(f"Error searching {platform_name}: {str(e)}")
            result['status'] = 'error'
            result['error'] = str(e)
            return result
            
    def _search_google_platform(self, email: str, platform: Dict, result: Dict) -> Dict:
        """Search email using Google platforms"""
        platform_name = platform.get('name', '')
        platform_url = platform.get('url', '')
        
        try:
            if 'google.com/search' in platform_url:
                # Google Search
                search_query = f'"{email}"'
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                
            elif 'images.google.com' in platform_url:
                # Google Images
                search_query = f'"{email}"'
                search_url = f"https://images.google.com/search?q={quote_plus(search_query)}"
                
            elif 'news.google.com' in platform_url:
                # Google News
                search_query = f'"{email}"'
                search_url = f"https://news.google.com/search?q={quote_plus(search_query)}"
                
            elif 'scholar.google.com' in platform_url:
                # Google Scholar
                search_query = f'"{email}"'
                search_url = f"https://scholar.google.com/scholar?q={quote_plus(search_query)}"
                
            else:
                # Generic Google platform search
                search_query = f'site:{platform_url} "{email}"'
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for results
                if self._has_search_results(soup, email):
                    result['status'] = 'found'
                    result['details']['search_url'] = search_url
                    result['details']['results_found'] = True
                    result['matches'] = self._extract_google_results(soup, email)
                else:
                    result['status'] = 'not_found'
                    result['details']['search_url'] = search_url
                    result['details']['results_found'] = False
            else:
                result['status'] = 'error'
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            
        return result
        
    def _search_public_platform(self, email: str, platform: Dict, result: Dict) -> Dict:
        """Search email on public platforms that don't require login"""
        platform_url = platform.get('url', '')
        search_endpoint = platform.get('search_endpoint', '/search')
        
        try:
            # Construct search URL
            base_url = f"https://{platform_url}"
            
            if search_endpoint:
                search_url = urljoin(base_url, search_endpoint)
                # Add search query parameter
                if '?' in search_url:
                    search_url += f"&q={quote_plus(email)}"
                else:
                    search_url += f"?q={quote_plus(email)}"
            else:
                # Use Google to search the site
                search_query = f'site:{platform_url} "{email}"'
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for email mentions in the page
                if self._contains_email(soup, email):
                    result['status'] = 'found'
                    result['details']['search_url'] = search_url
                    result['matches'] = self._extract_email_contexts(soup, email)
                else:
                    result['status'] = 'not_found'
                    result['details']['search_url'] = search_url
            else:
                result['status'] = 'error'
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            
        return result
        
    def _search_login_required_platform(self, email: str, platform: Dict, result: Dict) -> Dict:
        """Search email on platforms that require login (limited functionality)"""
        platform_url = platform.get('url', '')
        
        try:
            # For login-required platforms, we can only check public pages
            # or use Google to search the domain
            search_query = f'site:{platform_url} "{email}"'
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                if self._has_search_results(soup, email):
                    result['status'] = 'potential_match'
                    result['details']['search_url'] = search_url
                    result['details']['note'] = 'Found via Google search - login required for verification'
                    result['matches'] = self._extract_google_results(soup, email)
                else:
                    result['status'] = 'not_found'
                    result['details']['search_url'] = search_url
                    result['details']['note'] = 'No public results found via Google'
            else:
                result['status'] = 'error'
                result['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            
        return result
        
    def _has_search_results(self, soup: BeautifulSoup, email: str) -> bool:
        """Check if Google search results contain the email"""
        # Check for "No results found" or similar messages
        no_results_indicators = [
            "did not match any documents",
            "No results found",
            "Try different keywords",
            "Make sure all words are spelled correctly"
        ]
        
        page_text = soup.get_text().lower()
        for indicator in no_results_indicators:
            if indicator.lower() in page_text:
                return False
        
        # Look for actual search results
        search_results = soup.find_all(['div', 'li'], class_=re.compile(r'(result|search)'))
        
        for result_div in search_results:
            if email.lower() in result_div.get_text().lower():
                return True
                
        return len(search_results) > 0
        
    def _contains_email(self, soup: BeautifulSoup, email: str) -> bool:
        """Check if page content contains the email address"""
        page_text = soup.get_text().lower()
        return email.lower() in page_text
        
    def _extract_google_results(self, soup: BeautifulSoup, email: str) -> List[Dict]:
        """Extract search result snippets that mention the email"""
        matches = []
        
        # Find Google search result containers
        result_containers = soup.find_all(['div', 'li'], class_=re.compile(r'(g|result)'))
        
        for container in result_containers:
            text = container.get_text()
            if email.lower() in text.lower():
                # Try to extract title and URL
                title_elem = container.find(['h3', 'a'])
                title = title_elem.get_text() if title_elem else 'No title'
                
                url_elem = container.find('a', href=True)
                url = url_elem['href'] if url_elem else 'No URL'
                
                # Extract snippet
                snippet = text[:200] + '...' if len(text) > 200 else text
                
                matches.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'email_mentioned': email
                })
                
        return matches[:5]  # Return top 5 matches
        
    def _extract_email_contexts(self, soup: BeautifulSoup, email: str) -> List[Dict]:
        """Extract contexts where email appears on the page"""
        matches = []
        
        # Find all text nodes that contain the email
        for element in soup.find_all(text=re.compile(email, re.IGNORECASE)):
            parent = element.parent
            if parent:
                context = element.strip()
                
                # Get surrounding context
                full_text = parent.get_text()
                email_pos = full_text.lower().find(email.lower())
                
                if email_pos != -1:
                    start = max(0, email_pos - 50)
                    end = min(len(full_text), email_pos + len(email) + 50)
                    context = full_text[start:end]
                    
                    matches.append({
                        'context': context,
                        'element': parent.name,
                        'email_mentioned': email
                    })
                    
        return matches[:3]  # Return top 3 contexts
        
    def search_with_selenium(self, email: str, platform: Dict) -> Dict:
        """Use Selenium for JavaScript-heavy platforms (backup method)"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        driver = None
        result = {
            "platform": platform.get('name', 'Unknown'),
            "url": platform.get('url', ''),
            "email": email,
            "timestamp": time.time(),
            "status": "not_found",
            "details": {},
            "matches": []
        }
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            
            # Navigate to platform
            platform_url = f"https://{platform.get('url', '')}"
            driver.get(platform_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Search for email in page source
            if email.lower() in driver.page_source.lower():
                result['status'] = 'found'
                result['details']['method'] = 'selenium'
                result['details']['page_url'] = driver.current_url
            else:
                result['status'] = 'not_found'
                result['details']['method'] = 'selenium'
                
        except TimeoutException:
            result['status'] = 'error'
            result['error'] = 'Page load timeout'
        except WebDriverException as e:
            result['status'] = 'error'
            result['error'] = f"WebDriver error: {str(e)}"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        finally:
            if driver:
                driver.quit()
                
        return result
        
    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        import random
        new_ua = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': new_ua})
        
    def reset_session(self):
        """Reset session and get new proxy if available"""
        self.session.close()
        self.session = requests.Session()
        self.setup_session()
        self.rotate_user_agent()