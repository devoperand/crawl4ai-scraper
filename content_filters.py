#!/usr/bin/env python3
"""
Generic content filtering and cleaning module.
Replaces hardcoded site-specific logic with generic heuristics.
"""

import re
from typing import List, Dict, Tuple, Optional
from selector_utils import SelectorExtractor


class ContentCleaner:
    """Generic content cleaning based on common patterns and heuristics."""
    
    def __init__(self):
        # Common navigation indicators (generic patterns)
        self.nav_indicators = [
            'search', 'menu', 'navigation', 'navbar', 'sidebar', 'breadcrumb',
            'home', 'contact', 'about', 'login', 'sign in', 'sign up', 'register',
            'skip to content', 'skip to main', 'toggle menu', 'close menu'
        ]
        
        # Common footer indicators (generic patterns)
        self.footer_indicators = [
            'copyright', '©', 'all rights reserved', 'privacy policy', 'terms of service',
            'terms of use', 'cookie policy', 'was this page helpful', 'feedback',
            'x.com', 'twitter.com', 'linkedin.com', 'facebook.com', 'github.com',
            'on this page', 'yesno', 'rate this page', 'improve this page',
            'last modified', 'last updated', 'edit this page'
        ]
        
        # Content quality indicators (what suggests main content)
        self.content_indicators = [
            # Generic heading patterns
            lambda line: self._is_main_heading(line),
            lambda line: self._is_section_heading(line),
            # Paragraph content
            lambda line: self._is_substantial_paragraph(line),
            # List content
            lambda line: self._is_content_list(line),
            # Code blocks
            lambda line: self._is_code_content(line),
        ]
        
        # Skip patterns (things to always remove)
        self.skip_patterns = [
            'copy page',
            'copy link', 
            'share this',
            'print this page',
            'bookmark',
            'loading...',
            'please wait',
            'skip to content',
            'toggle navigation'
        ]
    
    def clean_markdown_content(self, markdown: str, title: str = "") -> str:
        """
        Clean markdown content using generic heuristics.
        
        Args:
            markdown: Raw markdown content
            title: Page title for context (optional)
            
        Returns:
            Cleaned markdown content
        """
        if not markdown:
            return markdown
        
        # MAJOR FIX: The markdown from crawl4ai comes as one long line with no breaks
        # We need to add proper paragraph breaks based on sentence structure
        
        # First, fix escaped newlines if they exist
        if '\\n' in markdown and markdown.count('\\n') > markdown.count('\n'):
            markdown = markdown.replace('\\n', '\n')
        
        # If the content is mostly one long line, fix it
        if markdown.count('\n') < 10 and len(markdown) > 500:
            # Add line breaks after sentences (but not after "e.g." or "i.e." etc)
            markdown = re.sub(r'(?<![eg])(?<![ie])\. ([A-Z])', r'.\n\n\1', markdown)
            
            # Generic pattern: Fix "Note" and "Tip" formatting
            markdown = re.sub(r'(?<!\n)(Tip|Note|Warning|Important|Caution)\s+([A-Z])', r'\n\n**\1:** \2', markdown)
            
            # Generic pattern: Add section breaks for common section starters
            markdown = re.sub(r'(?<!\n)(Using|Creating|Configuring|Setting up|Installing|Troubleshooting|Managing|Building|Deploying)\s+([a-z][^.]*?)(?=\s[A-Z])', r'\n\n## \1 \2', markdown)
            
            # Generic pattern: Detect and format simple tables (3+ items with similar structure)
            # This is a more generic approach than hardcoding specific content
            lines_for_table_check = markdown.split('.')
            for i, line in enumerate(lines_for_table_check):
                words = line.strip().split()
                # Look for patterns like "ItemType example.com AnotherType another.example"
                if len(words) >= 6 and len([w for w in words if '.' in w and len(w) > 5]) >= 2:
                    # This might be tabular data, but we'll let CSS selectors handle it instead
                    pass
        
        lines = markdown.split('\n')
        cleaned_lines = []
        content_started = False
        in_footer = False
        skip_navigation_section = True
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines at the beginning
            if not content_started and not stripped:
                continue
            
            # Check if we've hit footer content
            if not in_footer and self._is_footer_line(stripped):
                in_footer = True
                break
            
            # Skip lines that match skip patterns
            if self._should_skip_line(stripped):
                continue
            
            # Skip navigation sections more aggressively
            if skip_navigation_section and self._is_navigation_section(stripped, lines, i):
                continue
            
            # Check for main content start
            if not content_started:
                if self._is_main_content_start(stripped, title, lines, i):
                    content_started = True
                    skip_navigation_section = False  # Stop skipping once we hit main content
                else:
                    # Skip navigation/header content
                    continue
            
            # Additional filtering for content that got through
            if content_started and self._is_likely_navigation(stripped):
                continue
            
            # Process and enhance the line
            processed_line = self.enhance_markdown_formatting(line)
            cleaned_lines.append(processed_line)
        
        # Join and clean up extra whitespace
        result = '\n'.join(cleaned_lines)
        return self._clean_whitespace(result)
    
    def _is_main_content_start(self, line: str, title: str, all_lines: List[str], index: int) -> bool:
        """
        Determine if this line marks the start of main content.
        Uses generic heuristics instead of hardcoded patterns.
        """
        line_lower = line.lower()
        
        # Main heading (likely the page title or close to it)
        if line.startswith('# '):
            heading_text = line[2:].strip().lower()
            # Avoid navigation headings
            if not any(nav in heading_text for nav in ['home', 'menu', 'navigation', 'page']):
                # If we have a title, see if this heading is similar
                if title:
                    title_words = set(title.lower().split())
                    heading_words = set(heading_text.split())
                    # If at least 50% overlap, consider it main content
                    if len(title_words & heading_words) / max(len(title_words), 1) >= 0.5:
                        return True
                # Any substantial heading after skipping nav
                if len(heading_text) > 10:
                    return True
        
        # Section headings (##, ###, etc.)
        if re.match(r'^#{2,6}\\s+\\w', line) and len(line.strip()) > 10:
            heading_text = re.sub(r'^#{2,6}\\s+', '', line).strip().lower()
            # Skip nav-like headings
            if not any(nav in heading_text for nav in self.nav_indicators):
                return True
        
        # Substantial paragraph content
        if self._is_substantial_paragraph(line):
            return True
        
        # Content lists (not navigation lists)
        if self._is_content_list(line):
            return True
        
        # Code blocks or technical content
        if line.startswith('```') or line.strip().startswith('`'):
            return True
        
        return False
    
    def _is_main_heading(self, line: str) -> bool:
        """Check if line is a main heading (# Title)."""
        return line.startswith('# ') and len(line.strip()) > 3
    
    def _is_section_heading(self, line: str) -> bool:
        """Check if line is a section heading (##, ###, etc.)."""
        return re.match(r'^#{2,6}\\s+\\w', line) is not None
    
    def _is_substantial_paragraph(self, line: str) -> bool:
        """Check if line looks like substantial paragraph content."""
        stripped = line.strip()
        # Must be reasonably long and contain actual words
        if len(stripped) < 20:
            return False
        # Should contain multiple words
        words = stripped.split()
        if len(words) < 4:
            return False
        # Should not be navigation-like
        if any(nav in stripped.lower() for nav in self.nav_indicators[:5]):  # Most common nav terms
            return False
        return True
    
    def _is_content_list(self, line: str) -> bool:
        """Check if line is part of a content list (not navigation)."""
        stripped = line.strip()
        # List item markers
        if not (stripped.startswith('- ') or stripped.startswith('* ') or 
               re.match(r'^\\d+\\.\\s', stripped)):
            return False
        # Content should be substantial
        if len(stripped) < 10:
            return False
        # Should not be navigation
        if any(nav in stripped.lower() for nav in self.nav_indicators):
            return False
        return True
    
    def _is_code_content(self, line: str) -> bool:
        """Check if line contains code content."""
        stripped = line.strip()
        return (stripped.startswith('```') or 
               stripped.startswith('`') or
               '    ' in line[:4])  # Indented code
    
    def _is_navigation_section(self, line: str, all_lines: List[str], index: int) -> bool:
        """Check if this line is part of a navigation section."""
        line_lower = line.lower()
        
        # Common navigation section indicators
        nav_section_starts = [
            'search', 'navigation', 'menu', 'breadcrumb', 
            'skip to', 'table of contents', 'getting started',
            '##### getting started', '##### build with', '##### deployment',
            '##### administration', '##### configuration', '##### reference'
        ]
        
        return any(nav_start in line_lower for nav_start in nav_section_starts)
    
    def _is_likely_navigation(self, line: str) -> bool:
        """Additional check for navigation content that got through."""
        line_lower = line.lower()
        
        # Link-heavy lines (likely navigation menus)
        if line.count('[') > 3 and line.count('](') > 3:
            return True
        
        # Lines with common navigation terms
        nav_terms = ['overview', 'quickstart', 'getting started', 'reference', 'home']
        if any(term in line_lower for term in nav_terms) and len(line.strip()) < 100:
            return True
            
        return False
    
    def _is_footer_line(self, line: str) -> bool:
        """Check if line indicates start of footer content."""
        line_lower = line.lower()
        return any(footer in line_lower for footer in self.footer_indicators)
    
    def _should_skip_line(self, line: str) -> bool:
        """Check if line should be completely skipped."""
        line_lower = line.lower()
        return any(pattern in line_lower for pattern in self.skip_patterns)
    
    def enhance_markdown_formatting(self, line: str) -> str:
        """
        Enhance markdown formatting for better documentation.
        Generic improvements without site-specific logic.
        """
        if not line.strip():
            return line
        
        # Convert common documentation elements to proper markdown
        line = self._enhance_admonitions(line)
        line = self._enhance_code_blocks(line)
        line = self._enhance_links(line)
        
        return line
    
    def _enhance_admonitions(self, line: str) -> str:
        """Convert common admonition patterns to markdown."""
        stripped = line.strip()
        
        # Note/Tip/Warning patterns
        if stripped.startswith('Note:') or stripped.startswith('NOTE:'):
            return line.replace('Note:', '> **Note:**').replace('NOTE:', '> **Note:**')
        elif stripped.startswith('Tip:') or stripped.startswith('TIP:'):
            return line.replace('Tip:', '> **Tip:**').replace('TIP:', '> **Tip:**')
        elif stripped.startswith('Warning:') or stripped.startswith('WARNING:'):
            return line.replace('Warning:', '> **⚠️ Warning:**').replace('WARNING:', '> **⚠️ Warning:**')
        elif stripped.startswith('Important:') or stripped.startswith('IMPORTANT:'):
            return line.replace('Important:', '> **❗ Important:**').replace('IMPORTANT:', '> **❗ Important:**')
        
        return line
    
    def _enhance_code_blocks(self, line: str) -> str:
        """Improve code block formatting."""
        stripped = line.strip()
        
        # Detect language hints for code blocks
        if stripped == '```' and hasattr(self, '_prev_line'):
            prev = getattr(self, '_prev_line', '').lower()
            if any(lang in prev for lang in ['bash', 'python', 'javascript', 'json', 'yaml']):
                # This would need more context to implement properly
                pass
        
        self._prev_line = stripped
        return line
    
    def _enhance_links(self, line: str) -> str:
        """Clean up link formatting."""
        # Remove common link tracking parameters
        line = re.sub(r'(\\?utm_[^\\s]+)', '', line)
        line = re.sub(r'(\\?ref=[^\\s]+)', '', line)
        
        return line
    
    def _clean_whitespace(self, content: str) -> str:
        """Clean up excessive whitespace."""
        # Remove more than 2 consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in content.split('\n')]
        
        # Remove empty lines at start and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        return '\n'.join(lines)


class ConfigurableContentCleaner(ContentCleaner):
    """Extended version with configurable patterns and selector support."""
    
    def __init__(self, 
                 custom_nav_patterns: Optional[List[str]] = None, 
                 custom_footer_patterns: Optional[List[str]] = None,
                 custom_skip_patterns: Optional[List[str]] = None,
                 content_css_selectors: Optional[List[str]] = None,
                 content_xpath: Optional[List[str]] = None,
                 exclude_css_selectors: Optional[List[str]] = None,
                 exclude_xpath: Optional[List[str]] = None,
                 extraction_method: str = 'auto',
                 min_content_length: int = 100,
                 preserve_elements: Optional[List[str]] = None,
                 cleaning_profile: str = 'moderate'):
        """
        Initialize with optional custom patterns and selectors.
        
        Args:
            custom_nav_patterns: Additional navigation patterns to detect
            custom_footer_patterns: Additional footer patterns to detect  
            custom_skip_patterns: Additional patterns to skip
            content_css_selectors: CSS selectors for main content
            content_xpath: XPath expressions for main content
            exclude_css_selectors: CSS selectors to exclude
            exclude_xpath: XPath expressions to exclude
            extraction_method: 'css', 'xpath', or 'auto'
            min_content_length: Minimum length for valid content blocks
            preserve_elements: HTML elements to always preserve
            cleaning_profile: 'strict', 'moderate', or 'minimal'
        """
        super().__init__()
        
        # Extend pattern lists
        if custom_nav_patterns:
            self.nav_indicators.extend(custom_nav_patterns)
        if custom_footer_patterns:
            self.footer_indicators.extend(custom_footer_patterns)
        if custom_skip_patterns:
            self.skip_patterns.extend(custom_skip_patterns)
        
        # Selector configuration
        self.content_css_selectors = content_css_selectors or []
        self.content_xpath = content_xpath or []
        self.exclude_css_selectors = exclude_css_selectors or []
        self.exclude_xpath = exclude_xpath or []
        self.extraction_method = extraction_method
        
        # Content filtering settings
        self.min_content_length = min_content_length
        self.preserve_elements = preserve_elements or ['code', 'pre', 'blockquote']
        self.cleaning_profile = cleaning_profile
        
        # Initialize selector extractor
        self.selector_extractor = SelectorExtractor()
        
        # Apply cleaning profile
        self._apply_cleaning_profile(cleaning_profile)
    
    def _apply_cleaning_profile(self, profile: str):
        """Apply predefined cleaning profile settings."""
        if profile == 'strict':
            # Aggressive cleaning
            self.min_content_length = 200
            self.nav_indicators.extend(['menu', 'nav', 'sidebar', 'header', 'footer'])
            self.skip_patterns.extend(['advertisement', 'sponsored', 'promotion'])
        elif profile == 'minimal':
            # Light cleaning
            self.min_content_length = 50
            # Keep original indicators without adding more
        # 'moderate' uses default settings
    
    def extract_with_selectors(self, html: str) -> Optional[str]:
        """
        Extract content using configured selectors.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted content or None if no selectors configured
        """
        if not (self.content_css_selectors or self.content_xpath):
            return None
        
        if self.extraction_method == 'css':
            return self.selector_extractor.extract_by_css(
                html, self.content_css_selectors, self.exclude_css_selectors
            )
        elif self.extraction_method == 'xpath':
            return self.selector_extractor.extract_by_xpath(
                html, self.content_xpath, self.exclude_xpath
            )
        else:  # auto or combined
            return self.selector_extractor.extract_combined(
                html, 
                self.content_css_selectors, self.content_xpath,
                self.exclude_css_selectors, self.exclude_xpath
            )
    
    def clean_with_selectors(self, html: str, markdown: str, title: str = "") -> str:
        """
        Clean content with selector-based extraction first, then apply cleaning.
        
        Args:
            html: Raw HTML content
            markdown: Markdown content (may be ignored if selectors are used)
            title: Page title for context
            
        Returns:
            Cleaned content
        """
        # Try selector-based extraction first
        selector_content = self.extract_with_selectors(html)
        
        if selector_content and len(selector_content) >= self.min_content_length:
            # Apply markdown cleaning to selector-extracted content
            return self.clean_markdown_content(selector_content, title)
        
        # Fall back to regular markdown cleaning
        return self.clean_markdown_content(markdown, title)
    
    def set_selector_template(self, template_name: str):
        """
        Load and apply a predefined selector template.
        
        Args:
            template_name: Name of template (blog, news, documentation, etc.)
        """
        template = self.selector_extractor.get_template(template_name)
        if template:
            self.content_css_selectors = template.get('css', [])
            self.content_xpath = template.get('xpath', [])
            self.exclude_css_selectors = template.get('exclude_css', [])
            self.exclude_xpath = template.get('exclude_xpath', [])