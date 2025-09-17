#!/usr/bin/env python3
"""
Advanced Email OSINT Tool - FIXED VERSION
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

# Import utilities with proper error handling
try:
    from utils.scraper import EmailScraper
    from utils.proxy_manager import ProxyManager
    from utils.output_formatter import OutputFormatter
    from utils.email_validator import EmailValidator
except ImportError as e:
    print(f"Error importing utilities: {e}")
    print("Please ensure all utility files are present in the utils/ directory")
    sys.exit(1)


class OSINTEmailTool:
    def __init__(self, config_path: str = "config/platforms.json"):
        self.config_path = config_path
        self.platforms = self.load_platforms()
        
        # Initialize components with error handling
        try:
            self.proxy_manager = ProxyManager("proxies.txt")
            self.scraper = EmailScraper(self.proxy_manager)
            self.formatter = OutputFormatter()
            self.validator = EmailValidator()
        except Exception as e:
            logging.error(f"Error initializing components: {e}")
            raise
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration with error handling"""
        try:
            log_dir = "results/logs"
            os.makedirs(log_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"{log_dir}/osint_email_{timestamp}.log"
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            # Suppress some noisy loggers
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('selenium').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
            
        except Exception as e:
            print(f"Warning: Could not setup logging: {e}")
            # Fallback to basic console logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        
    def load_platforms(self) -> Dict:
        """Load platform configurations from JSON file with error handling"""
        try:
            if not os.path.exists(self.config_path):
                logging.error(f"Configuration file {self.config_path} not found")
                # Create default config directory and file
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                self.create_default_config()
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                platforms = json.load(f)
                
            logging.info(f"Loaded {sum(len(p) for p in platforms.values())} platforms from configuration")
            return platforms
            
        except FileNotFoundError:
            logging.error(f"Configuration file {self.config_path} not found")
            return self.get_default_platforms()
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in {self.config_path}: {e}")
            return self.get_default_platforms()
        except Exception as e:
            logging.error(f"Error loading platforms: {e}")
            return self.get_default_platforms()
            
    def create_default_config(self):
        """Create a basic default configuration file"""
        default_config = {
            "marketplaces": [
                {
                    "name": "eBay",
                    "url": "ebay.com",
                    "login_required": True,
                    "search_endpoint": "/sch/i.html",
                    "category": "ecommerce"
                },
                {
                    "name": "Amazon",
                    "url": "amazon.com", 
                    "login_required": True,
                    "search_endpoint": "/s",
                    "category": "ecommerce"
                }
            ],
            "discussions": [
                {
                    "name": "Reddit",
                    "url": "reddit.com",
                    "login_required": False,
                    "search_endpoint": "/search",
                    "category": "forum"
                },
                {
                    "name": "Stack Overflow",
                    "url": "stackoverflow.com",
                    "login_required": False,
                    "search_endpoint": "/search",
                    "category": "tech_forum"
                }
            ],
            "google": [
                {
                    "name": "Google Search",
                    "url": "google.com/search",
                    "login_required": False,
                    "search_endpoint": "",
                    "category": "web_search"
                },
                {
                    "name": "YouTube",
                    "url": "youtube.com",
                    "login_required": False,
                    "search_endpoint": "/results",
                    "category": "video_platform"
                }
            ]
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logging.info(f"Created default configuration file: {self.config_path}")
        except Exception as e:
            logging.error(f"Could not create default config: {e}")
            
    def get_default_platforms(self) -> Dict:
        """Return minimal default platforms if config loading fails"""
        return {
            "marketplaces": [],
            "discussions": [],
            "google": [
                {
                    "name": "Google Search",
                    "url": "google.com/search",
                    "login_required": False,
                    "search_endpoint": "",
                    "category": "web_search"
                }
            ]
        }
            
    def search_email(self, email: str, platforms: List[str] = None, max_workers: int = 5) -> Dict:
        """
        Search for email across specified platforms with comprehensive error handling
        
        Args:
            email: Email address to search
            platforms: List of platform types to search (marketplaces, discussions, google)
            max_workers: Number of concurrent workers
            
        Returns:
            Dictionary containing search results
        """
        # Validate email first
        if not self.validator.is_valid_email(email):
            logging.error(f"Invalid email format: {email}")
            return {
                "error": "Invalid email format",
                "email": email,
                "timestamp": datetime.now().isoformat(),
                "valid": False
            }
            
        if platforms is None:
            platforms = ["marketplaces", "discussions", "google"]
            
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "platforms_searched": platforms,
            "results": {},
            "metadata": {
                "tool_version": "1.0",
                "search_method": "automated",
                "max_workers": max_workers
            }
        }
        
        logging.info(f"Starting OSINT search for email: {email}")
        logging.info(f"Platforms to search: {', '.join(platforms)}")
        
        # Email validation details
        try:
            validation_result = self.validator.validate_email_advanced(email)
            results["email_validation"] = validation_result
            logging.info(f"Email validation score: {validation_result.get('score', 0)}/100")
        except Exception as e:
            logging.warning(f"Email validation failed: {e}")
            
        for platform_type in platforms:
            if platform_type not in self.platforms:
                logging.warning(f"Platform type '{platform_type}' not found in configuration")
                continue
                
            platform_list = self.platforms[platform_type]
            if not platform_list:
                logging.warning(f"No platforms configured for type '{platform_type}'")
                continue
                
            logging.info(f"Searching {platform_type} ({len(platform_list)} platforms)...")
            
            try:
                platform_results = self._search_platform_type(email, platform_type, max_workers)
                results["results"][platform_type] = platform_results
                
                # Log immediate results
                hits = sum(1 for r in platform_results if r.get('status') == 'found')
                potential = sum(1 for r in platform_results if r.get('status') == 'potential_match')
                logging.info(f"Completed {platform_type}: {hits} hits, {potential} potential matches")
                
            except Exception as e:
                logging.error(f"Error searching {platform_type}: {e}")
                results["results"][platform_type] = [{
                    "platform": "Error",
                    "url": "",
                    "status": "error",
                    "error": f"Platform search failed: {str(e)}",
                    "search_time": datetime.now().isoformat()
                }]
                
        # Generate summary
        try:
            results["summary"] = self._generate_summary(results["results"])
            logging.info(f"Search completed for {email}")
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            results["summary"] = {"error": "Could not generate summary"}
            
        return results
        
    def _search_platform_type(self, email: str, platform_type: str, max_workers: int) -> List[Dict]:
        """Search email across all platforms of a specific type with improved error handling"""
        platforms_list = self.platforms.get(platform_type, [])
        results = []
        
        # Limit workers to reasonable number
        max_workers = min(max_workers, len(platforms_list), 10)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_platform = {}
            for platform in platforms_list:
                try:
                    future = executor.submit(self._search_single_platform_safe, email, platform)
                    future_to_platform[future] = platform
                except Exception as e:
                    logging.error(f"Error submitting task for {platform.get('name', 'Unknown')}: {e}")
                    results.append({
                        "platform": platform.get('name', 'Unknown'),
                        "url": platform.get('url', ''),
                        "status": "error",
                        "error": f"Task submission failed: {str(e)}",
                        "search_time": datetime.now().isoformat()
                    })
            
            # Collect results with timeout
            for future in concurrent.futures.as_completed(future_to_platform, timeout=300):  # 5 minute timeout
                platform = future_to_platform[future]
                try:
                    result = future.result(timeout=60)  # 1 minute per platform
                    if result:
                        results.append(result)
                    else:
                        results.append({
                            "platform": platform.get('name', 'Unknown'),
                            "url": platform.get('url', ''),
                            "status": "error",
                            "error": "No result returned",
                            "search_time": datetime.now().isoformat()
                        })
                except concurrent.futures.TimeoutError:
                    logging.error(f"Timeout searching {platform.get('name', 'Unknown')}")
                    results.append({
                        "platform": platform.get('name', 'Unknown'),
                        "url": platform.get('url', ''),
                        "status": "error",
                        "error": "Search timeout",
                        "search_time": datetime.now().isoformat()
                    })
                except Exception as e:
                    logging.error(f"Error searching {platform.get('name', 'Unknown')}: {str(e)}")
                    results.append({
                        "platform": platform.get('name', 'Unknown'),
                        "url": platform.get('url', ''),
                        "status": "error",
                        "error": str(e),
                        "search_time": datetime.now().isoformat()
                    })
                    
        return results
        
    def _search_single_platform_safe(self, email: str, platform: Dict) -> Optional[Dict]:
        """Safely search for email on a single platform with comprehensive error handling"""
        platform_name = platform.get('name', 'Unknown')
        
        try:
            # Add small delay to avoid overwhelming servers
            time.sleep(0.5)
            
            result = self.scraper.search_email_on_platform(email, platform)
            
            # Validate result structure
            if not isinstance(result, dict):
                return {
                    "platform": platform_name,
                    "url": platform.get('url', ''),
                    "status": "error",
                    "error": "Invalid result format",
                    "search_time": datetime.now().isoformat()
                }
                
            # Ensure required fields exist
            required_fields = ['platform', 'url', 'status', 'search_time']
            for field in required_fields:
                if field not in result:
                    result[field] = {
                        'platform': platform_name,
                        'url': platform.get('url', ''),
                        'status': 'unknown',
                        'search_time': datetime.now().isoformat()
                    }.get(field, '')
                    
            return result
            
        except KeyboardInterrupt:
            logging.info(f"Search interrupted for {platform_name}")
            raise
        except Exception as e:
            logging.error(f"Error searching {platform_name}: {str(e)}")
            return {
                "platform": platform_name,
                "url": platform.get('url', ''),
                "status": "error",
                "error": str(e),
                "search_time": datetime.now().isoformat()
            }
            
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of search results with error handling"""
        summary = {
            "total_platforms_searched": 0,
            "platforms_with_hits": 0,
            "platforms_with_potential_matches": 0,
            "platforms_with_errors": 0,
            "hit_rate_percentage": 0.0,
            "potential_match_rate_percentage": 0.0,
            "error_rate_percentage": 0.0
        }
        
        try:
            for platform_type, platform_results in results.items():
                if not isinstance(platform_results, list):
                    continue
                    
                for result in platform_results:
                    if not isinstance(result, dict):
                        continue
                        
                    summary["total_platforms_searched"] += 1
                    
                    status = result.get("status", "unknown")
                    if status == "found":
                        summary["platforms_with_hits"] += 1
                    elif status == "potential_match":
                        summary["platforms_with_potential_matches"] += 1
                    elif status == "error":
                        summary["platforms_with_errors"] += 1
                        
            # Calculate percentages
            total = summary["total_platforms_searched"]
            if total > 0:
                summary["hit_rate_percentage"] = (summary["platforms_with_hits"] / total) * 100
                summary["potential_match_rate_percentage"] = (summary["platforms_with_potential_matches"] / total) * 100
                summary["error_rate_percentage"] = (summary["platforms_with_errors"] / total) * 100
                
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            summary["error"] = str(e)
            
        return summary
        
    def save_results(self, results: Dict, output_format: str = "json", 
                    custom_filename: str = None) -> str:
        """Save search results to file with error handling"""
        try:
            os.makedirs("results", exist_ok=True)
            
            if custom_filename:
                filename = custom_filename.rsplit('.', 1)[0]  # Remove extension
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                email_clean = results["email"].replace("@", "_at_").replace(".", "_")
                filename = f"results/osint_{email_clean}_{timestamp}"
                
            return self.formatter.save_results(results, filename, output_format)
            
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            raise
            
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'scraper') and self.scraper:
                self.scraper.close()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Email OSINT Tool - Search email across multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python osint_email.py --email user@example.com
  python osint_email.py --email user@example.com --platforms marketplaces discussions
  python osint_email.py --email user@example.com --output csv --workers 10
  python osint_email.py --email user@example.com --save-as custom_results.json --verbose
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
        choices=["json", "csv", "xml", "txt", "html", "xlsx"],
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
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Handle "all" platform selection
    if "all" in args.platforms:
        platforms = ["marketplaces", "discussions", "google"]
    else:
        platforms = args.platforms
        
    # Validate workers count
    if args.workers < 1 or args.workers > 20:
        print("Warning: Workers count should be between 1 and 20. Using default: 5")
        args.workers = 5
        
    osint_tool = None
    
    try:
        # Initialize OSINT tool
        print(f"Initializing OSINT tool...")
        osint_tool = OSINTEmailTool(args.config)
        
        # Perform search
        print(f"Starting search for: {args.email}")
        results = osint_tool.search_email(
            email=args.email,
            platforms=platforms,
            max_workers=args.workers
        )
        
        # Check for errors
        if "error" in results:
            print(f"Error: {results['error']}")
            sys.exit(1)
            
        # Save results
        print(f"Saving results...")
        output_file = osint_tool.save_results(
            results=results,
            output_format=args.output,
            custom_filename=args.save_as
        )
        
        # Print summary
        summary = results.get("summary", {})
        print(f"\n{'='*70}")
        print(f"EMAIL OSINT SEARCH SUMMARY FOR: {args.email}")
        print(f"{'='*70}")
        print(f"Total platforms searched: {summary.get('total_platforms_searched', 0)}")
        print(f"Platforms with hits: {summary.get('platforms_with_hits', 0)}")
        print(f"Potential matches: {summary.get('platforms_with_potential_matches', 0)}")
        print(f"Platforms with errors: {summary.get('platforms_with_errors', 0)}")
        print(f"Hit rate: {summary.get('hit_rate_percentage', 0):.2f}%")
        print(f"Results saved to: {output_file}")
        
        # Email validation info
        if "email_validation" in results:
            validation = results["email_validation"]
            print(f"Email validation score: {validation.get('score', 0)}/100")
            
        print(f"{'='*70}")
        
        # Exit with appropriate code
        hits = summary.get('platforms_with_hits', 0)
        potential = summary.get('platforms_with_potential_matches', 0)
        
        if hits > 0:
            sys.exit(0)  # Found results
        elif potential > 0:
            sys.exit(2)  # Potential matches only
        else:
            sys.exit(3)  # No results found
        
    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup resources
        if osint_tool:
            try:
                osint_tool.cleanup()
            except:
                pass


if __name__ == "__main__":
    main()