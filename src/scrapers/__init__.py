"""資料爬蟲模組"""

from src.scrapers.base import BaseScraper
from src.scrapers.google_news import GoogleNewsScraper
from src.scrapers.linkedin import LinkedInScraper, LinkedInURLHandler
from src.scrapers.news_api import NewsAPIScraper
from src.scrapers.ptt import PTTScraper
from src.scrapers.threads import ThreadsScraper

__all__ = [
    "BaseScraper",
    "GoogleNewsScraper",
    "LinkedInScraper",
    "LinkedInURLHandler",
    "NewsAPIScraper",
    "PTTScraper",
    "ThreadsScraper",
]
