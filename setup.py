from setuptools import setup, find_packages
from os import path
from io import open


def get_about():
    scope = {}
    with open("libsuitetecsa/__about__.py") as fp:
        exec(fp.read(), scope)
    return scope


def get_readme():
    """
        Get the long description from the README file
        :return:
        """
    with open(path.join(here, "README.md"), encoding="utf-8") as f:
        return f.read()


here = path.abspath(path.dirname(__file__))
about = get_about()

setup(
    name=about["__name__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    url=about["__url__"],
    author=about["__author__"],
    author_email=about["__email__"],
    license="GNU General Public License v3",
    platforms=["Unix"],
    classifiers=[
        "Topic :: Internet",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: Unix"
    ],
    keywords=about["__keywords__"],
    packages=find_packages(),
    install_requires=["requests~=2.27.1", "beautifulsoup4~=4.10.0"],
)
