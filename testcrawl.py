import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def main():
    #test_url = "https://www.hellofresh.es/recipes/hamburguesa-de-carne-vegana-y-patata-66e1441e323c9f705cd02eae"
    test_url = "https://pinchofyum.com/burger-bowls-with-house-sauce-and-ranch-fries"



    browser_config = BrowserConfig(
        headless=True,  
        verbose=False, # Set to True for more detailed logs
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        markdown_generator=DefaultMarkdownGenerator(
            # Using PruningContentFilter as in the example, adjust threshold if needed
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
        ),
    )
    
    print(f"Attempting to crawl: {test_url}")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=test_url,
            config=run_config
        )
        
        if result and result.markdown:
            print("\n--- Markdown Output ---")
            print(result.markdown.raw_markdown)
            # print(f"\nRaw Markdown Length: {len(result.markdown.raw_markdown)}")
            # print(f"Fit Markdown Length: {len(result.markdown.fit_markdown)}") # Fit markdown is often more concise
        else:
            print("Failed to retrieve markdown or result was empty.")

if __name__ == "__main__":
    asyncio.run(main())
