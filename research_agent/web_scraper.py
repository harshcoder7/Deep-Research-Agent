# research_agent/web_scraper.py
import requests
from bs4 import BeautifulSoup
import html2text
import logging
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import time

logger = logging.getLogger(__name__)

class WebScraper:
    """Scrapes web content from URLs with improved error handling and retries."""
    
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_tables = False
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configure headers to mimic a real browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Disable SSL verification warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a given URL with improved error handling."""
        logger.info(f"Scraping URL: {url}")
        
        try:
            # Try with SSL verification first
            try:
                response = self.session.get(
                    url,
                    headers=self.headers,
                    timeout=15,
                    verify=True
                )
            except requests.exceptions.SSLError:
                # If SSL verification fails, try without verification
                logger.warning(f"SSL verification failed for {url}, retrying without verification")
                response = self.session.get(
                    url,
                    headers=self.headers,
                    timeout=15,
                    verify=False
                )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch URL: {url}, status code: {response.status_code}")
                return None
            
            # Add a small delay to be respectful to servers
            time.sleep(1)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Get the text content
            text = self.html_converter.handle(str(soup))
            
            # Extract title
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text()
            
            # Clean up the text
            text = ' '.join(text.split())  # Remove extra whitespace
            
            return {
                "url": url,
                "title": title,
                "content": text[:50000],  # Limit content size
                "status": "success"
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while scraping URL {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while scraping URL {url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return None
