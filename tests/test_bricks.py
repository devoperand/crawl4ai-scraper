#!/usr/bin/env python3
"""
Test the generic content cleaning on Bricks Builder Academy
"""

import asyncio
from pathlib import Path
from crawler import CrawlConfig, crawl_single

async def test_bricks_academy():
    """Test generic content cleaning on Bricks Builder Academy"""
    
    # Configure settings
    config = CrawlConfig()
    config.output_dir = Path("/home/elvin/crawl4ai-scraper/bricks_output")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.verbose = True
    config.max_depth = 0  # Single page only
    config.rotate_user_agents = True
    
    # Test with documentation template since it's an educational/tutorial site
    config.selector_template = 'documentation'
    config.extraction_method = 'css'
    config.content_css_selectors = ['article', 'main', '.content', '.post-content', '.entry-content']
    config.exclude_css_selectors = ['.sidebar', '.navigation', '.menu', '.footer', '.header']
    config.cleaning_profile = 'moderate'
    
    test_url = "https://academy.bricksbuilder.io/article/create-your-own-elements/"
    
    print(f"Testing Bricks Builder Academy")
    print(f"URL: {test_url}")
    print(f"Output directory: {config.output_dir}")
    print("=" * 60)
    
    try:
        # Run the crawl
        result = await crawl_single(test_url, config, deep_crawl=False)
        
        # Display results
        print("\n" + "=" * 60)
        print("CRAWL RESULTS")
        print("=" * 60)
        
        if result.get('successful', 0) > 0:
            print(f"✅ Success!")
            print(f"Total URLs: {result.get('total_urls', 0)}")
            print(f"Successful: {result.get('successful', 0)}")
            print(f"Failed: {result.get('failed', 0)}")
            print(f"Content Length: {result.get('total_content_length', 0):,} chars")
            print(f"Output Directory: {result.get('output_directory', 'N/A')}")
            
            # Show content preview
            for res in result.get('results', []):
                if res.get('success') and res.get('markdown'):
                    preview = res['markdown'][:500] + "..." if len(res['markdown']) > 500 else res['markdown']
                    print(f"\nContent preview:\n{preview}")
                    print(f"\nTitle: {res.get('title', 'No title')}")
                    print(f"Description: {res.get('description', 'No description')}")
                    break
                    
            # Check if file was created
            from urllib.parse import urlparse
            parsed_url = urlparse(test_url)
            expected_filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_').rstrip('_') + ".md"
            expected_file = config.output_dir / expected_filename
            
            if expected_file.exists():
                print(f"\n✅ Output file created: {expected_file}")
                print(f"File size: {expected_file.stat().st_size:,} bytes")
            else:
                print(f"\n❌ Expected output file not found: {expected_file}")
                # List actual files created
                print("Files in output directory:")
                for file in config.output_dir.glob("*"):
                    print(f"  - {file.name}")
        else:
            print(f"❌ Failed: {result.get('message', 'Unknown error')}")
            if result.get('failed_urls'):
                for url, error in result['failed_urls']:
                    print(f"  {url}: {error}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bricks_academy())