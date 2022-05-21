#  Copyright (c) 2022. MarilaSoft.
#  #
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  #
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  #
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
    version='0.1.3b2',
    packages=['PyLibSuitETECSA', 'PyLibSuitETECSA.core'],
    url='https://github.com/SuitETECSA/PyLibSuitETECSA',
    license='GNU General Public License v3',
    author='lesclaz',
    author_email='lesclaz95@gmail.com',
    description='Una API que interactúa con los servicios web de ETECSA. ',
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    platforms=["Unix"],
    classifiers=[
        "Topic :: Internet",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: Unix"
    ],
    keywords="ETECSA nauta tools",
    install_requires=[
        "requests~=2.27.1",
        "beautifulsoup4~=4.10.0",
        "pytest~=7.1.2",
        "setuptools~=60.2.0"
    ],
)
