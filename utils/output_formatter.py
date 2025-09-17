"""
Output Formatter Utility Module
Handles formatting and saving OSINT results in various formats
"""

import json
import csv
import xml.etree.ElementTree as ET
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd


class OutputFormatter:
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xml', 'txt', 'html', 'xlsx']
        
    def save_results(self, results: Dict, filename: str, format_type: str = 'json') -> str:
        """
        Save results in specified format
        
        Args:
            results: Dictionary containing search results
            filename: Output filename (without extension)
            format_type: Output format ('json', 'csv', 'xml', 'txt', 'html', 'xlsx')
            
        Returns:
            Full path of saved file
        """
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")
            
        # Ensure results directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else "results", exist_ok=True)
        
        # Add extension if not present
        if not filename.endswith(f".{format_type}"):
            filename = f"{filename}.{format_type}"
            
        try:
            if format_type == 'json':
                return self._save_json(results, filename)
            elif format_type == 'csv':
                return self._save_csv(results, filename)
            elif format_type == 'xml':
                return self._save_xml(results, filename)
            elif format_type == 'txt':
                return self._save_txt(results, filename)
            elif format_type == 'html':
                return self._save_html(results, filename)
            elif format_type == 'xlsx':
                return self._save_xlsx(results, filename)
                
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")
            raise
            
    def _save_json(self, results: Dict, filename: str) -> str:
        """Save results as JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
        logging.info(f"Results saved to JSON: {filename}")
        return filename
        
    def _save_csv(self, results: Dict, filename: str) -> str:
        """Save results as CSV"""
        # Flatten the results for CSV format
        rows = []
        
        email = results.get('email', 'Unknown')
        timestamp = results.get('timestamp', '')
        
        for platform_type, platform_results in results.get('results', {}).items():
            for result in platform_results:
                row = {
                    'email': email,
                    'timestamp': timestamp,
                    'platform_type': platform_type,
                    'platform_name': result.get('platform', ''),
                    'platform_url': result.get('url', ''),
                    'status': result.get('status', ''),
                    'error': result.get('error', ''),
                    'matches_count': len(result.get('matches', [])),
                    'details': json.dumps(result.get('details', {})),
                    'first_match': ''
                }
                
                # Add first match details if available
                if result.get('matches'):
                    first_match = result['matches'][0]
                    row['first_match'] = json.dumps(first_match)
                    
                rows.append(row)
                
        # Write CSV
        if rows:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        else:
            # Write empty CSV with headers
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['email', 'timestamp', 'platform_type', 'platform_name', 'status', 'message'])
                writer.writerow([email, timestamp, 'No results', '', 'no_data', 'No platforms returned results'])
                
        logging.info(f"Results saved to CSV: {filename}")
        return filename
        
    def _save_xml(self, results: Dict, filename: str) -> str:
        """Save results as XML"""
        root = ET.Element('osint_results')
        
        # Add metadata
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'email').text = results.get('email', '')
        ET.SubElement(metadata, 'timestamp').text = str(results.get('timestamp', ''))
        ET.SubElement(metadata, 'platforms_searched').text = ', '.join(results.get('platforms_searched', []))
        
        # Add summary
        summary_data = results.get('summary', {})
        summary = ET.SubElement(root, 'summary')
        for key, value in summary_data.items():
            ET.SubElement(summary, key).text = str(value)
            
        # Add platform results
        platforms = ET.SubElement(root, 'platforms')
        
        for platform_type, platform_results in results.get('results', {}).items():
            platform_type_elem = ET.SubElement(platforms, 'platform_type', name=platform_type)
            
            for result in platform_results:
                platform_elem = ET.SubElement(platform_type_elem, 'platform')
                
                # Add basic info
                ET.SubElement(platform_elem, 'name').text = result.get('platform', '')
                ET.SubElement(platform_elem, 'url').text = result.get('url', '')
                ET.SubElement(platform_elem, 'status').text = result.get('status', '')
                
                if result.get('error'):
                    ET.SubElement(platform_elem, 'error').text = result.get('error', '')
                    
                # Add matches
                if result.get('matches'):
                    matches_elem = ET.SubElement(platform_elem, 'matches')
                    for match in result['matches']:
                        match_elem = ET.SubElement(matches_elem, 'match')
                        for key, value in match.items():
                            ET.SubElement(match_elem, key).text = str(value)
                            
        # Write XML file
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        
        logging.info(f"Results saved to XML: {filename}")
        return filename
        
    def _save_txt(self, results: Dict, filename: str) -> str:
        """Save results as plain text"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EMAIL OSINT SEARCH RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            # Metadata
            f.write(f"Email: {results.get('email', 'Unknown')}\n")
            f.write(f"Timestamp: {results.get('timestamp', 'Unknown')}\n")
            f.write(f"Platforms Searched: {', '.join(results.get('platforms_searched', []))}\n\n")
            
            # Summary
            summary = results.get('summary', {})
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Platforms Searched: {summary.get('total_platforms_searched', 0)}\n")
            f.write(f"Platforms with Hits: {summary.get('platforms_with_hits', 0)}\n")
            f.write(f"Platforms with Errors: {summary.get('platforms_with_errors', 0)}\n")
            f.write(f"Hit Rate: {summary.get('hit_rate_percentage', 0):.2f}%\n\n")
            
            # Platform results
            for platform_type, platform_results in results.get('results', {}).items():
                f.write(f"{platform_type.upper()} RESULTS\n")
                f.write("-" * 40 + "\n")
                
                for result in platform_results:
                    f.write(f"Platform: {result.get('platform', 'Unknown')}\n")
                    f.write(f"URL: {result.get('url', 'Unknown')}\n")
                    f.write(f"Status: {result.get('status', 'Unknown')}\n")
                    
                    if result.get('error'):
                        f.write(f"Error: {result.get('error', '')}\n")
                        
                    if result.get('matches'):
                        f.write(f"Matches Found: {len(result['matches'])}\n")
                        for i, match in enumerate(result['matches'], 1):
                            f.write(f"  Match {i}:\n")
                            for key, value in match.items():
                                f.write(f"    {key}: {value}\n")
                                
                    f.write("\n")
                    
                f.write("\n")
                
        logging.info(f"Results saved to TXT: {filename}")
        return filename
        
    def _save_html(self, results: Dict, filename: str) -> str:
        """Save results as HTML"""
        email = results.get('email', 'Unknown')
        timestamp = results.get('timestamp', 'Unknown')
        summary = results.get('summary', {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Email Results - {email}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        .summary-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }}
        .summary-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}
        .platform-section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .platform-header {{
            background: #343a40;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .platform-result {{
            padding: 20px;
            border-bottom: 1px solid #eee;
        }}
        .platform-result:last-child {{
            border-bottom: none;
        }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-found {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status-not-found {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .status-error {{
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }}
        .status-potential-match {{
            background: #cce7ff;
            color: #004085;
            border: 1px solid #99d6ff;
        }}
        .matches {{
            margin-top: 15px;
        }}
        .match {{
            background: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .error-message {{
            color: #dc3545;
            font-style: italic;
            margin-top: 10px;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metadata-item {{
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Email OSINT Results</h1>
        <div class="metadata">
            <div class="metadata-item">
                <strong>📧 Email:</strong> {email}
            </div>
            <div class="metadata-item">
                <strong>⏰ Timestamp:</strong> {timestamp}
            </div>
            <div class="metadata-item">
                <strong>🔎 Platforms:</strong> {', '.join(results.get('platforms_searched', []))}
            </div>
        </div>
    </div>
    
    <div class="summary">
        <h2>📊 Search Summary</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <span class="summary-number">{summary.get('total_platforms_searched', 0)}</span>
                Total Platforms
            </div>
            <div class="summary-item">
                <span class="summary-number">{summary.get('platforms_with_hits', 0)}</span>
                Hits Found
            </div>
            <div class="summary-item">
                <span class="summary-number">{summary.get('platforms_with_errors', 0)}</span>
                Errors
            </div>
            <div class="summary-item">
                <span class="summary-number">{summary.get('hit_rate_percentage', 0):.1f}%</span>
                Success Rate
            </div>
        </div>
    </div>
"""
        
        # Add platform results
        for platform_type, platform_results in results.get('results', {}).items():
            html_content += f"""
    <div class="platform-section">
        <div class="platform-header">
            {platform_type.replace('_', ' ').title()} Results
        </div>
"""
            
            for result in platform_results:
                status = result.get('status', 'unknown')
                status_class = f"status-{status.replace('_', '-')}"
                
                html_content += f"""
        <div class="platform-result">
            <h3>{result.get('platform', 'Unknown Platform')}</h3>
            <p><strong>URL:</strong> <a href="https://{result.get('url', '')}" target="_blank">{result.get('url', 'Unknown')}</a></p>
            <p><strong>Status:</strong> <span class="status {status_class}">{status}</span></p>
"""
                
                if result.get('error'):
                    html_content += f'<div class="error-message">❌ Error: {result["error"]}</div>'
                    
                if result.get('matches'):
                    html_content += f'<div class="matches"><h4>🎯 Matches Found ({len(result["matches"])}):</h4>'
                    
                    for i, match in enumerate(result['matches'], 1):
                        html_content += f'<div class="match"><strong>Match {i}:</strong><br>'
                        for key, value in match.items():
                            if key == 'url' and value.startswith('http'):
                                html_content += f'<strong>{key.title()}:</strong> <a href="{value}" target="_blank">{value[:100]}...</a><br>'
                            else:
                                display_value = str(value)[:200] + ('...' if len(str(value)) > 200 else '')
                                html_content += f'<strong>{key.title()}:</strong> {display_value}<br>'
                        html_content += '</div>'
                    
                    html_content += '</div>'
                    
                html_content += '</div>'
                
            html_content += '</div>'
            
        html_content += """
    <div class="footer">
        <p>Generated by Advanced Email OSINT Tool | September 2025</p>
        <p>⚠️ This report is for legitimate research purposes only</p>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logging.info(f"Results saved to HTML: {filename}")
        return filename
        
    def _save_xlsx(self, results: Dict, filename: str) -> str:
        """Save results as Excel file with multiple sheets"""
        try:
            import pandas as pd
        except ImportError:
            logging.error("pandas required for Excel output. Install with: pip install pandas openpyxl")
            raise ImportError("pandas required for Excel output")
            
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = results.get('summary', {})
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed results sheet
            rows = []
            email = results.get('email', 'Unknown')
            timestamp = results.get('timestamp', '')
            
            for platform_type, platform_results in results.get('results', {}).items():
                for result in platform_results:
                    base_row = {
                        'email': email,
                        'timestamp': timestamp,
                        'platform_type': platform_type,
                        'platform_name': result.get('platform', ''),
                        'platform_url': result.get('url', ''),
                        'status': result.get('status', ''),
                        'error': result.get('error', ''),
                        'matches_count': len(result.get('matches', []))
                    }
                    
                    if result.get('matches'):
                        for i, match in enumerate(result['matches']):
                            row = base_row.copy()
                            row['match_number'] = i + 1
                            row.update({f'match_{k}': v for k, v in match.items()})
                            rows.append(row)
                    else:
                        rows.append(base_row)
                        
            if rows:
                results_df = pd.DataFrame(rows)
                results_df.to_excel(writer, sheet_name='Detailed Results', index=False)
                
            # Platform-specific sheets
            for platform_type, platform_results in results.get('results', {}).items():
                platform_rows = []
                for result in platform_results:
                    platform_rows.append({
                        'platform_name': result.get('platform', ''),
                        'platform_url': result.get('url', ''),
                        'status': result.get('status', ''),
                        'error': result.get('error', ''),
                        'matches_found': len(result.get('matches', [])),
                        'details': str(result.get('details', {}))
                    })
                    
                if platform_rows:
                    platform_df = pd.DataFrame(platform_rows)
                    sheet_name = platform_type.title()[:31]  # Excel sheet name limit
                    platform_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
        logging.info(f"Results saved to Excel: {filename}")
        return filename
        
    def create_summary_report(self, results: Dict) -> str:
        """Create a summary report string"""
        email = results.get('email', 'Unknown')
        summary = results.get('summary', {})
        
        report = f"""
EMAIL OSINT SUMMARY REPORT
==========================

Target Email: {email}
Search Date: {results.get('timestamp', 'Unknown')}

OVERVIEW
--------
• Total Platforms Searched: {summary.get('total_platforms_searched', 0)}
• Platforms with Hits: {summary.get('platforms_with_hits', 0)}
• Platforms with Errors: {summary.get('platforms_with_errors', 0)}
• Success Rate: {summary.get('hit_rate_percentage', 0):.2f}%

PLATFORM BREAKDOWN
------------------
"""
        
        for platform_type, platform_results in results.get('results', {}).items():
            hits = sum(1 for r in platform_results if r.get('status') == 'found')
            total = len(platform_results)
            
            report += f"{platform_type.title()}: {hits}/{total} hits\n"
            
        return report
        
    def export_matches_only(self, results: Dict, filename: str) -> str:
        """Export only the matches to a JSON file"""
        matches_data = {
            "email": results.get('email'),
            "timestamp": results.get('timestamp'),
            "matches": []
        }
        
        for platform_type, platform_results in results.get('results', {}).items():
            for result in platform_results:
                if result.get('status') == 'found' and result.get('matches'):
                    for match in result['matches']:
                        match_entry = {
                            "platform_type": platform_type,
                            "platform_name": result.get('platform'),
                            "platform_url": result.get('url'),
                            "match_data": match
                        }
                        matches_data["matches"].append(match_entry)
                        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, indent=2, ensure_ascii=False, default=str)
            
        logging.info(f"Matches exported to: {filename}")
        return filename