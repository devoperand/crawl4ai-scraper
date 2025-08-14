#!/usr/bin/env python3
"""
Test User-Agent rotation
"""

import asyncio
from pathlib import Path
from crawler import CrawlConfig, ContentCrawler
import random

async def test_user_agent_rotation():
    """Test that User-Agent rotation is working"""
    
    print("Testing User-Agent Rotation")
    print("=" * 60)
    
    # Configure settings
    config = CrawlConfig()
    config.output_dir = Path("/home/elvin/crawl4ai-scraper/crawl_output")
    config.rotate_user_agents = True
    config.verbose = True
    
    print(f"User-Agent rotation enabled: {config.rotate_user_agents}")
    print(f"Available User-Agents: {len(config.user_agents_list)}")
    print("\nUser-Agent list:")
    for i, ua in enumerate(config.user_agents_list, 1):
        print(f"  {i}. {ua[:60]}...")
    
    # Test URLs
    test_urls = [
        "https://docs.github.com/en/pages",
        "https://docs.github.com/en/pages/quickstart",
        "https://docs.github.com/en/pages/getting-started-with-github-pages"
    ]
    
    print(f"\n{'='*60}")
    print("Testing rotation on multiple URLs:")
    print(f"{'='*60}")
    
    # Create content crawler
    crawler = ContentCrawler(config)
    
    # Note: The actual User-Agent selection happens inside crawl_single_url
    # We can see it in the verbose output
    print("\nCrawling multiple URLs - watch for User-Agent in output:")
    result = await crawler.crawl_urls(test_urls[:2])  # Just crawl 2 URLs for speed
    
    print(f"\n{'='*60}")
    print("Results:")
    print(f"{'='*60}")
    print(f"Total URLs: {result.get('total_urls', 0)}")
    print(f"Successful: {result.get('successful', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
    
    # Demonstrate manual rotation
    print(f"\n{'='*60}")
    print("Manual User-Agent selection demonstration:")
    print(f"{'='*60}")
    for i in range(5):
        selected_ua = random.choice(config.user_agents_list)
        print(f"  Selection {i+1}: {selected_ua[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_user_agent_rotation())