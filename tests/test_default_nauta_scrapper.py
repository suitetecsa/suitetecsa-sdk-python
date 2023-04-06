#  Copyright (c) 2023. Lesly Cintra Laza <a.k.a. lesclaz>.
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to the following conditions:
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
#  Software.
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#  WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
#  OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import unittest

from bs4 import BeautifulSoup

from suitetecsa_core.repository.scrapper_provider import DefaultNautaScrapper


class TestDefaultNautaScrapper(unittest.TestCase):

    def setUp(self):
        self.form_html = '<form><input type="text" name="username" value="John"><input type="password" name="password">' \
                         '</form>'
        self.form_soup = BeautifulSoup(self.form_html, 'html.parser')

    def test_get_inputs(self):
        expected_result = {'username': 'John', 'password': None}
        result = DefaultNautaScrapper._DefaultNautaScrapper__get_inputs(self.form_soup)
        self.assertEqual(result, expected_result, "El resultado no es el esperado.")


if __name__ == '__main__':
    unittest.main()
