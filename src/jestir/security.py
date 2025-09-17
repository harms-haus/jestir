#!/usr/bin/env python3
"""
Security auditing module for Jestir.

Provides dependency vulnerability scanning and code security analysis
using safety and bandit tools.
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, f"Command not found: {' '.join(cmd)}"


def audit_dependencies() -> None:
    """Audit dependencies for known security vulnerabilities using pip-audit."""
    print("🔍 Auditing dependencies for security vulnerabilities...")
    print("=" * 60)

    # Check if pip-audit is available
    success, output = run_command(
        ["pip-audit", "--version"], "Checking pip-audit version"
    )
    if not success:
        print("❌ pip-audit not found. Please install with: uv sync")
        sys.exit(1)

    # Run pip-audit check
    success, output = run_command(
        ["pip-audit", "--format=json"], "Running pip-audit vulnerability scan"
    )

    if success:
        try:
            # Parse JSON output
            result = json.loads(output)
            vulnerabilities = result.get("vulnerabilities", [])

            if not vulnerabilities:
                print("✅ No known security vulnerabilities found in dependencies")
            else:
                print(f"⚠️  Found {len(vulnerabilities)} security vulnerabilities:")
                for vuln in vulnerabilities:
                    package = vuln.get("package", "Unknown")
                    version = vuln.get("installed_version", "Unknown")
                    vuln_id = vuln.get("vulnerability", "Unknown")
                    severity = vuln.get("severity", "Unknown")
                    description = vuln.get("description", "No description")

                    print(f"  • {package} {version}")
                    print(f"    Vulnerability: {vuln_id}")
                    print(f"    Severity: {severity}")
                    print(f"    Description: {description}")
                    print()
        except json.JSONDecodeError:
            # Fallback to text output
            if "No known vulnerabilities found" in output:
                print("✅ No known security vulnerabilities found in dependencies")
            else:
                print("⚠️  Security vulnerabilities found:")
                print(output)
    else:
        print("❌ pip-audit scan failed:")
        print(output)
        sys.exit(1)


def audit_code() -> None:
    """Audit code for security issues using bandit."""
    print("🔍 Auditing code for security issues...")
    print("=" * 60)

    # Check if bandit is available
    success, output = run_command(["bandit", "--version"], "Checking bandit version")
    if not success:
        print("❌ Bandit not found. Please install with: uv sync")
        sys.exit(1)

    # Run bandit scan on source code
    src_path = Path(__file__).parent
    success, output = run_command(
        ["bandit", "-r", str(src_path), "-f", "json", "-ll"],
        "Running bandit security scan",
    )

    if success:
        try:
            # Parse JSON output
            results = json.loads(output)
            issues = results.get("results", [])

            if not issues:
                print("✅ No security issues found in code")
            else:
                print(f"⚠️  Found {len(issues)} security issues in code:")
                for issue in issues:
                    severity = issue.get("issue_severity", "Unknown")
                    confidence = issue.get("issue_confidence", "Unknown")
                    test_name = issue.get("test_name", "Unknown")
                    filename = issue.get("filename", "Unknown")
                    line_num = issue.get("line_number", "Unknown")

                    print(f"  • {severity.upper()} severity in {filename}:{line_num}")
                    print(f"    Test: {test_name}")
                    print(f"    Confidence: {confidence}")
                    print(
                        f"    Description: {issue.get('issue_text', 'No description')}"
                    )
                    print()
        except json.JSONDecodeError:
            # Fallback to text output
            if "No issues identified" in output or "No issues found" in output:
                print("✅ No security issues found in code")
            else:
                print("⚠️  Security issues found in code:")
                print(output)
    else:
        # Check if it's just a warning about no issues
        if "No issues identified" in output or "No issues found" in output:
            print("✅ No security issues found in code")
        else:
            print("❌ Bandit scan failed:")
            print(output)
            sys.exit(1)


def audit_all() -> None:
    """Run all security audits."""
    print("🛡️  Running comprehensive security audit...")
    print("=" * 60)

    # Audit dependencies
    audit_dependencies()
    print()

    # Audit code
    audit_code()
    print()

    print("✅ Security audit complete!")


def generate_security_report() -> None:
    """Generate a detailed security report."""
    print("📊 Generating security report...")
    print("=" * 60)

    report = {
        "timestamp": subprocess.run(
            ["date"], capture_output=True, text=True
        ).stdout.strip(),
        "dependencies": {},
        "code": {},
    }

    # Dependency audit
    success, output = run_command(["safety", "check", "--json"], "Dependency audit")
    if success:
        try:
            report["dependencies"] = json.loads(output)
        except json.JSONDecodeError:
            report["dependencies"] = {"error": "Failed to parse safety output"}
    else:
        report["dependencies"] = {"error": output}

    # Code audit
    src_path = Path(__file__).parent
    success, output = run_command(
        ["bandit", "-r", str(src_path), "-f", "json"], "Code audit"
    )
    if success:
        try:
            report["code"] = json.loads(output)
        except json.JSONDecodeError:
            report["code"] = {"error": "Failed to parse bandit output"}
    else:
        report["code"] = {"error": output}

    # Save report
    report_path = Path("security-report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 Security report saved to: {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python -m jestir.security <audit-deps|audit-code|audit-all|report>"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "audit-deps":
        audit_dependencies()
    elif command == "audit-code":
        audit_code()
    elif command == "audit-all":
        audit_all()
    elif command == "report":
        generate_security_report()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: audit-deps, audit-code, audit-all, report")
        sys.exit(1)
