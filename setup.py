#!/usr/bin/env python3
"""
BAC Hunter - Broken Access Control Security Testing Tool
Setup configuration for package installation
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = []
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
        return requirements

setup(
    name="bac-hunter",
    version="3.0.0",
    author="BAC Hunter Team",
    author_email="security@bachunter.com",
    description="Professional-grade Broken Access Control security testing platform",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/bachunter/bac-hunter",
    project_urls={
        "Bug Reports": "https://github.com/bachunter/bac-hunter/issues",
        "Source": "https://github.com/bachunter/bac-hunter",
        "Documentation": "https://bachunter.readthedocs.io/",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Security Researchers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.8.0",
        ],
        "ai": [
            "scikit-learn>=1.5.0",
            "tensorflow-cpu>=2.20.0",
            "torch>=2.2.0",
            "transformers>=4.37.0",
            "spacy>=3.7.0",
            "nltk>=3.9.0",
        ],
        "full": [
            "selenium>=4.23.0",
            "playwright>=1.47.0",
            "weasyprint>=62.0",
            "reportlab>=4.0.0",
            "matplotlib>=3.8.0",
            "seaborn>=0.13.0",
            "plotly>=5.17.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bac-hunter=bac_hunter.cli:app",
        ],
    },
    include_package_data=True,
    package_data={
        "bac_hunter": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="security, testing, access control, idor, vulnerability, web security, penetration testing",
    license="MIT",
    zip_safe=False,
)
