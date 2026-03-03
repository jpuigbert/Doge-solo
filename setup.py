from setuptools import setup, find_packages

setup(
    name="dogesolo",
    version="1.0.0",
    description="Mineria Dogecoin en solitari per a tothom",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PySide6>=6.6.0",
        "requests>=2.31.0",
        "psutil>=5.9.6",
        "python-bitcoinrpc>=1.0",
        "scrypt>=0.8.24",
        "base58>=2.1.1",
    ],
    entry_points={
        "console_scripts": ["dogesolo=src.main:main"],
        "gui_scripts": ["DogeSolo=src.main:main"],
    },
)