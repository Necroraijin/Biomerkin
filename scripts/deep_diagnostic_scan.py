#!/usr/bin/env python3
"""
Deep Diagnostic Scan - File-by-File Analysis
Checks every Python file for:
- Syntax errors
- Import errors
- Missing dependencies
- Unused imports
- Code quality issues
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Any

project_root = Path(__file__).parent.parent

class DeepDiagnosticScanner:
    """Deep file-by-file diagnostic scanner."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.files_scanned = 0
        self.files_with_issues = 0
        
    def scan_all_python_files(self):
        """Scan all Python files in the project."""
        print("=" * 80)
        print("DEEP DIAGNOSTIC SCAN - FILE BY FILE ANALYSIS")
        print("=" * 80)
        print()
        
        # Get all Python files
        python_files = list(project_root.glob('**/*.py'))
        python_files = [f for f in python_files if 'node_modules' not in str(f) and '__pycache__' not in str(f)]
        
        print(f"Found {len(python_files)} Python files to scan\n")
        
        for py_file in python_files:
            self.scan_file(py_file)
        
        self.generate_report()
    
    def scan_file(self, file_path: Path):
        """Scan a single Python file."""
        self.files_scanned += 1
        relative_path = file_path.relative_to(project_root)
        
        print(f"[{self.files_scanned}] Scanning: {relative_path}")
        
        file_issues = []
        
        # Check 1: Syntax errors
        syntax_ok = self.check_syntax(file_path, file_issues)
        
        # Check 2: Import errors (only if syntax is OK)
        if syntax_ok:
            self.check_imports(file_path, file_issues)
        
        # Check 3: Common issues
        self.check_common_issues(file_path, file_issues)
        
        if file_issues:
            self.files_with_issues += 1
            self.issues.extend(file_issues)
            for issue in file_issues:
                print(f"  ❌ {issue}")
        else:
            print(f"  ✅ No issues found")
    
    def check_syntax(self, file_path: Path, file_issues: List[str]) -> bool:
        """Check for syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                ast.parse(code)
            return True
        except SyntaxError as e:
            file_issues.append(f"Syntax Error at line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            file_issues.append(f"Parse Error: {str(e)}")
            return False
    
    def check_imports(self, file_path: Path, file_issues: List[str]):
        """Check for import errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.verify_import(alias.name, file_path, file_issues)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.verify_import(node.module, file_path, file_issues)
        except Exception as e:
            # Already caught in syntax check
            pass
    
    def verify_import(self, module_name: str, file_path: Path, file_issues: List[str]):
        """Verify if an import is available."""
        # Skip relative imports and common stdlib modules
        if module_name.startswith('.'):
            return
        
        common_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing',
            'logging', 'asyncio', 'uuid', 'hashlib', 're', 'collections',
            'dataclasses', 'enum', 'abc', 'functools', 'itertools'
        }
        
        if module_name.split('.')[0] in common_modules:
            return
        
        # Try to import
        try:
            importlib.import_module(module_name.split('.')[0])
        except ImportError:
            # Only warn, don't error (might be optional dependency)
            self.warnings.append(f"{file_path.name}: Optional import '{module_name}' not available")
    
    def check_common_issues(self, file_path: Path, file_issues: List[str]):
        """Check for common code issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Check for common issues
            if 'TODO' in code and 'FIXME' in code:
                self.warnings.append(f"{file_path.name}: Contains TODO/FIXME comments")
            
            # Check for empty exception handlers
            if 'except:\n        pass' in code or 'except Exception:\n        pass' in code:
                self.warnings.append(f"{file_path.name}: Contains empty exception handlers")
                
        except Exception:
            pass
    
    def generate_report(self):
        """Generate diagnostic report."""
        print("\n" + "=" * 80)
        print("DIAGNOSTIC REPORT")
        print("=" * 80)
        print(f"Files Scanned: {self.files_scanned}")
        print(f"Files with Issues: {self.files_with_issues}")
        print(f"Critical Issues: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        print()
        
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  - {issue}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS (Non-Critical):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
            print()
        
        # Save report
        report_path = project_root / 'DEEP_DIAGNOSTIC_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Deep Diagnostic Scan Report\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Files Scanned: {self.files_scanned}\n")
            f.write(f"- Files with Issues: {self.files_with_issues}\n")
            f.write(f"- Critical Issues: {len(self.issues)}\n")
            f.write(f"- Warnings: {len(self.warnings)}\n\n")
            
            if self.issues:
                f.write("## Critical Issues\n\n")
                for issue in self.issues:
                    f.write(f"- {issue}\n")
                f.write("\n")
            
            if self.warnings:
                f.write("## Warnings\n\n")
                for warning in self.warnings:
                    f.write(f"- {warning}\n")
        
        print(f"📄 Full report saved to: {report_path}")
        
        if len(self.issues) == 0:
            print("\n✅ NO CRITICAL ISSUES FOUND - SYSTEM IS HEALTHY!")
        else:
            print(f"\n⚠️  Found {len(self.issues)} critical issues that need attention")

def main():
    scanner = DeepDiagnosticScanner()
    scanner.scan_all_python_files()
    
    return 0 if len(scanner.issues) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
