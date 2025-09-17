from setuptools import setup, find_packages

setup(
    name="vastravista",
    version="1.0.0",
    author="Saumya Tiwari",
    author_email="your.email@example.com",
    description="AI-Powered Cloth Color Matching, Recommendation, and Virtual Try-On System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "opencv-python>=4.8.0",
        "mediapipe>=0.10.0",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "tensorflow>=2.13.0",
        "torch>=2.1.0",
        "Pillow>=10.0.0",
        "Flask>=3.0.0",
        "PyQt5>=5.15.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "black>=23.0.0", "flake8>=6.0.0"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
