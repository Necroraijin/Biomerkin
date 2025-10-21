#!/usr/bin/env python3
"""Simple file-by-file checker for Biomerkin project."""

import ast
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
issues_found = []
files_checked = 0

# Check only project files, not dependencies
project_dirs = ['biomerkin', 'lambda_functions', 'scripts', 'demo']

for dir_name in project_dirs:
    dir_path = project_root / dir_name
    if not dir_path.exists():
        continue
    
    for py_file in dir_path.glob('**/*.py'):
        files_checked += 1
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            issues_found.append(f"{py_file.name}: Syntax error at line {e.lineno}")
        except Exception as e:
            issues_found.append(f"{py_file.name}: {str(e)[:50]}")

print(f"Files checked: {files_checked}")
print(f"Issues found: {len(issues_found)}")

if issues_found:
    print("\nISSUES:")
    for issue in issues_found:
        print(f"  - {issue}")
else:
    print("\nALL FILES OK - NO SYNTAX ERRORS!")

sys.exit(0 if len(issues_found) == 0 else 1)
