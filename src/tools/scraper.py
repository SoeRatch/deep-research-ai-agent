"""
Web scraping tool for extracting and cleaning content from URLs.

Uses BeautifulSoup with intelligent text cleaning.
"""

from typing import Optional, Dict, Any, List
import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_fixed
import logging
import time

from src.config import Config

logger = logging.getLogger(__name__)


class WebScraper:
    """Scrapes and cleans web content."""
    
    # Tags to remove (boilerplate, ads, etc.)
    UNWANTED_TAGS = [
        'script', 'style', 'nav', 'header', 'footer',
        'aside', 'iframe', 'noscript', 'svg', 'form'
    ]
    
    # Classes/IDs commonly used for ads and navigation
    AD_PATTERNS = [
        'ad', 'advertisement', 'banner', 'popup', 'modal',
        'cookie', 'newsletter', 'subscribe', 'social-share',
        'related-posts', 'comments', 'sidebar'
    ]
    
    def __init__(self, config: Config):
        """
        Initialize scraper.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Respect rate limits (1 second between requests)
    
    def _respect_rate_limit(self):
        """Ensure minimum time between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(2),
        reraise=True
    )
    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        self._respect_rate_limit()
        
        try:
            response = self.session.get(
                url,
                timeout=self.config.request_timeout_seconds,
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _is_unwanted_element(self, element) -> bool:
        """Check if element should be removed."""
        # Check class and id for ad patterns
        if element.get('class'):
            classes = ' '.join(element.get('class', [])).lower()
            if any(pattern in classes for pattern in self.AD_PATTERNS):
                return True
        
        if element.get('id'):
            elem_id = element.get('id', '').lower()
            if any(pattern in elem_id for pattern in self.AD_PATTERNS):
                return True
        
        return False
    
    def clean_html(self, html: str) -> BeautifulSoup:
        """
        Clean HTML by removing unwanted elements.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned BeautifulSoup object
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted tags
        for tag in self.UNWANTED_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove elements matching ad patterns
        for element in soup.find_all():
            if self._is_unwanted_element(element):
                element.decompose()
        
        return soup
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main article/content from page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted text content
        """
        # Try common content containers first
        content_selectors = [
            {'name': 'article'},
            {'name': 'main'},
            {'class_': 'content'},
            {'class_': 'article'},
            {'class_': 'post'},
            {'id': 'content'},
            {'id': 'main-content'},
        ]
        
        for selector in content_selectors:
            container = soup.find(**selector)
            if container:
                # Get text from container
                text = container.get_text(separator='\n', strip=True)
                if len(text) > 200:  # Ensure meaningful content
                    return text
        
        # Fallback: get all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
            return text
        
        # Last resort: get all text
        return soup.get_text(separator='\n', strip=True)
    
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract metadata from page.
        
        Args:
            soup: BeautifulSoup object
            url: Original URL
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': None,
            'description': None,
            'author': None,
            'publish_date': None,
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'}) or \
                          soup.find('meta', attrs={'property': 'og:description'})
        if meta_description:
            metadata['description'] = meta_description.get('content', '')
        
        meta_author = soup.find('meta', attrs={'name': 'author'}) or \
                     soup.find('meta', attrs={'property': 'article:author'})
        if meta_author:
            metadata['author'] = meta_author.get('content', '')
        
        meta_date = soup.find('meta', attrs={'property': 'article:published_time'}) or \
                   soup.find('meta', attrs={'name': 'publish_date'})
        if meta_date:
            metadata['publish_date'] = meta_date.get('content', '')
        
        return metadata
    
    def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape and extract content from URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with content and metadata, or None if failed
        """
        logger.info(f"Scraping: {url}")
        
        html = self.fetch_url(url)
        if not html:
            return None
        
        try:
            # Clean HTML
            soup = self.clean_html(html)
            
            # Extract content and metadata
            content = self.extract_main_content(soup)
            metadata = self.extract_metadata(soup, url)
            
            result = {
                'url': url,
                'content': content,
                'content_length': len(content),
                'metadata': metadata
            }
            
            logger.info(f"Extracted {len(content)} characters from {url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse {url}: {e}")
            return None
    
    def batch_scrape(self, urls: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Scrape multiple URLs.
        
        Args:
            urls: List of URLs
            
        Returns:
            Dictionary mapping URLs to scraped content
        """
        results = {}
        for url in urls:
            try:
                result = self.scrape(url)
                results[url] = result
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                results[url] = None
        
        return results
