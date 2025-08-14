# 🕷️ Crawl4AI Interactive Web Scraper

A comprehensive Python 3.11+ compatible interactive web scraping tool built on top of [Crawl4AI](https://github.com/unclecode/crawl4ai) with advanced content extraction, user-agent rotation, and dry-run capabilities.

## ✨ Key Features

### 🎯 Multiple Crawling Modes
- **Single URL**: Crawl individual URLs with optional deep crawling
- **URL Pattern**: Use wildcards (`*`, `**`, `?`) to match specific URL patterns
- **Multiple URLs**: Batch process multiple URLs from manual input or file

### 🔍 Smart Discovery & Content Extraction
- **Two-phase approach**: Discovery → Content Extraction
- **BFS (Breadth-First Search)** strategy for link discovery
- **Interactive URL selection** after discovery phase
- **URL relationship tracking** for site mapping
- **Dry Run Mode**: Preview URLs without crawling content

### 🛡️ Advanced Anti-Detection Features
- **User-Agent Rotation**: Automatically rotates through 8 different browser user-agents
- **Request Delays**: Configurable delays between requests (0.1-10 seconds)
- **Concurrent Control**: Limit concurrent requests (1-10 simultaneous)
- **Retry Mechanisms**: Automatic retry on failures

### 🎨 Enhanced Content Extraction
- **CSS Selector Support**: Target specific content with CSS selectors
- **XPath Expression Support**: Advanced content targeting with XPath
- **Preset Templates**: Pre-configured selectors for common site types:
  - Blog (`article`, `.post-content`, `.entry-content`)
  - News (`.article-body`, `.story-content`)
  - Documentation (`.markdown-body`, `.doc-content`)
  - E-commerce (`.product-description`, `.product-details`)
  - Forum (`.post-body`, `.message-content`)
- **Generic Content Cleaning**: Automatically removes navigation, headers, footers
- **Smart Content Detection**: Identifies main content using heuristics

### 🧪 Testing & Validation Tools
- **Selector Testing**: Test CSS/XPath selectors on live URLs before crawling
- **Dry Run Mode**: Preview what will be crawled without downloading content
- **Interactive & CLI Dry Run**: Both menu toggle and `--dry-run` command flag
- **Content Preview**: See extraction results before committing to full crawl

### ✨ Complete Content Capture
- **Adaptive Scrolling**: Advanced JavaScript execution to trigger lazy loading
- **Smart Loading**: Waits for network idle to ensure complete page content
- **Enhanced Markdown**: Preserves links, images, code blocks, and proper formatting
- **Content Cleaning Profiles**: 
  - **Strict**: Aggressive cleaning, removes most non-content
  - **Moderate**: Balanced approach (default)
  - **Minimal**: Light cleaning, preserves most elements

### ⚙️ Comprehensive Configuration
- **Content Extraction Settings**: Configure CSS/XPath selectors, cleaning profiles
- **Request Settings**: Concurrent limits, delays, timeouts, retries
- **Output Configuration**: Organization strategies, naming conventions
- **Configuration Persistence**: Save/load settings as presets
- **Import/Export**: Share configurations across sessions

### 📊 Rich Interactive Interface
- **8-Option Main Menu**:
  1. Single URL crawling
  2. URL pattern crawling  
  3. Multiple URLs crawling
  4. Settings configuration
  5. Save/Load configurations
  6. **Toggle Dry Run Mode**
  7. **Test Content Selectors**
  8. Exit
- **Real-time progress bars** with status updates
- **Color-coded output** and formatted tables
- **Detailed result reporting** with statistics

### 📁 Advanced Output Management
- **5 Organization Strategies**: 
  - Flat (all files in one directory)
  - Mirror (preserves website structure)
  - Domain-grouped (groups by domain)
  - Date-organized (organizes by scraping date)
  - Custom patterns (user-defined structure)
- **4 Naming Conventions**: URL-based, Title-based, Timestamp, Hash
- **Metadata Options**: Include/exclude YAML front matter
- **Memory Efficient**: Files saved immediately to prevent memory issues

## 🚀 Installation

### Prerequisites
- **Python 3.11 or higher**
- pip package manager
- Virtual environment support

### Quick Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd crawl4ai-scraper
```

2. **Create virtual environment:**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows  
python -m venv venv
venv\Scripts\activate
```

3. **Run the tool (auto-installs dependencies):**
```bash
python3 main.py
```

### Verification
```bash
# Check dependencies
python3 main.py --check-deps

# Install dependencies manually if needed
python3 main.py --install-deps
```

## 🎮 Usage

### Basic Usage
```bash
# Interactive mode
python3 main.py

# Dry run mode (preview only)
python3 main.py --dry-run

# Skip dependency check (faster startup)
python3 main.py --skip-deps
```

### Command-Line Options
```bash
--check-deps    # Verify dependencies without installing
--install-deps  # Install dependencies and exit
--skip-deps     # Skip dependency checking
--dry-run       # Run in dry-run mode (discover URLs only)
```

## 🔧 Advanced Features

### User-Agent Rotation
Automatically rotates through 8 different browser user-agents:
- Chrome on Windows/Mac/Linux
- Firefox on Windows/Mac  
- Safari on Mac
- Edge on Windows

### Dry Run Mode
Two ways to enable:
1. **Command-line**: `python3 main.py --dry-run`
2. **Interactive**: Menu option 6 to toggle during session

**Dry run shows:**
- URLs that would be crawled
- File organization preview
- URL discovery tree
- No actual content download

### Content Extraction Testing
**Menu Option 7: Test Content Selectors**
- Test CSS selectors on live URLs
- Test XPath expressions
- Compare extraction methods
- Save working selectors to config

### CSS & XPath Selectors

**CSS Selector Examples:**
```css
article                    /* Main article content */
.post-content             /* Posts with post-content class */
#main-content             /* Element with main-content ID */
main .documentation       /* Documentation inside main */
```

**XPath Expression Examples:**
```xpath
//article                              /* Any article element */
//div[@class='content']                /* Div with content class */
//main//section[contains(@class,'doc')] /* Sections with 'doc' in class */
//div[@id='content']//p                /* Paragraphs in content div */
```

**Template Presets:**
- **Blog**: `article`, `.post-content`, `.entry-content`
- **News**: `.article-body`, `.story-content`
- **Documentation**: `.markdown-body`, `.doc-content`
- **E-commerce**: `.product-description`, `.product-details`
- **Forum**: `.post-body`, `.message-content`

## 📖 Examples

### 1. Single URL with Content Extraction
```
Menu: 1 (Single URL)
URL: https://docs.example.com/guide
Deep crawl: No

Output Configuration:
Directory: ./scraped_content
Organization: Mirror
Naming: Title-based
Metadata: Yes

Content Extraction:
Method: CSS
Selectors: article, .doc-content
Template: Documentation
```

### 2. Pattern Crawling with Dry Run
```bash
# First, test with dry run
python3 main.py --dry-run

Menu: 2 (URL Pattern)  
Base URL: https://docs.example.com
Patterns: **/api/**, **/guides/**
Exclude: */deprecated/*

# Review discovered URLs, then run actual crawl
python3 main.py

Menu: 2 (URL Pattern)
[Same configuration]
```

### 3. Bulk URL Processing
Create `urls.txt`:
```
https://blog.example.com/post1
https://blog.example.com/post2  
https://docs.example.com/api
```

Then:
```
Menu: 3 (Multiple URLs)
Input: file
File: urls.txt

Content Extraction:
Template: Blog
Method: Auto (CSS + XPath)
Cleaning: Moderate
```

### 4. Testing Selectors Before Crawling
```
Menu: 7 (Test Content Selectors)
Test URL: https://example.com/sample
CSS Selectors: article, .main-content
XPath: //main//div[@class='content']

# View extraction results
# Save working selectors to config
```

## ⚙️ Configuration Options

### Main Settings (Menu Option 4)
| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| **Output Directory** | Where to save content | `output/` | Any valid path |
| **Concurrent Requests** | Parallel requests | 3 | 1-10 |
| **Request Delay** | Seconds between requests | 1.0 | 0.1-10.0 |
| **Max Pages** | Maximum pages to crawl | 50 | 1-unlimited |
| **Max Depth** | Link following depth | 2 | 1-5 |
| **Cache Mode** | Enable request caching | True | True/False |
| **Include External** | Follow external links | False | True/False |

### Content Extraction Settings
| Setting | Description | Options |
|---------|-------------|---------|
| **Extraction Method** | Selector type | CSS, XPath, Auto |
| **Template** | Preset selectors | Blog, News, Documentation, etc. |
| **Cleaning Profile** | Content cleaning level | Strict, Moderate, Minimal |
| **Custom Selectors** | User-defined CSS/XPath | Any valid selectors |
| **Min Content Length** | Minimum content size | 50-500 chars |

## 🎯 URL Pattern Syntax

### Wildcards
- `*` - Matches any characters except `/`
- `**` - Matches any characters including `/`  
- `?` - Matches single character

### Examples
```
*/blog/*           # Matches /blog/ anywhere in path
**/docs/**         # Matches /docs/ with any path before/after
*.html             # Matches URLs ending with .html
*/api/v?/*         # Matches /api/v1/, /api/v2/, etc.
**/guide-*/**      # Matches any guide- prefixed sections
```

## 📁 Output Organization

### Organization Strategies

**1. Flat Structure (Default)**
```
output/
├── example_com_page1.md
├── example_com_blog_post.md
└── crawl_summary.json
```

**2. Mirror Structure**
```
output/
├── example.com/
│   ├── index.md
│   └── blog/
│       └── post1.md
└── docs.example.com/
    └── api/guide.md
```

**3. Domain Grouped**
```
output/
├── example.com/
│   ├── example_com_page1.md
│   └── example_com_blog_post.md
└── docs.example.com/
    └── docs_example_com_api.md
```

### Markdown Output Format
```markdown
---
url: https://example.com/page
title: Page Title
description: Page description
crawled_at: 2024-01-01T12:00:00Z
content_length: 5432
extraction_method: css
template_used: documentation
user_agent: Mozilla/5.0 (Windows NT 10.0...)
---

# Page Title

[Clean, formatted content with proper paragraphs, 
headers, code blocks, and links preserved]
```

## 🔍 Understanding Max Pages & Discovery Process

### How Max Pages Works

The `max_pages` setting is a crucial limit that controls the **URL discovery phase** before any content is actually crawled:

#### Discovery Process Flow
1. **URL Discovery Phase**: The crawler discovers URLs using BFS (Breadth-First Search)
2. **Max Pages Check**: Discovery stops when `max_pages` limit is reached
3. **User Selection**: You can interactively select which discovered URLs to crawl
4. **Content Extraction**: Only selected URLs have their content downloaded and processed

#### Important Behaviors
- **Discovery Limit**: Stops finding new URLs when limit reached, not by content quality
- **Pattern Matching**: Only first N URL matches are processed in discovery order
- **Breadth-First Order**: URLs discovered by depth level, not by relevance or importance
- **Memory Efficient**: Only discovered URL metadata is stored during discovery phase

### Recommended Max Pages Limits

#### By Use Case
| Use Case | Max Pages | Memory Usage | Discovery Time |
|----------|-----------|---------------|----------------|
| **Single Page Analysis** | 1-5 | ~100KB | < 30 seconds |
| **Small Site Section** | 10-25 | ~1MB | 1-2 minutes |
| **API Documentation** | 50-150 | ~5MB | 2-5 minutes |
| **Full Site Documentation** | 200-500 | ~20MB | 5-15 minutes |
| **Large Scale Discovery** | 500-1000 | ~50MB | 10-30 minutes |
| **Comprehensive Site Mapping** | 1000+ | ~100MB+ | 30+ minutes |

#### By Website Type
| Website Type | Recommended Limit | Reasoning |
|--------------|-------------------|-----------|
| **Personal Blogs** | 20-50 | Usually have limited content |
| **Corporate Websites** | 50-200 | Multiple sections, moderate size |
| **Documentation Sites** | 100-500 | Structured content, predictable size |
| **E-commerce Sites** | 200-1000 | Many product pages, large catalogs |
| **News/Media Sites** | 500-2000 | Extensive archives, many articles |

### Changing Max Pages Limit

#### During Session
1. **Settings Menu**: Go to Menu Option 4 (Settings Configuration)
2. **Crawling Settings**: Select option 1
3. **Modify Max Pages**: Enter new limit (1 to unlimited)
4. **Apply**: Changes take effect for subsequent crawls

#### Command Line Override
```bash
# Set higher limit for large sites
python3 main.py
# In settings, set max_pages to desired value

# Use dry run first to estimate scope
python3 main.py --dry-run
```

#### Configuration Presets
| Preset | Max Pages | Best For |
|---------|-----------|----------|
| **Fast** | 10 | Quick sampling |
| **Default** | 50 | Balanced approach |
| **Comprehensive** | 200 | Thorough coverage |
| **API Docs** | 100 | Technical documentation |

### Performance Considerations

#### Discovery Phase Performance
```
Max Pages    | Discovery Time | Memory Usage | Recommended For
-------------|----------------|---------------|----------------
1-50         | < 2 minutes   | < 5MB        | Testing, small sites
50-200       | 2-5 minutes   | 5-20MB       | Medium sites
200-500      | 5-15 minutes  | 20-50MB      | Large documentation
500-1000     | 10-30 minutes | 50-100MB     | Comprehensive crawls
1000+        | 30+ minutes   | 100MB+       | Site mapping projects
```

#### Factors Affecting Performance
- **Website Response Time**: Slower sites take longer to discover
- **Site Structure Complexity**: Deep nesting increases discovery time
- **Network Latency**: Remote sites or slow connections affect speed
- **Concurrent Discovery**: Higher concurrent limits speed up discovery
- **Pattern Complexity**: Complex URL patterns slow down matching

#### Memory Usage Breakdown
- **URL Metadata**: ~100 bytes per discovered URL
- **Page Relationships**: ~50 bytes per URL link relationship
- **Discovery Tree**: ~25 bytes per URL in BFS tree structure
- **Pattern Matching**: ~10 bytes per URL pattern evaluation

### Discovery vs Content Extraction

#### Two-Phase Process
```
Phase 1: Discovery (Affected by max_pages)
├── Find URLs matching patterns
├── Build site relationship tree
├── Stop when max_pages reached
└── Present URLs for selection

Phase 2: Content Extraction (User controlled)
├── User selects URLs to crawl
├── Download and process content
├── Apply CSS/XPath selectors
└── Save to organized output
```

#### Why This Matters
- **Large Sites**: Discovery might find 10,000+ URLs but you only want to crawl 100
- **Selective Crawling**: You can discover comprehensively but crawl selectively
- **Resource Management**: Discovery uses minimal resources, content extraction uses more

### Optimizing Max Pages Settings

#### For Specific Scenarios

**Scenario 1: Testing New Site**
```
Recommendation: max_pages = 10-25
Reason: Quick preview of site structure
Strategy: Use dry run mode first
```

**Scenario 2: Documentation Site**
```
Recommendation: max_pages = 100-300
Reason: Documentation is usually well-structured
Strategy: Use URL patterns to focus on docs sections
```

**Scenario 3: Blog/News Site**
```
Recommendation: max_pages = 200-500
Reason: Many articles, but you want comprehensive coverage
Strategy: Use date-based patterns if needed
```

**Scenario 4: E-commerce Site**
```
Recommendation: max_pages = 500-1000
Reason: Many product pages, categories
Strategy: Focus on specific product categories
```

### Warning Signs & Troubleshooting

#### Signs Max Pages is Too Low
- Discovery completes very quickly (< 30 seconds)
- Important pages missing from discovered URLs
- Discovery stops in middle of relevant sections
- User complains about incomplete coverage

#### Signs Max Pages is Too High  
- Discovery takes very long (> 15 minutes)
- System memory usage grows excessively
- Many irrelevant URLs discovered
- User overwhelmed by too many URL choices

#### Troubleshooting Tips
```bash
# Check current settings
Menu Option 4 → View current max_pages value

# Use dry run to test
python3 main.py --dry-run
# See how many URLs discovered before adjusting

# Start conservative, increase gradually
Start: 50 → Test → 100 → Test → 200 → etc.

# Use URL patterns to focus discovery
Use specific patterns instead of increasing max_pages
```

## 🛠️ Project Structure

```
crawl4ai-scraper/
├── main.py                 # Interactive CLI with 8-option menu
├── crawler.py              # Core crawling with user-agent rotation
├── content_filters.py      # Generic content cleaning
├── selector_utils.py       # CSS/XPath extraction utilities
├── output_manager.py       # Advanced output organization
├── config_manager.py       # Configuration persistence
├── dependency_checker.py   # Automatic dependency management
├── requirements.txt        # Python dependencies
├── CLAUDE.md              # Project instructions
└── README.md              # This file
```

## 📦 Dependencies

```
crawl4ai>=0.4.0      # Core web crawling engine
rich>=13.0.0         # Terminal UI components  
click>=8.1.0         # Command-line interface
aiofiles>=23.0.0     # Async file operations
beautifulsoup4       # HTML parsing for CSS selectors
lxml                 # XPath expression support
httpx               # HTTP client for selector testing
```

## 🚨 Troubleshooting

### Common Issues

**1. Import/Dependency Errors**
```bash
# Check and install dependencies
python3 main.py --check-deps
python3 main.py --install-deps
```

**2. Content Extraction Issues**
- Use **Menu Option 7** to test selectors first
- Try different templates (Blog, News, Documentation)
- Switch extraction method (CSS → XPath → Auto)
- Adjust cleaning profile (Strict → Moderate → Minimal)

**3. Access/Blocking Issues**
- Enable user-agent rotation (enabled by default)
- Increase request delays (1-2 seconds recommended)
- Reduce concurrent requests (try 1-2)
- Use dry run mode first to test

**4. Memory Issues with Large Crawls**
- Reduce `max_pages` setting
- Use more specific URL patterns
- Enable cache mode for re-crawling

**5. Dry Run Shows No URLs**
- Check URL patterns are correct
- Verify base URL is accessible
- Try broader patterns (*/docs/* instead of */docs/api/*)

## 💡 Performance Tips

### For Large Sites
- Use specific URL patterns to limit scope
- Set reasonable max_pages limits (100-500)
- Enable cache mode for re-crawling
- Use dry run first to verify scope

### For Quality Extraction
- Test selectors on sample URLs first (Menu Option 7)
- Use appropriate templates for site type
- Adjust cleaning profiles as needed
- Preview with dry run mode

### For Respectful Crawling
- Use 1-2 second delays between requests
- Limit concurrent requests to 1-3
- Check robots.txt compliance
- Enable user-agent rotation

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing patterns
- All dependencies added to requirements.txt
- Test new features with various website types
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Please respect website terms of service and robots.txt files when crawling.

---

**Built with ❤️ using [Crawl4AI](https://github.com/unclecode/crawl4ai)**

*Enhanced with advanced content extraction, user-agent rotation, dry-run capabilities, and comprehensive testing tools.*