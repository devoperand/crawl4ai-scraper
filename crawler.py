#!/usr/bin/env python3
"""
Core crawling logic for crawl4ai-interactive.
Handles URL discovery, pattern matching, and content extraction using Crawl4AI.
"""

import asyncio
import re
import fnmatch
import random
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin, unquote
import json
from datetime import datetime
import aiofiles
from content_filters import ContentCleaner, ConfigurableContentCleaner

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai import BM25ContentFilter, PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from output_manager import OutputManager


class CrawlConfig:
    """Configuration for crawling operations."""
    def __init__(self):
        self.max_depth = 2
        self.max_pages = 50
        self.include_external = False
        self.concurrent_limit = 3
        self.delay_between_requests = 1.0
        self.cache_mode = True
        self.timeout = 30
        self.retry_attempts = 2
        self.output_dir = Path("output")
        self.organize_by_structure = False
        self.verbose = True
        self.user_agent = None
        self.headers = {}
        self.proxy = None
        self.rotate_user_agents = True  # Enable User-Agent rotation by default
        self.user_agents_list = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            # Firefox on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            # Safari on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.dry_run = False  # Dry run mode flag
        
        # Content extraction configuration
        self.extraction_method = 'auto'  # 'css', 'xpath', or 'auto'
        self.content_css_selectors = []  # CSS selectors for main content
        self.content_xpath = []  # XPath expressions for main content
        self.exclude_css_selectors = []  # CSS selectors to exclude
        self.exclude_xpath = []  # XPath expressions to exclude
        self.cleaning_profile = 'moderate'  # 'strict', 'moderate', 'minimal', 'custom'
        self.selector_template = None  # Optional preset template name
        self.min_content_length = 100  # Minimum content length
        self.preserve_elements = ['code', 'pre', 'blockquote']  # Elements to preserve
        
        # Custom cleaning patterns
        self.custom_nav_patterns = []
        self.custom_footer_patterns = []
        self.custom_skip_patterns = []


class URLPatternHandler:
    """Handles URL pattern matching and wildcard conversion."""
    
    @staticmethod
    def convert_wildcard_to_regex(pattern: str) -> str:
        """
        Convert wildcard pattern to regex.
        * matches any sequence of characters (except /)
        ** matches any sequence including /
        ? matches single character
        """
        # Escape special regex characters except our wildcards
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('+', r'\+')
        pattern = pattern.replace('^', r'\^')
        pattern = pattern.replace('$', r'\$')
        pattern = pattern.replace('(', r'\(')
        pattern = pattern.replace(')', r'\)')
        pattern = pattern.replace('[', r'\[')
        pattern = pattern.replace(']', r'\]')
        pattern = pattern.replace('{', r'\{')
        pattern = pattern.replace('}', r'\}')
        
        # Convert wildcards
        pattern = pattern.replace('**', '<<<DOUBLESTAR>>>')
        pattern = pattern.replace('*', '[^/]*')
        pattern = pattern.replace('<<<DOUBLESTAR>>>', '.*')
        pattern = pattern.replace('?', '.')
        
        return f'^{pattern}$'
    
    @staticmethod
    def match_url_pattern(url: str, patterns: List[str], exclude_patterns: List[str] = None) -> bool:
        """Check if URL matches any of the patterns and not excluded."""
        # Check exclusions first
        if exclude_patterns:
            for pattern in exclude_patterns:
                regex = URLPatternHandler.convert_wildcard_to_regex(pattern)
                if re.match(regex, url):
                    return False
        
        # Check inclusions
        if not patterns:
            return True
        
        for pattern in patterns:
            regex = URLPatternHandler.convert_wildcard_to_regex(pattern)
            if re.match(regex, url):
                return True
        
        return False


class URLDiscovery:
    """Handles URL discovery and link extraction."""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.discovered_urls: Set[str] = set()
        self.url_relationships: Dict[str, List[str]] = {}
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain."""
        return self.extract_domain(url1) == self.extract_domain(url2)
    
    def normalize_url(self, url: str, base_url: str = None) -> str:
        """Normalize and resolve relative URLs."""
        if base_url:
            url = urljoin(base_url, url)
        
        # Remove fragment
        parsed = urlparse(url)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
        
        # Remove trailing slash unless it's the root
        if url.endswith('/') and len(parsed.path) > 1:
            url = url[:-1]
        
        return url
    
    async def discover_urls(self, start_url: str, patterns: List[str] = None, 
                          exclude_patterns: List[str] = None) -> List[str]:
        """
        Discover URLs starting from a given URL using BFS strategy.
        """
        discovered = set()
        to_visit = [start_url]
        visited = set()
        depth_map = {start_url: 0}
        
        async with AsyncWebCrawler(verbose=self.config.verbose) as crawler:
            max_pages_reached = False
            while to_visit and len(discovered) < self.config.max_pages:
                current_url = to_visit.pop(0)
                
                if current_url in visited:
                    continue
                
                current_depth = depth_map.get(current_url, 0)
                if current_depth > self.config.max_depth:
                    continue
                
                visited.add(current_url)
                
                try:
                    # Discovery crawl with better wait strategy for complete link discovery
                    config = CrawlerRunConfig(
                        cache_mode=CacheMode.ENABLED if self.config.cache_mode else CacheMode.BYPASS,
                        wait_until="networkidle",
                        page_timeout=self.config.timeout * 1000  # Convert seconds to milliseconds
                    )
                    
                    result = await crawler.arun(
                        url=current_url,
                        config=config
                    )
                    
                    if result.success:
                        # Add current URL to discovered if it matches patterns
                        if URLPatternHandler.match_url_pattern(current_url, patterns, exclude_patterns):
                            discovered.add(current_url)
                        
                        # Extract links
                        if result.links and current_depth < self.config.max_depth:
                            for link_data in result.links.get('internal', []):
                                link = link_data.get('href', '')
                                if not link:
                                    continue
                                
                                normalized = self.normalize_url(link, current_url)
                                
                                # Check if we should follow this link
                                if not self.config.include_external:
                                    if not self.is_same_domain(normalized, start_url):
                                        continue
                                
                                if normalized not in visited and normalized not in to_visit:
                                    to_visit.append(normalized)
                                    depth_map[normalized] = current_depth + 1
                                    
                                    # Track relationship
                                    if current_url not in self.url_relationships:
                                        self.url_relationships[current_url] = []
                                    self.url_relationships[current_url].append(normalized)
                
                except Exception as e:
                    if self.config.verbose:
                        print(f"Error discovering {current_url}: {e}")
                
                # Respect delay between requests
                if self.config.delay_between_requests > 0:
                    await asyncio.sleep(self.config.delay_between_requests)
        
        # Check if we stopped due to max_pages limit
        if to_visit and len(discovered) >= self.config.max_pages:
            if self.config.verbose:
                remaining_count = len(to_visit)
                print(f"⚠️  Max pages limit ({self.config.max_pages}) reached during discovery.")
                print(f"📊 Discovered: {len(discovered)} URLs")
                print(f"📋 Remaining undiscovered: {remaining_count}+ URLs")
                print(f"💡 To discover more URLs, increase 'Max Pages' in Settings (menu option 4)")
        
        self.discovered_urls = discovered
        return sorted(list(discovered))


class ContentCrawler:
    """Handles actual content extraction from URLs."""
    
    def __init__(self, config: CrawlConfig, output_manager=None):
        self.config = config
        self.output_manager = output_manager  # Optional output manager for advanced organization
        self.results: List[Dict[str, Any]] = []
        self.failed_urls: List[Tuple[str, str]] = []
        
        # Initialize content cleaner based on configuration
        if (config.content_css_selectors or config.content_xpath or 
            config.custom_nav_patterns or config.custom_footer_patterns or
            config.custom_skip_patterns or config.cleaning_profile != 'moderate'):
            # Use configurable cleaner if any custom settings are provided
            self.content_cleaner = ConfigurableContentCleaner(
                custom_nav_patterns=config.custom_nav_patterns,
                custom_footer_patterns=config.custom_footer_patterns,
                custom_skip_patterns=config.custom_skip_patterns,
                content_css_selectors=config.content_css_selectors,
                content_xpath=config.content_xpath,
                exclude_css_selectors=config.exclude_css_selectors,
                exclude_xpath=config.exclude_xpath,
                extraction_method=config.extraction_method,
                min_content_length=config.min_content_length,
                preserve_elements=config.preserve_elements,
                cleaning_profile=config.cleaning_profile
            )
            
            # Apply selector template if specified
            if config.selector_template:
                self.content_cleaner.set_selector_template(config.selector_template)
        else:
            # Use basic cleaner for default settings
            self.content_cleaner = ContentCleaner()
    
    def clean_markdown_content(self, markdown: str, title: str, html: str = None) -> str:
        """Clean and improve markdown formatting using content cleaner."""
        if isinstance(self.content_cleaner, ConfigurableContentCleaner) and html:
            # Use selector-based cleaning if available
            return self.content_cleaner.clean_with_selectors(html, markdown, title)
        else:
            # Use standard markdown cleaning
            return self.content_cleaner.clean_markdown_content(markdown, title)
    
    def _generate_enhanced_js(self) -> str:
        """Generate JavaScript for enhanced content loading with adaptive scrolling and element detection."""
        return """
        // Adaptive scrolling to trigger lazy loading
        const scrollToBottom = async () => {
            let lastHeight = document.body.scrollHeight;
            let attempts = 0;
            const maxAttempts = 5;
            
            console.log('Starting adaptive scroll...');
            
            while (attempts < maxAttempts) {
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 1000));
                
                const newHeight = document.body.scrollHeight;
                console.log(`Scroll attempt ${attempts + 1}: ${lastHeight} -> ${newHeight}`);
                
                if (newHeight > lastHeight) {
                    lastHeight = newHeight;
                    attempts = 0; // Reset counter when new content loads
                } else {
                    attempts++;
                }
            }
            
            console.log('Adaptive scroll completed');
        };
        
        await scrollToBottom();
        
        // Smart element detection for "Load More" buttons
        const loadMoreButtons = document.querySelectorAll(
            'button, a[href="#"], .load-more, .show-more, .view-more, [class*="load"], [class*="more"]'
        );
        
        console.log(`Found ${loadMoreButtons.length} potential load buttons`);
        
        for (let btn of loadMoreButtons) {
            const text = btn.textContent.toLowerCase();
            const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
            
            if (text.includes('load more') || text.includes('show more') || 
                text.includes('view more') || text.includes('read more') ||
                text.includes('see more') || text.includes('expand') ||
                ariaLabel.includes('load') || ariaLabel.includes('more')) {
                try {
                    console.log(`Clicking button: ${text}`);
                    btn.click();
                    await new Promise(r => setTimeout(r, 2000)); // Fallback timeout
                    break; // Only click the first matching button
                } catch (e) {
                    console.log(`Failed to click button: ${e.message}`);
                    // Continue if click fails
                }
            }
        }
        
        // Scroll back to top for consistent capture
        window.scrollTo(0, 0);
        await new Promise(r => setTimeout(r, 500));
        console.log('Enhanced content loading completed');
        """
    
    def url_to_filename(self, url: str) -> str:
        """Convert URL to valid filename."""
        parsed = urlparse(url)
        
        # Create filename from domain and path
        filename = parsed.netloc + parsed.path
        
        # Replace invalid characters
        filename = filename.replace('/', '_')
        filename = filename.replace('\\', '_')
        filename = filename.replace(':', '_')
        filename = filename.replace('*', '_')
        filename = filename.replace('?', '_')
        filename = filename.replace('"', '_')
        filename = filename.replace('<', '_')
        filename = filename.replace('>', '_')
        filename = filename.replace('|', '_')
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        # Add .md extension if not present
        if not filename.endswith('.md'):
            filename += '.md'
        
        return filename
    
    def get_output_path(self, url: str, content_data: Dict[str, Any] = None) -> Path:
        """Get output path for a URL based on organization settings."""
        # Use output manager if available for advanced organization
        if self.output_manager:
            if content_data is None:
                # Create minimal content data for path generation
                content_data = {'url': url, 'title': 'Untitled'}
            return self.output_manager.get_file_path(content_data, self.config.output_dir)
        
        # Fallback to original logic
        if self.config.organize_by_structure:
            # Mirror website structure
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if path_parts:
                # Create directory structure
                dir_path = self.config.output_dir / parsed.netloc / Path(*path_parts[:-1])
                filename = path_parts[-1] if path_parts[-1].endswith('.md') else f"{path_parts[-1]}.md"
            else:
                dir_path = self.config.output_dir / parsed.netloc
                filename = "index.md"
            
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path / filename
        else:
            # Flat structure
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            return self.config.output_dir / self.url_to_filename(url)
    
    async def crawl_single_url(self, url: str, crawler: AsyncWebCrawler) -> Dict[str, Any]:
        """Crawl a single URL and extract content."""
        try:
            # Build enhanced configuration (complete capture with cleaning)
            config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED if self.config.cache_mode else CacheMode.BYPASS,
                wait_until="networkidle",  # Wait for network to be idle
                page_timeout=45000,  # Increased timeout for complete loading (in ms)
                
                # JavaScript for adaptive scrolling and element detection
                js_code=self._generate_enhanced_js(),
                
                # Additional options for complete capture
                process_iframes=True,  # Include embedded content
                remove_overlay_elements=True,  # Remove popups/modals
                word_count_threshold=50,  # Minimum word count for content blocks
                excluded_tags=['nav', 'footer', 'header', 'aside'],  # Remove common boilerplate elements
                
                # Enhanced markdown generation
                markdown_generator=DefaultMarkdownGenerator(
                    options={
                        "ignore_links": False,  # Keep links
                        "ignore_images": False,  # Keep images
                        "body_width": 120,  # Wider body for better formatting
                    }
                ),
            )
            
            # User-Agent rotation or single user agent
            if self.config.rotate_user_agents and self.config.user_agents_list:
                config.user_agent = random.choice(self.config.user_agents_list)
                if self.config.verbose:
                    print(f"Using User-Agent: {config.user_agent[:50]}...")
            elif self.config.user_agent:
                config.user_agent = self.config.user_agent
            
            if self.config.headers:
                config.headers = self.config.headers
            
            if self.config.proxy:
                config.proxy = self.config.proxy
            
            result = await crawler.arun(
                url=url,
                config=config
            )
            
            if result.success:
                # Extract and clean content
                raw_markdown = result.markdown or ""
                raw_html = result.html or ""
                title = result.metadata.get('title', 'Untitled') if result.metadata else 'Untitled'
                
                # Always apply content cleaning in enhanced mode
                markdown_content = self.clean_markdown_content(raw_markdown, title, raw_html)
                
                # Check content quality
                if len(markdown_content.strip()) < 100:
                    # Content seems too short, might be incomplete
                    if self.config.verbose:
                        print(f"Warning: Content seems short for {url} ({len(markdown_content)} chars)")
                    
                    # Try to use cleaned_html as fallback if available
                    if hasattr(result, 'cleaned_html') and result.cleaned_html:
                        markdown_content = f"[Note: Minimal markdown extracted, showing cleaned content]\n\n{result.cleaned_html}"
                    elif not markdown_content:
                        markdown_content = "[No substantial content could be extracted from this page]"
                
                content_data = {
                    'url': url,
                    'title': result.metadata.get('title', 'Untitled') if result.metadata else 'Untitled',
                    'description': result.metadata.get('description', '') if result.metadata else '',
                    'markdown': markdown_content,
                    'content_length': len(markdown_content),
                    'links_count': len(result.links.get('internal', [])) + len(result.links.get('external', [])) if result.links else 0,
                    'crawled_at': datetime.now().isoformat(),
                    'success': True,
                    'enhanced_mode': True  # Always enhanced mode
                }
                
                # Save content immediately (to avoid memory issues)
                output_path = self.get_output_path(url, content_data)
                
                # Create directory if needed
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use output manager's format if available, otherwise use default
                if self.output_manager:
                    if self.output_manager.include_metadata:
                        formatted_content = self.output_manager._format_content_with_metadata(content_data)
                    else:
                        formatted_content = content_data.get('markdown', '')
                    
                    async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                        await f.write(formatted_content)
                else:
                    # Fallback: create basic markdown file
                    await self._save_basic_markdown(content_data, output_path)
                
                return content_data
            else:
                error_msg = f"Crawl failed: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}"
                self.failed_urls.append((url, error_msg))
                return {
                    'url': url,
                    'success': False,
                    'error': error_msg
                }
        
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.failed_urls.append((url, error_msg))
            return {
                'url': url,
                'success': False,
                'error': error_msg
            }
    
    async def _save_basic_markdown(self, content_data: Dict[str, Any], output_path: Path):
        """Save basic markdown content to file (fallback when no OutputManager)."""
        markdown_content = f"""# {content_data['title']}

{content_data['markdown']}
"""
        
        # Save to file
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(markdown_content)
    
    async def crawl_urls(self, urls: List[str], progress_callback=None) -> Dict[str, Any]:
        """
        Crawl multiple URLs with concurrency control.
        
        Args:
            urls: List of URLs to crawl
            progress_callback: Optional callback for progress updates
        """
        self.results = []
        self.failed_urls = []
        
        async with AsyncWebCrawler(verbose=self.config.verbose) as crawler:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.config.concurrent_limit)
            
            async def crawl_with_semaphore(url: str, index: int):
                async with semaphore:
                    if progress_callback:
                        progress_callback(index, len(urls), url)
                    
                    result = await self.crawl_single_url(url, crawler)
                    self.results.append(result)
                    
                    # Respect delay between requests
                    if self.config.delay_between_requests > 0:
                        await asyncio.sleep(self.config.delay_between_requests)
                    
                    return result
            
            # Crawl all URLs
            tasks = [crawl_with_semaphore(url, i) for i, url in enumerate(urls)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Prepare summary
        successful = [r for r in self.results if r.get('success')]
        failed = [r for r in self.results if not r.get('success')]
        
        summary = {
            'total_urls': len(urls),
            'successful': len(successful),
            'failed': len(failed),
            'total_content_length': sum(r.get('content_length', 0) for r in successful),
            'results': self.results,
            'failed_urls': self.failed_urls,
            'output_directory': str(self.config.output_dir)
        }
        
        # Save summary
        summary_path = self.config.output_dir / "crawl_summary.json"
        async with aiofiles.open(summary_path, 'w') as f:
            await f.write(json.dumps(summary, indent=2))
        
        return summary


async def crawl_with_discovery(start_url: str, config: CrawlConfig, 
                              patterns: List[str] = None,
                              exclude_patterns: List[str] = None,
                              progress_callback=None) -> Dict[str, Any]:
    """
    Perform discovery crawl followed by content extraction.
    """
    # Phase 1: Discovery
    if progress_callback:
        progress_callback(0, 2, "Starting URL discovery...")
    
    discovery = URLDiscovery(config)
    discovered_urls = await discovery.discover_urls(start_url, patterns, exclude_patterns)
    
    if progress_callback:
        progress_callback(1, 2, f"Discovered {len(discovered_urls)} URLs")
    
    # Check if dry run mode - return discovery results without crawling
    if config.dry_run:
        # Generate preview of file paths
        output_manager = OutputManager()
        file_preview = []
        for url in discovered_urls[:10]:  # Show first 10 as preview
            content_data = {'url': url, 'title': 'Preview'}
            file_path = output_manager.get_file_path(content_data, config.output_dir)
            file_preview.append(str(file_path))
        
        return {
            'dry_run': True,
            'total_urls': len(discovered_urls),
            'discovered_urls': discovered_urls,
            'file_preview': file_preview,
            'start_url': start_url,
            'url_relationships': discovery.url_relationships,
            'message': f'Dry run completed. Would crawl {len(discovered_urls)} URLs.'
        }
    
    # Phase 2: Content extraction (only if not dry run)
    if discovered_urls:
        crawler = ContentCrawler(config)
        summary = await crawler.crawl_urls(discovered_urls, progress_callback)
        summary['discovery'] = {
            'start_url': start_url,
            'discovered_count': len(discovered_urls),
            'url_relationships': discovery.url_relationships
        }
        return summary
    else:
        return {
            'total_urls': 0,
            'successful': 0,
            'failed': 0,
            'message': 'No URLs discovered matching the patterns'
        }


async def crawl_single(url: str, config: CrawlConfig, deep_crawl: bool = False,
                      patterns: List[str] = None, exclude_patterns: List[str] = None,
                      progress_callback=None) -> Dict[str, Any]:
    """
    Crawl a single URL with optional deep crawling.
    """
    if deep_crawl:
        return await crawl_with_discovery(url, config, patterns, exclude_patterns, progress_callback)
    else:
        # Check for dry run mode
        if config.dry_run:
            output_manager = OutputManager()
            content_data = {'url': url, 'title': 'Preview'}
            file_path = output_manager.get_file_path(content_data, config.output_dir)
            
            return {
                'dry_run': True,
                'total_urls': 1,
                'discovered_urls': [url],
                'file_preview': [str(file_path)],
                'message': 'Dry run completed. Would crawl 1 URL.'
            }
        
        crawler = ContentCrawler(config)
        return await crawler.crawl_urls([url], progress_callback)


async def crawl_multiple(urls: List[str], config: CrawlConfig, 
                        deep_crawl: bool = False,
                        patterns: List[str] = None,
                        exclude_patterns: List[str] = None,
                        progress_callback=None) -> Dict[str, Any]:
    """
    Crawl multiple URLs with optional deep crawling for each.
    """
    if deep_crawl:
        # Discover URLs for each starting point
        all_discovered = set()
        
        for url in urls:
            if progress_callback:
                progress_callback(0, len(urls), f"Discovering from {url}")
            
            discovery = URLDiscovery(config)
            discovered = await discovery.discover_urls(url, patterns, exclude_patterns)
            all_discovered.update(discovered)
        
        # Check for dry run mode
        if config.dry_run:
            output_manager = OutputManager()
            file_preview = []
            discovered_list = list(all_discovered)
            for url in discovered_list[:10]:  # Show first 10 as preview
                content_data = {'url': url, 'title': 'Preview'}
                file_path = output_manager.get_file_path(content_data, config.output_dir)
                file_preview.append(str(file_path))
            
            return {
                'dry_run': True,
                'total_urls': len(all_discovered),
                'discovered_urls': discovered_list,
                'file_preview': file_preview,
                'message': f'Dry run completed. Would crawl {len(all_discovered)} URLs.'
            }
        
        # Crawl all discovered URLs
        if all_discovered:
            crawler = ContentCrawler(config)
            return await crawler.crawl_urls(list(all_discovered), progress_callback)
        else:
            return {
                'total_urls': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No URLs discovered'
            }
    else:
        # Check for dry run mode
        if config.dry_run:
            output_manager = OutputManager()
            file_preview = []
            for url in urls[:10]:  # Show first 10 as preview
                content_data = {'url': url, 'title': 'Preview'}
                file_path = output_manager.get_file_path(content_data, config.output_dir)
                file_preview.append(str(file_path))
            
            return {
                'dry_run': True,
                'total_urls': len(urls),
                'discovered_urls': urls,
                'file_preview': file_preview,
                'message': f'Dry run completed. Would crawl {len(urls)} URLs.'
            }
        
        # Direct crawl without discovery
        crawler = ContentCrawler(config)
        return await crawler.crawl_urls(urls, progress_callback)


async def crawl_pattern(base_url: str, patterns: List[str], config: CrawlConfig,
                       exclude_patterns: List[str] = None,
                       progress_callback=None) -> Dict[str, Any]:
    """
    Crawl URLs matching specific patterns starting from a base URL.
    """
    return await crawl_with_discovery(base_url, config, patterns, exclude_patterns, progress_callback)

