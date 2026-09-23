#!/usr/bin/env python3
"""
FlyRank BE-05: The Polite Scraper
A respectful web scraper for books.toscrape.com practice sandbox.
"""

import os
import time
import hashlib
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Set, Dict, Any
from bs4 import BeautifulSoup
import json
import re
from pydantic import BaseModel, field_validator, HttpUrl
from decimal import Decimal
import traceback

# Configuration
USER_AGENT = "FlyRankBE05Bot/1.0 (Davionnic; educational)"
REQUEST_TIMEOUT = 10
MIN_DELAY = 0.5  # 500ms minimum delay between requests
BASE_URL = "https://books.toscrape.com/"

class BookRecord(BaseModel):
    """Pydantic schema for normalized book records."""
    title: str
    product_url: HttpUrl
    price_gbp: float
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None
    source_page: str
    fetched_at: str
    
    @field_validator('price_gbp', mode='before')
    @classmethod
    def parse_price(cls, v):
        """Extract and convert price to float GBP."""
        if isinstance(v, str):
            # Remove currency symbols and extract numeric value
            price_match = re.search(r'[\d.]+', v.replace('£', '').replace(',', ''))
            if price_match:
                return float(price_match.group())
        return float(v) if v is not None else 0.0
    
    @field_validator('product_url', mode='before') 
    @classmethod
    def validate_url(cls, v):
        """Ensure URL is absolute."""
        if isinstance(v, str):
            if not v.startswith('http'):
                # Convert relative to absolute
                from urllib.parse import urljoin
                return urljoin(BASE_URL, v)
            return v
        return str(v)

class ValidationError(BaseModel):
    """Schema for validation error records."""
    raw_data: Dict[str, Any]
    error_message: str
    field_errors: Dict[str, str] = {}

class RunReport(BaseModel):
    """Schema for run report."""
    start_time: str
    end_time: str
    total_runtime_seconds: float
    catalogue_pages_discovered: int
    books_discovered: int
    books_successfully_processed: int
    validation_errors: int
    failed_pages: int
    cache_hits: int
    network_requests: int
    retry_attempts: int
    error_summary: Dict[str, int] = {}
    sample_book_url: str = ""

class PoliteScraper:
    """A polite web scraper with caching and rate limiting."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.last_request_time = 0
        self.cache_dir = Path("cache")
        self.output_dir = Path("output")
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistics for run reporting
        self.stats = {
            'cache_hits': 0,
            'network_requests': 0,
            'retry_attempts': 0,
            'failed_pages': 0,
            'error_summary': {},
            'start_time': None,
            'end_time': None
        }
    
    def _wait_politely(self):
        """Ensure minimum delay between requests."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < MIN_DELAY:
            time.sleep(MIN_DELAY - time_since_last)
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path for a URL."""
        # Create a safe filename from URL
        parsed = urlparse(url)
        path_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        if parsed.path == "/" or parsed.path == "":
            filename = f"index-{path_hash}.html"
        else:
            # Clean path for filename
            clean_path = parsed.path.strip("/").replace("/", "-")
            if parsed.query:
                clean_path += f"-{hashlib.md5(parsed.query.encode()).hexdigest()[:8]}"
            filename = f"{clean_path}-{path_hash}.html"
        return self.cache_dir / filename
    
    def fetch_page(self, url: str, force_fetch: bool = False, max_retries: int = 1) -> tuple[str, bool, bool]:
        """
        Fetch a page with caching support and retry logic.
        Returns: (html_content, was_cache_hit, fetch_failed)
        """
        cache_path = self._get_cache_path(url)
        
        # Check cache first
        if not force_fetch and cache_path.exists():
            html = cache_path.read_text(encoding='utf-8')
            size = len(html)
            print(f"CACHE HIT: {url} ({size:,} bytes)")
            self.stats['cache_hits'] += 1
            return html, True, False
        
        # Try to fetch from web with retry logic
        for attempt in range(max_retries + 1):
            self._wait_politely()
            
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                html = response.text
                size = len(html)
                
                # Cache the result
                cache_path.write_text(html, encoding='utf-8')
                
                print(f"FETCH: {url} ({size:,} bytes)")
                self.last_request_time = time.time()
                self.stats['network_requests'] += 1
                
                return html, False, False
                
            except requests.RequestException as e:
                if attempt < max_retries:
                    # Retry for timeout/5xx errors only
                    if (isinstance(e, requests.Timeout) or 
                        (hasattr(e, 'response') and e.response is not None and e.response.status_code >= 500)):
                        print(f"Retrying {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        self.stats['retry_attempts'] += 1
                        time.sleep(1)  # Brief delay before retry
                        continue
                
                # Don't retry for 404/403 or final failure
                print(f"ERROR fetching {url}: {e}")
                self.stats['failed_pages'] += 1
                
                # Track error types
                error_type = type(e).__name__
                if hasattr(e, 'response') and e.response is not None:
                    error_type = f"{error_type}_{e.response.status_code}"
                self.stats['error_summary'][error_type] = self.stats['error_summary'].get(error_type, 0) + 1
                
                return "", False, True
        
        # Should never reach here
        return "", False, True
    
    def extract_book_urls(self, html: str, source_page_url: str) -> List[str]:
        """Extract all book detail page URLs from a catalogue page."""
        soup = BeautifulSoup(html, 'html.parser')
        book_urls = []
        
        # Find all book product containers
        for article in soup.find_all('article', class_='product_pod'):
            # Look for the link to the book detail page
            link = article.find('h3').find('a') if article.find('h3') else None
            if link and link.get('href'):
                # Convert relative URL to absolute
                book_url = urljoin(source_page_url, link['href'])
                book_urls.append(book_url)
        
        return book_urls
    
    def find_next_page_url(self, html: str, current_page_url: str) -> Optional[str]:
        """Find the URL of the next catalogue page."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for next page link
        next_link = soup.find('li', class_='next')
        if next_link:
            link = next_link.find('a')
            if link and link.get('href'):
                return urljoin(current_page_url, link['href'])
        
        return None
    
    def discover_catalogue_pages(self, max_pages: int = 3) -> tuple[List[str], List[str]]:
        """
        Discover catalogue pages and extract all book URLs.
        Returns: (catalogue_page_urls, all_book_urls)
        """
        catalogue_pages = []
        all_book_urls = []
        unique_book_urls = set()
        
        # Start with the first page
        current_url = BASE_URL
        
        for page_num in range(1, max_pages + 1):
            print(f"\nProcessing catalogue page {page_num}: {current_url}")
            
            # Fetch the catalogue page
            html, was_cached, fetch_failed = self.fetch_page(current_url)
            
            if fetch_failed:
                print(f"Failed to fetch catalogue page {page_num}, skipping")
                continue
                
            catalogue_pages.append(current_url)
            
            # Extract book URLs from this page
            book_urls = self.extract_book_urls(html, current_url)
            print(f"Found {len(book_urls)} books on page {page_num}")
            
            # Add to our collections (dedupe with set)
            for url in book_urls:
                if url not in unique_book_urls:
                    unique_book_urls.add(url)
                    all_book_urls.append(url)
            
            # Find next page (unless we're on the last requested page)
            if page_num < max_pages:
                next_url = self.find_next_page_url(html, current_url)
                if next_url:
                    current_url = next_url
                else:
                    print(f"No next page found after page {page_num}")
                    break
        
        return catalogue_pages, all_book_urls
    
    def extract_book_details(self, book_url: str, source_page: str) -> Optional[Dict[str, Any]]:
        """Extract detailed information from a book page."""
        html, was_cached, fetch_failed = self.fetch_page(book_url)
        
        if fetch_failed:
            print(f"Failed to fetch book page: {book_url}")
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title (from h1 in product_main)
        title_elem = soup.find('div', class_='product_main').find('h1') if soup.find('div', class_='product_main') else None
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        # Extract price (from price_color class)
        price_elem = soup.find('p', class_='price_color')
        price_text = price_elem.get_text(strip=True) if price_elem else "£0.00"
        
        # Extract availability (from instock availability class)
        availability_elem = soup.find('p', class_='instock availability')
        availability_text = availability_elem.get_text(strip=True) if availability_elem else "Unknown"
        
        # Extract rating (from star-rating class)
        rating_elem = soup.find('p', class_='star-rating')
        rating_text = None
        if rating_elem:
            # Rating is in the class name like "star-rating Three"
            classes = rating_elem.get('class', [])
            for cls in classes:
                if cls in ['One', 'Two', 'Three', 'Four', 'Five']:
                    rating_text = cls
                    break
        
        # Extract description (paragraph after product_description div)
        description = None
        desc_header = soup.find('div', id='product_description')
        if desc_header:
            desc_p = desc_header.find_next_sibling('p')
            if desc_p:
                description = desc_p.get_text(strip=True)
        
        # Current timestamp
        fetched_at = datetime.now().isoformat()
        
        return {
            'title': title,
            'product_url': book_url,
            'price_text': price_text,
            'availability_text': availability_text,
            'rating_text': rating_text,
            'description': description,
            'source_page': source_page,
            'fetched_at': fetched_at
        }
    
    def scrape_all_books(self, max_catalogue_pages: int = 3, include_fake_url: bool = False) -> List[Dict[str, Any]]:
        """Scrape details for all books from the specified number of catalogue pages."""
        self.stats['start_time'] = datetime.now().isoformat()
        
        # First, discover all catalogue pages and book URLs
        catalogue_pages, book_urls = self.discover_catalogue_pages(max_pages=max_catalogue_pages)
        
        # Add a deliberate fake URL for Stage 5 requirements
        if include_fake_url:
            fake_url = "https://books.toscrape.com/catalogue/fake-book-that-does-not-exist_0000/index.html"
            book_urls.append(fake_url)
            print(f"\nAdded deliberate fake URL for error testing: {fake_url}")
        
        print(f"\nStarting book detail extraction for {len(book_urls)} books...")
        
        books_data = []
        
        for i, book_url in enumerate(book_urls, 1):
            print(f"Fetching book {i}/{len(book_urls)}: {book_url}")
            
            # Determine which catalogue page this book came from
            source_page = "Unknown"
            for j, cat_page in enumerate(catalogue_pages):
                if i <= (j + 1) * 20:  # Assuming 20 books per page
                    source_page = cat_page
                    break
            
            try:
                book_data = self.extract_book_details(book_url, source_page)
                if book_data is not None:  # Only add successful extractions
                    books_data.append(book_data)
                    
                    # Print first record as required
                    if len(books_data) == 1:
                        print(f"\nFirst raw record:")
                        print(json.dumps(book_data, indent=2))
                
            except Exception as e:
                print(f"ERROR processing book {book_url}: {e}")
                self.stats['failed_pages'] += 1
                error_type = type(e).__name__
                self.stats['error_summary'][error_type] = self.stats['error_summary'].get(error_type, 0) + 1
                continue
        
        self.stats['end_time'] = datetime.now().isoformat()
        print(f"\nDetail pages fetched: detail_pages={len(books_data)}")
        return books_data
    
    def validate_and_save_books(self, raw_books_data: List[Dict[str, Any]]) -> tuple[List[BookRecord], List[ValidationError]]:
        """Validate raw book data and save to JSON files."""
        valid_books = []
        validation_errors = []
        
        print(f"\nValidating {len(raw_books_data)} book records...")
        
        for i, raw_book in enumerate(raw_books_data, 1):
            try:
                # Convert raw price_text to price_gbp for validation
                book_data = raw_book.copy()
                book_data['price_gbp'] = book_data.pop('price_text')
                
                # Validate with Pydantic
                validated_book = BookRecord(**book_data)
                valid_books.append(validated_book)
                
            except Exception as e:
                # Collect validation errors
                error_record = ValidationError(
                    raw_data=raw_book,
                    error_message=str(e),
                    field_errors={}
                )
                
                # Extract field-specific errors if available
                if hasattr(e, 'errors'):
                    for err in e.errors():
                        field = '.'.join(str(loc) for loc in err['loc'])
                        error_record.field_errors[field] = err['msg']
                
                validation_errors.append(error_record)
                print(f"Validation error for book {i}: {e}")
        
        # Save valid books
        books_file = self.output_dir / "books.json"
        valid_books_data = [book.model_dump(mode='json') for book in valid_books]
        
        with open(books_file, 'w', encoding='utf-8') as f:
            json.dump(valid_books_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(valid_books)} valid books to {books_file}")
        
        # Save validation errors if any
        if validation_errors:
            errors_file = self.output_dir / "errors.json" 
            errors_data = [error.model_dump(mode='json') for error in validation_errors]
            
            with open(errors_file, 'w', encoding='utf-8') as f:
                json.dump(errors_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved {len(validation_errors)} validation errors to {errors_file}")
        
        return valid_books, validation_errors
    
    def generate_run_report(self, catalogue_pages: List[str], books_discovered: int, 
                          valid_books: int, validation_errors: int) -> RunReport:
        """Generate a comprehensive run report."""
        start_time = datetime.fromisoformat(self.stats['start_time'])
        end_time = datetime.fromisoformat(self.stats['end_time'])
        runtime = (end_time - start_time).total_seconds()
        
        # Get sample book URL (first valid book if any exist)
        sample_url = ""
        if os.path.exists(self.output_dir / "books.json"):
            try:
                with open(self.output_dir / "books.json", 'r') as f:
                    books = json.load(f)
                    if books:
                        sample_url = books[0]['product_url']
            except Exception:
                pass
        
        report = RunReport(
            start_time=self.stats['start_time'],
            end_time=self.stats['end_time'],
            total_runtime_seconds=runtime,
            catalogue_pages_discovered=len(catalogue_pages),
            books_discovered=books_discovered,
            books_successfully_processed=valid_books,
            validation_errors=validation_errors,
            failed_pages=self.stats['failed_pages'],
            cache_hits=self.stats['cache_hits'],
            network_requests=self.stats['network_requests'],
            retry_attempts=self.stats['retry_attempts'],
            error_summary=self.stats['error_summary'],
            sample_book_url=sample_url
        )
        
        # Save report
        report_file = self.output_dir / "run-report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(mode='json'), f, indent=2, ensure_ascii=False)
        
        print(f"Run report saved to {report_file}")
        return report

def stage1():
    """Stage 1: Fetch and cache catalogue page 1."""
    scraper = PoliteScraper()
    
    # Fetch first catalogue page (main page is catalogue page 1)
    catalogue_url = BASE_URL
    html, was_cached = scraper.fetch_page(catalogue_url)
    
    # Also save with the expected filename for stage requirement
    cache_file = Path("cache/catalogue-page-1.html")
    cache_file.write_text(html, encoding='utf-8')
    
    print(f"\nStage 1 Complete:")
    print(f"- Cached catalogue page 1: {len(html):,} bytes")
    print(f"- Cache status: {'HIT' if was_cached else 'MISS'}")
    print(f"- File saved: {cache_file}")

def stage2():
    """Stage 2: Discover three catalogue pages."""
    scraper = PoliteScraper()
    
    # Discover catalogue pages and extract book URLs
    catalogue_pages, book_urls = scraper.discover_catalogue_pages(max_pages=3)
    
    print(f"\nStage 2 Complete:")
    print(f"catalogue_pages={len(catalogue_pages)} discovered={len(book_urls)} unique_urls={len(book_urls)}")
    print(f"\nCatalogue pages discovered:")
    for i, url in enumerate(catalogue_pages, 1):
        print(f"  {i}. {url}")
    
    return catalogue_pages, book_urls

def stage3():
    """Stage 3: Extract book details."""
    scraper = PoliteScraper()
    
    # Scrape all book details
    books_data = scraper.scrape_all_books(max_catalogue_pages=3)
    
    print(f"\nStage 3 Complete:")
    print(f"Extracted details for {len(books_data)} books")
    
    return books_data

def stage4():
    """Stage 4: Validate normalized records."""
    scraper = PoliteScraper()
    
    # Scrape all book details
    raw_books_data = scraper.scrape_all_books(max_catalogue_pages=3)
    
    # Validate and save
    valid_books, validation_errors = scraper.validate_and_save_books(raw_books_data)
    
    print(f"\nStage 4 Complete:")
    print(f"Valid books: {len(valid_books)}")
    print(f"Validation errors: {len(validation_errors)}")
    print(f"Total processed: {len(raw_books_data)}")
    
    # Verify rerun stays at 60
    print(f"Rerun verification: {len(raw_books_data)} books processed (should stay 60)")
    
    return valid_books, validation_errors

def stage5():
    """Stage 5: Survive failures, report the run."""
    scraper = PoliteScraper()
    
    # Scrape all book details WITH a deliberate fake URL for error testing
    raw_books_data = scraper.scrape_all_books(max_catalogue_pages=3, include_fake_url=True)
    
    # Validate and save
    valid_books, validation_errors = scraper.validate_and_save_books(raw_books_data)
    
    # Generate comprehensive run report
    catalogue_pages, _ = scraper.discover_catalogue_pages(max_pages=3)
    report = scraper.generate_run_report(
        catalogue_pages=catalogue_pages,
        books_discovered=len(raw_books_data) + 1,  # +1 for fake URL
        valid_books=len(valid_books),
        validation_errors=len(validation_errors)
    )
    
    print(f"\nStage 5 Complete:")
    print(f"Valid books processed: {len(valid_books)}")
    print(f"Failed pages: {scraper.stats['failed_pages']} (should be ≥1 due to fake URL)")
    print(f"Cache hits: {scraper.stats['cache_hits']}")
    print(f"Network requests: {scraper.stats['network_requests']}")
    print(f"Retry attempts: {scraper.stats['retry_attempts']}")
    print(f"Runtime: {report.total_runtime_seconds:.2f} seconds")
    
    return valid_books, validation_errors, report

def run_full_scraper():
    """Run the complete scraper pipeline - the main entry point for users."""
    print("FlyRank BE-05: The Polite Scraper")
    print("=" * 50)
    
    scraper = PoliteScraper()
    
    # Run the complete pipeline
    print("Starting complete scraping pipeline...")
    
    # Scrape all book details WITH error handling
    raw_books_data = scraper.scrape_all_books(max_catalogue_pages=3, include_fake_url=True)
    
    # Validate and save
    valid_books, validation_errors = scraper.validate_and_save_books(raw_books_data)
    
    # Generate comprehensive run report
    catalogue_pages, _ = scraper.discover_catalogue_pages(max_pages=3)
    report = scraper.generate_run_report(
        catalogue_pages=catalogue_pages,
        books_discovered=len(raw_books_data) + 1,  # +1 for fake URL
        valid_books=len(valid_books),
        validation_errors=len(validation_errors)
    )
    
    # Print summary
    print(f"\n🎉 Scraping Complete!")
    print(f"📚 Books processed: {len(valid_books)}")
    print(f"⏱️  Runtime: {report.total_runtime_seconds:.2f} seconds")
    print(f"💾 Cache hits: {scraper.stats['cache_hits']}")
    print(f"🌐 Network requests: {scraper.stats['network_requests']}")
    print(f"📁 Output files:")
    print(f"   - output/books.json ({len(valid_books)} books)")
    print(f"   - output/run-report.json (run statistics)")
    
    if scraper.stats['failed_pages'] > 0:
        print(f"⚠️  Failed pages: {scraper.stats['failed_pages']} (includes test failure)")

def main():
    """Main entry point - runs the appropriate stage or full scraper."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stage1":
        stage1()
    elif len(sys.argv) > 1 and sys.argv[1] == "stage2":
        stage2()
    elif len(sys.argv) > 1 and sys.argv[1] == "stage3":
        stage3()
    elif len(sys.argv) > 1 and sys.argv[1] == "stage4":
        stage4()
    elif len(sys.argv) > 1 and sys.argv[1] == "stage5":
        stage5()
    else:
        # Default: run the full scraper for end users
        run_full_scraper()

if __name__ == "__main__":
    main()