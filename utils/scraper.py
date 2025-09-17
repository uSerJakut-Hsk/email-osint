#!/usr/bin/env python3
"""
Web Scraper Utility for Email OSINT Tool
Author: Security Researcher
Date: September 2025
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import random
import logging
from typing import Dict, List, Optional, Any
import re
from urllib.parse import urljoin, urlparse, quote_plus
import os
import json
from datetime import datetime


class EmailScraper:
    """Advanced email scraper with multiple search strategies"""
    
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.driver = None
        self.setup_session()
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebPool/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
        ]
        
    def setup_session(self):
        """Setup requests session with headers and proxy"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(headers)
        
        # Set proxy if available
        if self.proxy_manager and self.proxy_manager.has_proxies():
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                self.session.proxies.update(proxy)
                
    def get_selenium_driver(self, headless=True):
        """Initialize Selenium WebDriver with proper options"""
        if self.driver:
            return self.driver
            
        try:
            chrome_options = Options()
            
            # Basic options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if headless:
                chrome_options.add_argument('--headless')
                
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # User agent
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            
            # Proxy setup
            if self.proxy_manager and self.proxy_manager.has_proxies():
                proxy = self.proxy_manager.get_proxy_string()
                if proxy:
                    chrome_options.add_argument(f'--proxy-server={proxy}')
                    
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return self.driver
            
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver: {e}")
            return None
            
    def search_email_on_platform(self, email: str, platform: Dict) -> Dict:
        """Search for email on a specific platform"""
        platform_name = platform.get('name', 'Unknown')
        platform_url = platform.get('url', '')
        
        logging.info(f"Searching {platform_name} for {email}")
        
        try:
            # Try different search methods
            result = None
            
            # Method 1: Google site search
            result = self._google_site_search(email, platform)
            if result and result.get('matches'):
                return result
                
            # Method 2: Platform direct search (if not login required)
            if not platform.get('login_required', False):
                result = self._direct_platform_search(email, platform)
                if result and result.get('matches'):
                    return result
                    
            # Method 3: Advanced Google search with variations
            result = self._advanced_google_search(email, platform)
            if result and result.get('matches'):
                return result
                
            # No results found
            return {
                'platform': platform_name,
                'url': platform_url,
                'status': 'not_found',
                'matches': [],
                'search_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error searching {platform_name}: {e}")
            return {
                'platform': platform_name,
                'url': platform_url,
                'status': 'error',
                'error': str(e),
                'search_time': datetime.now().isoformat()
            }
            
    def _google_site_search(self, email: str, platform: Dict) -> Dict:
        """Search using Google site: operator"""
        platform_name = platform.get('name', 'Unknown')
        platform_url = platform.get('url', '')
        
        try:
            # Build Google search query
            query = f'site:{platform_url} "{email}"'
            google_url = f"https://www.google.com/search?q={quote_plus(query)}"
            
            # Add random delay
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(google_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = []
            
            # Parse Google search results
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:5]:  # Limit to first 5 results
                try:
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    snippet_elem = result.find('span', class_='st') or result.find('div', class_='s')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href', '')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        # Check if email is mentioned in results
                        if email.lower() in (title.lower() + ' ' + snippet.lower()):
                            matches.append({
                                'title': title,
                                'url': link,
                                'snippet': snippet,
                                'confidence': 0.8,
                                'source': 'google_site_search'
                            })
                            
                except Exception as e:
                    logging.debug(f"Error parsing search result: {e}")
                    continue
                    
            status = 'found' if matches else 'not_found'
            
            return {
                'platform': platform_name,
                'url': platform_url,
                'status': status,
                'matches': matches,
                'search_method': 'google_site_search',
                'search_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Google site search failed for {platform_name}: {e}")
            raise
            
    def _direct_platform_search(self, email: str, platform: Dict) -> Dict:
        """Direct search on platform (if no login required)"""
        platform_name = platform.get('name', 'Unknown')
        platform_url = platform.get('url', '')
        search_endpoint = platform.get('search_endpoint', '/search')
        
        try:
            # Build search URL
            base_url = f"https://{platform_url}"
            search_url = urljoin(base_url, search_endpoint)
            
            # Try different search parameters
            search_params = [
                {'q': email},
                {'query': email},
                {'search': email},
                {'keyword': email},
                {'term': email}
            ]
            
            matches = []
            
            for params in search_params:
                try:
                    time.sleep(random.uniform(1, 2))
                    
                    response = self.session.get(search_url, params=params, timeout=15)
                    if response.status_code == 200:
                        matches.extend(self._parse_platform_results(response.text, email, platform))
                        
                    if matches:  # Stop if we found results
                        break
                        
                except Exception as e:
                    logging.debug(f"Search parameter {params} failed: {e}")
                    continue
                    
            status = 'found' if matches else 'not_found'
            
            return {
                'platform': platform_name,
                'url': platform_url,
                'status': status,
                'matches': matches,
                'search_method': 'direct_platform_search',
                'search_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Direct platform search failed for {platform_name}: {e}")
            raise
            
    def _advanced_google_search(self, email: str, platform: Dict) -> Dict:
        """Advanced Google search with email variations"""
        platform_name = platform.get('name', 'Unknown')
        platform_url = platform.get('url', '')
        
        try:
            username = email.split('@')[0]
            domain = email.split('@')[1]
            
            # Advanced search queries
            queries = [
                f'site:{platform_url} "{username}"',
                f'site:{platform_url} "{username}" "{domain}"',
                f'site:{platform_url} "{email.replace(".", " ")}"',
                f'site:{platform_url} "{username}*{domain}"'
            ]
            
            all_matches = []
            
            for query in queries:
                try:
                    google_url = f"https://www.google.com/search?q={quote_plus(query)}"
                    time.sleep(random.uniform(2, 4))
                    
                    response = self.session.get(google_url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    search_results = soup.find_all('div', class_='g')
                    
                    for result in search_results[:3]:
                        try:
                            title_elem = result.find('h3')
                            link_elem = result.find('a')
                            snippet_elem = result.find('span', class_='st') or result.find('div', class_='s')
                            
                            if title_elem and link_elem:
                                title = title_elem.get_text(strip=True)
                                link = link_elem.get('href', '')
                                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                                
                                # Check for email variations
                                content = (title + ' ' + snippet).lower()
                                confidence = 0.3
                                
                                if email.lower() in content:
                                    confidence = 0.9
                                elif username.lower() in content:
                                    confidence = 0.6
                                elif domain.lower() in content:
                                    confidence = 0.4
                                    
                                if confidence > 0.3:
                                    all_matches.append({
                                        'title': title,
                                        'url': link,
                                        'snippet': snippet,
                                        'confidence': confidence,
                                        'source': 'advanced_google_search',
                                        'query_used': query
                                    })
                                    
                        except Exception as e:
                            logging.debug(f"Error parsing advanced search result: {e}")
                            continue
                            
                except Exception as e:
                    logging.debug(f"Advanced query '{query}' failed: {e}")
                    continue
                    
            # Remove duplicates and sort by confidence
            unique_matches = []
            seen_urls = set()
            
            for match in sorted(all_matches, key=lambda x: x['confidence'], reverse=True):
                if match['url'] not in seen_urls:
                    unique_matches.append(match)
                    seen_urls.add(match['url'])
                    
            status = 'potential_match' if unique_matches else 'not_found'
            
            return {
                'platform': platform_name,
                'url': platform_url,
                'status': status,
                'matches': unique_matches[:5],  # Limit to top 5
                'search_method': 'advanced_google_search',
                'search_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Advanced Google search failed for {platform_name}: {e}")
            raise
            
    def _parse_platform_results(self, html_content: str, email: str, platform: Dict) -> List[Dict]:
        """Parse platform-specific search results"""
        matches = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Generic patterns for finding email mentions
            text_content = soup.get_text().lower()
            
            if email.lower() in text_content:
                # Try to find specific elements containing the email
                for element in soup.find_all(['div', 'span', 'p', 'a']):
                    element_text = element.get_text()
                    if email.lower() in element_text.lower():
                        matches.append({
                            'content': element_text.strip()[:200],
                            'element_type': element.name,
                            'confidence': 0.8,
                            'source': 'direct_platform_content'
                        })
                        
                        if len(matches) >= 3:  # Limit matches
                            break
                            
        except Exception as e:
            logging.debug(f"Error parsing platform results: {e}")
            
        return matches
        
    def close(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")
                
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logging.error(f"Error closing session: {e}")
                
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.close()