#!/usr/bin/env python3
"""
Jestir API Validation Script

Simple validation script to verify the Node.js API structure and functionality.
This script checks that all required files exist and have the correct structure.
"""

import os
import json
import re
from pathlib import Path

def validate_file_exists(filepath, description):
    """Validate that a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def validate_json_structure(filepath, required_fields):
    """Validate JSON file structure."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        for field in required_fields:
            if field not in data:
                print(f"❌ {filepath}: Missing required field '{field}'")
                return False

        print(f"✅ {filepath}: JSON structure valid")
        return True
    except Exception as e:
        print(f"❌ {filepath}: JSON validation failed - {e}")
        return False

def validate_js_file(filepath, required_exports):
    """Validate JavaScript file has required exports."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        for export_name in required_exports:
            # Check for both named exports and class definitions
            if (f"export {export_name}" not in content and
                f"export default {export_name}" not in content and
                f"class {export_name}" not in content):
                print(f"❌ {filepath}: Missing export '{export_name}'")
                return False

        print(f"✅ {filepath}: JavaScript exports valid")
        return True
    except Exception as e:
        print(f"❌ {filepath}: JavaScript validation failed - {e}")
        return False

def validate_api_methods(filepath, required_methods):
    """Validate that API class has required methods."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        for method in required_methods:
            # Check for both async and regular method definitions
            if (f"async {method}(" not in content and
                f"{method}(" not in content):
                print(f"❌ {filepath}: Missing method '{method}'")
                return False

        print(f"✅ {filepath}: API methods valid")
        return True
    except Exception as e:
        print(f"❌ {filepath}: Method validation failed - {e}")
        return False

def main():
    """Main validation function."""
    print("Jestir API Validation")
    print("====================")
    print()

    # Change to API directory
    api_dir = Path(__file__).parent
    os.chdir(api_dir)

    validation_results = []

    # Validate package.json
    print("1. Package Configuration")
    print("-" * 25)
    validation_results.append(validate_file_exists("package.json", "Package configuration"))
    if os.path.exists("package.json"):
        validation_results.append(validate_json_structure("package.json", [
            "name", "version", "description", "main", "type", "scripts", "dependencies"
        ]))
    print()

    # Validate main API file
    print("2. Main API File")
    print("-" * 20)
    validation_results.append(validate_file_exists("index.js", "Main API file"))
    if os.path.exists("index.js"):
        validation_results.append(validate_js_file("index.js", [
            "JestirAPI", "SessionManager", "ProgressTracker", "APIError"
        ]))

        # Validate API methods
        required_methods = [
            "generateContext", "generateNewContext", "generateOutline",
            "generateStory", "generateCompleteStory", "validateContext",
            "validateTemplates", "searchEntities", "listEntities",
            "getTokenStats", "getSessionInfo", "getAllSessions", "cleanupSessions"
        ]
        validation_results.append(validate_api_methods("index.js", required_methods))
    print()

    # Validate test files
    print("3. Test Files")
    print("-" * 15)
    validation_results.append(validate_file_exists("test/jestir-api.test.js", "Unit tests"))
    validation_results.append(validate_file_exists("test-runner.js", "Test runner"))
    print()

    # Validate example files
    print("4. Example Files")
    print("-" * 18)
    validation_results.append(validate_file_exists("examples/basic-usage.js", "Basic usage example"))
    validation_results.append(validate_file_exists("examples/web-server.js", "Web server example"))
    print()

    # Validate documentation
    print("5. Documentation")
    print("-" * 18)
    validation_results.append(validate_file_exists("README.md", "API documentation"))
    print()

    # Check file sizes
    print("6. File Sizes")
    print("-" * 15)
    files_to_check = [
        "index.js",
        "test/jestir-api.test.js",
        "examples/basic-usage.js",
        "examples/web-server.js",
        "README.md"
    ]

    for filepath in files_to_check:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 0:
                print(f"✅ {filepath}: {size:,} bytes")
            else:
                print(f"❌ {filepath}: Empty file")
                validation_results.append(False)
        else:
            print(f"❌ {filepath}: File not found")
            validation_results.append(False)
    print()

    # Summary
    print("Validation Summary")
    print("==================")
    total_checks = len(validation_results)
    passed_checks = sum(validation_results)
    failed_checks = total_checks - passed_checks

    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")

    if failed_checks == 0:
        print("\n✅ All validations passed! The Jestir API is ready for use.")
        return 0
    else:
        print(f"\n❌ {failed_checks} validation(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())
