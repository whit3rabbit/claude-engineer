from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-engineer",
    version="0.1.0",
    author="Doriandarko",
    author_email="dorian@example.com",  # Replace with actual email if available
    description="An interactive CLI leveraging Claude-3.5-Sonnet for software development tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Doriandarko/claude-engineer",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "colorama",
        "pygments",
        "tavily-python",
        "python-dotenv",
        "Pillow",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "claude-engineer=claude_engineer.cli:main",
        ],
    },
)