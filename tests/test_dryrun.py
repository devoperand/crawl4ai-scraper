#!/usr/bin/env python3
"""
Test dry run mode
"""

import asyncio
from pathlib import Path
from crawler import CrawlConfig, crawl_with_discovery

async def test_dry_run():
    """Test dry run mode for URL discovery"""
    
    # Configure settings
    config = CrawlConfig()
    config.output_dir = Path("/home/elvin/crawl4ai-scraper/crawl_output")
    config.dry_run = True  # Enable dry run mode
    config.max_depth = 1   # Discover one level deep
    config.max_pages = 10  # Limit pages
    config.verbose = True
    
    # Test URL
    test_url = "https://docs.github.com/en/pages"
    
    print(f"Testing DRY RUN mode")
    print(f"Starting URL: {test_url}")
    print(f"Max depth: {config.max_depth}")
    print(f"Max pages: {config.max_pages}")
    print("=" * 60)
    
    # Run discovery in dry run mode
    result = await crawl_with_discovery(
        test_url, 
        config,
        patterns=["https://docs.github.com/en/pages/*"],
        exclude_patterns=None
    )
    
    # Display dry run results
    print("\n" + "=" * 60)
    print("DRY RUN RESULTS")
    print("=" * 60)
    
    if result.get('dry_run'):
        print(f"✅ Dry run completed successfully")
        print(f"Total URLs discovered: {result.get('total_urls', 0)}")
        
        # Show discovered URLs
        discovered_urls = result.get('discovered_urls', [])
        if discovered_urls:
            print(f"\nURLs that WOULD be crawled (showing first 10):")
            for i, url in enumerate(discovered_urls[:10], 1):
                print(f"  {i}. {url}")
            if len(discovered_urls) > 10:
                print(f"  ... and {len(discovered_urls) - 10} more")
        
        # Show file preview
        file_preview = result.get('file_preview', [])
        if file_preview:
            print(f"\nSample output file paths:")
            for i, path in enumerate(file_preview[:5], 1):
                print(f"  {i}. {path}")
        
        print(f"\n{result.get('message', '')}")
        print("\n💡 Note: No content was actually crawled. This was a dry run.")
        print("To perform the actual crawl, set config.dry_run = False")
    else:
        print("❌ Not a dry run result")

if __name__ == "__main__":
    asyncio.run(test_dry_run())