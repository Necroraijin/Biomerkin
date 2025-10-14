#!/usr/bin/env python3
"""
Download sample genomic data for Biomerkin demo.
"""

import os
import urllib.request
from pathlib import Path


def download_file(url, filename):
    """Download file from URL."""
    print(f"📥 Downloading {filename}...")
    
    try:
        urllib.request.urlretrieve(url, filename)
        
        print(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False


def main():
    """Download sample datasets."""
    print("🧬 Downloading Biomerkin Sample Datasets")
    print("=" * 40)
    
    # Create sample_data directory
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample datasets
    datasets = [
        {
            "name": "BRCA1.fasta",
            "url": "https://www.ncbi.nlm.nih.gov/sviewer/viewer.fcgi?db=nuccore&id=NM_007294.3&rettype=fasta&retmode=text",
            "description": "BRCA1 gene - Breast cancer susceptibility"
        },
        {
            "name": "COVID19.fasta", 
            "url": "https://www.ncbi.nlm.nih.gov/sviewer/viewer.fcgi?db=nuccore&id=NC_045512.2&rettype=fasta&retmode=text",
            "description": "SARS-CoV-2 reference genome"
        },
        {
            "name": "TP53.fasta",
            "url": "https://www.ncbi.nlm.nih.gov/sviewer/viewer.fcgi?db=nuccore&id=NM_000546.5&rettype=fasta&retmode=text", 
            "description": "TP53 gene - Tumor suppressor"
        }
    ]
    
    success_count = 0
    for dataset in datasets:
        filepath = sample_dir / dataset["name"]
        print(f"\n📋 {dataset['description']}")
        
        if download_file(dataset["url"], filepath):
            success_count += 1
    
    print(f"\n🎉 Downloaded {success_count}/{len(datasets)} datasets successfully!")
    print(f"📁 Files saved to: {sample_dir.absolute()}")
    
    if success_count > 0:
        print("\n🚀 Ready to test Biomerkin:")
        print("biomerkin analyze sample_data/BRCA1.fasta")


if __name__ == "__main__":
    main()
