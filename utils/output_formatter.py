#!/usr/bin/env python3
"""
Output Formatter for Email OSINT Tool
Author: Security Researcher
Date: September 2025
"""

import json
import csv
import xml.etree.ElementTree as ET
import pandas as pd
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from xml.dom import minidom


class OutputFormatter:
    """Handles multiple output formats for search results"""
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xml', 'txt', 'html', 'xlsx']
        
    def save_results(self, results: Dict[str, Any], filename: str, format_type: str = 'json') -> str:
        """Save results in specified format"""
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.supported_formats}")
            
        # Ensure filename doesn't have extension
        base_filename = filename.rsplit('.', 1)[0]
        
        # Create results directory if it doesn't exist
        results_dir = os.path.dirname(base_filename) or 'results'
        os.makedirs(results_dir, exist_ok=True)
        
        # Format-specific saving
        if format_type == 'json':
            return self._save_json(results, base_filename)
        elif format_type == 'csv':
            return self._save_csv(results, base_filename)
        elif format_type == 'xml':
            return self._save_xml(results, base_filename)
        elif format_type == 'txt':
            return self._save_txt(results, base_filename)
        elif format_type == 'html':
            return self._save_html(results, base_filename)
        elif format_type == 'xlsx':
            return self._save_xlsx(results, base_filename)
        else:
            raise ValueError(f"Format {format_type} not implemented")
            
    def _save_json(self, results: Dict[str, Any], base_filename: str) -> str:
        """Save results as JSON"""
        filename = f"{base_filename}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                
            logging.info(f"Results saved to JSON: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error saving JSON: {e}")
            raise
            
    def _save_csv(self, results: Dict[str, Any], base_filename: str) -> str:
        """Save results as CSV"""
        filename = f"{base_filename}.csv"
        
        try:
            # Flatten results for CSV format
            flattened_data = self._flatten_results_for_tabular(results)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if flattened_data:
                    writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_data)
                else:
                    # Empty results
                    writer = csv.writer(f)
                    writer.writerow(['email', 'timestamp', 'status', 'message'])
                    writer.writerow([
                        results.get('email', ''), 
                        results.get('timestamp', ''), 
                        'no_results', 
                        'No matches found'
                    ])
                    
            logging.info(f"Results saved to CSV: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error saving CSV: {e}")
            raise
            
    def _save_xml(self, results: Dict[str, Any], base_filename: str) -> str:
        """Save results as XML"""
        filename = f"{base_filename}.xml"
        
        try:
            root = ET.Element('osint_results')
            
            # Add metadata
            metadata = ET.SubElement(root, 'metadata')
            ET.SubElement(metadata, 'email').text = results.get('email', '')
            ET.SubElement(metadata, 'timestamp').text = results.get('timestamp', '')
            ET.SubElement(metadata, 'tool_version').text = '1.0'
            
            # Add summary
            summary_data = results.get('summary', {})
            summary_elem = ET.SubElement(root, 'summary')
            for key, value in summary_data.items():
                ET.SubElement(summary_elem, key).text = str(value)
                
            # Add results
            results_elem = ET.SubElement(root, 'search_results')
            
            for platform_type, platform_results in results.get('results', {}).items():
                platform_elem = ET.SubElement(results_elem, 'platform_type', name=platform_type)
                
                for result in platform_results:
                    result_elem = ET.SubElement(platform_elem, 'result')
                    
                    # Add basic result info
                    ET.SubElement(result_elem, 'platform').text = result.get('platform', '')
                    ET.SubElement(result_elem, 'url').text = result.get('url', '')
                    ET.SubElement(result_elem, 'status').text = result.get('status', '')
                    ET.SubElement(result_elem, 'search_method').text = result.get('search_method', '')
                    ET.SubElement(result_elem, 'search_time').text = result.get('search_time', '')
                    
                    # Add matches
                    matches_elem = ET.SubElement(result_elem, 'matches')
                    for match in result.get('matches', []):
                        match_elem = ET.SubElement(matches_elem, 'match')
                        for key, value in match.items():
                            ET.SubElement(match_elem, key).text = str(value)
                            
                    # Add error if present
                    if result.get('error'):
                        ET.SubElement(result_elem, 'error').text = result.get('error', '')
                        
            # Pretty print XML
            xml_str = ET.tostring(root, encoding='unicode')
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
                
            logging.info(f"Results saved to XML: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error saving XML: {e}")
            raise
            
    def _save_txt(self, results: Dict[str, Any], base_filename: str) -> str:
        """Save results as plain text report"""
        filename = f"{base_filename}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Header
                f.write("="*80 + "\n")
                f.write("EMAIL OSINT INVESTIGATION REPORT\n")
                f.write("="*80 + "\n\n")
                
                # Basic info
                f.write(f"Target Email: {results.get('email', 'Unknown')}\n")
                f.write(f"Search Date: {results.get('timestamp', 'Unknown')}\n")
                f.write(f"Tool Version: 1.0 (September 2025)\n\n")
                
                # Summary
                summary = results.get('summary', {})
                f.write("SEARCH SUMMARY\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Platforms Searched: {summary.get('total_platforms_searched', 0)}\n")
                f.write(f"Platforms with Hits: {summary.get('platforms_with_hits', 0)}\n")
                f.write(f"Platforms with Errors: {summary.get('platforms_with_errors', 0)}\n")
                f.write(f"Success Rate: {summary.get('hit_rate_percentage', 0):.2f}%\n\n")
                
                # Detailed results
                f.write("DETAILED FINDINGS\n")
                f.write("-" * 40 + "\n\n")
                
                for platform_type, platform_results in results.get('results', {}).items():
                    f.write(f"[{platform_type.upper()}]\n")
                    f.write("="*60 + "\n")
                    
                    for result in platform_results:
                        status = result.get('status', 'unknown')
                        platform_name = result.get('platform', 'Unknown')
                        
                        if status == 'found':
                            f.write(f"✓ FOUND: {platform_name}\n")
                        elif status == 'potential_match':
                            f.write(f"? POTENTIAL: {platform_name}\n")
                        elif status == 'not_found':
                            f.write(f"✗ NOT FOUND: {platform_name}\n")
                        elif status == 'error':
                            f.write(f"! ERROR: {platform_name}\n")
                        else:
                            f.write(f"- UNKNOWN: {platform_name}\n")
                            
                        f.write(f"  URL: {result.get('url', 'N/A')}\n")
                        f.write(f"  Method: {result.get('search_method', 'N/A')}\n")
                        f.write(f"  Time: {result.get('search_time', 'N/A')}\n")
                        
                        # Show matches
                        matches = result.get('matches', [])
                        if matches:
                            f.write(f"  Matches: {len(matches)}\n")
                            for i, match in enumerate(matches[:3], 1):  # Show first 3 matches
                                f.write(f"    [{i}] {match.get('title', 'No title')}\n")
                                snippet = match.get('snippet', match.get('content', ''))
                                if snippet:
                                    f.write(f"        {snippet[:100]}{'...' if len(snippet) > 100 else ''}\n")
                                if match.get('url'):
                                    f.write(f"        URL: {match['url']}\n")
                                f.write(f"        Confidence: {match.get('confidence', 0):.2f}\n")
                                
                        # Show errors
                        if result.get('error'):
                            f.write(f"  Error: {result['error']}\n")
                            
                        f.write("\n")
                        
                    f.write("\n")
                    
                # Footer
                f.write("="*80 + "\n")
                f.write("Report generated by Advanced Email OSINT Tool v1.0\n")
                f.write("For educational and legitimate security research only\n")
                f.write("="*80 + "\n")
                
            logging.info(f"Results saved to TXT: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error saving TXT: {e}")
            raise
            
    def _save_html(self, results: Dict[str, Any], base_filename: str) -> str:
        """Save results as interactive HTML report"""
        filename = f"{base_filename}.html"
        
        try:
            html_content = self._generate_html_report(results)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logging.info(f"Results saved to HTML: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error saving HTML: {e}")
            raise
            
    def _save_xlsx(self, results: Dict[str, Any], base_filename: str) -> str:
        """Save results as Excel file"""
        filename = f"{base_filename}.xlsx"
        
        try:
            # Prepare data for Excel
            flattened_data = self._flatten_results_for_tabular(results)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = results.get('summary', {})
                summary_df = pd.DataFrame([summary_data]) if summary_data else pd.DataFrame()
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed results sheet
                if flattened_data:
                    df = pd.DataFrame(flattened_data)
                    df.to_excel(writer, sheet_name='Detailed Results', index=False)
                    
                # Platform breakdown
                platform_summary = []
                for platform_type, platform_results in results.get('results', {}).items():
                    hits = sum(1 for r in platform_results if r.get('status') == 'found')
                    potential = sum(1 for r in platform_results if r.get('status') == 'potential_match')
                    errors = sum(1 for r in platform_results if r.get('status') == 'error')
                    total = len(platform_results)
                    
                    platform_summary.append({
                        'Platform Type': platform_type,
                        'Total Searched': total,
                        'Hits': hits,
                        'Potential Matches': potential,
                        'Errors': errors,
                        'Success Rate': f"{(hits/total*100):.1f}%" if total > 0 else "0%"
                    })
                    
                if platform_summary:
                    platform_df = pd.DataFrame(platform_summary)
                    platform_df.to_excel(writer, sheet_name='Platform Breakdown', index=False)
                    
            logging.info(f"Results saved to Excel: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error saving Excel: {e}")
            raise
            
    def _flatten_results_for_tabular(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested results structure for tabular formats"""
        flattened = []
        
        email = results.get('email', '')
        timestamp = results.get('timestamp', '')
        
        for platform_type, platform_results in results.get('results', {}).items():
            for result in platform_results:
                base_row = {
                    'email': email,
                    'timestamp': timestamp,
                    'platform_type': platform_type,
                    'platform': result.get('platform', ''),
                    'url': result.get('url', ''),
                    'status': result.get('status', ''),
                    'search_method': result.get('search_method', ''),
                    'search_time': result.get('search_time', ''),
                    'error': result.get('error', ''),
                    'match_count': len(result.get('matches', []))
                }
                
                # If no matches, add the base row
                matches = result.get('matches', [])
                if not matches:
                    flattened.append(base_row)
                else:
                    # Add one row per match
                    for i, match in enumerate(matches):
                        row = base_row.copy()
                        row.update({
                            'match_index': i + 1,
                            'match_title': match.get('title', ''),
                            'match_url': match.get('url', ''),
                            'match_snippet': match.get('snippet', match.get('content', '')),
                            'match_confidence': match.get('confidence', 0),
                            'match_source': match.get('source', ''),
                        })
                        flattened.append(row)
                        
        return flattened
        
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate interactive HTML report"""
        email = results.get('email', 'Unknown')
        timestamp = results.get('timestamp', 'Unknown')
        summary = results.get('summary', {})
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email OSINT Report - {email}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.8;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .results-container {{
            padding: 30px;
        }}
        .platform-section {{
            margin-bottom: 40px;
        }}
        .platform-title {{
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
            display: flex;
            align-items: center;
        }}
        .platform-icon {{
            margin-right: 10px;
            font-size: 1.2em;
        }}
        .result-grid {{
            display: grid;
            gap: 20px;
        }}
        .result-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
        }}
        .result-card:hover {{
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            border-color: #3498db;
        }}
        .result-card.found {{
            border-left: 4px solid #27ae60;
        }}
        .result-card.potential {{
            border-left: 4px solid #f39c12;
        }}
        .result-card.not-found {{
            border-left: 4px solid #95a5a6;
        }}
        .result-card.error {{
            border-left: 4px solid #e74c3c;
        }}
        .result-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .platform-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-found {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        .status-potential {{
            background: #fef9e7;
            color: #f39c12;
        }}
        .status-not-found {{
            background: #f8f9fa;
            color: #95a5a6;
        }}
        .status-error {{
            background: #fdf2f2;
            color: #e74c3c;
        }}
        .matches {{
            margin-top: 15px;
        }}
        .match-item {{
            background: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .match-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        .match-snippet {{
            color: #7f8c8d;
            font-size: 0.9em;
            line-height: 1.4;
            margin-bottom: 8px;
        }}
        .match-url {{
            font-size: 0.8em;
            color: #3498db;
            word-break: break-all;
        }}
        .confidence {{
            float: right;
            font-size: 0.8em;
            background: #ecf0f1;
            padding: 2px 8px;
            border-radius: 10px;
            color: #2c3e50;
        }}
        .footer {{
            background: #34495e;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        .toggle-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .collapsible {{
            display: block;
        }}
        .collapsed {{
            display: none;
        }}
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
            }}
            .header {{
                padding: 20px;
            }}
            .header h1 {{
                font-size: 2em;
            }}
            .summary {{
                grid-template-columns: 1fr 1fr;
                padding: 20px;
            }}
            .results-container {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Email OSINT Report</h1>
            <p>Target: <strong>{email}</strong> | Generated: {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{summary.get('total_platforms_searched', 0)}</div>
                <div class="stat-label">Platforms Searched</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary.get('platforms_with_hits', 0)}</div>
                <div class="stat-label">Hits Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary.get('platforms_with_errors', 0)}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary.get('hit_rate_percentage', 0):.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <div class="results-container">
"""

        # Add platform sections
        for platform_type, platform_results in results.get('results', {}).items():
            platform_icons = {
                'marketplaces': '🛒',
                'discussions': '💬',
                'google': '🌐'
            }
            
            icon = platform_icons.get(platform_type, '🔍')
            html_template += f"""
            <div class="platform-section">
                <div class="platform-title">
                    <span class="platform-icon">{icon}</span>
                    {platform_type.title()}
                    <button class="toggle-btn" onclick="toggleSection('{platform_type}')">Toggle</button>
                </div>
                <div id="{platform_type}" class="result-grid collapsible">
"""

            for result in platform_results:
                status = result.get('status', 'unknown')
                status_class = status.replace('_', '-')
                status_text = status.replace('_', ' ').title()
                
                html_template += f"""
                    <div class="result-card {status_class}">
                        <div class="result-header">
                            <div class="platform-name">{result.get('platform', 'Unknown')}</div>
                            <div class="status-badge status-{status_class}">{status_text}</div>
                        </div>
                        <div><strong>URL:</strong> {result.get('url', 'N/A')}</div>
                        <div><strong>Method:</strong> {result.get('search_method', 'N/A')}</div>
                        <div><strong>Time:</strong> {result.get('search_time', 'N/A')}</div>
"""

                # Add matches
                matches = result.get('matches', [])
                if matches:
                    html_template += '<div class="matches"><strong>Matches:</strong>'
                    for match in matches[:5]:  # Show first 5 matches
                        confidence = match.get('confidence', 0)
                        html_template += f"""
                        <div class="match-item">
                            <div class="match-title">
                                {match.get('title', 'No title')}
                                <span class="confidence">Confidence: {confidence:.2f}</span>
                            </div>
"""
                        if match.get('snippet') or match.get('content'):
                            snippet = match.get('snippet', match.get('content', ''))[:200]
                            html_template += f'<div class="match-snippet">{snippet}{"..." if len(snippet) == 200 else ""}</div>'
                            
                        if match.get('url'):
                            html_template += f'<div class="match-url">{match["url"]}</div>'
                            
                        html_template += '</div>'
                    html_template += '</div>'

                # Add error if present
                if result.get('error'):
                    html_template += f'<div><strong>Error:</strong> {result["error"]}</div>'

                html_template += '</div>'

            html_template += '</div></div>'

        # Close HTML
        html_template += """
        </div>
        
        <div class="footer">
            <p>Generated by Advanced Email OSINT Tool v1.0 (September 2025)</p>
            <p>For educational and legitimate security research purposes only</p>
        </div>
    </div>
    
    <script>
        function toggleSection(sectionId) {
            const section = document.getElementById(sectionId);
            if (section.classList.contains('collapsed')) {
                section.classList.remove('collapsed');
                section.classList.add('collapsible');
            } else {
                section.classList.remove('collapsible');
                section.classList.add('collapsed');
            }
        }
        
        // Add click handlers for result cards
        document.querySelectorAll('.result-card').forEach(card => {
            card.addEventListener('click', function() {
                const matches = this.querySelector('.matches');
                if (matches) {
                    matches.style.display = matches.style.display === 'none' ? 'block' : 'none';
                }
            });
        });
    </script>
</body>
</html>
"""

        return html_template