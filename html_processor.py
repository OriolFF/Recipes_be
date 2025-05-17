import asyncio
import sys

# Set asyncio event loop policy for Windows if applicable
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import httpx
from crawl4ai import AsyncWebCrawler

class HtmlFetcher:
    async def fetch_html(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                return response.text
            except httpx.RequestError as exc:
                # Handle network errors, DNS failures, etc.
                print(f"An error occurred while requesting {url}: {exc}")
                raise  # Re-raise the exception to be handled by the caller
            except httpx.HTTPStatusError as exc:
                # Handle HTTP error responses (4xx, 5xx)
                print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
                raise # Re-raise the exception to be handled by the caller

class MarkdownConverter:
    def __init__(self):
        self.crawler = AsyncWebCrawler()

    async def to_markdown(self, html_content: str, url: str) -> str:
        import asyncio
        print(f"HTML_PROCESSOR (to_markdown): Current event loop policy: {type(asyncio.get_event_loop_policy())}")
        print(f"HTML_PROCESSOR (to_markdown): Current event loop: {type(asyncio.get_event_loop())}")
        print("HTML_PROCESSOR (to_markdown): Attempting to convert HTML to Markdown...")
        if not html_content:
            print("MarkdownConverter: No HTML content provided.")
            return ""
        # crawl4ai's 'arun' method expects a URL to correctly process relative links if any
        # and to understand the context, even if we already have the HTML.
        # If direct HTML processing is preferred and URL context isn't vital for crawl4ai here,
        # this might need adjustment based on crawl4ai's API for direct HTML string input.
        # For now, assuming we pass the original URL for context.
        # According to crawl4ai docs, it can take html_content directly.
        output = await self.crawler.arun(html_content=html_content, url=url)
        if output and output.markdown:
            return output.markdown
        return ""
