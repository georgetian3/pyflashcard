import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyflashcard",
    version="1.0",
    author="George Tian",
    author_email="pypi@georgetian.com",
    description="pyflashcard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/georgetian3/pyflashcard",
    project_urls={
        "Bug Tracker": "https://github.com/georgetian3/pyflashcard/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.8",
)