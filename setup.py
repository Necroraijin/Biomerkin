"""
Setup configuration for Biomerkin multi-agent bioinformatics system.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="biomerkin",
    version="0.1.0",
    author="Biomerkin Team",
    author_email="team@biomerkin.com",
    description="Multi-agent bioinformatics assistant for genomic analysis and treatment recommendations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/biomerkin/biomerkin-multi-agent-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "aws": [
            "moto>=4.2.0",  # For AWS mocking in tests
        ],
        "cache": [
            "redis>=4.6.0",
        ],
        "monitoring": [
            "psutil>=5.9.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "biomerkin=biomerkin.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "biomerkin": [
            "data/*.json",
            "templates/*.txt",
        ],
    },
    zip_safe=False,
)