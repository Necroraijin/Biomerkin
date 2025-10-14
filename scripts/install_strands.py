#!/usr/bin/env python3
"""
Installation script for AWS Strands Agents.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_strands_agents():
    """Install AWS Strands Agents SDK."""
    print("🚀 Installing AWS Strands Agents SDK...")
    
    try:
        # Install strands-agents
        subprocess.run([
            sys.executable, "-m", "pip", "install", "strands-agents"
        ], check=True)
        
        print("✅ Strands Agents SDK installed successfully!")
        
        # Verify installation
        try:
            import strands_agents
            print(f"✅ Verification successful: {strands_agents.__version__}")
            return True
        except ImportError:
            print("❌ Installation verification failed")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False


def main():
    """Main installation function."""
    print("🧬 Biomerkin - Strands Agents Installation")
    print("=" * 50)
    
    if install_strands_agents():
        print("\n🎉 Installation complete!")
        print("💡 You can now use enhanced features:")
        print("   • biomerkin analyze sequence.fasta --enhanced")
        print("   • biomerkin demo --type comprehensive")
        print("   • biomerkin status")
    else:
        print("\n❌ Installation failed!")
        print("💡 You can still use standard features without Strands Agents")
        sys.exit(1)


if __name__ == "__main__":
    main()

