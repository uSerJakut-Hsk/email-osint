"""
Unit tests for the OutputFormatter utility module
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch
import json
import csv
import xml.etree.ElementTree as ET
import tempfile
import os
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.output_formatter import OutputFormatter


class TestOutputFormatter:
    
    @pytest.fixture
    def formatter(self):
        """Create OutputFormatter instance"""
        return OutputFormatter()
    
    @pytest.fixture
    def sample_results(self):
        """Sample search results for testing"""
        return {
            "email": "test@example.com",
            "timestamp": "2025-09-16T14:30:22",
            "platforms_searched": ["marketplaces", "discussions"],
            "results": {
                "marketplaces": [
                    {
                        "platform": "eBay",
                        "url": "ebay.com",
                        "email": "test@example.com",
                        "timestamp": 1694874622.0,
                        "status": "found",
                        "details": {"search_url": "https://google.com/search?q=site:ebay.com+test@example.com"},
                        "matches": [
                            {
                                "title": "User Profile",
                                "url": "https://ebay.com/usr/testuser",
                                "snippet": "Profile for test@example.com"
                            }
                        ]
                    },
                    {
                        "platform": "Amazon",
                        "url": "amazon.com",
                        "email": "test@example.com",
                        "timestamp": 1694874622.0,
                        "status": "not_found",
                        "details": {"search_url": "https://google.com/search?q=site:amazon.com+test@example.com"},
                        "matches": []
                    }
                ],
                "discussions": [
                    {
                        "platform": "Reddit",
                        "url": "reddit.com",
                        "email": "test@example.com",
                        "timestamp": 1694874622.0,
                        "status": "error",
                        "details": {},
                        "matches": [],
                        "error": "HTTP 429"
                    }
                ]
            },
            "summary": {
                "total_platforms_searched": 3,
                "platforms_with_hits": 1,
                "platforms_with_errors": 1,
                "hit_rate_percentage": 33.33
            }
        }
    
    def test_formatter_initialization(self, formatter):
        """Test OutputFormatter initialization"""
        assert formatter is not None
        assert 'json' in formatter.supported_formats
        assert 'csv' in formatter.supported_formats
        assert 'xml' in formatter.supported_formats
        assert 'html' in formatter.supported_formats
    
    def test_save_results_json(self, formatter, sample_results):
        """Test saving results as JSON"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.json', ''), 'json')
            
            assert os.path.exists(result_file)
            assert result_file.endswith('.json')
            
            # Verify content
            with open(result_file, 'r') as f:
                loaded_data = json.load(f)
                assert loaded_data['email'] == 'test@example.com'
                assert 'summary' in loaded_data
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    def test_save_results_csv(self, formatter, sample_results):
        """Test saving results as CSV"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.csv', ''), 'csv')
            
            assert os.path.exists(result_file)
            assert result_file.endswith('.csv')
            
            # Verify content
            with open(result_file, 'r') as f:
                csv_reader = csv.DictReader(f)
                rows = list(csv_reader)
                assert len(rows) > 0
                
                # Check headers
                expected_headers = ['email', 'platform_type', 'platform_name', 'status']
                for header in expected_headers:
                    assert header in csv_reader.fieldnames
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    def test_save_results_xml(self, formatter, sample_results):
        """Test saving results as XML"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.xml', ''), 'xml')
            
            assert os.path.exists(result_file)
            assert result_file.endswith('.xml')
            
            # Verify content
            tree = ET.parse(result_file)
            root = tree.getroot()
            assert root.tag == 'osint_results'
            
            # Check for main sections
            metadata = root.find('metadata')
            assert metadata is not None
            assert metadata.find('email').text == 'test@example.com'
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    def test_save_results_txt(self, formatter, sample_results):
        """Test saving results as TXT"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.txt', ''), 'txt')
            
            assert os.path.exists(result_file)
            assert result_file.endswith('.txt')
            
            # Verify content
            with open(result_file, 'r') as f:
                content = f.read()
                assert 'EMAIL OSINT SEARCH RESULTS' in content
                assert 'test@example.com' in content
                assert 'SUMMARY' in content
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    def test_save_results_html(self, formatter, sample_results):
        """Test saving results as HTML"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.html', ''), 'html')
            
            assert os.path.exists(result_file)
            assert result_file.endswith('.html')
            
            # Verify content
            with open(result_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert '<!DOCTYPE html>' in content
                assert 'test@example.com' in content
                assert 'Email OSINT Results' in content
                assert 'summary-grid' in content  # CSS class
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    @patch('pandas.ExcelWriter')
    def test_save_results_xlsx(self, mock_excel_writer, formatter, sample_results):
        """Test saving results as Excel"""
        mock_writer = Mock()
        mock_excel_writer.return_value.__enter__ = Mock(return_value=mock_writer)
        mock_excel_writer.return_value.__exit__ = Mock(return_value=None)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlsx') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.xlsx', ''), 'xlsx')
            
            assert result_file.endswith('.xlsx')
            mock_excel_writer.assert_called_once()
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_save_results_unsupported_format(self, formatter, sample_results):
        """Test saving results with unsupported format"""
        with pytest.raises(ValueError) as exc_info:
            formatter.save_results(sample_results, "test", "unsupported")
        
        assert "Unsupported format" in str(exc_info.value)
    
    def test_create_summary_report(self, formatter, sample_results):
        """Test creating summary report"""
        report = formatter.create_summary_report(sample_results)
        
        assert isinstance(report, str)
        assert 'EMAIL OSINT SUMMARY REPORT' in report
        assert 'test@example.com' in report
        assert 'Total Platforms Searched: 3' in report
        assert 'Success Rate: 33.33%' in report
        assert 'Marketplaces: 1/2' in report
    
    def test_export_matches_only(self, formatter, sample_results):
        """Test exporting only matches"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.export_matches_only(sample_results, temp_file)
            
            assert os.path.exists(result_file)
            
            # Verify content
            with open(result_file, 'r') as f:
                matches_data = json.load(f)
                assert matches_data['email'] == 'test@example.com'
                assert 'matches' in matches_data
                assert len(matches_data['matches']) == 1  # Only eBay had matches
                
                match = matches_data['matches'][0]
                assert match['platform_name'] == 'eBay'
                assert match['platform_type'] == 'marketplaces'
                assert 'match_data' in match
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_save_results_with_extension(self, formatter, sample_results):
        """Test saving results with filename that already has extension"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name  # Already has .json extension
        
        try:
            result_file = formatter.save_results(sample_results, temp_file, 'json')
            
            assert result_file == temp_file
            assert os.path.exists(result_file)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_save_results_creates_directory(self, formatter, sample_results):
        """Test that save_results creates output directory if it doesn't exist"""
        import shutil
        
        test_dir = tempfile.mkdtemp()
        subdir_path = os.path.join(test_dir, 'new_subdir', 'test_results')
        
        try:
            result_file = formatter.save_results(sample_results, subdir_path, 'json')
            
            assert os.path.exists(result_file)
            assert os.path.dirname(result_file) == os.path.dirname(subdir_path + '.json')
            
        finally:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
    
    def test_empty_results_handling(self, formatter):
        """Test handling of empty results"""
        empty_results = {
            "email": "test@example.com",
            "timestamp": "2025-09-16T14:30:22", 
            "platforms_searched": [],
            "results": {},
            "summary": {
                "total_platforms_searched": 0,
                "platforms_with_hits": 0,
                "platforms_with_errors": 0,
                "hit_rate_percentage": 0.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # Should handle empty results gracefully
            result_file = formatter.save_results(empty_results, temp_file.replace('.json', ''), 'json')
            
            assert os.path.exists(result_file)
            
            with open(result_file, 'r') as f:
                loaded_data = json.load(f)
                assert loaded_data['email'] == 'test@example.com'
                assert loaded_data['summary']['total_platforms_searched'] == 0
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)


class TestOutputFormatterCSV:
    """Specific tests for CSV output functionality"""
    
    @pytest.fixture
    def formatter(self):
        return OutputFormatter()
    
    def test_csv_with_no_results(self, formatter):
        """Test CSV generation with no results"""
        no_results = {
            "email": "test@example.com",
            "timestamp": "2025-09-16T14:30:22",
            "platforms_searched": ["marketplaces"],
            "results": {},
            "summary": {"total_platforms_searched": 0}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(no_results, temp_file.replace('.csv', ''), 'csv')
            
            assert os.path.exists(result_file)
            
            with open(result_file, 'r') as f:
                csv_reader = csv.reader(f)
                rows = list(csv_reader)
                assert len(rows) >= 1  # At least header
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    def test_csv_with_multiple_matches(self, formatter):
        """Test CSV generation with multiple matches per platform"""
        results_with_matches = {
            "email": "test@example.com",
            "timestamp": "2025-09-16T14:30:22",
            "platforms_searched": ["marketplaces"],
            "results": {
                "marketplaces": [
                    {
                        "platform": "eBay",
                        "url": "ebay.com",
                        "status": "found",
                        "matches": [
                            {"title": "Profile 1", "url": "url1"},
                            {"title": "Profile 2", "url": "url2"}
                        ],
                        "details": {}
                    }
                ]
            },
            "summary": {"total_platforms_searched": 1}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(results_with_matches, temp_file.replace('.csv', ''), 'csv')
            
            assert os.path.exists(result_file)
            
            with open(result_file, 'r') as f:
                csv_reader = csv.DictReader(f)
                rows = list(csv_reader)
                # Should have 2 rows (one for each match)
                assert len(rows) == 2
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)


class TestOutputFormatterHTML:
    """Specific tests for HTML output functionality"""
    
    @pytest.fixture
    def formatter(self):
        return OutputFormatter()
    
    def test_html_css_styling(self, formatter, sample_results):
        """Test that HTML output includes proper CSS styling"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.html', ''), 'html')
            
            with open(result_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for CSS classes and styling
                css_elements = [
                    '.header', '.summary', '.platform-section',
                    '.status-found', '.status-not-found', '.status-error',
                    'grid-template-columns', 'background: linear-gradient'
                ]
                
                for element in css_elements:
                    assert element in content
                    
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)
    
    def test_html_interactive_elements(self, formatter, sample_results):
        """Test HTML output includes interactive elements"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(sample_results, temp_file.replace('.html', ''), 'html')
            
            with open(result_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for interactive elements
                assert 'href=' in content  # Links
                assert 'target="_blank"' in content  # External links
                assert '🔍' in content  # Emojis
                assert 'summary-number' in content  # Statistics
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)


class TestOutputFormatterIntegration:
    """Integration tests for OutputFormatter"""
    
    def test_all_formats_work(self):
        """Test that all supported formats can be generated"""
        formatter = OutputFormatter()
        
        sample_results = {
            "email": "integration@test.com",
            "timestamp": "2025-09-16T14:30:22",
            "platforms_searched": ["marketplaces"],
            "results": {
                "marketplaces": [
                    {
                        "platform": "TestPlatform",
                        "url": "test.com",
                        "status": "found",
                        "matches": [{"title": "Test"}],
                        "details": {}
                    }
                ]
            },
            "summary": {"total_platforms_searched": 1}
        }
        
        temp_dir = tempfile.mkdtemp()
        successful_formats = []
        
        try:
            for fmt in formatter.supported_formats:
                try:
                    if fmt == 'xlsx':
                        # Skip XLSX in this test if pandas not available
                        continue
                    
                    filename = os.path.join(temp_dir, f"test_{fmt}")
                    result_file = formatter.save_results(sample_results, filename, fmt)
                    
                    assert os.path.exists(result_file)
                    assert os.path.getsize(result_file) > 0  # File not empty
                    successful_formats.append(fmt)
                    
                except Exception as e:
                    pytest.fail(f"Format {fmt} failed: {str(e)}")
            
            # Should have successfully created most formats
            assert len(successful_formats) >= 4
            
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_large_results_handling(self):
        """Test handling of large result sets"""
        formatter = OutputFormatter()
        
        # Create large result set
        large_results = {
            "email": "large@test.com",
            "timestamp": "2025-09-16T14:30:22",
            "platforms_searched": ["marketplaces"],
            "results": {
                "marketplaces": []
            },
            "summary": {"total_platforms_searched": 100}
        }
        
        # Add many platforms
        for i in range(100):
            platform_result = {
                "platform": f"Platform{i}",
                "url": f"platform{i}.com",
                "status": "found" if i % 3 == 0 else "not_found",
                "matches": [{"title": f"Match{j}", "url": f"url{j}"} for j in range(5)] if i % 3 == 0 else [],
                "details": {"search_url": f"https://example.com/search{i}"}
            }
            large_results["results"]["marketplaces"].append(platform_result)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            result_file = formatter.save_results(large_results, temp_file.replace('.json', ''), 'json')
            
            assert os.path.exists(result_file)
            
            # Verify we can read it back
            with open(result_file, 'r') as f:
                loaded_data = json.load(f)
                assert len(loaded_data["results"]["marketplaces"]) == 100
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(result_file):
                os.unlink(result_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])