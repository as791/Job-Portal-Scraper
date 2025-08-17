#!/usr/bin/env python3
"""
Test runner script for the job scraper project.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type: str, verbose: bool = False):
    """Run tests based on the specified type."""
    base_cmd = ["python", "-m", "pytest", "--import-mode=importlib"]
    
    if verbose:
        base_cmd.append("-v")
    
    if test_type == "unit":
        # Run only unit tests (fast)
        cmd = base_cmd + ["-m", "not slow", "--tb=short"]
        print("🧪 Running unit tests...")
        
    elif test_type == "integration":
        # Run only integration tests (slow)
        cmd = base_cmd + ["-m", "slow", "--tb=short"]
        print("🔗 Running integration tests...")
        
    elif test_type == "fast":
        # Run fast tests (unit tests only)
        cmd = base_cmd + ["-m", "not slow", "--tb=short", "-x"]
        print("Running fast tests...")
        
    elif test_type == "all":
        # Run all tests
        cmd = base_cmd + ["--tb=short"]
        print("Running all tests...")
        
    elif test_type == "scrapers":
        # Run scraper-specific tests
        cmd = base_cmd + ["-k", "scraper", "--tb=short"]
        print("Running scraper tests...")
        
    elif test_type == "database":
        # Run database-specific tests
        cmd = base_cmd + ["-k", "database", "--tb=short"]
        print("Running database tests...")
        
    else:
        print(f"Unknown test type: {test_type}")
        print("Available types: unit, integration, fast, all, scrapers, database")
        return False
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"Tests completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for job scraper project")
    parser.add_argument(
        "type",
        choices=["unit", "integration", "fast", "all", "scrapers", "database"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("Error: 'tests' directory not found. Please run from project root.")
        sys.exit(1)
    
    success = run_tests(args.type, args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
