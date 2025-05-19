import asyncio
import sys
import httpx
from crawl4ai import AsyncWebCrawler

# Set asyncio event loop policy for Windows if applicable
# if sys.platform == "win32":
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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
    async def _perform_crawl_async(self, html_content: str, url: str) -> str:
        # This async function will be run inside asyncio.run() in a separate thread
        # It should get a fresh event loop that respects the global policy
        print(f"MD_CONVERTER (_perform_crawl_async thread): Current event loop policy: {type(asyncio.get_event_loop_policy())}", flush=True)
        print(f"MD_CONVERTER (_perform_crawl_async thread): Current event loop: {type(asyncio.get_event_loop())}", flush=True)
        try:
            async with AsyncWebCrawler() as crawler:
                crawl_result = await crawler.arun(html_content=html_content, url=url)
                if crawl_result and crawl_result.markdown:
                    return crawl_result.markdown
                return ""
        except Exception as e_crawl:
            print(f"MD_CONVERTER (_perform_crawl_async thread): Error during crawl4ai processing: {e_crawl}", flush=True)
            raise # Re-raise to be caught by the sync wrapper

    def _sync_crawl_wrapper(self, html_content: str, url: str) -> str:
        # This synchronous function is executed in a separate thread by asyncio.to_thread
        print(f"MD_CONVERTER (_sync_crawl_wrapper thread): Starting. Will call asyncio.run().", flush=True)
        try:
            # asyncio.run() will create and manage a new event loop for _perform_crawl_async
            # This new loop should be a ProactorEventLoop due to the globally set policy
            return asyncio.run(self._perform_crawl_async(html_content, url))
        except Exception as e_run:
            print(f"MD_CONVERTER (_sync_crawl_wrapper thread): asyncio.run() failed: {e_run}", flush=True)
            # Consider how to propagate this error. For now, return empty string or re-raise.
            return "" # Or re-raise specific errors if needed by caller

    async def to_markdown(self, html_content: str, url: str) -> str:
        print(f"MD_CONVERTER (to_markdown main thread): Current event loop policy: {type(asyncio.get_event_loop_policy())}", flush=True)
        print(f"MD_CONVERTER (to_markdown main thread): Current event loop: {type(asyncio.get_event_loop())}", flush=True)
        print("MD_CONVERTER (to_markdown main thread): Attempting to convert HTML to Markdown using asyncio.to_thread...", flush=True)
        
        if not html_content:
            print("MD_CONVERTER (to_markdown main thread): No HTML content provided.", flush=True)
            return ""

        try:
            # Run the synchronous wrapper (which internally uses asyncio.run) in a separate thread
            output_markdown = await asyncio.to_thread(self._sync_crawl_wrapper, html_content, url)
            print(f"MD_CONVERTER (to_markdown main thread): Conversion completed. Markdown length: {len(output_markdown)}", flush=True)
            return output_markdown
        except Exception as e:
            print(f"MD_CONVERTER (to_markdown main thread): Error calling asyncio.to_thread or _sync_crawl_wrapper: {e}", flush=True)
            # Re-raise to be caught by the service layer, or handle as appropriate
            raise
