#!/usr/bin/env python3
"""
web_scraper.py — Simple web scraper with rate limiting and CSV export
Scrapes web pages and extracts data using regex patterns or CSS selectors
"""

import urllib.request
import urllib.parse
import re
import csv
import time
import logging
import argparse
from typing import List, Dict, Optional
from html.parser import HTMLParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper with rate limiting"""
    
    def __init__(self, rate_limit: float = 1.0, user_agent: str = "Mozilla/5.0"):
        self.rate_limit = rate_limit
        self.user_agent = user_agent
        self.last_request = 0
    
    def _fetch(self, url: str) -> Optional[str]:
        """Fetch a URL with rate limiting"""
        # Rate limiting
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.last_request = time.time()
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_links(self, html: str, base_url: str = "") -> List[str]:
        """Extract all links from HTML"""
        links = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        result = []
        for link in links:
            if link.startswith("http"):
                result.append(link)
            elif link.startswith("/") and base_url:
                result.append(base_url.rstrip("/") + link)
            elif link.startswith("#") or link.startswith("mailto:"):
                continue
            else:
                result.append(link)
        return result
    
    def extract_pattern(self, html: str, pattern: str, group: int = 0) -> List[str]:
        """Extract text matching a regex pattern"""
        matches = re.findall(pattern, html, re.IGNORECASE | re.MULTILINE)
        if isinstance(matches, list) and matches and isinstance(matches[0], tuple):
            return [m[group] for m in matches]
        return matches
    
    def extract_table(self, html: str) -> List[List[str]]:
        """Extract all tables from HTML as list of rows"""
        tables = []
        # Find table content
        table_matches = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        
        for table in table_matches:
            rows = []
            row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
            for row in row_matches:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
                cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        
        return tables
    
    def scrape_url(self, url: str, patterns: Dict[str, str] = None) -> Dict:
        """Scrape a single URL"""
        html = self._fetch(url)
        if not html:
            return {}
        
        result = {"url": url}
        
        if patterns:
            for name, pattern in patterns.items():
                result[name] = self.extract_pattern(html, pattern)
        else:
            result["links"] = self.extract_links(html, url)
            result["title"] = self.extract_pattern(html, r'<title[^>]*>(.*?)</title>', 0)
        
        return result
    
    def crawl(self, start_url: str, max_pages: int = 10, pattern: str = None) -> List[Dict]:
        """Crawl multiple pages"""
        visited = set()
        to_visit = [start_url]
        results = []
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            
            visited.add(url)
            logger.info(f"Crawling: {url}")
            
            html = self._fetch(url)
            if not html:
                continue
            
            result = self.scrape_url(url, {pattern: pattern} if pattern else None)
            results.append(result)
            
            # Add new links to visit
            for link in self.extract_links(html, url):
                if link not in visited and len(to_visit) < max_pages:
                    to_visit.append(link)
        
        return results
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """Save scraped data to CSV"""
        if not data:
            logger.warning("No data to save")
            return
        
        # Collect all field names
        fieldnames = set()
        for row in data:
            fieldnames.update(row.keys())
        fieldnames = sorted(fieldnames)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Convert lists to strings
                clean_row = {}
                for k, v in row.items():
                    if isinstance(v, list):
                        clean_row[k] = "; ".join(str(x) for x in v)
                    else:
                        clean_row[k] = v
                writer.writerow(clean_row)
        
        logger.info(f"Saved {len(data)} rows to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Web Scraper")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--pattern", help="Regex pattern to extract")
    parser.add_argument("--name", default="matches", help="Field name for pattern results")
    parser.add_argument("--output", default="scraped.csv", help="Output CSV file")
    parser.add_argument("--rate", type=float, default=1.0, help="Rate limit (seconds)")
    parser.add_argument("--max-pages", type=int, default=1, help="Max pages to crawl")
    args = parser.parse_args()
    
    scraper = WebScraper(rate_limit=args.rate)
    
    if args.max_pages > 1:
        results = scraper.crawl(args.url, args.max_pages, args.pattern)
    else:
        result = scraper.scrape_url(args.url, {args.name: args.pattern} if args.pattern else None)
        results = [result]
    
    # Print summary
    for r in results[:5]:
        print(f"URL: {r.get('url', 'N/A')}")
        for k, v in r.items():
            if k != "url":
                if isinstance(v, list):
                    print(f"  {k}: {len(v)} matches")
                else:
                    print(f"  {k}: {v}")
        print()
    
    # Save to CSV
    scraper.save_to_csv(results, args.output)


if __name__ == "__main__":
    main()