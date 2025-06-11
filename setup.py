"""
Configuration du package BlissLearn.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="blisslearn",
    version="2.2.0",
    author="BlissLearn Team",
    author_email="contact@blisslearn.com",
    description="Système de recommandation de cours en ligne",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/votre-username/blisslearn",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.26.2",
        "pandas>=2.1.3",
        "scikit-learn>=1.3.2",
        "nltk>=3.8.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "blisslearn=src.recommender.engine:main",
        ],
    },
    package_data={
        "blisslearn": ["data/*.csv"],
    },
) 