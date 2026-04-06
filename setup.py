import os
import codecs

from setuptools import setup
from setuptools import find_packages

PROJECT = os.path.abspath(os.path.dirname(__file__))
REQUIRE_PATH = "requirements.txt"
EXCLUDES = (
    "tests", "bin", "docs", "fixtures", "register", "notebooks", "examples",
)

with open(os.path.join(PROJECT, 'README.rst')) as f:
    long_description = f.read()


def read(*parts):
    """
    Assume UTF-8 encoding and return the contents of the file located at the
    absolute path from the REPOSITORY joined with *parts.
    """
    with codecs.open(os.path.join(PROJECT, *parts), 'rb', 'utf-8') as f:
        return f.read()


def get_requires(path=REQUIRE_PATH):
    """
    Yields a generator of requirements as defined by the REQUIRE_PATH which
    should point to a requirements.txt output by `pip freeze`.
    """
    for line in read(path).splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            yield line


setup(
    name="py-votesmart",
    version="2.0.2",
    description="Python library for the Vote Smart REST API 2.0",
    author="Nathan Danielsen <nathan.danielsen@gmail.com>",
    author_email="nathan.danielsen@gmail.com",
    license="BSD",
    url="https://github.com/NationalJournal/py-votesmart/",
    long_description=long_description,
    packages=find_packages(where=PROJECT, exclude=EXCLUDES),
    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=list(get_requires()),
    python_requires=">=3.6",
)
