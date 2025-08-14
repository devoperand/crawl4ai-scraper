#!/usr/bin/env python3
"""
Dependency checker for crawl4ai-interactive project.
Verifies that all required packages are installed and matches imports with requirements.txt
"""

import ast
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import Set, List, Dict, Tuple
import re


class DependencyChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.python_files = ["main.py", "crawler.py"]
        self.stdlib_modules = self._get_stdlib_modules()
        self.import_mapping = {
            # Map import names to package names
            'crawl4ai': 'crawl4ai',
            'rich': 'rich',
            'click': 'click',
            'aiofiles': 'aiofiles',
            # Standard library modules (no installation needed)
            'asyncio': None,
            'pathlib': None,
            'typing': None,
            're': None,
            'glob': None,
            'fnmatch': None,
            'urllib': None,
            'os': None,
            'sys': None,
            'json': None,
            'time': None,
            'datetime': None,
            'collections': None,
            'itertools': None,
            'functools': None,
            'signal': None,
        }

    def _get_stdlib_modules(self) -> Set[str]:
        """Get a set of standard library module names."""
        import sys
        stdlib = set(sys.builtin_module_names)
        # Add commonly used stdlib modules
        stdlib.update({
            'asyncio', 'pathlib', 'typing', 're', 'glob', 'fnmatch',
            'urllib', 'os', 'sys', 'json', 'time', 'datetime',
            'collections', 'itertools', 'functools', 'ast', 'subprocess',
            'importlib', 'logging', 'traceback', 'inspect', 'warnings',
            'copy', 'shutil', 'tempfile', 'io', 'string', 'random',
            'math', 'statistics', 'decimal', 'fractions', 'numbers', 'signal'
        })
        return stdlib

    def extract_imports(self, filepath: Path) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()
        
        if not filepath.exists():
            return imports
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        imports.add(module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        imports.add(module)
        except Exception as e:
            print(f"Warning: Could not parse {filepath}: {e}")
        
        return imports

    def get_all_imports(self) -> Set[str]:
        """Get all imports from project Python files."""
        all_imports = set()
        
        for py_file in self.python_files:
            filepath = self.project_root / py_file
            if filepath.exists():
                file_imports = self.extract_imports(filepath)
                all_imports.update(file_imports)
                print(f"Found imports in {py_file}: {file_imports}")
        
        return all_imports

    def filter_third_party_imports(self, imports: Set[str]) -> Set[str]:
        """Filter out standard library imports, keeping only third-party packages."""
        third_party = set()
        
        # Local modules to exclude
        local_modules = {'dependency_checker', 'crawler'}
        
        for imp in imports:
            # Skip if it's a local module
            if imp in local_modules:
                continue
            
            # Skip if it's in standard library
            if imp in self.stdlib_modules:
                continue
            
            # Get the package name from mapping
            if imp in self.import_mapping:
                package = self.import_mapping[imp]
                if package:  # None means stdlib
                    third_party.add(package)
            else:
                # Assume it's third-party if not in mapping or stdlib
                third_party.add(imp)
        
        return third_party

    def read_requirements(self) -> Set[str]:
        """Read package names from requirements.txt."""
        requirements = set()
        
        if not self.requirements_file.exists():
            return requirements
        
        with open(self.requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before any version specifier)
                    package = re.split(r'[<>=!]', line)[0].strip()
                    requirements.add(package.lower())
        
        return requirements

    def check_installed(self, package: str) -> Tuple[bool, str]:
        """Check if a package is installed and return version."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Extract version from output
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        version = line.split(':', 1)[1].strip()
                        return True, version
            return False, ""
        except Exception:
            return False, ""

    def install_package(self, package: str, silent: bool = False) -> bool:
        """Install a package using pip."""
        try:
            if not silent:
                print(f"Installing {package}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            if not silent:
                print(f"Error installing {package}: {e}")
            return False
    
    def install_from_requirements(self, silent: bool = False) -> bool:
        """Install all packages from requirements.txt automatically."""
        if not self.requirements_file.exists():
            if not silent:
                print(f"❌ requirements.txt not found at {self.requirements_file}")
            return False
        
        if not silent:
            print("Installing packages from requirements.txt...")
        
        # Try bulk install first
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(self.requirements_file), '--quiet'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                if not silent:
                    print("✅ All packages installed successfully from requirements.txt")
                return True
            
            # If bulk install failed, try individual packages
            if not silent:
                print("Bulk install failed, trying individual packages...")
            
            requirements = self.read_requirements()
            failed_packages = []
            
            for package in requirements:
                installed, _ = self.check_installed(package)
                if not installed:
                    if not self.install_package(package, silent):
                        failed_packages.append(package)
            
            if failed_packages:
                if not silent:
                    print(f"❌ Failed to install: {failed_packages}")
                return False
            
            if not silent:
                print("✅ All packages installed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            if not silent:
                print("❌ Installation timed out")
            return False
        except Exception as e:
            if not silent:
                print(f"❌ Installation error: {e}")
            return False
    
    def get_missing_packages(self) -> List[str]:
        """Get list of missing packages from requirements.txt."""
        if not self.requirements_file.exists():
            return []
        
        requirements = self.read_requirements()
        missing = []
        
        for package in requirements:
            installed, _ = self.check_installed(package)
            if not installed:
                missing.append(package)
        
        return missing

    def generate_requirements(self, imports: Set[str]) -> List[str]:
        """Generate requirements.txt content from imports."""
        requirements = []
        
        for package in sorted(imports):
            installed, version = self.check_installed(package)
            if installed and version:
                # Use >= for flexibility
                requirements.append(f"{package}>={version}")
            else:
                # Use latest version indicator
                requirements.append(package)
        
        return requirements

    def run_check(self) -> bool:
        """Run the complete dependency check."""
        print("=" * 60)
        print("Dependency Checker for crawl4ai-interactive")
        print("=" * 60)
        
        # Step 1: Get all imports from Python files
        print("\n1. Scanning Python files for imports...")
        all_imports = self.get_all_imports()
        
        # Step 2: Filter to third-party packages only
        third_party = self.filter_third_party_imports(all_imports)
        print(f"\nThird-party packages found in code: {third_party}")
        
        # Step 3: Read requirements.txt
        print("\n2. Reading requirements.txt...")
        requirements = self.read_requirements()
        
        if not self.requirements_file.exists():
            print("   requirements.txt not found!")
        else:
            print(f"   Packages in requirements.txt: {requirements}")
        
        # Step 4: Check for missing packages in requirements.txt
        print("\n3. Checking requirements.txt completeness...")
        missing_in_requirements = third_party - requirements
        
        if missing_in_requirements:
            print(f"   ⚠️  Missing in requirements.txt: {missing_in_requirements}")
            print("\n   Suggested requirements.txt content:")
            print("   " + "-" * 40)
            for req in self.generate_requirements(third_party):
                print(f"   {req}")
            print("   " + "-" * 40)
        else:
            print("   ✅ All imports are covered in requirements.txt")
        
        # Step 5: Check installed packages
        print("\n4. Checking installed packages...")
        missing_packages = []
        installed_packages = []
        
        for package in third_party:
            installed, version = self.check_installed(package)
            if installed:
                installed_packages.append(f"{package} ({version})")
            else:
                missing_packages.append(package)
        
        if installed_packages:
            print("   ✅ Installed packages:")
            for pkg in installed_packages:
                print(f"      - {pkg}")
        
        if missing_packages:
            print(f"\n   ❌ Missing packages: {missing_packages}")
            
            # Check if we should auto-install
            auto_install = '--auto-install' in sys.argv or '--auto' in sys.argv
            
            if auto_install:
                print("\n   Auto-installing missing packages...")
                success = self.install_from_requirements(silent=False)
                if not success:
                    return False
            else:
                # Offer to install
                try:
                    response = input("\n   Would you like to install missing packages? (y/n): ")
                    if response.lower() == 'y':
                        for package in missing_packages:
                            if self.install_package(package):
                                print(f"   ✅ Successfully installed {package}")
                            else:
                                print(f"   ❌ Failed to install {package}")
                                return False
                except (EOFError, KeyboardInterrupt):
                    print("\n   Installation cancelled.")
                    return False
        
        # Step 6: Final status
        print("\n" + "=" * 60)
        if not missing_packages and not missing_in_requirements:
            print("✅ All dependencies are satisfied!")
            print("=" * 60)
            return True
        elif not missing_packages:
            print("⚠️  Dependencies installed but requirements.txt needs updating")
            print("=" * 60)
            return True
        else:
            print("❌ Some dependencies are missing")
            print("=" * 60)
            return False


def ensure_dependencies(auto_install: bool = True, silent: bool = False) -> bool:
    """Ensure all dependencies are installed (used by main.py)."""
    checker = DependencyChecker()
    
    # Get missing packages from requirements.txt
    missing = checker.get_missing_packages()
    
    if not missing:
        if not silent:
            print("✅ All dependencies are already installed")
        return True
    
    if not silent:
        print(f"Found {len(missing)} missing packages: {missing}")
    
    if auto_install:
        return checker.install_from_requirements(silent=silent)
    
    return False


def main():
    """Main entry point for dependency checker."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dependency checker for crawl4ai-interactive')
    parser.add_argument('--auto-install', '--auto', action='store_true',
                       help='Automatically install missing packages')
    parser.add_argument('--install-only', action='store_true',
                       help='Only install packages from requirements.txt and exit')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check dependencies without installing')
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    if args.install_only:
        # Just install from requirements.txt
        success = checker.install_from_requirements(silent=False)
        sys.exit(0 if success else 1)
    
    if args.check_only:
        # Only check, don't install
        missing = checker.get_missing_packages()
        if missing:
            print(f"Missing packages: {missing}")
            print("Run with --auto-install to install them automatically")
            sys.exit(1)
        else:
            print("✅ All dependencies are satisfied")
            sys.exit(0)
    
    # Run the full check (with auto-install if specified)
    success = checker.run_check()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

