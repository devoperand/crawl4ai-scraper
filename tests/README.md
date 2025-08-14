# Test Files

This directory contains test scripts for the crawl4ai-scraper project.

## Test Files Description

| Test File | Description | Purpose |
|-----------|-------------|---------|
| `test_bricks.py` | Tests generic content cleaning on Bricks Builder Academy | Validates generic content extraction works on different site types |
| `test_crawl.py` | Tests GitHub documentation crawling | Validates core crawling functionality on GitHub docs |
| `test_dryrun.py` | Tests dry run functionality | Validates URL discovery without content extraction |
| `test_generic.py` | Tests generic content cleaning | Validates content cleaning works across different sites |
| `test_output_manager.py` | Tests output management system | Validates file organization and output strategies |
| `test_selectors.py` | Tests CSS/XPath selector functionality | Validates CSS and XPath content extraction |
| `test_user_agent.py` | Tests user-agent rotation | Validates anti-detection user-agent switching |

## Running Tests

### Individual Tests
```bash
# Test specific functionality
python3 tests/test_selectors.py
python3 tests/test_user_agent.py
python3 tests/test_dryrun.py
```

### All Tests
```bash
# Run all tests in sequence
for test in tests/test_*.py; do
    echo "Running $test..."
    python3 "$test"
done
```

## Test Requirements

- Virtual environment activated
- All dependencies installed (`python3 main.py --install-deps`)
- Internet connection (tests use live URLs)

## Test Guidelines

- Each test should be self-contained
- Use test URLs that are stable and publicly accessible
- Include both positive and edge case testing
- Clean up any test output files after completion