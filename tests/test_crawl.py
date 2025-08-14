#!/usr/bin/env python3
"""
Test script for crawling GitHub documentation
"""

import asyncio
from pathlib import Path
from crawler import CrawlConfig, crawl_single
from content_filters import ConfigurableContentCleaner

async def test_github_docs():
    """Test crawling GitHub documentation page"""
    
    # Configure settings
    config = CrawlConfig()
    config.output_dir = Path("/home/elvin/crawl4ai-scraper/crawl_output")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up content extraction for documentation
    config.selector_template = 'documentation'
    config.extraction_method = 'css'
    config.content_css_selectors = ['article', 'main', '.markdown-body']
    config.exclude_css_selectors = ['.sidebar', 'nav', 'footer']
    config.cleaning_profile = 'moderate'
    config.verbose = True
    config.max_depth = 0  # Single page only
    config.rotate_user_agents = True
    
    # Test URL
    test_url = "https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages"
    
    print(f"Testing crawler with URL: {test_url}")
    print(f"Output directory: {config.output_dir}")
    print("=" * 60)
    
    # Run the crawl
    result = await crawl_single(test_url, config, deep_crawl=False)
    
    # Display results
    print("\n" + "=" * 60)
    print("CRAWL RESULTS")
    print("=" * 60)
    
    if result.get('dry_run'):
        print("This was a dry run - no content was actually crawled")
    else:
        print(f"Total URLs: {result.get('total_urls', 0)}")
        print(f"Successful: {result.get('successful', 0)}")
        print(f"Failed: {result.get('failed', 0)}")
        print(f"Content Length: {result.get('total_content_length', 0):,} chars")
        print(f"Output Directory: {result.get('output_directory', 'N/A')}")
        
        if result.get('failed_urls'):
            print("\nFailed URLs:")
            for url, error in result['failed_urls']:
                print(f"  - {url}: {error}")
        
        # Check if file was created
        expected_file = config.output_dir / "docs.github.com_en_pages_configuring-a-custom-domain-for-your-github-pages-site_about-custom-domains-and-github-pages.md"
        if expected_file.exists():
            print(f"\n✅ Output file created: {expected_file}")
            print(f"File size: {expected_file.stat().st_size:,} bytes")
            
            # Show first 500 chars of content
            with open(expected_file, 'r') as f:
                content = f.read()
                preview = content[:500] + "..." if len(content) > 500 else content
                print(f"\nContent preview:\n{preview}")
        else:
            print(f"\n❌ Expected output file not found: {expected_file}")

if __name__ == "__main__":
    asyncio.run(test_github_docs())