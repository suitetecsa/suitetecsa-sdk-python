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

import re
from typing import Union
import bs4

VARIOUS_ERRORS = "Se han detectado algunos errores."
USER_PORTAL = "user_portal"
NAUTA = "Nauta"


_re_fail_reason = {
    USER_PORTAL: re.compile(r"toastr\.error\('(?P<reason>[^']*?)'\)"),
    NAUTA: re.compile(r'alert\("(?P<reason>[^"]*?)"\)')
}


def __find_in_user_portal(soup: bs4.BeautifulSoup) -> Union[list, str, None]:
    error = soup.find_all("li", {"class": "sub-message"})
    if error:
        return [
            msg.text for msg in soup.find_all("li", {"class": "sub-message"})
        ] if error.text.startswith(VARIOUS_ERRORS) else error.text


def find_errors(soup: bs4.BeautifulSoup, portal: str = USER_PORTAL) -> Union[list, str, None]:
    script_text = soup.find_all("script")[-1].get_text().strip()

    match = _re_fail_reason[portal].match(script_text)
    if match:
        soup = bs4.BeautifulSoup(match.group("reason"), "html.parser")
        if portal == USER_PORTAL:
            return __find_in_user_portal(soup)
        else:
            soup.text
