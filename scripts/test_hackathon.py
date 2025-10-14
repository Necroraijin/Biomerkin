#!/usr/bin/env python3
"""
Test script for Biomerkin hackathon submission.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def test_cli():
    """Test CLI functionality."""
    print("🧪 Testing CLI...")
    
    try:
        # Test help command
        result = subprocess.run(['python', '-m', 'biomerkin.cli', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ CLI help works")
        else:
            print("❌ CLI help failed")
            return False
        
        # Test status command
        result = subprocess.run(['python', '-m', 'biomerkin.cli', 'status'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ CLI status works")
        else:
            print(f"❌ CLI status failed: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


def test_imports():
    """Test all imports work."""
    print("📦 Testing imports...")
    
    try:
        import biomerkin
        import biomerkin.agents
        import biomerkin.models
        import biomerkin.services
        import biomerkin.utils
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_sample_data():
    """Test sample data exists."""
    print("🧬 Testing sample data...")
    
    sample_files = [
        "sample_data/BRCA1.fasta",
        "sample_data/COVID19.fasta", 
        "sample_data/TP53.fasta"
    ]
    
    found_files = 0
    for file_path in sample_files:
        if Path(file_path).exists():
            print(f"✅ Found {file_path}")
            found_files += 1
        else:
            print(f"❌ Missing {file_path}")
    
    if found_files > 0:
        print(f"✅ Found {found_files}/{len(sample_files)} sample files")
        return True
    else:
        print("❌ No sample data found")
        return False


def main():
    """Run all tests."""
    print("🚀 Biomerkin Hackathon Test Suite")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("CLI Test", test_cli),
        ("Sample Data Test", test_sample_data)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        if test_func():
            passed += 1
    
    print(f"\n🎯 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Ready for hackathon submission.")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before submission.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
