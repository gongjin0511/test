"""
Setup script for OKX AI Trading System - Python Edition
"""

from setuptools import setup, find_packages

with open("README_PYTHON.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="okx-ai-trading",
    version="1.0.0",
    author="OKX Trading Team",
    description="Autonomous AI-powered trading system for OKX exchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/okx-ai-trading",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.27.0",
        "ccxt>=4.2.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "ta>=0.11.0",
        "aiosqlite>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "okx-trading=src.main:main",
        ],
    },
)
