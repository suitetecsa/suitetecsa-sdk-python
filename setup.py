#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2023 Lesly Cintra Laza <a.k.a. lesclaz>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))


def get_readme():
    """
        Get the long description from the README file
        :return:
        """
    with open(path.join(here, "README.md"), encoding="utf-8") as f:
        return f.read()


setup(
    name='PyLibSuitETECSA',
    version='1.0.0b1',
    packages=['PyLibSuitETECSA', 'PyLibSuitETECSA.core', 'PyLibSuitETECSA.utils'],
    url='https://github.com/SuitETECSA/PyLibSuitETECSA',
    license='MIT',
    author='lesclaz',
    author_email='lesclaz95@gmail.com',
    description='Una API que interactúa con los servicios web de ETECSA. ',
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    platforms=["Unix"],
    classifiers=[
        "Topic :: Internet",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: Unix"
    ],
    keywords="ETECSA nauta tools",
    install_requires=[
        'requests',
        'beautifulsoup4',
        'setuptools',
        'html5lib'
    ],
)
