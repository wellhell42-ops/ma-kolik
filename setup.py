"""Setup script for Maçkolik İstatistik Toplayıcı."""

from setuptools import setup, find_packages

setup(
    name="mackolik-stats",
    version="1.0.0",
    description="Maçkolik.com'dan profesyonel futbol istatistikleri çekme aracı",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "openpyxl>=3.1.0",
        "rich>=13.0.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "mackolik=main:main",
        ],
        "gui_scripts": [
            "mackolik-gui=gui:main",
        ],
    },
)
