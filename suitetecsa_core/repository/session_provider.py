#  Copyright (c) 2023. Lesly Cintra Laza <a.k.a. lesclaz>
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

from abc import ABCMeta, abstractmethod
from copy import copy

from requests import Response, Session
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

from suitetecsa_core import Portal
from suitetecsa_core.exceptions import ConnectionException


class NautaSession(metaclass=ABCMeta):
    """
    Clase abstracta que define los métodos y propiedades necesarios para manejar una sesión en Nauta.
    """

    _headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                  'image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'es-419,es;q=0.6',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    _login_action: str
    _username: str = None
    _csrf: str = None
    _wlan_user_ip: str = None
    _csrf_hw: str = None
    _attribute_uuid: str = None
    _is_logged_in: bool = False
    _is_user_logged_in: bool = _username is not None

    @property
    @abstractmethod
    def user_cookies(self) -> dict:
        """
        Propiedad que devuelve los cookies de la sesión de usuario, en forma de un diccionario.

        :return: Un diccionario con los cookies de la sesión de usuario.
        """
        pass

    @user_cookies.setter
    @abstractmethod
    def user_cookies(self, value: dict):
        """
        Propiedad que permite establecer los cookies de la sesión de usuario.

        :param value: Un diccionario con los cookies que se desean establecer.
        """
        pass

    @property
    @abstractmethod
    def connect_cookies(self) -> dict:
        """
        Propiedad que devuelve los cookies de la sesión de conexión, en forma de un diccionario.

        :return: Un diccionario con los cookies de la sesión de conexión.
        """
        pass

    @connect_cookies.setter
    @abstractmethod
    def connect_cookies(self, value: dict):
        """
        Propiedad que permite establecer los cookies de la sesión de conexión.

        :param value: Un diccionario con los cookies que se desean establecer.
        """
        pass

    @abstractmethod
    def get(self, portal_manager: Portal, url: str, data: dict = None, parse_response: bool = True) -> Response:
        """
        Realiza una petición HTTP GET a la URL especificada, utilizando la sesión de usuario o de conexión según 
        corresponda.

        :param parse_response:
        :param portal_manager: Un objeto `Portal` que indica si se debe usar la sesión de usuario o de conexión.
        :param url: La URL a la que se hará la petición.
        :param data: Opcionalmente, los datos que se enviarán con la petición.
        :return: Un objeto `Response` con la respuesta a la petición.
        """
        pass

    @abstractmethod
    def post(self, portal_manager: Portal, url: str, data: dict = None, parse_response: bool = True) -> Response:
        """
        Realiza una petición HTTP POST a la URL especificada, utilizando la sesión de usuario o de conexión según
        corresponda.

        :param parse_response:
        :param portal_manager: Un objeto `Portal` que indica si se debe usar la sesión de usuario o de conexión.
        :param url: La URL a la que se hará la petición.
        :param data: Opcionalmente, los datos que se enviarán con la petición.
        :return: Un objeto `Response` con la respuesta a la petición.
        """
        pass

    @staticmethod
    def parse_response(response: Response) -> None:
        if not response.ok:
            raise ConnectionException(
                f"{response.status_code} :: {response.reason}"
            )

    @property
    def is_logged_in(self):
        return self._is_logged_in

    @property
    def is_user_logged_in(self) -> bool:
        return self._is_user_logged_in

    @property
    def wlan_user_ip(self):
        return self._wlan_user_ip

    @property
    def csrf_hw(self):
        return self._csrf_hw

    @property
    def username(self):
        return self._username

    @property
    def attribute_uuid(self):
        return self._attribute_uuid

    @property
    def csrf(self):
        return self._csrf

    @csrf.setter
    def csrf(self, value):
        self._csrf = value

    @property
    def login_action(self):
        return self._login_action


class DefaultNautaSession(NautaSession):
    """
    Implementación concreta de `NautaSession` que maneja la sesión del usuario y la sesión de conexión.
    """

    def __init__(self, session: Session) -> None:
        """
        Constructor de la clase.

        :param session: Una sesión de `requests.Session`.
        """
        self.__user_session = session
        self.__user_session.headers = self._headers
        self.__connect_session = copy(session)

    @property
    def user_cookies(self) -> dict:
        """
        Propiedad que devuelve los cookies de la sesión de usuario, en forma de un diccionario.

        :return: Un diccionario con los cookies de la sesión de usuario.
        """
        return dict_from_cookiejar(self.__user_session.cookies)

    @user_cookies.setter
    def user_cookies(self, value: dict):
        """
        Propiedad que permite establecer los cookies de la sesión de usuario.

        :param value: Un diccionario con los cookies que se desean establecer.
        """
        self.__user_session.cookies = cookiejar_from_dict(value)

    @property
    def connect_cookies(self) -> dict:
        """
        Propiedad que devuelve los cookies de la sesión de conexión, en forma de un diccionario.

        :return: Un diccionario con los cookies de la sesión de conexión.
        """
        return dict_from_cookiejar(self.__connect_session.cookies)

    @connect_cookies.setter
    def connect_cookies(self, value: dict):
        """
        Propiedad que permite establecer los cookies de la sesión de conexión.

        :param value: Un diccionario con los cookies que se desean establecer.
        """
        self.__connect_session.cookies = cookiejar_from_dict(value)

    def get(self, portal_manager: Portal, url: str, data: dict = None, parse_response: bool = True) -> Response:
        """
        Realiza una petición HTTP GET a la URL especificada, utilizando la sesión de usuario o de conexión según
        corresponda.

        :param parse_response:
        :param portal_manager: Un objeto `Portal` que indica si se debe usar la sesión de usuario o de conexión.
        :param url: La URL a la que se hará la petición.
        :param data: Opcionalmente, los datos que se enviarán con la petición.
        :return: Un objeto `Response` con la respuesta a la petición.
        """
        response = self.__user_session.get(url,
                                           data=data) if portal_manager == Portal.USER else self.__connect_session.get(
            url, data=data)
        if parse_response:
            NautaSession.parse_response(response)
        return response

    def post(self, portal_manager: Portal, url: str, data: dict = None, parse_response: bool = True) -> Response:
        """
        Realiza una petición HTTP POST a la URL especificada, utilizando la sesión de usuario o de conexión según
        corresponda.

        :param parse_response:
        :param portal_manager: Un objeto `Portal` que indica si se debe usar la sesión de usuario o de conexión.
        :param url: La URL a la que se hará la petición.
        :param data: Opcionalmente, los datos que se enviarán con la petición.
        :return: Un objeto `Response` con la respuesta a la petición.
        """
        response = self.__user_session.post(
            url,
            data=data
        ) if portal_manager == Portal.USER else self.__connect_session.post(
            url, data=data
        )

        if parse_response:
            NautaSession.parse_response(response)

        return response
