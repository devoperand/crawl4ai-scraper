#!/usr/bin/env python3
"""
Test the selector functionality
"""

import asyncio
import httpx
from selector_utils import SelectorExtractor

async def test_selector_functionality():
    """Test CSS and XPath selectors on GitHub docs"""
    
    url = "https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages"
    
    print(f"Testing selectors on: {url}")
    print("=" * 60)
    
    # Fetch HTML
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        html_content = response.text
    
    print(f"✅ Fetched HTML ({len(html_content):,} chars)")
    
    # Initialize extractor
    extractor = SelectorExtractor()
    
    # Test different selector combinations
    test_cases = [
        {
            "name": "CSS - Article only",
            "css": ["article"],
            "xpath": []
        },
        {
            "name": "CSS - Main content",
            "css": ["main", ".markdown-body"],
            "xpath": []
        },
        {
            "name": "XPath - Article content",
            "css": [],
            "xpath": ["//article", "//main"]
        },
        {
            "name": "Combined - Best of both",
            "css": ["article", ".markdown-body"],
            "xpath": ["//main//div[@class='content']"]
        },
        {
            "name": "Documentation template",
            "template": "documentation"
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"{'='*60}")
        
        if "template" in test:
            # Use template
            template = extractor.get_template(test["template"])
            if template:
                results = extractor.test_selectors(
                    html_content,
                    template.get('css', []),
                    template.get('xpath', [])
                )
            else:
                results = {}
        else:
            # Use provided selectors
            results = extractor.test_selectors(
                html_content,
                test.get("css", []),
                test.get("xpath", [])
            )
        
        for method, content in results.items():
            if content:
                # Clean up whitespace for display
                content_preview = ' '.join(content.split())[:200] + "..."
                print(f"\n{method.upper()} Result:")
                print(f"  Length: {len(content):,} chars")
                print(f"  Preview: {content_preview}")
            else:
                print(f"\n{method.upper()}: No content extracted")
    
    # Test selector validation
    print(f"\n{'='*60}")
    print("Testing Selector Validation")
    print(f"{'='*60}")
    
    valid_css = ["article", ".content", "#main"]
    invalid_css = ["article{", "..content", "#main)"]
    
    for selector in valid_css:
        is_valid, error = extractor.validate_css_selector(selector)
        print(f"CSS '{selector}': {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
    
    for selector in invalid_css:
        is_valid, error = extractor.validate_css_selector(selector)
        print(f"CSS '{selector}': {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
    
    # Test XPath validation
    valid_xpath = ["//article", "//div[@class='content']", "//main//p"]
    invalid_xpath = ["//article[", "div[@class='content']", "//main//"]
    
    print()
    for xpath in valid_xpath:
        is_valid, error = extractor.validate_xpath(xpath)
        print(f"XPath '{xpath}': {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
    
    for xpath in invalid_xpath:
        is_valid, error = extractor.validate_xpath(xpath)
        print(f"XPath '{xpath}': {'✅ Valid' if is_valid else f'❌ Invalid'}")

if __name__ == "__main__":
    asyncio.run(test_selector_functionality())