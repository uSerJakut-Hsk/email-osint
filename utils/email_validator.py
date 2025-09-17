"""
Email Validator Utility Module
Validates email addresses and extracts email-related information
"""

import re
import dns.resolver
import socket
import logging
from typing import Dict, List, Optional, Tuple
import smtplib
from email.utils import parseaddr


class EmailValidator:
    def __init__(self):
        # Email regex pattern (RFC 5322 compliant)
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # Common disposable email domains
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'yopmail.com', 'maildrop.cc', 'trashmail.com',
            'getnada.com', 'mohmal.com', 'sharklasers.com'
        }
        
        # Common email providers for categorization
        self.email_providers = {
            'gmail.com': 'Google',
            'yahoo.com': 'Yahoo',
            'outlook.com': 'Microsoft',
            'hotmail.com': 'Microsoft',
            'live.com': 'Microsoft',
            'msn.com': 'Microsoft',
            'aol.com': 'AOL',
            'icloud.com': 'Apple',
            'me.com': 'Apple',
            'mac.com': 'Apple',
            'protonmail.com': 'ProtonMail',
            'tutanota.com': 'Tutanota',
            'zoho.com': 'Zoho',
            'fastmail.com': 'FastMail'
        }
        
    def is_valid_email(self, email: str) -> bool:
        """
        Validate email address format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid format, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
            
        # Basic format check
        if not self.email_pattern.match(email):
            return False
            
        # Additional checks
        if email.count('@') != 1:
            return False
            
        local, domain = email.split('@')
        
        # Local part checks
        if not local or len(local) > 64:
            return False
            
        # Domain checks
        if not domain or len(domain) > 255:
            return False
            
        # Check for consecutive dots
        if '..' in email:
            return False
            
        # Check for leading/trailing dots in local part
        if local.startswith('.') or local.endswith('.'):
            return False
            
        return True
        
    def extract_email_info(self, email: str) -> Dict[str, any]:
        """
        Extract information from email address
        
        Args:
            email: Email address to analyze
            
        Returns:
            Dictionary containing email information
        """
        if not self.is_valid_email(email):
            return {"error": "Invalid email format"}
            
        local, domain = email.split('@')
        
        info = {
            "email": email,
            "local_part": local,
            "domain": domain,
            "is_valid": True,
            "provider": self.email_providers.get(domain.lower(), "Unknown"),
            "is_disposable": domain.lower() in self.disposable_domains,
            "domain_info": self.analyze_domain(domain)
        }
        
        # Analyze local part
        info["local_analysis"] = self.analyze_local_part(local)
        
        return info
        
    def analyze_local_part(self, local: str) -> Dict[str, any]:
        """Analyze the local part of email address"""
        analysis = {
            "length": len(local),
            "has_numbers": bool(re.search(r'\d', local)),
            "has_special_chars": bool(re.search(r'[._%+-]', local)),
            "pattern_type": "unknown"
        }
        
        # Detect common patterns
        if '.' in local:
            parts = local.split('.')
            if len(parts) == 2:
                analysis["pattern_type"] = "firstname.lastname"
                analysis["potential_firstname"] = parts[0]
                analysis["potential_lastname"] = parts[1]
        elif re.match(r'^[a-zA-Z]+\d+$', local):
            analysis["pattern_type"] = "name_number"
        elif re.match(r'^[a-zA-Z]+$', local):
            analysis["pattern_type"] = "single_word"
        elif re.search(r'\d{4}', local):
            analysis["pattern_type"] = "contains_year"
            year_match = re.search(r'(19|20)\d{2}', local)
            if year_match:
                analysis["potential_birth_year"] = year_match.group()
                
        return analysis
        
    def analyze_domain(self, domain: str) -> Dict[str, any]:
        """Analyze domain information"""
        domain_info = {
            "domain": domain,
            "tld": domain.split('.')[-1] if '.' in domain else domain,
            "subdomain_count": len(domain.split('.')) - 1,
            "mx_records": [],
            "a_records": [],
            "domain_exists": False,
            "mx_exists": False
        }
        
        try:
            # Check A records
            a_records = dns.resolver.resolve(domain, 'A')
            domain_info["a_records"] = [str(record) for record in a_records]
            domain_info["domain_exists"] = True
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            pass
            
        try:
            # Check MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            domain_info["mx_records"] = [f"{record.priority} {record.exchange}" for record in mx_records]
            domain_info["mx_exists"] = True
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            pass
            
        return domain_info
        
    def check_email_deliverability(self, email: str, timeout: int = 10) -> Dict[str, any]:
        """
        Check if email address is potentially deliverable
        
        Args:
            email: Email address to check
            timeout: Timeout in seconds for checks
            
        Returns:
            Dictionary with deliverability information
        """
        if not self.is_valid_email(email):
            return {"error": "Invalid email format", "deliverable": False}
            
        local, domain = email.split('@')
        
        result = {
            "email": email,
            "domain_exists": False,
            "mx_exists": False,
            "smtp_check": False,
            "deliverable_score": 0,
            "details": {}
        }
        
        try:
            # Check if domain exists (A record)
            dns.resolver.resolve(domain, 'A')
            result["domain_exists"] = True
            result["deliverable_score"] += 30
            
        except Exception as e:
            result["details"]["domain_error"] = str(e)
            
        try:
            # Check MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            result["mx_exists"] = True
            result["deliverable_score"] += 40
            result["details"]["mx_records"] = [str(record) for record in mx_records]
            
            # Try SMTP connection (basic check)
            if mx_records:
                mx_server = str(mx_records[0].exchange)
                try:
                    server = smtplib.SMTP(timeout=timeout)
                    server.connect(mx_server, 25)
                    server.helo()
                    code, message = server.rcpt(email)
                    server.quit()
                    
                    if code == 250:
                        result["smtp_check"] = True
                        result["deliverable_score"] += 30
                    elif code in [450, 451, 452]:  # Temporary failure
                        result["deliverable_score"] += 15
                        result["details"]["smtp_note"] = "Temporary failure"
                        
                except Exception as e:
                    result["details"]["smtp_error"] = str(e)
                    
        except Exception as e:
            result["details"]["mx_error"] = str(e)
            
        # Determine deliverability
        if result["deliverable_score"] >= 70:
            result["deliverable"] = True
        elif result["deliverable_score"] >= 40:
            result["deliverable"] = "maybe"
        else:
            result["deliverable"] = False
            
        return result
        
    def extract_emails_from_text(self, text: str) -> List[str]:
        """
        Extract email addresses from text
        
        Args:
            text: Text to search for email addresses
            
        Returns:
            List of unique email addresses found
        """
        # More comprehensive email regex for extraction
        email_regex = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        emails = email_regex.findall(text)
        
        # Validate and deduplicate
        valid_emails = []
        for email in emails:
            if self.is_valid_email(email) and email not in valid_emails:
                valid_emails.append(email)
                
        return valid_emails
        
    def normalize_email(self, email: str) -> str:
        """
        Normalize email address (lowercase, trim)
        
        Args:
            email: Email address to normalize
            
        Returns:
            Normalized email address
        """
        if not email:
            return ""
            
        return email.strip().lower()
        
    def generate_email_variations(self, email: str) -> List[str]:
        """
        Generate common variations of an email address
        
        Args:
            email: Base email address
            
        Returns:
            List of email variations
        """
        if not self.is_valid_email(email):
            return []
            
        local, domain = email.split('@')
        variations = [email]
        
        # Add variations with different separators
        if '.' in local:
            # Replace dots with underscores
            variations.append(local.replace('.', '_') + '@' + domain)
            # Remove dots
            variations.append(local.replace('.', '') + '@' + domain)
            
        if '_' in local:
            # Replace underscores with dots
            variations.append(local.replace('_', '.') + '@' + domain)
            # Remove underscores
            variations.append(local.replace('_', '') + '@' + domain)
            
        # Add common number variations
        if not re.search(r'\d', local):
            for num in ['1', '01', '2024', '2025']:
                variations.append(local + num + '@' + domain)
                variations.append(local + '.' + num + '@' + domain)
                variations.append(local + '_' + num + '@' + domain)
                
        # Remove duplicates and invalid emails
        unique_variations = []
        for var in variations:
            if self.is_valid_email(var) and var not in unique_variations:
                unique_variations.append(var)
                
        return unique_variations
        
    def is_business_email(self, email: str) -> bool:
        """
        Determine if email appears to be a business/corporate email
        
        Args:
            email: Email address to check
            
        Returns:
            True if likely business email, False otherwise
        """
        if not self.is_valid_email(email):
            return False
            
        domain = email.split('@')[1].lower()
        
        # Not a business email if it's a common personal provider
        personal_providers = {
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'live.com', 'msn.com', 'aol.com', 'icloud.com',
            'me.com', 'mac.com'
        }
        
        if domain in personal_providers:
            return False
            
        # Likely business if it's not a common personal provider
        # and has a proper domain structure
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            return True
            
        return False
        
    def get_email_reputation(self, email: str) -> Dict[str, any]:
        """
        Get reputation information for email address
        
        Args:
            email: Email address to check
            
        Returns:
            Dictionary with reputation information
        """
        if not self.is_valid_email(email):
            return {"error": "Invalid email format"}
            
        domain = email.split('@')[1].lower()
        
        reputation = {
            "email": email,
            "domain": domain,
            "is_disposable": domain in self.disposable_domains,
            "is_business": self.is_business_email(email),
            "provider": self.email_providers.get(domain, "Unknown"),
            "risk_score": 0,
            "risk_factors": []
        }
        
        # Calculate risk score
        if reputation["is_disposable"]:
            reputation["risk_score"] += 50
            reputation["risk_factors"].append("Disposable email domain")
            
        if not reputation["is_business"] and domain not in self.email_providers:
            reputation["risk_score"] += 20
            reputation["risk_factors"].append("Unknown email provider")
            
        # Check domain age and other factors could be added here
        # with additional APIs or databases
        
        # Determine overall risk level
        if reputation["risk_score"] >= 70:
            reputation["risk_level"] = "high"
        elif reputation["risk_score"] >= 40:
            reputation["risk_level"] = "medium"
        else:
            reputation["risk_level"] = "low"
            
        return reputation
        
    def batch_validate_emails(self, emails: List[str]) -> Dict[str, Dict]:
        """
        Validate multiple email addresses
        
        Args:
            emails: List of email addresses to validate
            
        Returns:
            Dictionary mapping emails to their validation results
        """
        results = {}
        
        for email in emails:
            try:
                results[email] = self.extract_email_info(email)
            except Exception as e:
                results[email] = {"error": str(e), "is_valid": False}
                
        return results
        
    def find_similar_emails(self, email: str, email_list: List[str]) -> List[Dict]:
        """
        Find similar email addresses in a list
        
        Args:
            email: Target email address
            email_list: List of emails to compare against
            
        Returns:
            List of similar emails with similarity scores
        """
        if not self.is_valid_email(email):
            return []
            
        similar_emails = []
        target_local = email.split('@')[0].lower()
        target_domain = email.split('@')[1].lower()
        
        for candidate in email_list:
            if not self.is_valid_email(candidate) or candidate.lower() == email.lower():
                continue
                
            candidate_local = candidate.split('@')[0].lower()
            candidate_domain = candidate.split('@')[1].lower()
            
            similarity_score = 0
            similarity_factors = []
            
            # Domain similarity
            if candidate_domain == target_domain:
                similarity_score += 50
                similarity_factors.append("Same domain")
            elif candidate_domain.split('.')[-1] == target_domain.split('.')[-1]:
                similarity_score += 20
                similarity_factors.append("Same TLD")
                
            # Local part similarity
            if candidate_local == target_local:
                similarity_score += 50
                similarity_factors.append("Identical local part")
            else:
                # Check for partial matches
                if candidate_local in target_local or target_local in candidate_local:
                    similarity_score += 30
                    similarity_factors.append("Partial local part match")
                    
                # Check for common variations
                if (candidate_local.replace('.', '') == target_local.replace('.', '') or
                    candidate_local.replace('_', '') == target_local.replace('_', '')):
                    similarity_score += 40
                    similarity_factors.append("Similar local part (punctuation difference)")
                    
            if similarity_score >= 30:  # Minimum threshold
                similar_emails.append({
                    "email": candidate,
                    "similarity_factors": similarity_factors
                    "similarity_score": similarity_score,
                })
                
        # Sort by similarity score
        similar_emails.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_emails[:10]  # Return top 10 matches