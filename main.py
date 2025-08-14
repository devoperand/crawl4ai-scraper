#!/usr/bin/env python3
"""
Interactive CLI for crawl4ai-interactive.
Provides user interface for web scraping with complete control.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import signal
from config_manager import ConfigManager, config_to_crawl_config, crawl_config_to_dict

# We'll import these after dependency check
console = None
Console = None
Prompt = None
IntPrompt = None
Confirm = None
Table = None
Progress = None
SpinnerColumn = None
TextColumn = None
BarColumn = None
TaskProgressColumn = None
Panel = None
Text = None
rprint = None

# Crawler imports will be done after dependency check
CrawlConfig = None
URLPatternHandler = None
URLDiscovery = None
ContentCrawler = None
crawl_single = None
crawl_multiple = None
crawl_pattern = None
crawl_with_discovery = None
OutputManager = None

def import_dependencies():
    """Import dependencies after they've been installed."""
    global console, Console, Prompt, IntPrompt, Confirm, Table, Progress
    global SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Panel, Text, rprint
    global CrawlConfig, URLPatternHandler, URLDiscovery, ContentCrawler
    global crawl_single, crawl_multiple, crawl_pattern, crawl_with_discovery, OutputManager
    
    from rich.console import Console as _Console
    from rich.prompt import Prompt as _Prompt, IntPrompt as _IntPrompt, Confirm as _Confirm
    from rich.table import Table as _Table
    from rich.progress import Progress as _Progress, SpinnerColumn as _SpinnerColumn
    from rich.progress import TextColumn as _TextColumn, BarColumn as _BarColumn
    from rich.progress import TaskProgressColumn as _TaskProgressColumn
    from rich.panel import Panel as _Panel
    from rich.text import Text as _Text
    from rich import print as _rprint
    
    Console = _Console
    Prompt = _Prompt
    IntPrompt = _IntPrompt
    Confirm = _Confirm
    Table = _Table
    Progress = _Progress
    SpinnerColumn = _SpinnerColumn
    TextColumn = _TextColumn
    BarColumn = _BarColumn
    TaskProgressColumn = _TaskProgressColumn
    Panel = _Panel
    Text = _Text
    rprint = _rprint
    console = Console()
    
    # Import crawler modules
    from crawler import (
        CrawlConfig as _CrawlConfig,
        URLPatternHandler as _URLPatternHandler,
        URLDiscovery as _URLDiscovery,
        ContentCrawler as _ContentCrawler,
        crawl_single as _crawl_single,
        crawl_multiple as _crawl_multiple,
        crawl_pattern as _crawl_pattern,
        crawl_with_discovery as _crawl_with_discovery
    )
    from output_manager import OutputManager as _OutputManager
    
    CrawlConfig = _CrawlConfig
    URLPatternHandler = _URLPatternHandler
    URLDiscovery = _URLDiscovery
    ContentCrawler = _ContentCrawler
    crawl_single = _crawl_single
    crawl_multiple = _crawl_multiple
    crawl_pattern = _crawl_pattern
    crawl_with_discovery = _crawl_with_discovery
    OutputManager = _OutputManager
    
    return console


def run_with_args():
    """Run with command line arguments (after dependencies are installed)."""
    import click
    
    @click.command()
    @click.option('--check-deps', is_flag=True, help='Only run dependency check')
    @click.option('--install-deps', is_flag=True, help='Install dependencies from requirements.txt and exit')
    @click.option('--skip-deps', is_flag=True, help='Skip dependency checking')
    @click.option('--dry-run', is_flag=True, help='Run in dry-run mode - discover URLs without crawling content')
    def cli_main(check_deps, install_deps, skip_deps, dry_run):
        """Crawl4AI Interactive Web Scraper"""
        
        # Import dependency checker (minimal dependency)
        from dependency_checker import DependencyChecker, ensure_dependencies
        
        if install_deps:
            # Only install dependencies and exit
            print("[Installing dependencies from requirements.txt...]")
            checker = DependencyChecker()
            success = checker.install_from_requirements(silent=False)
            if success:
                print("✅ All dependencies installed successfully!")
                sys.exit(0)
            else:
                print("❌ Failed to install some dependencies")
                sys.exit(1)
        
        if check_deps:
            # Only check dependencies
            checker = DependencyChecker()
            missing = checker.get_missing_packages()
            if missing:
                print(f"⚠️  Missing packages: {missing}")
                print("Run with --install-deps to install them")
                sys.exit(1)
            else:
                print("✅ All dependencies are satisfied")
                sys.exit(0)
        
        # Check and install dependencies before importing heavy modules
        if not skip_deps:
            print("Checking and installing dependencies...")
            success = ensure_dependencies(auto_install=True, silent=False)
            if not success:
                print("❌ Failed to install dependencies.")
                print("Please run manually: pip install -r requirements.txt")
                sys.exit(1)
            print("✅ All dependencies satisfied\n")
        
        # Now import the heavy dependencies
        global console
        console = import_dependencies()
        
        # Run the interactive CLI
        cli = InteractiveCLI(dry_run=dry_run)
        
        try:
            asyncio.run(cli.run(skip_deps=skip_deps))
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[red]Fatal error: {e}[/red]")
            sys.exit(1)
    
    cli_main()


class InteractiveCLI:
    """Interactive command-line interface for web crawling."""
    
    def __init__(self, dry_run=False):
        # Dependencies should be imported before creating CLI
        if CrawlConfig is None:
            import_dependencies()
        
        self.config = CrawlConfig()
        self.console = Console()
        self.output_manager = OutputManager()
        self.config_manager = ConfigManager()
        self.current_progress = None
        self.interrupted = False
        self.scraped_content = []  # Store scraped content for later saving
        self.dry_run = dry_run  # Dry run mode from command line
        
        # Set dry_run in config if passed from command line
        if dry_run:
            self.config.dry_run = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self.interrupted = True
        self.console.print("\n[yellow]⚠️  Interrupting... Please wait for current operation to complete.[/yellow]")
    
    def display_banner(self):
        """Display welcome banner."""
        dry_run_text = ""
        if self.dry_run:
            dry_run_text = "\n[yellow]🔍 DRY RUN MODE ENABLED (from command line)[/yellow]"
        
        banner = Panel.fit(
            Text.from_markup(
                "[bold blue]🕷️  Crawl4AI Interactive Web Scraper[/bold blue]\n"
                "[dim]Powerful web scraping with complete control[/dim]" + dry_run_text
            ),
            border_style="blue"
        )
        self.console.print(banner)
        self.console.print()
    
    def main_menu(self) -> str:
        """Display main menu and get user choice."""
        # Show dry run status in header
        dry_run_status = "[green]ON[/green]" if self.config.dry_run else "[dim]OFF[/dim]"
        self.console.print(f"[bold]Dry Run Mode:[/bold] {dry_run_status}")
        self.console.print()
        
        self.console.print("[bold]Select Crawling Mode:[/bold]")
        self.console.print("1. [cyan]Single URL[/cyan] - Crawl one URL with optional deep crawling")
        self.console.print("2. [cyan]URL Pattern[/cyan] - Crawl URLs matching wildcard patterns")
        self.console.print("3. [cyan]Multiple URLs[/cyan] - Crawl a list of URLs")
        self.console.print("4. [cyan]Configure Settings[/cyan] - Adjust crawling parameters")
        self.console.print("5. [cyan]Save/Load Configuration[/cyan] - Manage configuration presets")
        self.console.print("6. [cyan]Toggle Dry Run Mode[/cyan] - Switch dry run on/off")
        self.console.print("7. [cyan]Test Content Selectors[/cyan] - Test CSS/XPath selectors")
        self.console.print("8. [cyan]Exit[/cyan]")
        self.console.print()
        
        choice = Prompt.ask(
            "Enter your choice",
            choices=["1", "2", "3", "4", "5", "6", "7", "8"],
            default="1"
        )
        
        return choice
    
    
    def get_single_url_input(self) -> tuple:
        """Get single URL input from user."""
        self.console.print("\n[bold]Single URL Mode[/bold]")
        
        url = Prompt.ask("Enter URL to crawl")
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        deep_crawl = Confirm.ask("Enable deep crawl to discover linked pages?", default=False)
        
        patterns = []
        exclude_patterns = []
        
        if deep_crawl:
            self.console.print("\n[dim]Deep crawl will discover all linked pages from this URL[/dim]")
            
            use_patterns = Confirm.ask("Apply URL patterns to filter discovered pages?", default=False)
            
            if use_patterns:
                patterns = self.get_url_patterns()
                
                use_exclusions = Confirm.ask("Add exclusion patterns?", default=False)
                if use_exclusions:
                    exclude_patterns = self.get_url_patterns(exclude=True)
        
        return url, deep_crawl, patterns, exclude_patterns
    
    def get_url_patterns(self, exclude: bool = False) -> List[str]:
        """Get URL patterns from user."""
        patterns = []
        pattern_type = "exclusion" if exclude else "inclusion"
        
        self.console.print(f"\n[bold]Enter {pattern_type} patterns:[/bold]")
        self.console.print("[dim]Examples: */blog/*, **/docs/**, *.html, */api/*[/dim]")
        self.console.print(f"[dim]Enter empty pattern to finish[/dim]")
        
        while True:
            pattern = Prompt.ask(f"{pattern_type.capitalize()} pattern", default="")
            if not pattern:
                break
            patterns.append(pattern)
            
            # Show example matches
            example_urls = [
                "https://example.com/blog/post1",
                "https://example.com/docs/api/reference",
                "https://example.com/about.html"
            ]
            
            matches = []
            for url in example_urls:
                if URLPatternHandler.match_url_pattern(url, [pattern]):
                    matches.append(url)
            
            if matches:
                self.console.print(f"[green]✓ Pattern would match URLs like: {matches[0]}[/green]")
        
        return patterns
    
    def get_pattern_input(self) -> tuple:
        """Get pattern-based crawling input."""
        self.console.print("\n[bold]URL Pattern Mode[/bold]")
        
        base_url = Prompt.ask("Enter base URL to start discovery")
        
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        
        self.console.print("\n[bold]Define URL patterns to match:[/bold]")
        patterns = self.get_url_patterns()
        
        if not patterns:
            self.console.print("[yellow]No patterns defined - will discover all URLs[/yellow]")
            patterns = None
        
        use_exclusions = Confirm.ask("Add exclusion patterns?", default=False)
        exclude_patterns = []
        if use_exclusions:
            exclude_patterns = self.get_url_patterns(exclude=True)
        
        return base_url, patterns, exclude_patterns
    
    def get_multiple_urls_input(self) -> tuple:
        """Get multiple URLs input."""
        self.console.print("\n[bold]Multiple URLs Mode[/bold]")
        
        input_method = Prompt.ask(
            "Input method",
            choices=["manual", "file"],
            default="manual"
        )
        
        urls = []
        
        if input_method == "manual":
            self.console.print("[dim]Enter URLs separated by commas or one per line[/dim]")
            self.console.print("[dim]Enter empty line to finish[/dim]")
            
            while True:
                line = Prompt.ask("URL(s)", default="")
                if not line:
                    break
                
                # Handle comma-separated or single URL
                if ',' in line:
                    url_list = [u.strip() for u in line.split(',')]
                else:
                    url_list = [line.strip()]
                
                for url in url_list:
                    if url:
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        urls.append(url)
        
        else:  # file input
            filepath = Prompt.ask("Enter path to file containing URLs")
            filepath = Path(filepath)
            
            if filepath.exists():
                with open(filepath, 'r') as f:
                    for line in f:
                        url = line.strip()
                        if url and not url.startswith('#'):
                            if not url.startswith(('http://', 'https://')):
                                url = 'https://' + url
                            urls.append(url)
            else:
                self.console.print(f"[red]File not found: {filepath}[/red]")
                return [], False, [], []
        
        if urls:
            self.console.print(f"[green]Loaded {len(urls)} URLs[/green]")
            
            # Show first few URLs
            self.console.print("\n[bold]URLs to crawl:[/bold]")
            for i, url in enumerate(urls[:5], 1):
                self.console.print(f"  {i}. {url}")
            if len(urls) > 5:
                self.console.print(f"  ... and {len(urls) - 5} more")
        
        deep_crawl = Confirm.ask("\nApply deep crawl to all URLs?", default=False)
        
        patterns = []
        exclude_patterns = []
        
        if deep_crawl:
            use_patterns = Confirm.ask("Apply URL patterns for discovery?", default=False)
            if use_patterns:
                patterns = self.get_url_patterns()
                
                use_exclusions = Confirm.ask("Add exclusion patterns?", default=False)
                if use_exclusions:
                    exclude_patterns = self.get_url_patterns(exclude=True)
        
        return urls, deep_crawl, patterns, exclude_patterns
    
    def configure_settings(self):
        """Configure crawling settings."""
        self.console.print("\n[bold]Crawling Configuration[/bold]")
        
        # Output directory
        current_output = self.config.output_dir
        self.console.print(f"\nCurrent output directory: [cyan]{current_output}[/cyan]")
        
        change_output = Confirm.ask("Change output directory?", default=False)
        if change_output:
            new_output = Prompt.ask("Enter output directory path", default=str(current_output))
            self.config.output_dir = Path(new_output)
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Concurrent requests with recommendations
        self.console.print(f"\nCurrent concurrent limit: [cyan]{self.config.concurrent_limit}[/cyan]")
        self.console.print("[dim]Recommendations: 1-3 for respectful crawling, 5+ for faster scraping (be considerate)[/dim]")
        new_concurrent = IntPrompt.ask(
            "Maximum concurrent requests",
            default=self.config.concurrent_limit,
            choices=list(map(str, range(1, 11)))
        )
        
        if new_concurrent > 5:
            self.console.print(f"[yellow]💡 Note:[/yellow] {new_concurrent} concurrent requests is aggressive - ensure target site can handle this")
        
        self.config.concurrent_limit = new_concurrent
        
        # Request delay with validation
        self.console.print(f"\nCurrent delay between requests: [cyan]{self.config.delay_between_requests}s[/cyan]")
        self.console.print("[dim]Recommendations: 1-2s for respectful crawling, 0.5s+ for faster (check robots.txt)[/dim]")
        delay_str = Prompt.ask(
            "Delay between requests (seconds)",
            default=str(self.config.delay_between_requests)
        )
        new_delay = float(delay_str)
        
        if new_delay < 0.5 and self.config.concurrent_limit > 3:
            self.console.print(f"[red]⚠️  Warning:[/red] Very low delay ({new_delay}s) + high concurrency ({self.config.concurrent_limit}) may overwhelm servers")
            self.console.print("[dim]Consider increasing delay or reducing concurrent requests[/dim]")
        elif new_delay < 0.1:
            self.console.print(f"[yellow]💡 Note:[/yellow] {new_delay}s delay is very aggressive - ensure this is appropriate")
        
        self.config.delay_between_requests = new_delay
        
        # Max pages with recommendations
        self.console.print(f"\nCurrent max pages: [cyan]{self.config.max_pages}[/cyan]")
        self.console.print("\n[bold]Recommended Max Pages by Use Case:[/bold]")
        self.console.print("  • Single page documentation: [dim]1-10[/dim]")
        self.console.print("  • API documentation: [dim]20-100[/dim]") 
        self.console.print("  • Complete site documentation: [dim]100-500[/dim]")
        self.console.print("  • Large scale discovery: [dim]500+[/dim]")
        
        new_max_pages = IntPrompt.ask(
            "Maximum pages to crawl",
            default=self.config.max_pages
        )
        
        # Validate and provide warnings
        if new_max_pages > 1000:
            warning = Confirm.ask(
                f"\n[yellow]⚠️  Warning:[/yellow] {new_max_pages} pages may use significant resources.\n"
                "This could take a long time and use substantial memory/storage.\n"
                "Continue with this setting?",
                default=False
            )
            if not warning:
                self.console.print("[dim]Keeping current setting...[/dim]")
            else:
                self.config.max_pages = new_max_pages
        elif new_max_pages > 500:
            self.console.print(f"[yellow]💡 Note:[/yellow] {new_max_pages} pages is quite large - ensure you have adequate resources")
            self.config.max_pages = new_max_pages
        else:
            self.config.max_pages = new_max_pages
        
        # Max depth
        self.console.print(f"\nCurrent max depth: [cyan]{self.config.max_depth}[/cyan]")
        self.config.max_depth = IntPrompt.ask(
            "Maximum crawl depth",
            default=self.config.max_depth,
            choices=list(map(str, range(1, 6)))
        )
        
        # Cache mode
        self.config.cache_mode = Confirm.ask(
            "\nEnable cache mode?",
            default=self.config.cache_mode
        )
        
        # File organization
        self.config.organize_by_structure = Confirm.ask(
            "\nOrganize files by website structure?",
            default=self.config.organize_by_structure
        )
        
        # Include external links
        self.config.include_external = Confirm.ask(
            "\nInclude external domain links in discovery?",
            default=self.config.include_external
        )
        
        # Content extraction settings
        configure_extraction = Confirm.ask(
            "\nConfigure content extraction settings (CSS/XPath selectors)?",
            default=False
        )
        if configure_extraction:
            self.configure_content_extraction()
        
        # Enhanced mode is always enabled (no user choice needed)
        self.console.print(f"\n[bold green]✓[/bold green] Enhanced capture mode: [cyan]Always Enabled[/cyan]")
        self.console.print("[dim]Complete content capture with cleaning, adaptive scrolling, and boilerplate removal[/dim]")
        
        self.display_config_summary()
    
    def display_config_summary(self):
        """Display current configuration summary."""
        table = Table(title="Current Configuration", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Output Directory", str(self.config.output_dir))
        table.add_row("Concurrent Requests", str(self.config.concurrent_limit))
        table.add_row("Request Delay", f"{self.config.delay_between_requests}s")
        table.add_row("Max Pages", str(self.config.max_pages))
        table.add_row("Max Depth", str(self.config.max_depth))
        table.add_row("Cache Mode", "✓" if self.config.cache_mode else "✗")
        table.add_row("Organize by Structure", "✓" if self.config.organize_by_structure else "✗")
        table.add_row("Include External", "✓" if self.config.include_external else "✗")
        table.add_row("Enhanced Capture", "✓ Always Enabled")
        
        self.console.print(table)
    
    async def test_content_selectors(self):
        """Test CSS/XPath selectors on a sample URL."""
        self.console.print("\n[bold]Test Content Selectors[/bold]")
        self.console.print("="*50)
        
        # Get test URL
        test_url = Prompt.ask("\nEnter URL to test selectors on")
        if not test_url:
            return
        
        # Configure selectors for testing
        self.console.print("\n[bold]Configure Test Selectors:[/bold]")
        
        # CSS selectors
        css_selectors = []
        add_css = Confirm.ask("Add CSS selectors?", default=True)
        if add_css:
            css_input = Prompt.ask("CSS selectors (comma-separated)", default="article, main, .content")
            css_selectors = [s.strip() for s in css_input.split(',') if s.strip()]
        
        # XPath expressions
        xpath_expressions = []
        add_xpath = Confirm.ask("Add XPath expressions?", default=False)
        if add_xpath:
            xpath_input = Prompt.ask("XPath expressions (comma-separated)")
            xpath_expressions = [s.strip() for s in xpath_input.split(',') if s.strip()]
        
        if not css_selectors and not xpath_expressions:
            self.console.print("[yellow]No selectors provided. Using default extraction.[/yellow]")
        
        # Fetch and test
        self.console.print("\n[dim]Fetching content...[/dim]")
        
        try:
            # Import required modules
            from selector_utils import SelectorExtractor
            import httpx
            
            # Fetch HTML content
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, follow_redirects=True)
                html_content = response.text
            
            # Test selectors
            extractor = SelectorExtractor()
            results = extractor.test_selectors(html_content, css_selectors, xpath_expressions)
            
            # Display results
            self.console.print("\n[bold green]✓ Selector Test Results[/bold green]")
            self.console.print("="*50)
            
            for method, content in results.items():
                self.console.print(f"\n[bold]{method.upper()} Method:[/bold]")
                if content:
                    # Show preview (first 500 chars)
                    preview = content[:500] + "..." if len(content) > 500 else content
                    self.console.print(f"[dim]Content length: {len(content)} chars[/dim]")
                    self.console.print(f"\n{preview}")
                else:
                    self.console.print("[red]No content extracted[/red]")
            
            # Ask if user wants to save these selectors
            if css_selectors or xpath_expressions:
                save_selectors = Confirm.ask("\n\nSave these selectors to configuration?", default=False)
                if save_selectors:
                    self.config.content_css_selectors = css_selectors
                    self.config.content_xpath = xpath_expressions
                    self.console.print("[green]✓ Selectors saved to configuration[/green]")
        
        except Exception as e:
            self.console.print(f"[red]Error testing selectors: {e}[/red]")
    
    def configure_content_extraction(self):
        """Configure content extraction settings with CSS/XPath selectors."""
        self.console.print("\n[bold]Content Extraction Settings[/bold]")
        self.console.print("="*50)
        
        # Extraction method
        self.console.print("\n[bold]Extraction Method:[/bold]")
        self.console.print("1. CSS Selectors (simpler, widely used)")
        self.console.print("2. XPath (more powerful, complex queries)")
        self.console.print("3. Auto (use both)")
        
        method_choice = Prompt.ask(
            "Choose extraction method",
            choices=["1", "2", "3"],
            default="3"
        )
        
        if method_choice == "1":
            self.config.extraction_method = 'css'
        elif method_choice == "2":
            self.config.extraction_method = 'xpath'
        else:
            self.config.extraction_method = 'auto'
        
        # Selector templates
        use_template = Confirm.ask("\nUse a preset selector template?", default=False)
        if use_template:
            self.console.print("\n[bold]Available Templates:[/bold]")
            self.console.print("1. Blog (articles, posts)")
            self.console.print("2. News (news articles)")
            self.console.print("3. Documentation (technical docs)")
            self.console.print("4. E-commerce (product pages)")
            self.console.print("5. Forum (discussion threads)")
            
            template_choice = Prompt.ask(
                "Choose template",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )
            
            templates = {
                "1": "blog",
                "2": "news",
                "3": "documentation",
                "4": "ecommerce",
                "5": "forum"
            }
            self.config.selector_template = templates[template_choice]
            self.console.print(f"[green]✓ Applied {templates[template_choice]} template[/green]")
        
        # Custom selectors
        if self.config.extraction_method in ['css', 'auto']:
            add_css = Confirm.ask("\nAdd custom CSS selectors for content?", default=False)
            if add_css:
                self.console.print("[dim]Enter CSS selectors (comma-separated, e.g., article, .content, #main)[/dim]")
                css_input = Prompt.ask("Content CSS selectors")
                self.config.content_css_selectors = [s.strip() for s in css_input.split(',') if s.strip()]
                
                # Exclusion selectors
                add_exclude_css = Confirm.ask("Add CSS selectors to exclude?", default=False)
                if add_exclude_css:
                    exclude_css = Prompt.ask("Exclude CSS selectors")
                    self.config.exclude_css_selectors = [s.strip() for s in exclude_css.split(',') if s.strip()]
        
        if self.config.extraction_method in ['xpath', 'auto']:
            add_xpath = Confirm.ask("\nAdd custom XPath expressions?", default=False)
            if add_xpath:
                self.console.print("[dim]Enter XPath expressions (comma-separated)[/dim]")
                xpath_input = Prompt.ask("Content XPath")
                self.config.content_xpath = [s.strip() for s in xpath_input.split(',') if s.strip()]
                
                # Exclusion XPath
                add_exclude_xpath = Confirm.ask("Add XPath expressions to exclude?", default=False)
                if add_exclude_xpath:
                    exclude_xpath = Prompt.ask("Exclude XPath")
                    self.config.exclude_xpath = [s.strip() for s in exclude_xpath.split(',') if s.strip()]
        
        # Cleaning profile
        self.console.print("\n[bold]Cleaning Profile:[/bold]")
        self.console.print("1. Strict (aggressive cleaning)")
        self.console.print("2. Moderate (balanced)")
        self.console.print("3. Minimal (light cleaning)")
        
        profile_choice = Prompt.ask(
            "Choose cleaning profile",
            choices=["1", "2", "3"],
            default="2"
        )
        
        profiles = {"1": "strict", "2": "moderate", "3": "minimal"}
        self.config.cleaning_profile = profiles[profile_choice]
        
        # Custom patterns
        add_patterns = Confirm.ask("\nAdd custom cleaning patterns?", default=False)
        if add_patterns:
            nav_patterns = Prompt.ask("Navigation patterns to remove (comma-separated)", default="")
            if nav_patterns:
                self.config.custom_nav_patterns = [p.strip() for p in nav_patterns.split(',') if p.strip()]
            
            footer_patterns = Prompt.ask("Footer patterns to remove (comma-separated)", default="")
            if footer_patterns:
                self.config.custom_footer_patterns = [p.strip() for p in footer_patterns.split(',') if p.strip()]
        
        self.console.print("\n[green]✓ Content extraction settings configured[/green]")
    
    def manage_configurations(self):
        """Manage configuration presets - save, load, list, delete."""
        while True:
            self.console.print("\\n" + "="*50)
            self.console.print("[bold]Configuration Management[/bold]")
            self.console.print("="*50)
            
            self.console.print("1. [cyan]Load Configuration[/cyan] - Load saved configuration")
            self.console.print("2. [cyan]Save Current Configuration[/cyan] - Save current settings")
            self.console.print("3. [cyan]List Saved Configurations[/cyan] - View all saved configs")
            self.console.print("4. [cyan]Delete Configuration[/cyan] - Remove saved configuration")
            self.console.print("5. [cyan]Create Presets[/cyan] - Generate common presets")
            self.console.print("6. [cyan]Export Configuration[/cyan] - Export to file")
            self.console.print("7. [cyan]Import Configuration[/cyan] - Import from file")
            self.console.print("8. [cyan]Back to Main Menu[/cyan]")
            self.console.print()
            
            config_choice = Prompt.ask(
                "Choose an option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                default="1"
            )
            
            if config_choice == "1":
                self._load_configuration()
            elif config_choice == "2":
                self._save_current_configuration()
            elif config_choice == "3":
                self._list_configurations()
            elif config_choice == "4":
                self._delete_configuration()
            elif config_choice == "5":
                self._create_presets()
            elif config_choice == "6":
                self._export_configuration()
            elif config_choice == "7":
                self._import_configuration()
            elif config_choice == "8":
                break
    
    def _load_configuration(self):
        """Load a saved configuration."""
        configs = self.config_manager.list_configs()
        if not configs:
            self.console.print("[yellow]No saved configurations found[/yellow]")
            return
        
        # Display available configurations
        self.console.print("\\n[bold]Available Configurations:[/bold]")
        table = Table(show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Name", style="white")
        table.add_column("Description", style="dim")
        table.add_column("Saved", style="dim")
        
        for i, config_info in enumerate(configs, 1):
            saved_at = config_info.get('saved_at', 'Unknown')
            if saved_at != 'Unknown':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(saved_at.replace('Z', '+00:00') if saved_at.endswith('Z') else saved_at)
                    saved_at = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            table.add_row(
                str(i),
                config_info["name"],
                config_info.get("description", "No description")[:40],
                saved_at
            )
        
        self.console.print(table)
        
        # Get user choice
        try:
            choice = IntPrompt.ask(
                "\\nEnter configuration number to load (0 to cancel)",
                choices=[str(i) for i in range(0, len(configs) + 1)],
                default=0
            )
            
            if choice == 0:
                return
            
            config_name = configs[choice - 1]["name"]
            config_data = self.config_manager.load_config(config_name)
            
            if config_data:
                # Apply configuration to current config
                self.config = config_to_crawl_config(config_data, CrawlConfig)
                
                # Apply output settings if available
                output_settings = config_data.get("output_settings", {})
                if output_settings:
                    for key, value in output_settings.items():
                        if hasattr(self.output_manager, key):
                            setattr(self.output_manager, key, value)
                
                self.console.print(f"[green]✓ Configuration '{config_name}' loaded successfully[/green]")
                self.display_config_summary()
            else:
                self.console.print(f"[red]Failed to load configuration '{config_name}'[/red]")
                
        except ValueError:
            self.console.print("[red]Invalid selection[/red]")
    
    def _save_current_configuration(self):
        """Save current configuration."""
        config_name = Prompt.ask("\\nEnter configuration name")
        if not config_name:
            self.console.print("[yellow]Configuration name cannot be empty[/yellow]")
            return
        
        description = Prompt.ask("Enter description (optional)", default="")
        
        # Convert current config to dictionary
        config_dict = crawl_config_to_dict(self.config, self.output_manager)
        config_dict["description"] = description or f"Configuration saved on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if self.config_manager.save_config(config_name, config_dict):
            self.console.print(f"[green]✓ Configuration '{config_name}' saved successfully[/green]")
        else:
            self.console.print(f"[red]Failed to save configuration '{config_name}'[/red]")
    
    def _list_configurations(self):
        """List all saved configurations."""
        configs = self.config_manager.list_configs()
        if not configs:
            self.console.print("[yellow]No saved configurations found[/yellow]")
            return
        
        self.console.print(f"\\n[bold]Found {len(configs)} configurations:[/bold]")
        
        for config_info in configs:
            panel_content = []
            panel_content.append(f"Description: {config_info.get('description', 'No description')}")
            panel_content.append(f"Settings: {config_info.get('settings_count', 0)} parameters")
            
            created = config_info.get('created_at', 'Unknown')
            saved = config_info.get('saved_at', 'Unknown')
            if created != 'Unknown':
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00') if created.endswith('Z') else created)
                    created = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            if saved != 'Unknown':
                try:
                    dt = datetime.fromisoformat(saved.replace('Z', '+00:00') if saved.endswith('Z') else saved)
                    saved = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
                    
            panel_content.append(f"Created: {created}")
            panel_content.append(f"Saved: {saved}")
            
            panel = Panel(
                "\\n".join(panel_content),
                title=f"[bold cyan]{config_info['name']}[/bold cyan]",
                border_style="blue"
            )
            self.console.print(panel)
    
    def _delete_configuration(self):
        """Delete a saved configuration."""
        configs = self.config_manager.list_configs()
        if not configs:
            self.console.print("[yellow]No saved configurations found[/yellow]")
            return
        
        # Show configurations (excluding default)
        deletable_configs = [c for c in configs if c["name"] != "default"]
        if not deletable_configs:
            self.console.print("[yellow]No deletable configurations found (default cannot be deleted)[/yellow]")
            return
        
        self.console.print("\\n[bold]Select configuration to delete:[/bold]")
        for i, config_info in enumerate(deletable_configs, 1):
            self.console.print(f"{i}. {config_info['name']} - {config_info.get('description', 'No description')}")
        
        try:
            choice = IntPrompt.ask(
                "\\nEnter configuration number to delete (0 to cancel)",
                choices=[str(i) for i in range(0, len(deletable_configs) + 1)],
                default=0
            )
            
            if choice == 0:
                return
            
            config_name = deletable_configs[choice - 1]["name"]
            
            # Confirm deletion
            if Confirm.ask(f"Are you sure you want to delete '{config_name}'?", default=False):
                if self.config_manager.delete_config(config_name):
                    self.console.print(f"[green]✓ Configuration '{config_name}' deleted successfully[/green]")
                else:
                    self.console.print(f"[red]Failed to delete configuration '{config_name}'[/red]")
            
        except ValueError:
            self.console.print("[red]Invalid selection[/red]")
    
    def _create_presets(self):
        """Create common configuration presets."""
        self.console.print("\\n[bold]Creating configuration presets...[/bold]")
        
        self.config_manager.create_presets()
        self.console.print("[green]✓ Configuration presets created:[/green]")
        self.console.print("  • [cyan]fast[/cyan] - Quick crawling for fast results")
        self.console.print("  • [cyan]comprehensive[/cyan] - Thorough crawling for complete coverage")  
        self.console.print("  • [cyan]api_docs[/cyan] - Optimized for API documentation sites")
    
    def _export_configuration(self):
        """Export configuration to file."""
        configs = self.config_manager.list_configs()
        if not configs:
            self.console.print("[yellow]No configurations to export[/yellow]")
            return
        
        # Select configuration
        self.console.print("\\n[bold]Select configuration to export:[/bold]")
        for i, config_info in enumerate(configs, 1):
            self.console.print(f"{i}. {config_info['name']} - {config_info.get('description', 'No description')}")
        
        try:
            choice = IntPrompt.ask(
                "\\nEnter configuration number (0 to cancel)",
                choices=[str(i) for i in range(0, len(configs) + 1)],
                default=0
            )
            
            if choice == 0:
                return
            
            config_name = configs[choice - 1]["name"]
            export_path = Prompt.ask(
                "Enter export file path",
                default=f"{config_name}_config.json"
            )
            
            export_path = Path(export_path)
            if self.config_manager.export_config(config_name, export_path):
                self.console.print(f"[green]✓ Configuration exported to '{export_path}'[/green]")
            else:
                self.console.print(f"[red]Failed to export configuration[/red]")
                
        except ValueError:
            self.console.print("[red]Invalid selection[/red]")
    
    def _import_configuration(self):
        """Import configuration from file."""
        import_path = Prompt.ask("\\nEnter path to configuration file")
        if not import_path:
            return
        
        import_path = Path(import_path)
        config_name = Prompt.ask(
            "Enter new configuration name (leave empty to use file name)",
            default=""
        )
        
        if self.config_manager.import_config(import_path, config_name or None):
            name = config_name or import_path.stem
            self.console.print(f"[green]✓ Configuration '{name}' imported successfully[/green]")
        else:
            self.console.print(f"[red]Failed to import configuration[/red]")
    
    def select_urls_interactive(self, urls: List[str]) -> List[str]:
        """Interactive URL selection from discovered URLs."""
        if not urls:
            return urls
        
        self.console.print(f"\n[bold]Discovered {len(urls)} URLs[/bold]")
        
        # Display URLs in a table
        table = Table(show_header=True, title="Discovered URLs")
        table.add_column("#", style="cyan", width=4)
        table.add_column("URL", style="white")
        
        for i, url in enumerate(urls, 1):
            table.add_row(str(i), url)
        
        self.console.print(table)
        
        # Selection options
        self.console.print("\n[bold]Selection Options:[/bold]")
        self.console.print("1. Crawl all discovered URLs")
        self.console.print("2. Select specific URLs")
        self.console.print("3. Enter range (e.g., 1-10)")
        self.console.print("4. Cancel")
        
        choice = Prompt.ask("Your choice", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            return urls
        elif choice == "2":
            selected = []
            self.console.print("[dim]Enter URL numbers separated by commas (e.g., 1,3,5)[/dim]")
            selection = Prompt.ask("Select URLs")
            
            for num_str in selection.split(','):
                try:
                    num = int(num_str.strip())
                    if 1 <= num <= len(urls):
                        selected.append(urls[num - 1])
                except ValueError:
                    pass
            
            return selected
        elif choice == "3":
            range_str = Prompt.ask("Enter range (e.g., 1-10)")
            try:
                start, end = map(int, range_str.split('-'))
                return urls[start-1:end]
            except:
                self.console.print("[red]Invalid range format[/red]")
                return []
        else:
            return []
    
    def progress_callback(self, current: int, total: int, message: str):
        """Callback for progress updates."""
        if self.current_progress:
            task_id = self.current_progress.task_ids[0]
            self.current_progress.update(task_id, completed=current, total=total, description=message[:50])
    
    async def execute_crawl(self, mode: str, params: Dict[str, Any]):
        """Execute the crawling operation based on mode (without saving files)."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            self.current_progress = progress
            
            if mode == "single":
                url, deep_crawl, patterns, exclude_patterns = params.values()
                
                task = progress.add_task(
                    f"Crawling {url}...",
                    total=1 if not deep_crawl else 100
                )
                
                # Create crawler with output manager
                crawler = ContentCrawler(self.config, self.output_manager)
                result = await crawler.crawl_urls([url], self.progress_callback)
                
            elif mode == "pattern":
                base_url, patterns, exclude_patterns = params.values()
                
                task = progress.add_task(
                    f"Pattern crawling from {base_url}...",
                    total=100
                )
                
                # Pattern crawling with discovery
                discovery = URLDiscovery(self.config)
                discovered_urls = await discovery.discover_urls(base_url, patterns, exclude_patterns)
                
                if discovered_urls:
                    crawler = ContentCrawler(self.config, self.output_manager)
                    result = await crawler.crawl_urls(discovered_urls, self.progress_callback)
                    result['discovery'] = {
                        'start_url': base_url,
                        'discovered_count': len(discovered_urls)
                    }
                else:
                    result = {
                        'total_urls': 0,
                        'successful': 0,
                        'failed': 0,
                        'message': 'No URLs discovered matching patterns'
                    }
                
            elif mode == "multiple":
                urls, deep_crawl, patterns, exclude_patterns = params.values()
                
                task = progress.add_task(
                    f"Crawling {len(urls)} URLs...",
                    total=len(urls)
                )
                
                if deep_crawl:
                    # Deep crawl for multiple URLs
                    all_discovered = set()
                    for url in urls:
                        discovery = URLDiscovery(self.config)
                        discovered = await discovery.discover_urls(url, patterns, exclude_patterns)
                        all_discovered.update(discovered)
                    
                    if all_discovered:
                        crawler = ContentCrawler(self.config, self.output_manager)
                        result = await crawler.crawl_urls(list(all_discovered), self.progress_callback)
                    else:
                        result = {
                            'total_urls': 0,
                            'successful': 0,
                            'failed': 0,
                            'message': 'No URLs discovered'
                        }
                else:
                    # Direct crawl without discovery
                    crawler = ContentCrawler(self.config, self.output_manager)
                    result = await crawler.crawl_urls(urls, self.progress_callback)
            
            else:
                result = None
        
        self.current_progress = None
        return result
    
    def display_dry_run_results(self, result: Dict[str, Any]):
        """Display dry run results showing what would be crawled."""
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold yellow]🔍 Dry Run Complete![/bold yellow]")
        self.console.print("=" * 60)
        
        # Summary
        self.console.print(f"\n[bold]Dry Run Summary:[/bold]")
        self.console.print(f"• Would crawl [cyan]{result.get('total_urls', 0)}[/cyan] URLs")
        
        # Show discovered URLs
        discovered_urls = result.get('discovered_urls', [])
        if discovered_urls:
            self.console.print(f"\n[bold]URLs that would be crawled:[/bold]")
            
            # Create table for URLs
            table = Table(show_header=True, title="Discovered URLs")
            table.add_column("#", style="cyan", width=4)
            table.add_column("URL", style="white")
            
            # Show first 20 URLs
            for i, url in enumerate(discovered_urls[:20], 1):
                table.add_row(str(i), url)
            
            if len(discovered_urls) > 20:
                table.add_row("...", f"[dim](and {len(discovered_urls) - 20} more URLs)[/dim]")
            
            self.console.print(table)
        
        # Show file preview
        file_preview = result.get('file_preview', [])
        if file_preview:
            self.console.print(f"\n[bold]Sample output file paths:[/bold]")
            for i, path in enumerate(file_preview[:5], 1):
                self.console.print(f"  {i}. {path}")
            if len(file_preview) > 5:
                self.console.print(f"  [dim]... (showing first 5 of {len(discovered_urls)} files)[/dim]")
        
        # URL relationships if available
        url_relationships = result.get('url_relationships', {})
        if url_relationships and len(url_relationships) > 0:
            self.console.print(f"\n[bold]URL Discovery Tree (sample):[/bold]")
            for parent, children in list(url_relationships.items())[:3]:
                self.console.print(f"  • {parent}")
                for child in children[:3]:
                    self.console.print(f"    └─ {child}")
                if len(children) > 3:
                    self.console.print(f"    └─ [dim](... {len(children) - 3} more)[/dim]")
        
        self.console.print(f"\n[yellow]ℹ️  This was a dry run. No content was actually crawled.[/yellow]")
        self.console.print("[dim]To perform the actual crawl, disable dry run mode (option 6 in main menu)[/dim]")
    
    def display_results(self, result: Dict[str, Any]):
        """Display crawling results."""
        if not result:
            return
        
        # Check if this is a dry run result
        if result.get('dry_run'):
            self.display_dry_run_results(result)
            return
        
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold green]✓ Crawling Complete![/bold green]")
        self.console.print("=" * 60)
        
        # Summary table
        table = Table(title="Crawl Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total URLs", str(result.get('total_urls', 0)))
        table.add_row("Successful", str(result.get('successful', 0)))
        table.add_row("Failed", str(result.get('failed', 0)))
        table.add_row("Total Content Size", f"{result.get('total_content_length', 0):,} chars")
        table.add_row("Output Directory", result.get('output_directory', str(self.config.output_dir)))
        
        self.console.print(table)
        
        # Failed URLs if any
        if result.get('failed_urls'):
            self.console.print("\n[bold red]Failed URLs:[/bold red]")
            for url, error in result['failed_urls']:
                self.console.print(f"  • {url}")
                self.console.print(f"    [dim]{error}[/dim]")
        
        # Discovery info if available
        if result.get('discovery'):
            disc = result['discovery']
            self.console.print(f"\n[bold]Discovery Info:[/bold]")
            self.console.print(f"  Start URL: {disc['start_url']}")
            self.console.print(f"  URLs Discovered: {disc['discovered_count']}")
        
        # Max pages limit info
        if result.get('successful', 0) == self.config.max_pages:
            self.console.print(f"\n[bold yellow]💡 Max Pages Limit Reached:[/bold yellow]")
            self.console.print(f"  Crawled: {result.get('successful', 0)} pages (limit: {self.config.max_pages})")
            self.console.print(f"  [dim]If results seem incomplete, increase max pages in Settings (option 4)[/dim]")
    
    async def run(self, skip_deps: bool = False):
        """Main run loop."""
        # Import dependencies after installation
        global console
        console = import_dependencies()
        
        self.display_banner()
        
        # Dependencies are already checked/installed in main()
        
        while not self.interrupted:
            try:
                choice = self.main_menu()
                
                if choice == "1":
                    # Single URL
                    url, deep_crawl, patterns, exclude_patterns = self.get_single_url_input()
                    
                    # Configure output BEFORE crawling starts
                    estimated_urls = 1
                    if deep_crawl:
                        estimated_urls = "1+" # Could discover more
                    
                    output_dir = self.output_manager.prompt_output_configuration(
                        self.console, estimated_urls, self.config
                    )
                    self.config.output_dir = output_dir
                    
                    if deep_crawl and patterns:
                        # Discovery phase
                        self.console.print("\n[bold]Starting discovery phase...[/bold]")
                        discovery = URLDiscovery(self.config)
                        discovered = await discovery.discover_urls(url, patterns, exclude_patterns)
                        
                        if discovered:
                            selected = self.select_urls_interactive(discovered)
                            if selected:
                                # Update estimated count
                                self.console.print(f"\n[cyan]Crawling {len(selected)} selected URLs...[/cyan]")
                                
                                # Crawl selected URLs with configured output
                                crawler = ContentCrawler(self.config, self.output_manager)
                                result = await crawler.crawl_urls(selected, self.progress_callback)
                                self.display_results(result)
                        else:
                            self.console.print("[yellow]No URLs discovered matching patterns[/yellow]")
                    else:
                        # Direct crawl
                        result = await self.execute_crawl("single", {
                            'url': url,
                            'deep_crawl': deep_crawl,
                            'patterns': patterns,
                            'exclude_patterns': exclude_patterns
                        })
                        self.display_results(result)
                
                elif choice == "2":
                    # Pattern crawling
                    base_url, patterns, exclude_patterns = self.get_pattern_input()
                    
                    # Configure output BEFORE crawling
                    output_dir = self.output_manager.prompt_output_configuration(
                        self.console, "Unknown (pattern discovery)", self.config
                    )
                    self.config.output_dir = output_dir
                    
                    result = await self.execute_crawl("pattern", {
                        'base_url': base_url,
                        'patterns': patterns,
                        'exclude_patterns': exclude_patterns
                    })
                    self.display_results(result)
                
                elif choice == "3":
                    # Multiple URLs
                    urls, deep_crawl, patterns, exclude_patterns = self.get_multiple_urls_input()
                    
                    if urls:
                        # Configure output BEFORE crawling
                        estimated_count = len(urls)
                        if deep_crawl:
                            estimated_count = f"{len(urls)}+ (with discovery)"
                        
                        output_dir = self.output_manager.prompt_output_configuration(
                            self.console, estimated_count, self.config
                        )
                        self.config.output_dir = output_dir
                        
                        result = await self.execute_crawl("multiple", {
                            'urls': urls,
                            'deep_crawl': deep_crawl,
                            'patterns': patterns,
                            'exclude_patterns': exclude_patterns
                        })
                        self.display_results(result)
                
                elif choice == "4":
                    # Configure settings
                    self.configure_settings()
                
                elif choice == "5":
                    # Configuration management
                    self.manage_configurations()
                
                elif choice == "6":
                    # Toggle Dry Run Mode
                    self.config.dry_run = not self.config.dry_run
                    status = "enabled" if self.config.dry_run else "disabled"
                    self.console.print(f"\n[green]✓ Dry Run mode {status}[/green]")
                    if self.config.dry_run:
                        self.console.print("[yellow]ℹ️  In dry run mode, URLs will be discovered but content won't be crawled[/yellow]")
                    self.console.print()
                
                elif choice == "7":
                    # Test Content Selectors
                    await self.test_content_selectors()
                
                elif choice == "8":
                    # Exit
                    self.console.print("\n[bold blue]Thank you for using Crawl4AI Interactive![/bold blue]")
                    break
                
                # Ask to continue
                if choice in ["1", "2", "3"]:
                    if not Confirm.ask("\n\nContinue with another crawl?", default=True):
                        break
            
            except KeyboardInterrupt:
                self.interrupted = True
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                if Confirm.ask("Continue?", default=True):
                    continue
                else:
                    break


def main():
    """Main entry point - handles dependencies first, then CLI args."""
    
    # Import dependency checker (always available)
    from dependency_checker import ensure_dependencies
    
    # First, always ensure dependencies are installed
    print("🕷️  Crawl4AI Interactive Web Scraper")
    print("=====================================")
    print("Checking and installing dependencies...")
    
    success = ensure_dependencies(auto_install=True, silent=False)
    if not success:
        print("❌ Failed to install dependencies.")
        print("Please run manually: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All dependencies satisfied\n")
    
    # Now import the heavy dependencies
    global console
    console = import_dependencies()
    
    # Check if we have arguments (after dependencies are installed)
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        cli = InteractiveCLI()
        
        try:
            asyncio.run(cli.run(skip_deps=True))  # Skip deps since we already checked
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[red]Fatal error: {e}[/red]")
            sys.exit(1)
    
    else:
        # Handle command line arguments (click is now available)
        run_with_args()


if __name__ == "__main__":
    main()

