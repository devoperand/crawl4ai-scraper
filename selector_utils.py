#!/usr/bin/env python3
"""
Selector utilities for content extraction using CSS selectors and XPath expressions.
Provides flexible content targeting and extraction capabilities.
"""

from typing import List, Dict, Optional, Tuple, Union
from bs4 import BeautifulSoup
import lxml.html
from lxml import etree
import re


class SelectorExtractor:
    """Handles content extraction using CSS selectors and XPath expressions."""
    
    def __init__(self):
        """Initialize the selector extractor."""
        self.selector_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load predefined selector templates for common website types."""
        return {
            'blog': {
                'css': ['article', '.post-content', '.entry-content', 'main article', '.blog-post'],
                'xpath': ['//article', '//div[@class="post-content"]', '//div[contains(@class, "entry-content")]'],
                'exclude_css': ['.comments', '.sidebar', '.related-posts', '.share-buttons'],
                'exclude_xpath': ['//div[@class="comments"]', '//aside', '//div[contains(@class, "related")]']
            },
            'news': {
                'css': ['.article-body', '.story-content', '.news-content', 'article.main-content'],
                'xpath': ['//div[@class="article-body"]', '//div[contains(@class, "story-content")]'],
                'exclude_css': ['.advertisement', '.newsletter-signup', '.trending'],
                'exclude_xpath': ['//div[contains(@class, "ad")]', '//div[@class="newsletter"]']
            },
            'documentation': {
                'css': ['.markdown-body', '.doc-content', '.documentation', 'article.content'],
                'xpath': ['//div[@class="markdown-body"]', '//section[@class="content"]'],
                'exclude_css': ['.toc', '.nav-sidebar', '.footer-nav'],
                'exclude_xpath': ['//nav', '//div[@class="table-of-contents"]']
            },
            'ecommerce': {
                'css': ['.product-description', '.product-details', '.item-description'],
                'xpath': ['//div[@class="product-description"]', '//section[contains(@class, "product-info")]'],
                'exclude_css': ['.reviews', '.recommendations', '.recently-viewed'],
                'exclude_xpath': ['//div[@class="reviews"]', '//div[contains(@class, "recommended")]']
            },
            'forum': {
                'css': ['.post-body', '.message-content', '.forum-post', '.comment-body'],
                'xpath': ['//div[@class="post-body"]', '//div[contains(@class, "message")]'],
                'exclude_css': ['.signature', '.user-info', '.post-meta'],
                'exclude_xpath': ['//div[@class="signature"]', '//div[@class="user-profile"]']
            }
        }
    
    def extract_by_css(self, html: str, selectors: List[str], 
                      exclude_selectors: Optional[List[str]] = None) -> str:
        """
        Extract content using CSS selectors.
        
        Args:
            html: HTML content to extract from
            selectors: List of CSS selectors to match content
            exclude_selectors: Optional list of CSS selectors to exclude
            
        Returns:
            Extracted text content
        """
        if not html or not selectors:
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        extracted_elements = []
        
        # Extract content matching selectors
        for selector in selectors:
            try:
                elements = soup.select(selector)
                extracted_elements.extend(elements)
            except Exception as e:
                # Invalid selector, skip
                continue
        
        # Remove excluded elements
        if exclude_selectors:
            for element in extracted_elements[:]:
                for exclude_selector in exclude_selectors:
                    try:
                        if element.select_one(exclude_selector):
                            extracted_elements.remove(element)
                            break
                        # Check if element itself matches exclusion
                        parent = element.parent
                        if parent and parent.select(exclude_selector):
                            if element in parent.select(exclude_selector):
                                extracted_elements.remove(element)
                                break
                    except Exception:
                        continue
        
        # Combine text from all extracted elements
        text_parts = []
        for element in extracted_elements:
            text = element.get_text(separator=' ', strip=True)
            if text:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def extract_by_xpath(self, html: str, xpath_expressions: List[str],
                        exclude_xpath: Optional[List[str]] = None) -> str:
        """
        Extract content using XPath expressions.
        
        Args:
            html: HTML content to extract from
            xpath_expressions: List of XPath expressions to match content
            exclude_xpath: Optional list of XPath expressions to exclude
            
        Returns:
            Extracted text content
        """
        if not html or not xpath_expressions:
            return ""
        
        try:
            # Parse HTML with lxml
            tree = lxml.html.fromstring(html)
        except Exception:
            return ""
        
        extracted_elements = []
        
        # Extract content matching XPath expressions
        for xpath in xpath_expressions:
            try:
                elements = tree.xpath(xpath)
                extracted_elements.extend(elements)
            except Exception:
                # Invalid XPath, skip
                continue
        
        # Remove excluded elements
        if exclude_xpath:
            for exclude_expr in exclude_xpath:
                try:
                    excluded = tree.xpath(exclude_expr)
                    for element in excluded:
                        if element in extracted_elements:
                            extracted_elements.remove(element)
                except Exception:
                    continue
        
        # Extract text from elements
        text_parts = []
        for element in extracted_elements:
            try:
                # Get text content from element and its descendants
                text = ' '.join(element.itertext()).strip()
                if text:
                    text_parts.append(text)
            except Exception:
                continue
        
        return '\n\n'.join(text_parts)
    
    def extract_combined(self, html: str, 
                        css_selectors: Optional[List[str]] = None,
                        xpath_expressions: Optional[List[str]] = None,
                        exclude_css: Optional[List[str]] = None,
                        exclude_xpath: Optional[List[str]] = None) -> str:
        """
        Extract content using both CSS selectors and XPath expressions.
        
        Args:
            html: HTML content to extract from
            css_selectors: Optional list of CSS selectors
            xpath_expressions: Optional list of XPath expressions
            exclude_css: Optional CSS selectors to exclude
            exclude_xpath: Optional XPath expressions to exclude
            
        Returns:
            Combined extracted text content
        """
        content_parts = []
        
        # Extract using CSS selectors
        if css_selectors:
            css_content = self.extract_by_css(html, css_selectors, exclude_css)
            if css_content:
                content_parts.append(css_content)
        
        # Extract using XPath
        if xpath_expressions:
            xpath_content = self.extract_by_xpath(html, xpath_expressions, exclude_xpath)
            if xpath_content:
                content_parts.append(xpath_content)
        
        # Remove duplicates while preserving order
        if len(content_parts) > 1:
            # Simple deduplication based on content similarity
            unique_parts = []
            seen = set()
            for part in content_parts:
                # Create a normalized version for comparison
                normalized = re.sub(r'\s+', ' ', part.lower()[:100])
                if normalized not in seen:
                    seen.add(normalized)
                    unique_parts.append(part)
            return '\n\n'.join(unique_parts)
        
        return '\n\n'.join(content_parts)
    
    def validate_css_selector(self, selector: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a CSS selector.
        
        Args:
            selector: CSS selector to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Test selector with dummy HTML
            soup = BeautifulSoup('<div></div>', 'html.parser')
            soup.select(selector)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def validate_xpath(self, xpath: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an XPath expression.
        
        Args:
            xpath: XPath expression to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Test XPath with dummy HTML
            tree = lxml.html.fromstring('<div></div>')
            tree.xpath(xpath)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_template(self, template_name: str) -> Optional[Dict[str, List[str]]]:
        """
        Get a predefined selector template.
        
        Args:
            template_name: Name of the template (blog, news, etc.)
            
        Returns:
            Template dictionary or None if not found
        """
        return self.selector_templates.get(template_name)
    
    def test_selectors(self, html: str, 
                      css_selectors: Optional[List[str]] = None,
                      xpath_expressions: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Test selectors and return extracted content for comparison.
        
        Args:
            html: HTML content to test on
            css_selectors: CSS selectors to test
            xpath_expressions: XPath expressions to test
            
        Returns:
            Dictionary with extraction results for each method
        """
        results = {}
        
        if css_selectors:
            results['css'] = self.extract_by_css(html, css_selectors)
        
        if xpath_expressions:
            results['xpath'] = self.extract_by_xpath(html, xpath_expressions)
        
        if css_selectors and xpath_expressions:
            results['combined'] = self.extract_combined(
                html, css_selectors, xpath_expressions
            )
        
        return results


def extract_with_method(html: str, method: str, config: Dict[str, List[str]]) -> str:
    """
    Convenience function to extract content based on method.
    
    Args:
        html: HTML content
        method: 'css', 'xpath', or 'auto'
        config: Dictionary with selector configuration
        
    Returns:
        Extracted content
    """
    extractor = SelectorExtractor()
    
    if method == 'css':
        return extractor.extract_by_css(
            html, 
            config.get('content_css', []),
            config.get('exclude_css', [])
        )
    elif method == 'xpath':
        return extractor.extract_by_xpath(
            html,
            config.get('content_xpath', []),
            config.get('exclude_xpath', [])
        )
    else:  # auto or combined
        return extractor.extract_combined(
            html,
            config.get('content_css', []),
            config.get('content_xpath', []),
            config.get('exclude_css', []),
            config.get('exclude_xpath', [])
        )