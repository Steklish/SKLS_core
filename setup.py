from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define the package dependencies
install_requires = [
    # Core dependencies
    "pydantic>=1.10.0",
    
    # Embedding dependencies
    "requests>=2.25.0",
    "chromadb>=0.4.0",
    
    # Generator dependencies
    "json_repair>=0.28.0",
    "pyparsing>=3.0.0",
    "tqdm>=4.60.0",
    "python-dotenv>=0.19.0",
    "google-generativeai>=0.3.0",
    
    # Neo4j dependencies
    "neo4j>=5.0.0",
    
    # Additional dependencies
    "typing-extensions>=4.0.0",
]

setup(
    name="skls-core",
    version="0.1.0",
    author="SKLS",
    author_email="author@example.com",
    description="A comprehensive knowledge graph and language processing system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/skls_core",
    packages=find_packages(exclude=["tests*", "examples*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
        "all": [
            "skls-core[dev]",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add any CLI scripts here if needed in the future
        ],
    },
    include_package_data=True,
    zip_safe=False,
)