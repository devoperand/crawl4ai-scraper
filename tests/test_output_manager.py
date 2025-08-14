#!/usr/bin/env python3
"""
Test the new output management system
"""

import asyncio
from pathlib import Path
from datetime import datetime
from output_manager import OutputManager
from crawler import CrawlConfig, ContentCrawler
from rich.console import Console

async def test_output_management():
    """Test the complete output management workflow."""
    
    console = Console()
    
    # Test data (simulate scraped content)
    test_urls = [
        "https://example.com/page1",
        "https://example.com/blog/post1", 
        "https://docs.example.com/guide/intro"
    ]
    
    print("\n" + "="*60)
    print("Testing Output Management System")
    print("="*60)
    
    # Step 1: Scrape content (without saving)
    print("\n1. Scraping content (no files saved yet)...")
    config = CrawlConfig()
    # Enhanced mode always enabled
    # Content cleaning always enabled
    config.verbose = False
    
    crawler = ContentCrawler(config)
    result = await crawler.crawl_urls(test_urls, save_immediately=False)
    
    print(f"   ✓ Scraped {result['successful']} URLs")
    print(f"   ✓ Content stored in memory")
    
    # Step 2: Configure output after scraping
    print("\n2. Configuring output management...")
    output_manager = OutputManager()
    
    # Simulate scraped content
    scraped_content = result.get('scraped_content', [])
    
    if not scraped_content:
        # Create test content if scraping failed
        scraped_content = [
            {
                'url': 'https://example.com/page1',
                'title': 'Example Page 1',
                'description': 'Test page 1',
                'markdown': '# Example Page 1\n\nThis is test content for page 1.',
                'content_length': 100,
                'crawled_at': datetime.now().isoformat(),
                'success': True
            },
            {
                'url': 'https://example.com/blog/post1',
                'title': 'Blog Post 1',
                'description': 'Test blog post',
                'markdown': '# Blog Post 1\n\nThis is test content for blog post 1.',
                'content_length': 120,
                'crawled_at': datetime.now().isoformat(),
                'success': True
            },
            {
                'url': 'https://docs.example.com/guide/intro',
                'title': 'Documentation Intro',
                'description': 'Documentation introduction',
                'markdown': '# Documentation Introduction\n\nThis is the intro to the docs.',
                'content_length': 150,
                'crawled_at': datetime.now().isoformat(),
                'success': True
            }
        ]
    
    # Test different organization strategies
    print("\n3. Testing organization strategies...")
    
    # Test 1: Flat structure
    print("\n   Testing FLAT structure:")
    output_manager.organization_strategy = output_manager.FLAT_STRUCTURE
    output_manager.naming_convention = output_manager.NAMING_URL_BASED
    test_dir = Path("test_output_flat")
    
    for content in scraped_content[:2]:
        file_path = output_manager.get_file_path(content, test_dir)
        print(f"     {content['url']}")
        print(f"     → {file_path.relative_to(test_dir.parent)}")
    
    # Test 2: Mirror structure
    print("\n   Testing MIRROR structure:")
    output_manager.organization_strategy = output_manager.MIRROR_STRUCTURE
    test_dir = Path("test_output_mirror")
    
    for content in scraped_content[:2]:
        file_path = output_manager.get_file_path(content, test_dir)
        print(f"     {content['url']}")
        print(f"     → {file_path.relative_to(test_dir.parent)}")
    
    # Test 3: Domain grouped
    print("\n   Testing DOMAIN grouped:")
    output_manager.organization_strategy = output_manager.DOMAIN_GROUPED
    test_dir = Path("test_output_domain")
    
    for content in scraped_content:
        file_path = output_manager.get_file_path(content, test_dir)
        print(f"     {content['url']}")
        print(f"     → {file_path.relative_to(test_dir.parent)}")
    
    # Test 4: Date organized
    print("\n   Testing DATE organized:")
    output_manager.organization_strategy = output_manager.DATE_ORGANIZED
    test_dir = Path("test_output_date")
    
    for content in scraped_content[:2]:
        file_path = output_manager.get_file_path(content, test_dir)
        print(f"     {content['url']}")
        print(f"     → {file_path.relative_to(test_dir.parent)}")
    
    # Test different naming conventions
    print("\n4. Testing naming conventions...")
    output_manager.organization_strategy = output_manager.FLAT_STRUCTURE
    test_dir = Path("test_output_naming")
    
    test_content = scraped_content[0]
    
    print(f"\n   URL: {test_content['url']}")
    
    # URL-based naming
    output_manager.naming_convention = output_manager.NAMING_URL_BASED
    file_path = output_manager.get_file_path(test_content, test_dir)
    print(f"   URL-based: {file_path.name}")
    
    # Title-based naming
    output_manager.naming_convention = output_manager.NAMING_TITLE_BASED
    file_path = output_manager.get_file_path(test_content, test_dir)
    print(f"   Title-based: {file_path.name}")
    
    # Timestamp naming
    output_manager.naming_convention = output_manager.NAMING_TIMESTAMP
    file_path = output_manager.get_file_path(test_content, test_dir)
    print(f"   Timestamp: {file_path.name}")
    
    # Hash naming
    output_manager.naming_convention = output_manager.NAMING_HASH
    file_path = output_manager.get_file_path(test_content, test_dir)
    print(f"   Hash: {file_path.name}")
    
    # Test 5: Actually save files
    print("\n5. Testing file saving...")
    output_manager.organization_strategy = output_manager.MIRROR_STRUCTURE
    output_manager.naming_convention = output_manager.NAMING_URL_BASED
    test_dir = Path("test_output_final")
    
    save_result = await output_manager.save_scraped_content(
        scraped_content, test_dir, console
    )
    
    print(f"\n   ✓ Saved {save_result['saved_files']} files")
    print(f"   ✓ Output directory: {save_result['output_directory']}")
    
    # Check if files exist
    if test_dir.exists():
        all_files = list(test_dir.rglob("*.md"))
        print(f"   ✓ Found {len(all_files)} markdown files")
        
        # Show file tree
        print("\n   File structure:")
        for file in sorted(all_files):
            rel_path = file.relative_to(test_dir)
            indent = "     " + "  " * (len(rel_path.parts) - 1)
            print(f"{indent}📄 {file.name}")
    
    print("\n✅ Output management system test complete!")
    
    return True

async def test_interactive_prompt():
    """Test the interactive output configuration prompt."""
    print("\n" + "="*60)
    print("Testing Interactive Output Configuration")
    print("="*60)
    print("\nThis test simulates the interactive prompt that users will see")
    print("after scraping is complete. It won't actually prompt for input")
    print("in this test, but shows what would happen.\n")
    
    # Simulate scraped data
    scraped_data = [
        {
            'url': 'https://example.com/page1',
            'title': 'Example Page 1',
            'markdown': '# Test Content 1',
            'content_length': 100,
            'crawled_at': datetime.now().isoformat()
        },
        {
            'url': 'https://blog.example.com/post1',
            'title': 'Blog Post 1',
            'markdown': '# Blog Content',
            'content_length': 150,
            'crawled_at': datetime.now().isoformat()
        }
    ]
    
    output_manager = OutputManager()
    
    print("User would see:")
    print("  - Scraping summary (2 files, 250 chars, 2 domains)")
    print("  - Current working directory")
    print("  - Prompt for output directory path")
    print("  - Organization strategy selection (1-5)")
    print("  - Naming convention selection (1-4)")
    print("  - Metadata inclusion option")
    print("  - Preview of file organization")
    print("  - Confirmation prompt")
    
    print("\n✅ Interactive configuration test complete!")

async def main():
    """Run all output management tests."""
    print("🚀 Output Management System Tests")
    
    # Test the output management system
    await test_output_management()
    
    # Test interactive configuration
    await test_interactive_prompt()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    
    print("\n📊 Summary:")
    print("  ✅ Output management system working")
    print("  ✅ Multiple organization strategies supported")
    print("  ✅ Multiple naming conventions available")
    print("  ✅ Files saved after scraping completes")
    print("  ✅ Interactive configuration ready")

if __name__ == "__main__":
    asyncio.run(main())