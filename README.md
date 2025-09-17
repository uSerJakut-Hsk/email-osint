# 🔍 Advanced Email OSINT Tool

**Version:** 1.0  
**Date:** September 2025  
**Author:** Security Researcher  

A comprehensive Open Source Intelligence (OSINT) tool for investigating email addresses across multiple platforms including marketplaces, discussion forums, and Google services.

## ⚡ Features

- **Multi-Platform Search**: Search across 100+ platforms including marketplaces, forums, and Google services
- **Concurrent Processing**: Multi-threaded searches for faster results
- **Proxy Support**: Built-in proxy rotation to avoid rate limiting
- **Multiple Output Formats**: JSON, CSV, XML, TXT, HTML, and Excel
- **GUI Interface**: User-friendly graphical interface
- **Email Validation**: Advanced email validation and analysis
- **Comprehensive Reporting**: Detailed reports with statistics and summaries

## 🎯 Supported Platforms

### Marketplaces (30+ platforms)
- Amazon, eBay, Etsy, AliExpress
- Fiverr, Upwork, Freelancer
- Airbnb, Shopee, Zalando
- And many more...

### Discussion Forums (20+ platforms)
- Reddit, Stack Overflow, GitHub
- Quora, Discord, Steam Community
- XDA Forums, HackerNews
- And many more...

### Google Platforms (18+ services)
- Google Search, Images, News
- YouTube, Google Scholar
- Google Maps, Shopping
- And many more...

## 📋 Requirements

- Python 3.8+ 
- Chrome/Chromium browser (for Selenium)
- Internet connection
- 4GB+ RAM recommended

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/advanced-email-osint.git
cd advanced-email-osint
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Setup Proxies (Optional)
```bash
# Add proxy list to proxies.txt
# Format: http://ip:port or ip:port
```

## 💻 Usage

### Command Line Interface

#### Basic Usage
```bash
python osint_email.py --email user@example.com
```

#### Advanced Usage
```bash
# Search specific platforms
python osint_email.py --email user@example.com --platforms marketplaces discussions

# Specify output format
python osint_email.py --email user@example.com --output html

# Use more workers
python osint_email.py --email user@example.com --workers 10

# Custom output filename
python osint_email.py --email user@example.com --save-as my_results.json

# Enable verbose logging
python osint_email.py --email user@example.com --verbose
```

### GUI Interface
```bash
python osint_email_gui.py
```

### Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `--email, -e` | Email address to search | Required |
| `--platforms, -p` | Platform types to search | all |
| `--output, -o` | Output format | json |
| `--workers, -w` | Concurrent workers | 5 |
| `--save-as` | Custom filename | Auto-generated |
| `--config` | Config file path | config/platforms.json |
| `--verbose, -v` | Enable verbose output | False |

### Platform Options
- `marketplaces`: E-commerce and service platforms
- `discussions`: Forums and discussion platforms  
- `google`: Google services and platforms
- `all`: Search all platform types

### Output Formats
- `json`: JSON format (default)
- `csv`: CSV spreadsheet
- `xml`: XML format
- `txt`: Plain text report
- `html`: Interactive HTML report
- `xlsx`: Excel spreadsheet

## 📁 Project Structure

```
advanced-email-osint/
├── osint_email.py              # Main CLI script
├── osint_email_gui.py          # GUI interface
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                 # Git ignore rules
├── .env                       # Environment variables
├── config/
│   └── platforms.json         # Platform configurations
├── results/                   # Output directory
├── utils/
│   ├── scraper.py            # Web scraping utilities
│   ├── proxy_manager.py      # Proxy management
│   ├── output_formatter.py   # Output formatting
│   └── email_validator.py    # Email validation
├── tests/                     # Unit tests
├── docs/                      # Documentation
└── proxies.txt               # Proxy list
```

## ⚙️ Configuration

### Platform Configuration
Edit `config/platforms.json` to add or modify search platforms:

```json
{
  "marketplaces": [
    {
      "name": "Platform Name",
      "url": "example.com",
      "login_required": false,
      "search_endpoint": "/search",
      "category": "ecommerce"
    }
  ]
}
```

### Environment Variables
Create `.env` file for sensitive configurations:

```env
# Google API (optional)
GOOGLE_API_KEY=your_api_key

# Proxy authentication (optional)  
PROXY_AUTH=user:pass

# Rate limiting
MAX_REQUESTS_PER_MINUTE=60
```

### Proxy Configuration
Add proxies to `proxies.txt`:

```
# HTTP proxies
http://proxy1.example.com:8080
http://user:pass@proxy2.example.com:8080

# IP:PORT format (assumes HTTP)
192.168.1.100:3128
203.0.113.1:8080
```

## 📊 Output Examples

### Summary Report
```
EMAIL OSINT SEARCH SUMMARY FOR: user@example.com
============================================================
Total platforms searched: 75
Platforms with hits: 12
Platforms with errors: 3
Hit rate: 16.00%
Results saved to: results/osint_user_at_example_20250916_143022.json
============================================================
```

### JSON Output Structure
```json
{
  "email": "user@example.com",
  "timestamp": "2025-09-16T14:30:22",
  "platforms_searched": ["marketplaces", "discussions", "google"],
  "results": {
    "marketplaces": [
      {
        "platform": "eBay",
        "url": "ebay.com",
        "status": "found",
        "matches": [
          {
            "title": "User Profile",
            "url": "https://ebay.com/usr/user123",
            "snippet": "Profile found..."
          }
        ]
      }
    ]
  },
  "summary": {
    "total_platforms_searched": 75,
    "platforms_with_hits": 12,
    "hit_rate_percentage": 16.0
  }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_scraper.py

# Run with coverage
python -m pytest tests/ --cov=utils/
```

## 🛠️ Development

### Adding New Platforms

1. Edit `config/platforms.json`
2. Add platform configuration:
   ```json
   {
     "name": "New Platform",
     "url": "newplatform.com",
     "login_required": false,
     "search_endpoint": "/search",
     "category": "your_category"
   }
   ```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints where possible
- Write comprehensive docstrings

## ⚠️ Legal and Ethical Considerations

### ⚖️ Legal Compliance
- **Respect Terms of Service**: Always comply with platform ToS
- **Rate Limiting**: Tool includes delays to respect server resources
- **No Authentication Bypass**: Does not attempt to bypass login requirements
- **Public Data Only**: Searches only publicly available information

### 🎯 Legitimate Use Cases
- ✅ Security research and threat intelligence
- ✅ Corporate security investigations
- ✅ Academic research (with proper ethics approval)
- ✅ Personal privacy auditing
- ✅ Fraud investigation by authorized personnel

### 🚫 Prohibited Uses
- ❌ Harassment or stalking
- ❌ Identity theft or impersonation
- ❌ Unauthorized commercial data collection
- ❌ Violation of privacy laws (GDPR, CCPA, etc.)
- ❌ Any illegal activities

### 📜 Disclaimer
This tool is provided for educational and legitimate security research purposes only. Users are responsible for ensuring their use complies with applicable laws and regulations. The authors assume no liability for misuse of this software.

## 🔧 Troubleshooting

### Common Issues

**Issue**: "Module not found" errors
```bash
# Solution: Ensure virtual environment is activated and dependencies installed
pip install -r requirements.txt
```

**Issue**: Selenium WebDriver errors
```bash
# Solution: Install Chrome and update webdriver
pip install --upgrade webdriver-manager
```

**Issue**: Proxy connection failures
```bash
# Solution: Validate proxy list and format
python -c "from utils.proxy_manager import ProxyManager; pm = ProxyManager(); pm.validate_all_proxies()"
```

**Issue**: Rate limiting / blocked requests
```bash
# Solution: Add more proxies or increase delays
# Edit scraper.py and increase time.sleep() values
```

### Performance Tips

1. **Use Proxies**: Rotate IP addresses to avoid rate limiting
2. **Adjust Workers**: Reduce concurrent workers if getting blocked
3. **Platform Selection**: Target specific platforms instead of searching all
4. **Caching**: Results are cached to avoid duplicate searches

### Logs and Debugging

Logs are saved to `results/logs/` directory:
```bash
# View recent logs
tail -f results/logs/osint_email_*.log

# Enable debug logging
python osint_email.py --email test@example.com --verbose
```

## 📞 Support

### Getting Help

1. **Documentation**: Check `docs/` directory
2. **Issues**: Open GitHub issue with details
3. **Discussions**: Use GitHub Discussions for questions

### Reporting Bugs

Please include:
- Python version and OS
- Complete error message
- Steps to reproduce
- Expected vs actual behavior

## 🗺️ Roadmap

### Version 1.1 (Coming Soon)
- [ ] API integrations (Shodan, Have I Been Pwned)
- [ ] Machine learning for result classification
- [ ] Advanced email pattern recognition
- [ ] Real-time monitoring capabilities

### Version 1.2
- [ ] Mobile app interface
- [ ] Cloud deployment options
- [ ] Integration with SIEM platforms
- [ ] Advanced visualization features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Requests](https://requests.readthedocs.io/) - HTTP library
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - Web scraping
- [Selenium](https://selenium.dev/) - Web automation
- [Pandas](https://pandas.pydata.org/) - Data processing
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework

## ⭐ Star History

If you find this tool useful, please consider giving it a star!
---


**⚠️ Remember: Use this tool responsibly and ethically. Respect privacy and follow applicable laws.**