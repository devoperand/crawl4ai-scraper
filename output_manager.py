#!/usr/bin/env python3
"""
Output Management System for crawl4ai-scraper
Handles directory configuration, file organization, and naming conventions
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse
from datetime import datetime
import json
import hashlib


class OutputManager:
    """Manages output directory structure and file organization after scraping."""
    
    # File organization strategies
    FLAT_STRUCTURE = "flat"
    MIRROR_STRUCTURE = "mirror"
    DOMAIN_GROUPED = "domain"
    DATE_ORGANIZED = "date"
    CUSTOM_PATTERN = "custom"
    
    # File naming conventions
    NAMING_URL_BASED = "url_based"
    NAMING_TITLE_BASED = "title_based"
    NAMING_TIMESTAMP = "timestamp"
    NAMING_HASH = "hash"
    
    def __init__(self):
        self.organization_strategy = self.FLAT_STRUCTURE
        self.naming_convention = self.NAMING_URL_BASED
        self.base_output_dir = Path("output")
        self.include_metadata = True
        self.timestamp_format = "%Y%m%d_%H%M%S"
        self.max_filename_length = 255
        
    def prompt_output_configuration(self, console, estimated_urls: int = None, config=None) -> Path:
        """
        Prompt user for output configuration BEFORE crawling starts.
        
        Args:
            console: Rich console for formatted output
            estimated_urls: Estimated number of URLs to be crawled (optional)
            config: CrawlConfig object with max_pages setting (optional)
            
        Returns:
            Path: The configured output directory
        """
        from rich.table import Table
        from rich.prompt import Prompt, Confirm, IntPrompt
        from rich.panel import Panel
        
        # Show configuration header
        console.print("\n" + "="*60)
        console.print("[bold]Output Configuration[/bold]")
        console.print("="*60)
        
        if estimated_urls:
            console.print(f"Estimated URLs to crawl: [cyan]{estimated_urls}[/cyan]")
        
        # Show max pages warning if applicable
        if config and hasattr(config, 'max_pages'):
            console.print(f"Current max pages limit: [yellow]{config.max_pages}[/yellow]")
            
            # Check for potential issues
            try:
                if estimated_urls and isinstance(estimated_urls, int) and estimated_urls > config.max_pages:
                    console.print(f"[bold red]⚠️  WARNING:[/bold red] Estimated URLs ({estimated_urls}) exceeds max pages limit ({config.max_pages})")
                    console.print(f"[dim]Only the first {config.max_pages} discovered URLs will be crawled.[/dim]")
                    console.print(f"[dim]To crawl more URLs, go to Settings Menu (option 4) and increase 'Max Pages'.[/dim]")
                elif estimated_urls and "+" in str(estimated_urls):
                    console.print(f"[bold yellow]💡 NOTE:[/bold yellow] Discovery may find more URLs than the current limit ({config.max_pages})")
                    console.print(f"[dim]If results seem incomplete, consider increasing max pages in Settings.[/dim]")
            except (ValueError, TypeError):
                # Handle non-numeric estimated_urls gracefully
                pass
        
        # Output Directory Configuration
        console.print("\n[bold]Output Directory Configuration[/bold]")
        console.print(f"Current working directory: [cyan]{os.getcwd()}[/cyan]")
        
        # Get output directory
        output_path = Prompt.ask(
            "\nEnter output directory path",
            default=str(self.base_output_dir)
        )
        
        # Handle relative and absolute paths
        output_dir = self._resolve_path(output_path)
        
        # Show resolved path
        console.print(f"Resolved path: [green]{output_dir.absolute()}[/green]")
        
        # Confirm directory creation if it doesn't exist
        if not output_dir.exists():
            create_dir = Confirm.ask(
                f"\nDirectory does not exist. Create it?",
                default=True
            )
            if not create_dir:
                # Ask for alternative path
                return self.prompt_output_configuration(console, estimated_urls, config)
        
        # File Organization Strategy
        console.print("\n[bold]File Organization Strategy[/bold]")
        console.print("1. [cyan]Flat[/cyan] - All files in one directory")
        console.print("2. [cyan]Mirror[/cyan] - Maintain website URL structure")
        console.print("3. [cyan]Domain[/cyan] - Group by domain")
        console.print("4. [cyan]Date[/cyan] - Organize by scraping date")
        console.print("5. [cyan]Custom[/cyan] - Custom pattern-based organization")
        
        org_choice = IntPrompt.ask(
            "Select organization strategy",
            choices=[1, 2, 3, 4, 5],
            default=1
        )
        
        org_strategies = {
            1: self.FLAT_STRUCTURE,
            2: self.MIRROR_STRUCTURE,
            3: self.DOMAIN_GROUPED,
            4: self.DATE_ORGANIZED,
            5: self.CUSTOM_PATTERN
        }
        self.organization_strategy = org_strategies[org_choice]
        
        # Custom pattern configuration
        if self.organization_strategy == self.CUSTOM_PATTERN:
            pattern = Prompt.ask(
                "Enter custom organization pattern",
                default="{domain}/{year}/{month}/{filename}"
            )
            self.custom_pattern = pattern
        
        # File Naming Convention
        console.print("\n[bold]File Naming Convention[/bold]")
        console.print("1. [cyan]URL-based[/cyan] - Convert URL to filename")
        console.print("2. [cyan]Title-based[/cyan] - Use page title")
        console.print("3. [cyan]Timestamp[/cyan] - Include timestamp in filename")
        console.print("4. [cyan]Hash[/cyan] - Use URL hash for unique names")
        
        naming_choice = IntPrompt.ask(
            "Select naming convention",
            choices=[1, 2, 3, 4],
            default=1
        )
        
        naming_conventions = {
            1: self.NAMING_URL_BASED,
            2: self.NAMING_TITLE_BASED,
            3: self.NAMING_TIMESTAMP,
            4: self.NAMING_HASH
        }
        self.naming_convention = naming_conventions[naming_choice]
        
        # Include metadata in files?
        self.include_metadata = Confirm.ask(
            "\nInclude metadata in markdown files?",
            default=True
        )
        
        # Show preview of file organization with sample URLs
        sample_urls = [
            {'url': 'https://example.com/page1', 'title': 'Example Page 1'},
            {'url': 'https://example.com/blog/post1', 'title': 'Blog Post 1'},
            {'url': 'https://docs.example.com/api/guide', 'title': 'API Guide'}
        ]
        self._show_organization_preview(console, output_dir, sample_urls)
        
        # Confirm configuration
        proceed = Confirm.ask(
            "\nProceed with this configuration?",
            default=True
        )
        
        if not proceed:
            return self.prompt_output_configuration(console, estimated_urls, config)
        
        self.base_output_dir = output_dir
        return output_dir
    
    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve path string to absolute Path object.
        Handles both absolute and relative paths.
        """
        path = Path(path_str).expanduser()
        
        if not path.is_absolute():
            # Convert relative to absolute based on current working directory
            path = Path.cwd() / path
        
        return path.resolve()
    
    def _show_organization_preview(self, console, output_dir: Path, sample_data: List[Dict]):
        """Show preview of how files will be organized."""
        from rich.tree import Tree
        
        console.print("\n[bold]Organization Preview:[/bold]")
        
        tree = Tree(f"📁 {output_dir.name}/")
        
        for item in sample_data:
            if 'url' in item:
                file_path = self.get_file_path(item, output_dir)
                relative_path = file_path.relative_to(output_dir)
                
                # Build tree structure
                parts = relative_path.parts
                current = tree
                for part in parts[:-1]:
                    # Find or create subdirectory in tree
                    found = False
                    for child in current.children:
                        if child.label.strip().endswith(f"{part}/"):
                            current = child
                            found = True
                            break
                    if not found:
                        current = current.add(f"📁 {part}/")
                
                # Add file
                current.add(f"📄 {parts[-1]}")
        
        if len(sample_data) < len(sample_data):
            tree.add("... more files")
        
        console.print(tree)
    
    def get_file_path(self, content_data: Dict[str, Any], base_dir: Path) -> Path:
        """
        Generate file path based on organization strategy and naming convention.
        
        Args:
            content_data: Dictionary containing scraped content and metadata
            base_dir: Base output directory
            
        Returns:
            Path: Complete file path for saving content
        """
        # Generate filename
        filename = self._generate_filename(content_data)
        
        # Generate directory structure based on strategy
        if self.organization_strategy == self.FLAT_STRUCTURE:
            file_path = base_dir / filename
            
        elif self.organization_strategy == self.MIRROR_STRUCTURE:
            # Mirror the URL structure
            url = content_data.get('url', '')
            parsed = urlparse(url)
            
            # Create directory structure from URL path
            url_path = parsed.path.strip('/')
            if url_path:
                path_parts = url_path.split('/')
                # Remove filename if present
                if '.' in path_parts[-1]:
                    path_parts = path_parts[:-1]
                
                if path_parts:
                    dir_path = base_dir / parsed.netloc / Path(*path_parts)
                else:
                    dir_path = base_dir / parsed.netloc
            else:
                dir_path = base_dir / parsed.netloc
            
            file_path = dir_path / filename
            
        elif self.organization_strategy == self.DOMAIN_GROUPED:
            # Group by domain
            url = content_data.get('url', '')
            domain = urlparse(url).netloc or 'unknown'
            file_path = base_dir / domain / filename
            
        elif self.organization_strategy == self.DATE_ORGANIZED:
            # Organize by date
            date_str = datetime.now().strftime("%Y/%m/%d")
            file_path = base_dir / date_str / filename
            
        elif self.organization_strategy == self.CUSTOM_PATTERN:
            # Custom pattern-based organization
            file_path = self._apply_custom_pattern(content_data, base_dir, filename)
        
        else:
            file_path = base_dir / filename
        
        return file_path
    
    def _generate_filename(self, content_data: Dict[str, Any]) -> str:
        """Generate filename based on naming convention."""
        base_name = ""
        
        if self.naming_convention == self.NAMING_URL_BASED:
            # Convert URL to filename
            url = content_data.get('url', 'unknown')
            parsed = urlparse(url)
            
            # Combine domain and path
            domain = parsed.netloc.replace('www.', '')
            path = parsed.path.strip('/')
            
            if path:
                # Replace path separators with underscores
                path_clean = path.replace('/', '_').replace('-', '_')
                base_name = f"{domain}_{path_clean}"
            else:
                base_name = domain
                
        elif self.naming_convention == self.NAMING_TITLE_BASED:
            # Use page title
            title = content_data.get('title', 'untitled')
            # Clean title for filename
            base_name = re.sub(r'[^\w\s-]', '', title.lower())
            base_name = re.sub(r'[-\s]+', '_', base_name)
            
        elif self.naming_convention == self.NAMING_TIMESTAMP:
            # Include timestamp
            timestamp = datetime.now().strftime(self.timestamp_format)
            url = content_data.get('url', 'unknown')
            domain = urlparse(url).netloc.replace('www.', '') or 'unknown'
            base_name = f"{domain}_{timestamp}"
            
        elif self.naming_convention == self.NAMING_HASH:
            # Use URL hash
            url = content_data.get('url', 'unknown')
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            domain = urlparse(url).netloc.replace('www.', '') or 'unknown'
            base_name = f"{domain}_{url_hash}"
        
        # Clean filename
        base_name = self._clean_filename(base_name)
        
        # Ensure .md extension
        if not base_name.endswith('.md'):
            base_name += '.md'
        
        return base_name
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename to be valid across different operating systems."""
        # Remove invalid characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Limit length
        if len(filename) > self.max_filename_length - 3:  # Reserve space for .md
            filename = filename[:self.max_filename_length - 3]
        
        # Remove trailing dots and spaces
        filename = filename.rstrip('. ')
        
        # Ensure filename is not empty
        if not filename:
            filename = "unnamed"
        
        return filename
    
    def _apply_custom_pattern(self, content_data: Dict, base_dir: Path, filename: str) -> Path:
        """Apply custom pattern for file organization."""
        pattern = getattr(self, 'custom_pattern', '{domain}/{filename}')
        
        # Parse URL components
        url = content_data.get('url', '')
        parsed = urlparse(url)
        
        # Available variables for pattern
        now = datetime.now()
        variables = {
            'domain': parsed.netloc.replace('www.', '') or 'unknown',
            'subdomain': parsed.netloc.split('.')[0] if '.' in parsed.netloc else '',
            'path': parsed.path.strip('/').replace('/', '_'),
            'year': now.strftime('%Y'),
            'month': now.strftime('%m'),
            'day': now.strftime('%d'),
            'date': now.strftime('%Y%m%d'),
            'filename': filename
        }
        
        # Replace variables in pattern
        path_str = pattern
        for key, value in variables.items():
            path_str = path_str.replace(f'{{{key}}}', value)
        
        # Clean up any remaining braces
        path_str = re.sub(r'{[^}]*}', '', path_str)
        
        return base_dir / path_str
    
    async def save_scraped_content(self, scraped_data: List[Dict[str, Any]], 
                                  output_dir: Path, console) -> Dict[str, Any]:
        """
        Save all scraped content to the configured output directory.
        
        Args:
            scraped_data: List of scraped content dictionaries
            output_dir: Configured output directory
            console: Rich console for progress display
            
        Returns:
            Dictionary with save operation results
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        import aiofiles
        
        saved_files = []
        failed_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                f"Saving {len(scraped_data)} files...",
                total=len(scraped_data)
            )
            
            for item in scraped_data:
                try:
                    # Generate file path
                    file_path = self.get_file_path(item, output_dir)
                    
                    # Create directory if needed
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Prepare content
                    if self.include_metadata:
                        content = self._format_content_with_metadata(item)
                    else:
                        content = item.get('markdown', '')
                    
                    # Save file
                    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                        await f.write(content)
                    
                    saved_files.append(str(file_path))
                    progress.update(task, advance=1, description=f"Saved: {file_path.name}")
                    
                except Exception as e:
                    failed_files.append({
                        'url': item.get('url', 'unknown'),
                        'error': str(e)
                    })
                    progress.update(task, advance=1, description=f"Failed: {item.get('url', 'unknown')}")
        
        # Save summary report
        summary_path = output_dir / "scraping_summary.json"
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(scraped_data),
            'saved_files': len(saved_files),
            'failed_files': len(failed_files),
            'organization_strategy': self.organization_strategy,
            'naming_convention': self.naming_convention,
            'output_directory': str(output_dir),
            'saved_paths': saved_files,
            'failures': failed_files
        }
        
        async with aiofiles.open(summary_path, 'w') as f:
            await f.write(json.dumps(summary, indent=2))
        
        return summary
    
    def _format_content_with_metadata(self, content_data: Dict[str, Any]) -> str:
        """Format content with metadata header."""
        metadata = {
            'url': content_data.get('url', ''),
            'title': content_data.get('title', 'Untitled'),
            'description': content_data.get('description', ''),
            'crawled_at': content_data.get('crawled_at', datetime.now().isoformat()),
            'content_length': content_data.get('content_length', 0),
            'capture_mode': 'enhanced'
        }
        
        # Format as YAML front matter
        header_lines = ['---']
        for key, value in metadata.items():
            header_lines.append(f"{key}: {value}")
        header_lines.append('---')
        header_lines.append('')
        
        # Add title and content
        title = content_data.get('title', 'Untitled')
        markdown = content_data.get('markdown', '')
        
        # Combine all parts
        return '\n'.join(header_lines) + f"# {title}\n\n{markdown}"