#!/usr/bin/env python3
"""
Proxy Manager for Email OSINT Tool
Author: Security Researcher
Date: September 2025
"""

import random
import requests
import logging
import time
import threading
from typing import List, Dict, Optional, Any
import os
from urllib.parse import urlparse
import socket
import concurrent.futures
from datetime import datetime, timedelta


class ProxyManager:
    """Manages proxy rotation and validation"""
    
    def __init__(self, proxy_file: str = "proxies.txt", max_retries: int = 3):
        self.proxy_file = proxy_file
        self.max_retries = max_retries
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = []
        self.current_index = 0
        self.lock = threading.Lock()
        
        # Load proxy authentication from environment
        self.proxy_auth = os.getenv('PROXY_AUTH')
        
        # Performance tracking
        self.proxy_performance = {}
        
        # Load proxies on initialization
        self.load_proxies()
        
    def load_proxies(self):
        """Load proxy list from file"""
        if not os.path.exists(self.proxy_file):
            logging.warning(f"Proxy file {self.proxy_file} not found. Creating default file.")
            self._create_default_proxy_file()
            return
            
        try:
            with open(self.proxy_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxy = self._parse_proxy_line(line)
                    if proxy:
                        self.proxies.append(proxy)
                        
            logging.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
            
            # Validate proxies on startup if enabled
            if os.getenv('PROXY_VALIDATION_ON_STARTUP', 'false').lower() == 'true':
                self.validate_all_proxies()
                
        except Exception as e:
            logging.error(f"Error loading proxy file: {e}")
            
    def _create_default_proxy_file(self):
        """Create default proxy file with examples"""
        default_content = """# Proxy List for Email OSINT Tool
# Format: http://ip:port or https://ip:port
# With authentication: http://user:pass@ip:port
# 
# Examples:
# http://proxy1.example.com:8080
# http://user:pass@proxy2.example.com:3128
# https://secure-proxy.example.com:8080
#
# Add your proxies below:

"""
        try:
            with open(self.proxy_file, 'w') as f:
                f.write(default_content)
            logging.info(f"Created default proxy file: {self.proxy_file}")
        except Exception as e:
            logging.error(f"Failed to create default proxy file: {e}")
            
    def _parse_proxy_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a proxy line into a dictionary"""
        try:
            # Handle different proxy formats
            if '://' in line:
                # Full URL format
                parsed = urlparse(line)
                proxy_dict = {
                    'http': line,
                    'https': line
                }
            else:
                # IP:PORT format, assume HTTP
                if ':' in line:
                    host, port = line.split(':', 1)
                    if self.proxy_auth:
                        proxy_url = f"http://{self.proxy_auth}@{host}:{port}"
                    else:
                        proxy_url = f"http://{host}:{port}"
                    proxy_dict = {
                        'http': proxy_url,
                        'https': proxy_url
                    }
                else:
                    return None
                    
            # Add metadata
            proxy_dict['original'] = line
            proxy_dict['last_used'] = None
            proxy_dict['failures'] = 0
            proxy_dict['successes'] = 0
            proxy_dict['avg_response_time'] = 0
            
            return proxy_dict
            
        except Exception as e:
            logging.debug(f"Error parsing proxy line '{line}': {e}")
            return None
            
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next available proxy with rotation"""
        if not self.working_proxies and not self.proxies:
            return None
            
        with self.lock:
            # Use working proxies first
            proxy_list = self.working_proxies if self.working_proxies else self.proxies
            
            if not proxy_list:
                return None
                
            # Round-robin selection
            proxy = proxy_list[self.current_index % len(proxy_list)]
            self.current_index += 1
            
            # Update last used time
            proxy['last_used'] = datetime.now()
            
            return proxy
            
    def get_proxy_string(self) -> Optional[str]:
        """Get proxy as string for use with Selenium"""
        proxy = self.get_proxy()
        if proxy:
            return proxy.get('http', '').replace('http://', '')
        return None
        
    def has_proxies(self) -> bool:
        """Check if any proxies are available"""
        return len(self.proxies) > 0 or len(self.working_proxies) > 0
        
    def mark_proxy_failed(self, proxy: Dict[str, str]):
        """Mark a proxy as failed"""
        with self.lock:
            proxy['failures'] += 1
            
            # Remove from working proxies if too many failures
            if proxy['failures'] >= self.max_retries:
                if proxy in self.working_proxies:
                    self.working_proxies.remove(proxy)
                if proxy not in self.failed_proxies:
                    self.failed_proxies.append(proxy)
                    
                logging.warning(f"Proxy {proxy.get('original', 'unknown')} marked as failed")
                
    def mark_proxy_success(self, proxy: Dict[str, str], response_time: float = 0):
        """Mark a proxy as successful"""
        with self.lock:
            proxy['successes'] += 1
            
            # Update average response time
            if response_time > 0:
                if proxy['avg_response_time'] == 0:
                    proxy['avg_response_time'] = response_time
                else:
                    proxy['avg_response_time'] = (proxy['avg_response_time'] + response_time) / 2
                    
            # Add to working proxies if not already there
            if proxy not in self.working_proxies:
                self.working_proxies.append(proxy)
                
    def validate_proxy(self, proxy: Dict[str, str], timeout: int = 10) -> bool:
        """Validate a single proxy"""
        test_urls = [
            'http://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'http://ip-api.com/json'
        ]
        
        for url in test_urls:
            try:
                start_time = time.time()
                
                response = requests.get(
                    url,
                    proxies=proxy,
                    timeout=timeout,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.mark_proxy_success(proxy, response_time)
                    logging.info(f"Proxy {proxy.get('original', 'unknown')} validated successfully ({response_time:.2f}s)")
                    return True
                    
            except Exception as e:
                logging.debug(f"Proxy validation failed for {proxy.get('original', 'unknown')}: {e}")
                continue
                
        self.mark_proxy_failed(proxy)
        return False
        
    def validate_all_proxies(self, max_workers: int = 10):
        """Validate all proxies concurrently"""
        if not self.proxies:
            logging.warning("No proxies to validate")
            return
            
        logging.info(f"Validating {len(self.proxies)} proxies...")
        
        start_time = time.time()
        validated_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.validate_proxy, proxy): proxy
                for proxy in self.proxies
            }
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    is_valid = future.result(timeout=30)
                    if is_valid:
                        validated_count += 1
                except Exception as e:
                    logging.error(f"Proxy validation error: {e}")
                    self.mark_proxy_failed(proxy)
                    
        end_time = time.time()
        validation_time = end_time - start_time
        
        logging.info(f"Proxy validation completed: {validated_count}/{len(self.proxies)} working proxies in {validation_time:.2f}s")
        
        # Sort working proxies by performance
        self.working_proxies.sort(key=lambda x: x.get('avg_response_time', 999))
        
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        total_proxies = len(self.proxies)
        working_proxies = len(self.working_proxies)
        failed_proxies = len(self.failed_proxies)
        
        return {
            'total_proxies': total_proxies,
            'working_proxies': working_proxies,
            'failed_proxies': failed_proxies,
            'success_rate': (working_proxies / total_proxies * 100) if total_proxies > 0 else 0,
            'current_index': self.current_index,
        }
        
    def reset_failed_proxies(self):
        """Reset failed proxies (give them another chance)"""
        with self.lock:
            for proxy in self.failed_proxies[:]:
                proxy['failures'] = 0
                proxy['successes'] = 0
                self.failed_proxies.remove(proxy)
                
            logging.info("Reset all failed proxies")
            
    def add_proxy(self, proxy_string: str) -> bool:
        """Add a new proxy dynamically"""
        proxy = self._parse_proxy_line(proxy_string)
        if proxy:
            with self.lock:
                self.proxies.append(proxy)
            logging.info(f"Added new proxy: {proxy_string}")
            return True
        return False
        
    def remove_proxy(self, proxy_string: str) -> bool:
        """Remove a proxy"""
        with self.lock:
            for proxy_list in [self.proxies, self.working_proxies, self.failed_proxies]:
                for proxy in proxy_list[:]:
                    if proxy.get('original') == proxy_string:
                        proxy_list.remove(proxy)
                        logging.info(f"Removed proxy: {proxy_string}")
                        return True
        return False
        
    def save_working_proxies(self, filename: str = "working_proxies.txt"):
        """Save currently working proxies to a file"""
        try:
            with open(filename, 'w') as f:
                f.write(f"# Working proxies as of {datetime.now().isoformat()}\n")
                f.write(f"# Total: {len(self.working_proxies)} proxies\n\n")
                
                for proxy in self.working_proxies:
                    original = proxy.get('original', '')
                    response_time = proxy.get('avg_response_time', 0)
                    successes = proxy.get('successes', 0)
                    failures = proxy.get('failures', 0)
                    
                    f.write(f"{original}  # RT: {response_time:.2f}s, Success: {successes}, Fail: {failures}\n")
                    
            logging.info(f"Saved {len(self.working_proxies)} working proxies to {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving working proxies: {e}")
            return False
            
    def test_proxy_connectivity(self, proxy: Dict[str, str], target_url: str = None) -> Dict[str, Any]:
        """Test proxy connectivity to specific target"""
        if not target_url:
            target_url = "https://www.google.com"
            
        result = {
            'proxy': proxy.get('original', 'unknown'),
            'target_url': target_url,
            'success': False,
            'response_time': 0,
            'status_code': 0,
            'error': None,
            'ip_address': None
        }
        
        try:
            start_time = time.time()
            
            response = requests.get(
                target_url,
                proxies=proxy,
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            result['response_time'] = time.time() - start_time
            result['status_code'] = response.status_code
            result['success'] = response.status_code == 200
            
            # Try to get IP address
            try:
                ip_response = requests.get(
                    'https://api.ipify.org?format=json',
                    proxies=proxy,
                    timeout=10
                )
                if ip_response.status_code == 200:
                    result['ip_address'] = ip_response.json().get('ip')
            except:
                pass
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def get_best_proxy(self) -> Optional[Dict[str, str]]:
        """Get the best performing proxy"""
        if not self.working_proxies:
            return None
            
        # Sort by success rate and response time
        best_proxy = min(
            self.working_proxies,
            key=lambda x: (
                x.get('failures', 0) / max(x.get('successes', 1), 1),  # Failure rate
                x.get('avg_response_time', 999)  # Response time
            )
        )
        
        return best_proxy
        
    def cleanup_old_performance_data(self, days: int = 7):
        """Clean up old performance data"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            for proxy in self.proxies + self.working_proxies + self.failed_proxies:
                last_used = proxy.get('last_used')
                if last_used and isinstance(last_used, datetime) and last_used < cutoff_date:
                    # Reset performance counters for old data
                    proxy['failures'] = 0
                    proxy['successes'] = 0
                    proxy['avg_response_time'] = 0