#!/usr/bin/env python3
"""
Advanced Email OSINT Tool
Author: Security Researcher
Date: September 2025
Description: Comprehensive email OSINT tool for searching across marketplaces, forums, and Google platforms
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import concurrent.futures
import time

from utils.scraper import EmailScraper
from utils.proxy_manager import ProxyManager
from utils.output_formatter import OutputFormatter
from utils.email_validator import EmailValidator


class OSINTEmailTool:
    def __init__(self, config_path: str = "config/platforms.json"):
        self.config_path = config_path
        self.platforms = self.load_platforms()
        self.proxy_manager = ProxyManager("proxies.txt")
        self.scraper = EmailScraper(self.proxy_manager)
        self.formatter = OutputFormatter()
        self.validator = EmailValidator()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = "results/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{log_dir}/osint_email_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def load_platforms(self) -> Dict:
        """Load platform configurations from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file {self.config_path} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in {self.config_path}")
            sys.exit(1)
            
    def search_email(self, email: str, platforms: List[str] = None, max_workers: int = 5) -> Dict:
        """
        Search for email across specified platforms
        
        Args:
            email: Email address to search
            platforms: List of platform types to search (marketplaces, discussions, google)
            max_workers: Number of concurrent workers
            
        Returns:
            Dictionary containing search results
        """
        if not self.validator.is_valid_email(email):
            logging.error(f"Invalid email format: {email}")
            return {"error": "Invalid email format"}
            
        if platforms is None:
            platforms = ["marketplaces", "discussions", "google"]
            
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "platforms_searched": platforms,
            "results": {}
        }
        
        logging.info(f"Starting OSINT search for email: {email}")
        
        for platform_type in platforms:
            if platform_type not in self.platforms:
                logging.warning(f"Platform type '{platform_type}' not found in configuration")
                continue
                
            logging.info(f"Searching {platform_type}...")
            platform_results = self._search_platform_type(email, platform_type, max_workers)
            results["results"][platform_type] = platform_results
            
        results["summary"] = self._generate_summary(results["results"])
        
        logging.info(f"Search completed for {email}")
        return results
        
    def _search_platform_type(self, email: str, platform_type: str, max_workers: int) -> List[Dict]:
        """Search email across all platforms of a specific type"""
        platforms_list = self.platforms.get(platform_type, [])
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_platform = {
                executor.submit(self._search_single_platform, email, platform): platform
                for platform in platforms_list
            }
            
            for future in concurrent.futures.as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    logging.error(f"Error searching {platform.get('name', 'Unknown')}: {str(e)}")
                    results.append({
                        "platform": platform.get('name', 'Unknown'),
                        "url": platform.get('url', ''),
                        "status": "error",
                        "error": str(e)
                    })
                    
        return results
        
    def _search_single_platform(self, email: str, platform: Dict) -> Optional[Dict]:
        """Search for email on a single platform"""
        try:
            result = self.scraper.search_email_on_platform(email, platform)
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            return result
            
        except Exception as e:
            logging.error(f"Error searching {platform.get('name', 'Unknown')}: {str(e)}")
            return {
                "platform": platform.get('name', 'Unknown'),
                "url": platform.get('url', ''),
                "status": "error",
                "error": str(e)
            }
            
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of search results"""
        summary = {
            "total_platforms_searched": 0,
            "platforms_with_hits": 0,
            "platforms_with_errors": 0,
            "hit_rate_percentage": 0.0
        }
        
        for platform_type, platform_results in results.items():
            for result in platform_results:
                summary["total_platforms_searched"] += 1
                
                if result.get("status") == "found":
                    summary["platforms_with_hits"] += 1
                elif result.get("status") == "error":
                    summary["platforms_with_errors"] += 1
                    
        if summary["total_platforms_searched"] > 0:
            summary["hit_rate_percentage"] = (
                summary["platforms_with_hits"] / summary["total_platforms_searched"]
            ) * 100
            
        return summary
        
    def save_results(self, results: Dict, output_format: str = "json", 
                    custom_filename: str = None) -> str:
        """Save search results to file"""
        os.makedirs("results", exist_ok=True)
        
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_clean = results["email"].replace("@", "_at_").replace(".", "_")
            filename = f"results/osint_{email_clean}_{timestamp}"
            
        return self.formatter.save_results(results, filename, output_format)


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Email OSINT Tool - Search email across multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python osint_email.py --email user@example.com
  python osint_email.py --email user@example.com --platforms marketplaces discussions
  python osint_email.py --email user@example.com --output csv --workers 10
  python osint_email.py --email user@example.com --save-as custom_results.json
        """
    )
    
    parser.add_argument(
        "--email", "-e",
        required=True,
        help="Email address to search for"
    )
    
    parser.add_argument(
        "--platforms", "-p",
        nargs="+",
        choices=["marketplaces", "discussions", "google", "all"],
        default=["all"],
        help="Platform types to search (default: all)"
    )
    
    parser.add_argument(
        "--output", "-o",
        choices=["json", "csv", "xml", "txt"],
        default="json",
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5)"
    )
    
    parser.add_argument(
        "--save-as",
        help="Custom filename for output"
    )
    
    parser.add_argument(
        "--config",
        default="config/platforms.json",
        help="Path to platforms configuration file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Handle "all" platform selection
    if "all" in args.platforms:
        platforms = ["marketplaces", "discussions", "google"]
    else:
        platforms = args.platforms
        
    try:
        # Initialize OSINT tool
        osint_tool = OSINTEmailTool(args.config)
        
        # Perform search
        results = osint_tool.search_email(
            email=args.email,
            platforms=platforms,
            max_workers=args.workers
        )
        
        # Save results
        output_file = osint_tool.save_results(
            results=results,
            output_format=args.output,
            custom_filename=args.save_as
        )
        
        # Print summary
        summary = results.get("summary", {})
        print(f"\n{'='*60}")
        print(f"OSINT SEARCH SUMMARY FOR: {args.email}")
        print(f"{'='*60}")
        print(f"Total platforms searched: {summary.get('total_platforms_searched', 0)}")
        print(f"Platforms with hits: {summary.get('platforms_with_hits', 0)}")
        print(f"Platforms with errors: {summary.get('platforms_with_errors', 0)}")
        print(f"Hit rate: {summary.get('hit_rate_percentage', 0):.2f}%")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()