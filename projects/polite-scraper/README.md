# FlyRank BE-05: The Polite Scraper

A respectful web scraper implementation for educational purposes, targeting the books.toscrape.com practice sandbox.

## Quick Start

### One-Command Install and Run

```bash
# Install dependencies and run the scraper
pip install -r requirements.txt && python3 scraper.py
```

This produces:
- `output/books.json` - 60 normalized book records
- `output/run-report.json` - Comprehensive run statistics
- `cache/` - Cached HTML (gitignored, reduces server load on reruns)

## Project Classification

### Target Site Analysis
- **URL**: https://books.toscrape.com
- **Type**: Practice sandbox (explicitly labeled "Books to Scrape - Sandbox")
- **Purpose**: Educational web scraping practice site
- **Robots.txt**: Not found (404) - no explicit restrictions
- **Meta robots**: `NOARCHIVE,NOCACHE` - prevents search engine caching but doesn't restrict scraping
- **Scope**: First 3 catalogue pages (~60 unique books)

### Data Schema

Books are validated and normalized using Pydantic schemas:

```python
{
  "title": str,                    # Book title
  "product_url": str,              # Absolute URL to book detail page
  "price_gbp": float,              # Price converted to GBP float
  "availability_text": str,        # Raw availability text
  "rating_text": str | null,      # Star rating (One/Two/Three/Four/Five)
  "description": str | null,       # Book description (null if missing)
  "source_page": str,              # Catalogue page URL where book was found
  "fetched_at": str               # ISO timestamp of fetch
}
```

### Politeness Features

1. **Respectful Rate Limiting**: Minimum 500ms delays between live requests
2. **Proper Identification**: User-Agent `FlyRankBE05Bot/1.0 (Davionnic; educational)`
3. **Smart Caching**: Reduces server load, enables fast reruns
4. **Timeout Handling**: 10-second timeouts prevent hanging
5. **Retry Logic**: Single retry for 5xx/timeout errors, never for 404/403
6. **Error Independence**: Per-page failure isolation ensures maximum data collection

### Technical Limitations

- **No Browser Automation**: Uses HTTP requests + BeautifulSoup for speed and simplicity
  - Faster execution (completes in ~1 second with cache)
  - Lower resource usage
  - Suitable for static HTML content
  - Would require Selenium/Playwright for JavaScript-heavy sites

- **Cache Dependency**: Subsequent runs rely heavily on cached content
- **Single-threaded**: Sequential processing for politeness
- **Limited Retry**: Only one retry attempt per failed request

## Sample Run Report

```json
{
  "start_time": "2026-09-23T10:29:35.262981",
  "end_time": "2026-09-23T10:29:35.934098", 
  "total_runtime_seconds": 0.671117,
  "catalogue_pages_discovered": 3,
  "books_discovered": 61,
  "books_successfully_processed": 60,
  "validation_errors": 0,
  "failed_pages": 1,
  "cache_hits": 66,
  "network_requests": 0,
  "retry_attempts": 0,
  "error_summary": {"HTTPError_404": 1},
  "sample_book_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
}
```

## Data Scope & Ethics

### Robots.txt Analysis
**Result**: No robots.txt file found (HTTP 404)
- **Implication**: No explicit crawling restrictions  
- **Interpretation**: As a practice sandbox, the site appears designed for scraping exercises
- **Documented at**: 2026-09-23 10:23 UTC

### Ethics Statement
This scraper follows ethical guidelines:

1. **Educational Purpose**: Designed for learning web scraping techniques
2. **Sandbox Target**: Uses a site explicitly created for practice
3. **Respectful Rate Limiting**: Minimum 500ms delays between requests
4. **Proper Identification**: Clear User-Agent identifying educational purpose
5. **Reasonable Scope**: Limited to 60 books across 3 pages
6. **Caching Strategy**: Reduces server load through intelligent caching
7. **Error Handling**: Respects HTTP status codes and implements retry limits

## Technical Implementation

- **Language**: Python 3.10+
- **Dependencies**: requests, beautifulsoup4, pydantic
- **Architecture**: Single-threaded, cache-first, failure-tolerant
- **Output**: JSON with full data validation
- **Caching**: Intelligent file-based caching under `cache/` (gitignored)