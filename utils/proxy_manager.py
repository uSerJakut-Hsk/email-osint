"""
Proxy Manager Utility Module
Handles proxy rotation and validation for OSINT operations
"""

import random
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple
import threading
from urllib.parse import urlparse


class ProxyManager:
    def __init__(self, proxy_file: str = "proxies.txt", timeout: int = 10):
        self.proxy_file = proxy_file
        self.timeout = timeout
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.current_proxy_index = 0
        self.lock = threading.Lock()
        
        # Load proxies from file
        self.load_proxies()
        
        # Validate proxies on startup (optional)
        # self.validate_all_proxies()
        
    def load_proxies(self) -> None:
        """Load proxy list from file"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and not proxy.startswith('#'):
                        if self._is_valid_proxy_format(proxy):
                            self.proxies.append(proxy)
                        else:
                            logging.warning(f"Invalid proxy format: {proxy}")
                            
            logging.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
            
        except FileNotFoundError:
            logging.warning(f"Proxy file {self.proxy_file} not found. Running without proxies.")
            self.proxies = []
        except Exception as e:
            logging.error(f"Error loading proxies: {str(e)}")
            self.proxies = []
            
    def _is_valid_proxy_format(self, proxy: str) -> bool:
        """Validate proxy format"""
        try:
            # Check if it's a URL format
            if proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                parsed = urlparse(proxy)
                return bool(parsed.hostname and parsed.port)
            
            # Check if it's IP:PORT format
            if ':' in proxy:
                host, port = proxy.rsplit(':', 1)
                return bool(host) and port.isdigit() and 1 <= int(port) <= 65535
                
            return False
        except:
            return False
            
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next available proxy"""
        if not self.proxies:
            return None
            
        with self.lock:
            # If we have working proxies, use them first
            if self.working_proxies:
                proxy_url = random.choice(self.working_proxies)
            else:
                # Use any available proxy
                available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
                if not available_proxies:
                    # Reset failed proxies if all have failed
                    self.failed_proxies.clear()
                    available_proxies = self.proxies
                    
                proxy_url = random.choice(available_proxies)
                
        return self._format_proxy_dict(proxy_url)
        
    def _format_proxy_dict(self, proxy_url: str) -> Dict[str, str]:
        """Format proxy URL into requests-compatible dictionary"""
        if proxy_url.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        else:
            # Assume HTTP proxy for IP:PORT format
            formatted_proxy = f"http://{proxy_url}"
            return {
                'http': formatted_proxy,
                'https': formatted_proxy
            }
            
    def validate_proxy(self, proxy_url: str) -> Tuple[bool, float]:
        """
        Validate a single proxy
        
        Returns:
            Tuple of (is_working, response_time)
        """
        proxy_dict = self._format_proxy_dict(proxy_url)
        
        test_urls = [
            'http://httpbin.org/ip',
            'https://httpbin.org/ip',
            'http://icanhazip.com',
            'https://api.ipify.org?format=json'
        ]
        
        for test_url in test_urls:
            try:
                start_time = time.time()
                
                response = requests.get(
                    test_url,
                    proxies=proxy_dict,
                    timeout=self.timeout,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    logging.info(f"Proxy {proxy_url} is working (response time: {response_time:.2f}s)")
                    return True, response_time
                    
            except Exception as e:
                logging.debug(f"Proxy {proxy_url} failed test with {test_url}: {str(e)}")
                continue
                
        logging.warning(f"Proxy {proxy_url} failed all tests")
        return False, 0.0
        
    def validate_all_proxies(self) -> None:
        """Validate all proxies and update working proxies list"""
        if not self.proxies:
            return
            
        logging.info(f"Validating {len(self.proxies)} proxies...")
        
        working_proxies = []
        failed_proxies = set()
        
        for proxy in self.proxies:
            is_working, response_time = self.validate_proxy(proxy)
            
            if is_working:
                working_proxies.append(proxy)
            else:
                failed_proxies.add(proxy)
                
            # Small delay to avoid overwhelming test servers
            time.sleep(0.5)
            
        with self.lock:
            self.working_proxies = working_proxies
            self.failed_proxies = failed_proxies
            
        logging.info(f"Validation complete: {len(working_proxies)} working, {len(failed_proxies)} failed")
        
    def mark_proxy_failed(self, proxy_url: str) -> None:
        """Mark a proxy as failed"""
        with self.lock:
            self.failed_proxies.add(proxy_url)
            if proxy_url in self.working_proxies:
                self.working_proxies.remove(proxy_url)
                
        logging.warning(f"Marked proxy as failed: {proxy_url}")
        
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from available proxies"""
        return self.get_proxy()
        
    def get_proxy_stats(self) -> Dict[str, int]:
        """Get proxy statistics"""
        return {
            "total_proxies": len(self.proxies),
            "working_proxies": len(self.working_proxies),
            "failed_proxies": len(self.failed_proxies),
            "available_proxies": len(self.proxies) - len(self.failed_proxies)
        }
        
    def reset_failed_proxies(self) -> None:
        """Reset failed proxies list (give them another chance)"""
        with self.lock:
            self.failed_proxies.clear()
            
        logging.info("Reset failed proxies list")
        
    def add_proxy(self, proxy_url: str) -> bool:
        """Add a new proxy to the list"""
        if not self._is_valid_proxy_format(proxy_url):
            logging.error(f"Invalid proxy format: {proxy_url}")
            return False
            
        with self.lock:
            if proxy_url not in self.proxies:
                self.proxies.append(proxy_url)
                logging.info(f"Added new proxy: {proxy_url}")
                return True
            else:
                logging.info(f"Proxy already exists: {proxy_url}")
                return False
                
    def remove_proxy(self, proxy_url: str) -> bool:
        """Remove a proxy from the list"""
        with self.lock:
            if proxy_url in self.proxies:
                self.proxies.remove(proxy_url)
                if proxy_url in self.working_proxies:
                    self.working_proxies.remove(proxy_url)
                self.failed_proxies.discard(proxy_url)
                logging.info(f"Removed proxy: {proxy_url}")
                return True
            else:
                logging.warning(f"Proxy not found: {proxy_url}")
                return False
                
    def save_proxies(self, filename: str = None) -> None:
        """Save current proxy list to file"""
        if filename is None:
            filename = self.proxy_file
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Proxy list for OSINT Email Tool\n")
                f.write("# Format: http://ip:port or ip:port\n")
                f.write("# Lines starting with # are comments\n\n")
                
                for proxy in self.proxies:
                    status = " # Working" if proxy in self.working_proxies else ""
                    status = " # Failed" if proxy in self.failed_proxies else status
                    f.write(f"{proxy}{status}\n")
                    
            logging.info(f"Saved {len(self.proxies)} proxies to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving proxies: {str(e)}")
            
    def test_proxy_connectivity(self, proxy_url: str) -> Dict[str, any]:
        """Test proxy connectivity and get detailed information"""
        proxy_dict = self._format_proxy_dict(proxy_url)
        
        result = {
            "proxy": proxy_url,
            "is_working": False,
            "response_time": 0.0,
            "ip_address": None,
            "location": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Test basic connectivity
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            result["response_time"] = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                result["is_working"] = True
                result["ip_address"] = data.get("origin", "Unknown")
                
                # Try to get location info (optional)
                try:
                    location_response = requests.get(
                        f'http://ip-api.com/json/{result["ip_address"]}',
                        timeout=5
                    )
                    if location_response.status_code == 200:
                        location_data = location_response.json()
                        result["location"] = f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}"
                except:
                    result["location"] = "Unknown"
                    
            else:
                result["error"] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    def get_best_proxies(self, count: int = 5) -> List[str]:
        """Get the best performing proxies"""
        if not self.working_proxies:
            return []
            
        # For now, just return random working proxies
        # In the future, could implement performance tracking
        return random.sample(
            self.working_proxies, 
            min(count, len(self.working_proxies))
        )
        
    def is_proxy_available(self) -> bool:
        """Check if any proxy is available"""
        return len(self.proxies) > len(self.failed_proxies)