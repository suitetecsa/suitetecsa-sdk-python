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


class Action:
    LOGIN = "login_action"
    LOGOUT = "logout_action"
    LOAD_USER_INFO = "load_user_info_action"
    RECHARGE = "recharge_action"
    TRANSFER = "transfer_action"
    CHANGE_PASSWORD = "change_password_action"
    CHANGE_EMAIL_PASSWORD = "change_email_password_action"
    GET_CONNECTIONS = "get_connections_action"
    GET_RECHARGES = "get_recharges_action"
    GET_TRANSFERS = "get_transfers_action"
    GET_QUOTES_FUND = "get_quotes_fund_action"


class Portal:
    USER_PORTAL = 0
    NAUTA = 1


VARIOUS_ERRORS = "Se han detectado algunos errores."

# Un diccionario que contiene dos expresiones regulares. El primero se usa para
# encontrar el mensaje de error en el portal de usuario, y el segundo se usa
# para encontrar el mensaje de error en el portal Nauta.
re_fail_reason = {
    Portal.USER_PORTAL: re.compile(r"toastr\.error\('(?P<reason>[^']*?)'\)"),
    Portal.NAUTA: re.compile(r'alert\("(?P<reason>[^"]*?)"\)')
}


def find_errors(
        soup: bs4.BeautifulSoup, portal: str = Portal.USER_PORTAL
) -> Union[list, str, None]:
    """
    Toma la última etiqueta de script en el HTML, extrae el texto y luego usa
    una expresión regular para encontrar el mensaje de error.
    
    :param soup: bs4.hermosa sopa
    :type soup: bs4.BeautifulSoup
    :param portal: El portal para buscar errores en
    :type portal: str
    :return: Una lista de errores.
    """
    script_text = soup.find_all("script")[-1].get_text().strip()

    match = re_fail_reason[portal].match(script_text)
    if match:
        soup = bs4.BeautifulSoup(match.group("reason"), "html.parser")
        if portal == Portal.USER_PORTAL:
            return __find_in_user_portal(soup)
        else:
            soup.text


def __find_in_user_portal(soup: bs4.BeautifulSoup) -> Union[list, str, None]:
    """
    Devuelve una lista de mensajes de error si el error es un error de "varios
    errores", de lo contrario, devuelve el mensaje de error
    
    :param soup: bs4.hermosa sopa
    :type soup: bs4.BeautifulSoup
    :return: Una lista de errores o una cadena de un error.
    """
    error = soup.find("li", {"class": "msg_error"})
    if error:
        return [
            msg.text for msg in error.find_all("li", {"class": "sub-message"})
        ] if soup.text.startswith(VARIOUS_ERRORS) else error.text
