#!/usr/bin/env python3
"""
Email Validator for Email OSINT Tool
Author: Security Researcher
Date: September 2025
"""

import re
import dns.resolver
import smtplib
import socket
import logging
from typing import Dict, List, Optional, Tuple, Any
from email_validator import validate_email, EmailNotValidError
import requests
import json
from datetime import datetime, timedelta
import os


class EmailValidator:
    """Advanced email validation with multiple validation methods"""
    
    def __init__(self):
        self.disposable_domains = set()
        self.load_disposable_domains()
        
        # Email regex patterns
        self.basic_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        self.advanced_pattern = re.compile(
            r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
        )
        
        # Cache for DNS lookups
        self.dns_cache = {}
        self.cache_expiry = timedelta(hours=24)
        
    def load_disposable_domains(self):
        """Load list of disposable email domains"""
        disposable_domains_list = [
            '10minutemail.com', '20minutemail.com', '33mail.com', '3utilities.com',
            'emailondeck.com', 'fakeinbox.com', 'guerrillamail.com', 'mailinator.com',
            'mailtmp.com', 'mohmal.com', 'sharklasers.com', 'tempmail.org',
            'throwaway.email', 'tmpmail.org', 'yopmail.com', 'dispostable.com',
            'mailnesia.com', 'sneakemail.com', 'spamgourmet.com', 'tempail.com',
            'temp-mail.org', 'getairmail.com', 'armyspy.com', 'cuvox.de',
            'dayrep.com', 'einrot.com', 'fleckens.hu', 'gustr.com',
            'jourrapide.com', 'superrito.com', 'teleworm.us', 'rhynoodle.com'
        ]
        
        self.disposable_domains.update(disposable_domains_list)
        
        # Try to load additional domains from online source
        try:
            self.load_online_disposable_domains()
        except Exception as e:
            logging.debug(f"Could not load online disposable domains: {e}")
            
    def load_online_disposable_domains(self):
        """Load disposable domains from online source"""
        urls = [
            'https://raw.githubusercontent.com/martenson/disposable-email-domains/master/disposable_email_blocklist.conf',
            'https://raw.githubusercontent.com/disposable/disposable-email-domains/master/domains.txt'
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    domains = response.text.strip().split('\n')
                    for domain in domains:
                        domain = domain.strip().lower()
                        if domain and not domain.startswith('#'):
                            self.disposable_domains.add(domain)
                    break
            except Exception as e:
                logging.debug(f"Failed to load from {url}: {e}")
                continue
                
        logging.info(f"Loaded {len(self.disposable_domains)} disposable email domains")
        
    def is_valid_email(self, email: str) -> bool:
        """Basic email format validation"""
        if not email or not isinstance(email, str):
            return False
            
        email = email.strip().lower()
        
        # Basic format check
        if not self.advanced_pattern.match(email):
            return False
            
        # Length checks
        if len(email) > 254:  # RFC 5321 limit
            return False
            
        local, domain = email.rsplit('@', 1)
        if len(local) > 64:  # RFC 5321 limit
            return False
            
        return True
        
    def validate_email_advanced(self, email: str) -> Dict[str, Any]:
        """Comprehensive email validation with detailed results"""
        result = {
            'email': email,
            'valid': False,
            'checks': {
                'format': False,
                'dns_exists': False,
                'mx_record': False,
                'disposable': False,
                'smtp_valid': False
            },
            'details': {},
            'score': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Step 1: Format validation
            result['checks']['format'] = self.is_valid_email(email)
            if not result['checks']['format']:
                result['details']['format_error'] = 'Invalid email format'
                return result
                
            # Step 2: Use email-validator library
            try:
                validation = validate_email(email)
                result['details']['normalized_email'] = validation.email
                result['details']['local_part'] = validation.local
                result['details']['domain'] = validation.domain
                result['score'] += 20
            except EmailNotValidError as e:
                result['details']['validation_error'] = str(e)
                return result
                
            domain = email.split('@')[1].lower()
            
            # Step 3: Check for disposable email
            result['checks']['disposable'] = domain in self.disposable_domains
            if result['checks']['disposable']:
                result['details']['disposable_domain'] = True
                result['score'] -= 30
            else:
                result['score'] += 10
                
            # Step 4: DNS validation
            dns_result = self.validate_domain_dns(domain)
            result['checks']['dns_exists'] = dns_result['exists']
            result['checks']['mx_record'] = dns_result['has_mx']
            result['details']['dns'] = dns_result
            
            if result['checks']['dns_exists']:
                result['score'] += 25
            if result['checks']['mx_record']:
                result['score'] += 25
                
            # Step 5: SMTP validation (optional and slower)
            smtp_enabled = os.getenv('SMTP_VALIDATION_ENABLED', 'false').lower() == 'true'
            if smtp_enabled and result['checks']['mx_record']:
                smtp_result = self.validate_smtp(email)
                result['checks']['smtp_valid'] = smtp_result['valid']
                result['details']['smtp'] = smtp_result
                
                if result['checks']['smtp_valid']:
                    result['score'] += 20
                    
            # Final validation score
            result['valid'] = (
                result['checks']['format'] and
                result['checks']['dns_exists'] and
                result['checks']['mx_record'] and
                not result['checks']['disposable']
            )
            
            # Adjust score based on overall validity
            if result['valid']:
                result['score'] = max(result['score'], 70)
            else:
                result['score'] = min(result['score'], 50)
                
        except Exception as e:
            result['details']['validation_exception'] = str(e)
            logging.error(f"Email validation error: {e}")
            
        return result
        
    def validate_domain_dns(self, domain: str) -> Dict[str, Any]:
        """Validate domain DNS records"""
        # Check cache first
        cache_key = f"dns_{domain}"
        if cache_key in self.dns_cache:
            cached_result, timestamp = self.dns_cache[cache_key]
            if datetime.now() - timestamp < self.cache_expiry:
                return cached_result
                
        result = {
            'domain': domain,
            'exists': False,
            'has_mx': False,
            'has_a': False,
            'mx_records': [],
            'a_records': [],
            'error': None
        }
        
        try:
            # Check A record (domain exists)
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                result['has_a'] = True
                result['exists'] = True
                result['a_records'] = [str(record) for record in a_records]
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass
            except Exception as e:
                result['error'] = f"A record lookup failed: {str(e)}"
                
            # Check MX record (can receive email)
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                result['has_mx'] = True
                result['exists'] = True
                result['mx_records'] = [
                    {'priority': record.preference, 'exchange': str(record.exchange)}
                    for record in mx_records
                ]
                # Sort by priority
                result['mx_records'].sort(key=lambda x: x['priority'])
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass
            except Exception as e:
                if not result['error']:
                    result['error'] = f"MX record lookup failed: {str(e)}"
                    
        except Exception as e:
            result['error'] = f"DNS validation failed: {str(e)}"
            
        # Cache the result
        self.dns_cache[cache_key] = (result, datetime.now())
        
        return result
        
    def validate_smtp(self, email: str, timeout: int = 10) -> Dict[str, Any]:
        """Validate email using SMTP (can be slow and may be blocked)"""
        result = {
            'email': email,
            'valid': False,
            'reachable': False,
            'error': None,
            'mx_used': None,
            'response_code': None
        }
        
        try:
            domain = email.split('@')[1]
            
            # Get MX records
            dns_result = self.validate_domain_dns(domain)
            if not dns_result['has_mx']:
                result['error'] = 'No MX records found'
                return result
                
            # Try each MX record
            for mx_record in dns_result['mx_records']:
                mx_host = mx_record['exchange'].rstrip('.')
                result['mx_used'] = mx_host
                
                try:
                    # Connect to SMTP server
                    server = smtplib.SMTP(timeout=timeout)
                    server.set_debuglevel(0)
                    
                    # Connect and identify
                    response_code, response_msg = server.connect(mx_host, 25)
                    result['response_code'] = response_code
                    
                    if response_code == 220:
                        result['reachable'] = True
                        
                        # HELO
                        server.helo()
                        
                        # MAIL FROM
                        server.mail('test@example.com')
                        
                        # RCPT TO - this is where we test the email
                        code, message = server.rcpt(email)
                        result['response_code'] = code
                        
                        # Code 250 means accepted, 550 means rejected
                        if code == 250:
                            result['valid'] = True
                        elif code == 550:
                            result['valid'] = False
                            result['error'] = 'Email address rejected'
                        else:
                            result['error'] = f"Unexpected response: {code} {message}"
                            
                    server.quit()
                    break  # Successfully tested
                    
                except smtplib.SMTPConnectError as e:
                    result['error'] = f"Connection failed to {mx_host}: {str(e)}"
                    continue  # Try next MX record
                except smtplib.SMTPException as e:
                    result['error'] = f"SMTP error with {mx_host}: {str(e)}"
                    continue
                except socket.timeout:
                    result['error'] = f"Timeout connecting to {mx_host}"
                    continue
                except Exception as e:
                    result['error'] = f"Unexpected error with {mx_host}: {str(e)}"
                    continue
                    
        except Exception as e:
            result['error'] = f"SMTP validation failed: {str(e)}"
            
        return result
        
    def extract_emails_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract and validate email addresses from text"""
        email_pattern = re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        )
        
        found_emails = []
        matches = email_pattern.finditer(text)
        
        for match in matches:
            email = match.group().lower()
            start_pos = match.start()
            end_pos = match.end()
            
            # Basic validation
            is_valid = self.is_valid_email(email)
            
            found_emails.append({
                'email': email,
                'position': (start_pos, end_pos),
                'valid_format': is_valid,
                'context': text[max(0, start_pos-20):end_pos+20]
            })
            
        return found_emails
        
    def generate_email_variations(self, email: str) -> List[str]:
        """Generate common email variations for searching"""
        if not self.is_valid_email(email):
            return []
            
        local, domain = email.split('@')
        variations = []
        
        # Original email
        variations.append(email)
        
        # With dots removed/added
        if '.' in local:
            variations.append(local.replace('.', '') + '@' + domain)
        else:
            # Add dots in common positions
            if len(local) > 1:
                variations.append(local[0] + '.' + local[1:] + '@' + domain)
            if len(local) > 3:
                variations.append(local[:2] + '.' + local[2:] + '@' + domain)
                
        # With numbers
        for i in range(1, 100):
            variations.append(local + str(i) + '@' + domain)
            if i <= 10:
                variations.append(local + '0' + str(i) + '@' + domain)
                
        # With common additions
        common_additions = ['1', '01', '2025', 'new', 'official', 'real']
        for addition in common_additions:
            variations.append(local + addition + '@' + domain)
            
        # Underscore variations
        if '.' in local:
            variations.append(local.replace('.', '_') + '@' + domain)
        if '_' in local:
            variations.append(local.replace('_', '.') + '@' + domain)
            
        # Hyphen variations
        if '.' in local:
            variations.append(local.replace('.', '-') + '@' + domain)
        if '-' in local:
            variations.append(local.replace('-', '.') + '@' + domain)
            
        # Remove duplicates and invalid emails
        valid_variations = []
        seen = set()
        
        for variation in variations:
            if variation not in seen and self.is_valid_email(variation):
                valid_variations.append(variation)
                seen.add(variation)
                
        return valid_variations[:20]  # Limit to 20 variations
        
    def get_email_provider_info(self, email: str) -> Dict[str, Any]:
        """Get information about the email provider"""
        if not self.is_valid_email(email):
            return {}
            
        domain = email.split('@')[1].lower()
        
        # Common email providers
        providers = {
            'gmail.com': {
                'name': 'Google Gmail',
                'type': 'Free',
                'security': 'High',
                'popularity': 'Very High'
            },
            'yahoo.com': {
                'name': 'Yahoo Mail',
                'type': 'Free',
                'security': 'Medium',
                'popularity': 'High'
            },
            'outlook.com': {
                'name': 'Microsoft Outlook',
                'type': 'Free',
                'security': 'High',
                'popularity': 'High'
            },
            'hotmail.com': {
                'name': 'Microsoft Hotmail',
                'type': 'Free',
                'security': 'Medium',
                'popularity': 'Medium'
            },
            'icloud.com': {
                'name': 'Apple iCloud',
                'type': 'Free',
                'security': 'High',
                'popularity': 'Medium'
            },
            'protonmail.com': {
                'name': 'ProtonMail',
                'type': 'Privacy-focused',
                'security': 'Very High',
                'popularity': 'Low'
            },
        }
        
        provider_info = providers.get(domain, {
            'name': f'Unknown ({domain})',
            'type': 'Unknown',
            'security': 'Unknown',
            'popularity': 'Unknown'
        })
        
        provider_info['domain'] = domain
        provider_info['is_disposable'] = domain in self.disposable_domains
        
        return provider_info
        
    def validate_email_list(self, emails: List[str]) -> Dict[str, Any]:
        """Validate a list of emails and return summary"""
        results = {
            'total_emails': len(emails),
            'valid_emails': 0,
            'invalid_emails': 0,
            'disposable_emails': 0,
            'detailed_results': [],
            'summary': {}
        }
        
        for email in emails:
            validation = self.validate_email_advanced(email)
            results['detailed_results'].append(validation)
            
            if validation['valid']:
                results['valid_emails'] += 1
            else:
                results['invalid_emails'] += 1
                
            if validation['checks']['disposable']:
                results['disposable_emails'] += 1
                
        # Calculate percentages
        total = results['total_emails']
        if total > 0:
            results['summary'] = {
                'valid_percentage': (results['valid_emails'] / total) * 100,
                'invalid_percentage': (results['invalid_emails'] / total) * 100,
                'disposable_percentage': (results['disposable_emails'] / total) * 100
            }
            
        return results