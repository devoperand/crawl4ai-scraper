#!/usr/bin/env python3
"""
Test the generic content cleaning on different types of websites
"""

import asyncio
from pathlib import Path
from crawler import CrawlConfig, crawl_single

async def test_generic_cleaning():
    """Test generic content cleaning on various website types"""
    
    # Configure settings
    config = CrawlConfig()
    config.output_dir = Path("/home/elvin/crawl4ai-scraper/test_generic_output")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.verbose = True
    config.max_depth = 0  # Single page only
    config.rotate_user_agents = True
    
    # Test different website types
    test_urls = [
        {
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "name": "Python Docs",
            "template": "documentation"
        },
        {
            "url": "https://reactjs.org/docs/getting-started.html", 
            "name": "React Docs",
            "template": "documentation"  
        },
        {
            "url": "https://www.example.com",
            "name": "Simple Site",
            "template": None
        }
    ]
    
    for test in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print(f"URL: {test['url']}")
        print(f"{'='*60}")
        
        # Configure for this test
        if test['template']:
            config.selector_template = test['template']
        else:
            config.selector_template = None
            
        try:
            # Run the crawl
            result = await crawl_single(test['url'], config, deep_crawl=False)
            
            # Display results
            if result.get('successful', 0) > 0:
                print(f"✅ Success: {result['total_content_length']:,} chars extracted")
                
                # Show content preview
                for res in result.get('results', []):
                    if res.get('success') and res.get('markdown'):
                        preview = res['markdown'][:300] + "..." if len(res['markdown']) > 300 else res['markdown']
                        print(f"\nContent preview:\n{preview}")
                        break
            else:
                print(f"❌ Failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_generic_cleaning())