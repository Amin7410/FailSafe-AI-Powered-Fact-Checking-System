# ./factcheck/utils/web_util.py

import requests
import backoff
import time
import bs4
import asyncio
import re
from bs4 import BeautifulSoup
from httpx import AsyncHTTPTransport
from httpx._client import AsyncClient
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"
MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"
headers = {"User-Agent": USER_AGENT}


def is_tag_visible(element: bs4.element) -> bool:
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ] or isinstance(element, bs4.element.Comment):
        return False
    return True


transport = AsyncHTTPTransport(retries=3)


async def httpx_get(url: str, headers: dict):
    try:
        async with AsyncClient(transport=transport) as client:
            response = await client.get(url, headers=headers, timeout=3)
            response = response if response.status_code == 200 else None
            if not response:
                return False, None
            else:
                return True, response
    except Exception as e:  # noqa: F841
        return False, None


async def httpx_bind_key(url: str, headers: dict, key: str = ""):
    flag, response = await httpx_get(url, headers)
    return flag, response, url, key


def crawl_web(query_url_dict: dict):
    tasks = list()
    for query, urls in query_url_dict.items():
        for url in urls:
            task = httpx_bind_key(url=url, headers=headers, key=query)
            tasks.append(task)
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(asyncio.gather(*tasks))
    return responses


def common_web_request(url: str, query: str = None, timeout: int = 3):
    resp = requests.get(url, headers=headers, timeout=timeout)
    if query:
        return resp, query
    else:
        return resp


def parse_response(response: requests.Response, url: str, query: str = None):
    html_content = response.text
    url = url
    try:
        soup = bs4.BeautifulSoup(html_content, "html.parser")
        texts = soup.findAll(text=True)
        visible_text = filter(is_tag_visible, texts)
    except Exception as _:  # noqa: F841
        return None, url, query

    web_text = " ".join(t.strip() for t in visible_text).strip()

    web_text = " ".join(web_text.split())
    return web_text, url, query


def scrape_url(url: str, timeout: float = 3):

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as _:  # noqa: F841
        return None, url

    try:
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        texts = soup.findAll(text=True)

        visible_text = filter(is_tag_visible, texts)
    except Exception as _:  # noqa: F841
        return None, url

    web_text = " ".join(t.strip() for t in visible_text).strip()

    web_text = " ".join(web_text.split())
    return web_text, url


def crawl_google_web(response, top_k: int = 10):
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    valid_node_list = list()
    for node in soup.find_all("a", {"href": True}):
        if node.findChildren("h3"):
            valid_node_list.append(node)
    result_urls = list()
    for node in valid_node_list:
        result_urls.append(node.get("href"))
    return result_urls[:top_k]


def is_url(text):
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    return re.match(url_pattern, text) is not None


def scrape_url_content(url):
    logger.info(f"--- Starting URL scrape process: {url} ---")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Request successful, Status Code: {response.status_code}")
        
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|main|post|body'))
        
        if main_content:
            logger.info("Found main content tag (article, main, etc.). Extracting text.")
            text = main_content.get_text(separator=' ', strip=True)
        else:
            logger.warning("Main content tag not found. Using entire <body> as fallback.")
            body = soup.find('body')
            if body:
                text = body.get_text(separator=' ', strip=True)
            else:
                logger.error("Could not find <body> tag in the page.")
                return None, "Could not find any content in the page."
        
        cleaned_text = ' '.join(text.split())
        logger.info(f"--- Scrape successful! Extracted {len(cleaned_text)} chars. ---")
        return cleaned_text, None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting URL: {e}", exc_info=True)
        return None, f"Error fetching the URL. See server log for details."
    except Exception as e:
        logger.error(f"Unexpected error during content parsing: {e}", exc_info=True)
        return None, f"An unexpected error occurred. See server log for details."