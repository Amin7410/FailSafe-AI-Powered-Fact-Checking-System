# factcheck/utils/deep_scraper.py

import trafilatura
from concurrent.futures import ThreadPoolExecutor
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class DeepScraper:
    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def scrape_url(self, url: str, max_chars: int = 3000) -> str | None:
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            
            if not text:
                return None

            if len(text) > max_chars:
                text = text[:max_chars] + "... [Content Truncated]"
            
            return text
        except Exception as e:
            logger.warning(f"Deep scraping failed for {url}: {e}")
            return None

    def scrape_batch(self, urls: list[str]) -> dict[str, str]:
        if not urls:
            return {}
        
        logger.info(f"Deep scraping {len(urls)} URLs in parallel...")
        results = {}
        
        futures = {self.executor.submit(self.scrape_url, url): url for url in urls}
        
        for future in futures:
            url = futures[future]
            try:
                content = future.result()
                if content:
                    results[url] = content
            except Exception:
                continue
                
        return results