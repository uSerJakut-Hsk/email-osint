#!/usr/bin/env python3
"""
Unit Tests for Email Validator
Author: Security Researcher
Date: September 2025
"""

import unittest
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.email_validator import EmailValidator


class TestEmailValidator(unittest.TestCase):
    """Test cases for EmailValidator class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.validator = EmailValidator()
        
    def test_valid_emails(self):
        """Test validation of valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@example.org',
            'firstname+lastname@example.co.uk',
            'email@123.123.123.123',  # IP domain (valid format)
            'test_email@example-domain.com',
            '12345@example.com',
            'user@very-long-domain-name.com',
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(self.validator.is_valid_email(email))
                
    def test_invalid_emails(self):
        """Test validation of invalid email addresses"""
        invalid_emails = [
            '',  # Empty string
            'invalid',  # No @ symbol
            'invalid@',  # No domain
            '@invalid.com',  # No local part
            'invalid@.com',  # Invalid domain
            'invalid.@example.com',  # Dot at end of local part
            '.invalid@example.com',  # Dot at start of local part
            'invalid..email@example.com',  # Double dots
            'invalid@example.',  # Domain ends with dot
            'invalid@.example.com',  # Domain starts with dot
            'invalid@example..com',  # Double dots in domain
            'a' * 65 + '@example.com',  # Local part too long
            'test@' + 'a' * 250 + '.com',  # Total length too long
            'invalid email@example.com',  # Space in email
            'invalid@exam ple.com',  # Space in domain
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(self.validator.is_valid_email(email))
                
    def test_disposable_email_detection(self):
        """Test detection of disposable email domains"""
        disposable_emails = [
            'test@10minutemail.com',
            'user@mailinator.com',
            'temp@guerrillamail.com',
            'fake@yopmail.com'
        ]
        
        for email in disposable_emails:
            with self.subTest(email=email):
                result = self.validator.validate_email_advanced(email)
                self.assertTrue(result['checks']['disposable'])
                
    def test_email_variations_generation(self):
        """Test generation of email variations"""
        test_email = 'john.doe@example.com'
        variations = self.validator.generate_email_variations(test_email)
        
        # Should include original email
        self.assertIn(test_email, variations)
        
        # Should generate variations
        self.assertGreater(len(variations), 1)
        
        # Should generate dot removal
        self.assertIn('johndoe@example.com', variations)
        
        # Should generate numbered variations
        self.assertIn('john.doe1@example.com', variations)
        
        # All variations should be valid format
        for variation in variations:
            self.assertTrue(self.validator.is_valid_email(variation))
            
    def test_email_extraction_from_text(self):
        """Test extraction of emails from text"""
        text = """
        Contact us at support@example.com or sales@company.org
        You can also reach admin@test-site.co.uk
        Invalid emails like invalid@.com should be ignored
        """
        
        extracted = self.validator.extract_emails_from_text(text)
        
        # Should find 3 valid emails
        valid_emails = [e for e in extracted if e['valid_format']]
        self.assertEqual(len(valid_emails), 3)
        
        # Check specific emails were found
        found_emails = [e['email'] for e in valid_emails]
        self.assertIn('support@example.com', found_emails)
        self.assertIn('sales@company.org', found_emails)
        self.assertIn('admin@test-site.co.uk', found_emails)
        
    def test_email_provider_info(self):
        """Test email provider information retrieval"""
        # Test Gmail
        gmail_info = self.validator.get_email_provider_info('test@gmail.com')
        self.assertEqual(gmail_info['name'], 'Google Gmail')
        self.assertEqual(gmail_info['type'], 'Free')
        
        # Test unknown provider
        unknown_info = self.validator.get_email_provider_info('test@unknown-domain.com')
        self.assertIn('unknown-domain.com', unknown_info['name'].lower())
        
    def test_dns_validation_caching(self):
        """Test DNS validation caching"""
        domain = 'example.com'
        
        # First call should perform DNS lookup
        result1 = self.validator.validate_domain_dns(domain)
        
        # Second call should use cache
        result2 = self.validator.validate_domain_dns(domain)
        
        # Results should be identical
        self.assertEqual(result1, result2)
        
    def test_advanced_email_validation(self):
        """Test advanced email validation"""
        # Test valid email
        result = self.validator.validate_email_advanced('test@example.com')
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertIn('checks', result)
        self.assertIn('score', result)
        
        # Test invalid email
        result = self.validator.validate_email_advanced('invalid-email')
        self.assertFalse(result['valid'])
        self.assertFalse(result['checks']['format'])
        
    def test_email_list_validation(self):
        """Test validation of email lists"""
        email_list = [
            'valid1@example.com',
            'valid2@example.org',
            'invalid-email',
            'test@mailinator.com'  # disposable
        ]
        
        results = self.validator.validate_email_list(email_list)
        
        self.assertEqual(results['total_emails'], 4)
        self.assertGreaterEqual(results['valid_emails'], 2)
        self.assertGreaterEqual(results['invalid_emails'], 1)
        self.assertGreaterEqual(results['disposable_emails'], 1)
        self.assertIn('summary', results)
        
    def test_case_insensitivity(self):
        """Test that email validation is case insensitive"""
        emails = [
            'Test@Example.com',
            'TEST@EXAMPLE.COM',
            'test@example.com'
        ]
        
        for email in emails:
            self.assertTrue(self.validator.is_valid_email(email))
            
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test None input
        self.assertFalse(self.validator.is_valid_email(None))
        
        # Test empty string
        self.assertFalse(self.validator.is_valid_email(''))
        
        # Test whitespace
        self.assertFalse(self.validator.is_valid_email('  '))
        
        # Test maximum length email (should be valid)
        long_local = 'a' * 64
        long_domain = 'b' * 60 + '.com'
        long_email = f'{long_local}@{long_domain}'
        self.assertTrue(self.validator.is_valid_email(long_email))
        
    def test_international_domains(self):
        """Test international domain names"""
        # These should be valid format-wise
        international_emails = [
            'test@xn--fsq.com',  # Punycode domain
            'user@example.co.uk',
            'admin@site.org.au'
        ]
        
        for email in international_emails:
            self.assertTrue(self.validator.is_valid_email(email))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)