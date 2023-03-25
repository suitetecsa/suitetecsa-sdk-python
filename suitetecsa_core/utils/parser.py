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

import re
import bs4

from suitetecsa_core import Portal


__various_errors_text = "Se han detectado algunos errores."
__re_fail_reason = {
    Portal.USER: re.compile(r"toastr\.error\('(?P<reason>[^']*?)'\)"),
    Portal.CONNECT: re.compile(r'alert\("(?P<reason>[^"]*?)"\)')
}


def parse_errors(
        soup: bs4.BeautifulSoup, portal: Portal = Portal.USER
) -> list[str] | str | None:
    """
    Toma la última etiqueta de script en el HTML, extrae el texto y luego usa
    una expresión regular para encontrar el mensaje de error.

    :param soup: bs4.hermosa sopa
    :type soup: bs4.BeautifulSoup
    :param portal: El portal para buscar errores en
    :type portal: str
    :return: Una lista de errores.
    """
    tag_script: bs4.Tag = soup.find_all("script")
    if tag_script:
        script_text = tag_script[-1].contents[0].strip()
        match = __re_fail_reason[portal].match(script_text)
        if match:
            soup = bs4.BeautifulSoup(match.group("reason"), "html5lib")
            if portal == Portal.USER:
                error = soup.select_one('li:is(.msg_error)')
                if error:
                    return [
                        msg.text for msg in error.select('li:is(.sub-message)')
                    ] if soup.text.startswith(__various_errors_text) else error.text
            else:
                soup.text
