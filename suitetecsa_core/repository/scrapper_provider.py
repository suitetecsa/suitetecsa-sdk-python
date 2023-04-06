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
import logging
import math
import re
from abc import ABCMeta, abstractmethod
from typing import Type, Optional

from bs4 import BeautifulSoup, Tag

from suitetecsa_core import Portal, Action
from suitetecsa_core.domain.model import ConnectionsSummary, RechargesSummary, TransfersSummary, QuotesPaidSummary, \
    Connection, Recharge, Transfer, QuotePaid
from suitetecsa_core.domain.model.nauta_user import NautaUser
from suitetecsa_core.core.exceptions import GetInfoException, NotLoggedIn, PreLoginException, LoginException, \
    RechargeException, TransferException, ChangePasswordException, LogoutException
from suitetecsa_core.repository.session_provider import NautaSession
from suitetecsa_core.utils.nauta import str_to_float, convert_to_bytes, parse_datetime, str_to_date, parse_errors, \
    time_string_to_seconds

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s :: %(levelname)s :: %(message)s"
)
logger = logging.getLogger()


class NautaScrapper(metaclass=ABCMeta):
    _connect_domain: str = "secure.etecsa.net"
    _base_url: dict = {
        Portal.CONNECT: f'https://{_connect_domain}:8443/',
        Portal.USER: 'https://www.portal.nauta.cu/'
    }
    _portals_urls = {
        Portal.CONNECT: {
            Action.LOGOUT:
                'LogoutServlet',
            Action.LOAD_USER_INFORMATION:
                'EtecsaQueryServlet',
            Action.CHECK_CONNECTION: 'http://www.cubadebate.cu/'
        },
        Portal.USER: {
            Action.LOGIN: "user/login/es-es",
            Action.LOAD_USER_INFORMATION: "useraaa/user_info",
            Action.RECHARGE: "useraaa/recharge_account",
            Action.TRANSFER: "useraaa/transfer_balance",
            Action.NAUTA_HOGAR_PAID: "useraaa/transfer_nautahogarpaid",
            Action.CHANGE_PASSWORD: "useraaa/change_password",
            Action.CHANGE_EMAIL_PASSWORD: "mail/change_password",
            Action.GET_CONNECTIONS: {
                "base": "useraaa/service_detail/",
                "summary": "useraaa/service_detail_summary/",
                "list": "useraaa/service_detail_list/"
            },
            Action.GET_RECHARGES: {
                "base": "useraaa/recharge_detail/",
                "summary": "useraaa/recharge_detail_summary/",
                "list": "useraaa/recharge_detail_list/"
            },
            Action.GET_TRANSFERS: {
                "base": "useraaa/transfer_detail/",
                "summary": "useraaa/transfer_detail_summary/",
                "list": "useraaa/transfer_detail_list/",
            },
            Action.GET_QUOTES_PAID: {
                "base": "useraaa/nautahogarpaid_detail/",
                "summary": "useraaa/nautahogarpaid_detail_summary/",
                "list": "useraaa/nautahogarpaid_detail_list/"
            },
            Action.LOGOUT: "user/logout"
        }
    }
    _is_nauta_home: bool = False

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_logged_in(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_user_logged_in(self):
        pass

    @property
    @abstractmethod
    def user_information(self) -> NautaUser:
        pass

    @abstractmethod
    def get_connect_information(self, username: str, password: str) -> dict:
        pass

    @property
    @abstractmethod
    def data_session(self) -> dict:
        pass

    @data_session.setter
    @abstractmethod
    def data_session(self, value: dict):
        pass

    @property
    @abstractmethod
    def captcha_image(self):
        pass

    @abstractmethod
    def check_portal_access(self):
        pass

    @abstractmethod
    def connect(self, username: str, password: str):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def login(self, username: str, password: str, captcha_code: str):
        pass

    @abstractmethod
    def logout(self):
        pass

    @abstractmethod
    def to_up(self, recharge_code):
        pass

    @abstractmethod
    def transfer(self, amount: float, password: str, destination_account: str = None):
        pass

    @abstractmethod
    def change_password(self, old_password: str, new_password: str):
        pass

    @abstractmethod
    def change_email_password(self, old_password: str, new_password: str):
        pass

    @abstractmethod
    def get_connections_summary(self, year: int, month: int) -> ConnectionsSummary:
        pass

    @abstractmethod
    def get_recharges_summary(self, year: int, month: int) -> RechargesSummary:
        pass

    @abstractmethod
    def get_transfers_summary(self, year: int, month: int) -> TransfersSummary:
        pass

    @abstractmethod
    def get_quotes_paid_summary(self, year: int, month: int) -> QuotesPaidSummary:
        pass

    @abstractmethod
    def get_connections(
            self, year: int, month: int, summary: ConnectionsSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[Connection]:
        pass

    @abstractmethod
    def get_recharges(
            self, year: int, month: int, summary: RechargesSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[Recharge]:
        pass

    @abstractmethod
    def get_transfers(
            self, year: int, month: int, summary: TransfersSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[Transfer]:
        pass

    @abstractmethod
    def get_quotes_paid(
            self, year: int, month: int, summary: QuotesPaidSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[QuotePaid]:
        pass

    @property
    def is_nauta_home(self):
        return self._is_nauta_home


# noinspection PyTypeChecker
class DefaultNautaScrapper(NautaScrapper):

    def __init__(self, scrapper: BeautifulSoup, session: NautaSession):
        self.__session = session
        self.__scrapper = scrapper

    def __make_url(
            self, portal_manager: Portal, action: Action, get_action: bool = False, sub_action: Optional[str] = None,
            year_month_selected: Optional[str] = None, count: Optional[int] = None, page: Optional[int] = None
    ) -> str:
        """
        Construye una URL para una acción determinada en un portal determinado.

        :param portal_manager: Un objeto Portal que representa el portal en el que se realizará la acción.
        :param action: Una enumeración Action que representa la acción que se realizará en el portal.
        :param get_action: Un booleano que indica si se debe obtener una URL básica para la acción dada o una URL más
        detallada. El valor predeterminado es False.
        :param sub_action: Una cadena que representa la sub-acción que se realizará en la acción dada. El valor
        predeterminado es None.
        :param year_month_selected: Una cadena que representa el año y mes seleccionados para la acción de lista.
        Requerido si la sub-acción es 'list'.
        :param count: Un entero que representa el número máximo de elementos que se deben recuperar para la acción de
        lista. Requerido si la sub-acción es 'list'.
        :param page: Un entero que representa el número de página que se debe recuperar para la acción de lista. El
        valor predeterminado es None, lo que significa que se recuperarán todos los elementos.

        :return: Una cadena que representa la URL construida para la acción dada en el portal dado.

        :raises ValueError: Si year_month_selected o count están ausentes cuando sub_action es 'list'.
        """
        if action == Action.CHECK_CONNECTION:
            return self._portals_urls[portal_manager][action]
        elif not get_action:
            return f'{self._base_url[portal_manager]}{self._portals_urls[portal_manager][action]}'
        else:
            url = f'{self._base_url[portal_manager]}{self._portals_urls[portal_manager][action][sub_action]}'
            if sub_action in ('base', 'summary'):
                return url
            elif sub_action == 'list':
                if not year_month_selected:
                    raise ValueError("year_month_selected is required for 'list' sub-action")
                if not count:
                    raise ValueError("count is required for 'list' sub-action")
                else:
                    return f'{url}{year_month_selected}/{count}' \
                        if not page else f'{url}{year_month_selected}/{count}/{page}'

    @staticmethod
    def __get_inputs(form_soup: Tag) -> dict:
        """
        Obtiene los valores de entrada de un formulario HTML dado y los devuelve en un diccionario.

        :param form_soup: El objeto BeautifulSoup que representa el formulario HTML.
        :type form_soup: bs4.Tag
        :return: Un diccionario que contiene los valores de entrada del formulario.
        :rtype: dict
        """
        return {
            _["name"]: _.get("value", default=None)
            for _ in form_soup.select("input[name]")
        }

    @staticmethod
    def __get_csrf(soup: BeautifulSoup) -> str:
        """
        Obtiene el valor del token CSRF de una página web y lo devuelve como una cadena.

        :param soup: El objeto BeautifulSoup que representa la página web.
        :type soup: BeautifulSoup
        :return: El valor del token CSRF de la página web.
        :rtype: str
        """
        return soup.select_one('input[name=csrf]').attrs["value"]

    def __get_information_user(self, soup: BeautifulSoup) -> NautaUser:
        keys = [
            'username', 'blocking_date', 'date_of_elimination',
            'account_type', 'service_type', 'credit', 'time',
            'mail_account', 'offer', 'monthly_fee', 'download_speeds',
            'upload_speeds', 'phone', 'link_identifiers',
            'link_status', 'activation_date', 'blocking_date_home',
            'date_of_elimination_home', 'quote_paid', 'voucher', 'debt'
        ]
        user_info = {}
        for _index, attr in enumerate(
                soup.select_one('.z-depth-1').select('.m6')
        ):
            user_info = {
                **user_info,
                keys[_index]: attr.select_one('p').text.strip()
            }
        self._is_nauta_home = "offer" in user_info.keys()
        return NautaUser.from_dict(user_info)

    @staticmethod
    def __get_information_connect(soup: BeautifulSoup) -> dict:
        keys = [
            "account_status",
            "credit",
            "expiration_date",
            "access_areas",
            "from",
            "to",
            "time"
        ]
        return {
            'account_info': {
                keys[count]: value.text.strip()
                for count, value in enumerate(soup.select(
                    '#sessioninfo > tbody > tr > :not(td.key)'
                ))
            },
            'lasts_connections': [
                {
                    keys[count + 4]: value.text.strip()
                    for count, value in enumerate(tr.select('td'))
                } for tr in soup.select(
                    '#sesiontraza > tbody > tr'
                )
            ]
        }

    @staticmethod
    def __find_errors(soup: BeautifulSoup, portal_manager: Portal, exception: Type[Exception], message: str):
        errors = parse_errors(soup, portal_manager)
        if errors:
            raise exception(f"{message} :: {errors}")

    def __user_session_init(self):
        response = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.LOGIN
            )
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, PreLoginException, "Fail during pre login action")
        self.__session.csrf = self.__get_csrf(soup)

    def __connect_session_init(self):
        """
        Inicializa una sesión de conexión en Portal Nauta.

        :raises PreLoginException: Si ya se ha iniciado una sesión de conexión.
        """

        if self.is_connected:
            raise PreLoginException("Ya estás conectado a internet")

        # Primera pasada: se espera una redirección
        response = self.__session.get(
            Portal.CONNECT,
            self.__make_url(
                Portal.CONNECT,
                Action.CHECK_CONNECTION
            )
        )
        # Obteniendo datos previos al inicio de sesión
        logger.debug("Obtaining pre login data")
        soup = BeautifulSoup(response.text, "html5lib")
        action = soup.form["action"]
        data = self.__get_inputs(soup)

        # Segunda pasada: contentando con el portal
        logger.debug(f"Connecting to {action}")
        response = self.__session.post(
            Portal.CONNECT,
            action,
            data
        )

        # Obteniendo datos para establecer la sesión
        logger.debug("Obtaining data for make a session")
        soup = BeautifulSoup(response.text, "html5lib")
        form_soup = soup.select_one("#formulario")
        data = self.__get_inputs(form_soup)

        # Estableciendo datos para la sesión
        logger.debug("Establishing data for the session")
        self.__session._login_action = form_soup["action"]
        self.__session._csrf_hw = data["CSRFHW"]
        self.__session._wlan_user_ip = data["wlanuserip"]

    def __get_summary_html_content(self, year: int, month: int, action: Action) -> list[Tag]:
        """
        Este método privado devuelve el contenido HTML del resumen para un año, mes y acción dados.

        :param year: Un entero que representa el año.
        :param month: Un entero que representa el mes.
        :param action: Un valor enum de Action que representa la acción.
        :return: Una lista de elementos div con la clase card-content, que contienen el contenido HTML del resumen para
        la acción, año y mes dados.
        :raises: GetInfoException: Si ocurren errores al enviar las solicitudes GET o POST o al analizar el HTML de
        respuesta.
        """
        actions_details = {
            Action.GET_CONNECTIONS: "service_detail",
            Action.GET_RECHARGES: "recharge_detail",
            Action.GET_QUOTES_PAID: "nautahogarpaid_detail",
            Action.GET_TRANSFERS: "transfer_detail"
        }
        errors_messages = {
            Action.GET_CONNECTIONS: "Error al obtener el resumen de conexiones",
            Action.GET_RECHARGES: "Error al obtener el resumen de recargas",
            Action.GET_QUOTES_PAID: "Error al obtener el resumen de cotizaciones pagadas",
            Action.GET_TRANSFERS: "Error al obtener el resumen de transferencias"
        }
        year_month = f"{year}-{month:02}"

        # Obtención del token csrf requerido para esta acción
        response_get = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                action,
                True,
                "base"
            )
        )
        soup = BeautifulSoup(response_get.text, "html5lib")
        self.__find_errors(soup, Portal.USER, GetInfoException, errors_messages[action])
        csrf = self.__get_csrf(soup)

        # Intentando obtener el resumen de la acción
        response = self.__session.post(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                action,
                True,
                "summary"
            ),
            {
                "csrf": csrf,
                "year_month": year_month,
                "list_type": actions_details[action]
            }
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, GetInfoException, errors_messages[action])

        # Devolviendo una lista de divs con la clase card-content
        return soup.select_one('#content').select('.card-content')

    def __get_action_per_page_as_row_html(
            self, action: Action, year_month_selected: str, count: int, large: int = 0, _reversed: bool = False
    ) -> list[Tag]:
        """
        Este método privado devuelve una lista de objetos Tag que representan las filas de una tabla de una página web.

        :param action: Una instancia de la enumeración Action que representa la acción a realizar.
        :param year_month_selected: Una cadena que representa el año y mes seleccionados.
        :param count: Un entero que representa el número total de elementos.
        :param large: Un entero que especifica el número máximo de filas a devolver. El valor por defecto es 0, lo que
        significa que se devolverán todas las filas.
        :param _reversed: Un valor booleano que indica si las filas deben ser devueltas en orden inverso. El valor por
        defecto es False.
        :return: Una lista de objetos Tag que representan las filas de una tabla de una página web.
        """
        rows = []
        totals_pages = math.ceil(count / 14)
        current_page = totals_pages if _reversed else 1
        if large == 0:
            large = count

        while len(rows) < large and current_page >= 1:
            page = current_page if current_page != 1 else None
            url = self.__make_url(
                portal_manager=Portal.USER, action=action, get_action=True, sub_action='list',
                year_month_selected=year_month_selected, count=count, page=page
            )
            table_body = self.__get_table_body_html(url)
            if table_body:
                rows_page = [row for row in reversed(table_body.select('tr'))] \
                    if _reversed else \
                    [row for row in table_body.select('tr')]
                rows.extend(
                    rows_page[:abs(large) - len(rows)]
                )
            current_page += -1 if _reversed else 1
        return rows

    def __get_table_body_html(self, url: str) -> Tag:
        """
        Este método privado devuelve el contenido HTML del cuerpo de una tabla de una página web.

        :param url: Una cadena que representa la URL de la página web.
        :return: Un objeto de tipo Tag que representa el contenido HTML del cuerpo de una tabla de una página web.
        """
        response = self.__session.get(Portal.USER, url)
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, GetInfoException, "Fail to obtain information")
        return soup.select_one(".responsive-table > tbody")

    @property
    def is_connected(self) -> bool:
        logger.debug("Checking connection")
        response = self.__session.get(Portal.CONNECT, self.__make_url(Portal.CONNECT, Action.CHECK_CONNECTION))
        return self._connect_domain not in response.url

    @property
    def is_logged_in(self) -> bool:
        return self.__session.is_logged_in

    @property
    def is_user_logged_in(self):
        return self.__session.is_user_logged_in

    @property
    def user_information(self) -> NautaUser:
        """
        Devuelve la información del usuario que ha iniciado sesión.

        :return: Un objeto NautaUser que contiene la información del usuario.
        :rtype: NautaUser

        :raises NotLoggedIn: Si el usuario no ha iniciado sesión.
        """
        if not self.__session.is_user_logged_in:
            raise GetInfoException(
                "This session is not logged in"
            )
        response = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.LOAD_USER_INFORMATION
            )
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, GetInfoException, "Error al obtener la información del usuario")
        return self.__get_information_user(soup)

    @property
    def remaining_time(self) -> str:
        if not self.__session.is_logged_in:
            raise GetInfoException("This session is not logged in")
        response = self.__session.post(
            Portal.CONNECT,
            self.__make_url(
                Portal.CONNECT,
                Action.LOAD_USER_INFORMATION
            ),
            {
                "op": "getLeftTime",
                "ATTRIBUTE_UUID": self.__session.attribute_uuid,
                "CSRFHW": self.__session.csrf_hw,
                "wlanuserip": self.__session.wlan_user_ip,
                "username": self.__session.username,
            }
        )
        return response.text.strip()

    def check_portal_access(self):
        try:
            response = self.__session.get(
                Portal.CONNECT,
                self.__make_url(
                    Portal.CONNECT,
                    Action.CHECK_CONNECTION
                )
            )
            return self._connect_domain in response.url
        except Type[Exception]:
            return False

    def get_connect_information(self, username: str, password: str) -> dict[str, str | dict[str, str]]:
        """
        Obtiene la información de conexión del usuario y la devuelve en un diccionario.

        :param username: Nombre de usuario del usuario.
        :type username: str
        :param password: Contraseña del usuario.
        :type password: str
        :return: Un diccionario que contiene la información de conexión del usuario.
        :rtype: dict[str, Union[str, dict[str, str]]]

        :raises GetInfoException: Si no se puede obtener la información del usuario.
        """

        response = self.__session.post(
            Portal.CONNECT,
            self.__make_url(
                Portal.CONNECT,
                Action.LOAD_USER_INFORMATION
            ),
            {
                'username': username,
                'password': password,
                'wlanuserip': self.__session.wlan_user_ip,
                'CSRFHW': self.__session.csrf_hw,
                'lang': ''
            }
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.CONNECT, GetInfoException, "Error al obtener la información del usuario")
        return self.__get_information_connect(soup)

    @property
    def data_session(self) -> dict:
        """
        Devuelve un diccionario con la información de la sesión actual.

        :return: Un diccionario que contiene la información de la sesión actual.
        :rtype: dict
        :raises NotLoggedIn: Si el usuario no ha iniciado sesión.
        """

        if not self.__session.is_logged_in:
            raise NotLoggedIn("No has iniciado sesión")
        return {
            'username': self.__session.username,
            'cookies': self.__session.connect_cookies,
            'wlanuserip': self.__session.wlan_user_ip,
            'CSRFHW': self.__session.csrf_hw,
            'ATTRIBUTE_UUID': self.__session.attribute_uuid
        }

    @property
    def captcha_image(self) -> bytes:
        """
        Devuelve la imagen del captcha actual en formato de bytes.

        :return: La imagen del captcha actual en formato de bytes.
        :rtype: bytes
        :raises UserSessionException: Si no se puede inicializar la sesión de usuario.
        """

        if not self.__session.csrf:
            self.__user_session_init()
        return self.__session.get(
            Portal.USER,
            "https://www.portal.nauta.cu/captcha/?"
        ).content

    def connect(self, username: str, password: str):
        """
        Inicia una conexión con Portal Nauta utilizando el nombre de usuario y la contraseña proporcionados.

        :param username: Nombre de usuario para la conexión.
        :param password: Contraseña para la conexión.
        :raises LoginException: Si no se puede iniciar sesión en el portal.
        """

        if not self.__session.csrf_hw:
            self.__connect_session_init()
        response = self.__session.post(
            Portal.CONNECT,
            self.__session.login_action,
            {
                "CSRFHW": self.__session.csrf_hw,
                "wlanuserip": self.__session.wlan_user_ip,
                "username": username,
                "password": password
            }
        )
        if "online.do" not in response.url:
            self.__find_errors(
                BeautifulSoup(response.text, "html5lib"),
                Portal.CONNECT,
                LoginException,
                "No se pudo iniciar sesión en el portal"
            )
        self.__session._attribute_uuid = re.search(r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', response.text).group(1)

    def disconnect(self):
        """
        Cierra la sesión en el portal cautivo.

        :raises NotLoggedIn: Si no se ha iniciado sesión.
        :raises LogoutException: Si no se pudo cerrar la sesión correctamente.

        """
        if not self.is_logged_in:
            raise NotLoggedIn("You are not logged in")
        response = self.__session.post(
            Portal.CONNECT,
            f"{self.__make_url(Portal.CONNECT, Action.LOGOUT)}?CSRFHW={self.__session.csrf_hw}&"
            f"username={self.__session.username}&ATTRIBUTE_UUID={self.__session.attribute_uuid}&"
            f"wlanuserip={self.__session.wlan_user_ip}"
        )
        if "SUCCESS" not in response.text.upper():
            raise LogoutException(
                f"Fail to logout :: {response.text[:100]}"
            )

    def login(self, username: str, password: str, captcha_code: str) -> NautaUser:
        """
        Inicia sesión en el portal de usuario de Nauta utilizando el nombre de usuario, contraseña y código captcha
        proporcionados.

        :param username: Nombre de usuario para la conexión.
        :param password: Contraseña para la conexión.
        :param captcha_code: Código captcha para la conexión.
        :raises ValueError: Si se proporciona un valor vacío para el nombre de usuario, contraseña o código captcha.
        :raises LoginException: Si no se puede iniciar sesión en el portal.
        :return: Objeto NautaUser que contiene la información del usuario.
        """

        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        if not password:
            raise ValueError("La contraseña es obligatoria")
        if not captcha_code:
            raise ValueError("El código captcha es obligatorio")

        response = self.__session.post(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.LOGIN
            ),
            {
                'csrf': self.__session.csrf,
                'login_user': username,
                'password_user': password,
                'captcha': captcha_code.upper(),
                'btn_submit': ''
            }
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, LoginException, "No se pudo iniciar sesión en el portal")
        self.__session._username = username
        return self.__get_information_user(soup)

    def logout(self):
        """
        Cierra la sesión en el portal de usuario de Nauta eliminando las cookies y el token CSRF de la sesión.
        """
        self.__session.user_cookies = None
        self.__session.csrf = None

    def to_up(self, recharge_code):
        """
        Intenta recargar el saldo de la cuenta utilizando el código de recarga proporcionado.

        :param recharge_code: Código de recarga para la recarga del saldo.
        :raises RechargeException: Si no se puede recargar el saldo de la cuenta.
        """

        # Obtención del token csrf requerido para esta acción
        response_get = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.RECHARGE
            )
        )
        soup = BeautifulSoup(response_get.text, "html5lib")
        self.__find_errors(soup, Portal.USER, RechargeException, "No se pudo recargar el saldo de la cuenta")
        csrf = self.__get_csrf(soup)

        # Intento de recarga del saldo de la cuenta
        response = self.__session.post(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.RECHARGE
            ),
            {
                "csrf": csrf,
                "recharge_code": recharge_code,
                "btn_submit": ""
            }
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, RechargeException, "No se pudo recargar el saldo de la cuenta")

    def transfer(self, amount: float, password: str, destination_account: str = None):
        """
        Intenta transferir una cantidad de saldo especificada a una cuenta de destino utilizando la contraseña
        proporcionada.

        :param amount: Cantidad de saldo a transferir.
        :param password: Contraseña para la transferencia del saldo.
        :param destination_account: Cuenta de destino para la transferencia del saldo. Si no se proporciona, se
        intentará la cuota de nauta hogar.
        :raises TransferException: Si no se puede transferir el saldo a la cuenta de destino.
        """

        # Obtención del token csrf requerido para esta acción
        response_get = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.TRANSFER
            )
        )
        soup = BeautifulSoup(response_get.text, "html5lib")
        self.__find_errors(soup, Portal.USER, TransferException,
                           "No se pudo transferir el saldo a la cuenta de destino")
        csrf = self.__get_csrf(soup)

        # Intento de transferencia del saldo
        data = {
            "csrf": csrf,
            "transfer": f"{amount:.2f}".replace(".", ","),
            "password_user": password,
            "action": "checkdata"
        }
        if destination_account:
            data["id_cuenta"] = destination_account
        response = self.__session.post(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.TRANSFER
            ),
            data
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, TransferException,
                           "No se pudo transferir el saldo a la cuenta de destino")

    def change_password(self, old_password: str, new_password: str):
        """
        Intenta cambiar la contraseña actual por una nueva utilizando la contraseña actual y la nueva contraseña
        proporcionadas.

        :param old_password: Contraseña actual para la cuenta.
        :param new_password: Nueva contraseña para la cuenta.
        :raises ChangePasswordException: Si no se puede cambiar la contraseña de la cuenta.
        """

        # Obtención del token csrf requerido para esta acción
        response_get = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.CHANGE_PASSWORD
            )
        )
        soup = BeautifulSoup(response_get.text, "html5lib")
        self.__find_errors(soup, Portal.USER, ChangePasswordException, "No se pudo cambiar la contraseña de la cuenta")
        csrf = self.__get_csrf(soup)

        # Intento de cambio de contraseña
        response = self.__session.post(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.CHANGE_PASSWORD
            ),
            {
                "csrf": csrf,
                "old_password": old_password,
                "new_password": new_password,
                "repeat_new_password": new_password,
                "btn_submit": ""
            }
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(soup, Portal.USER, ChangePasswordException, "No se pudo cambiar la contraseña de la cuenta")

    def change_email_password(self, old_password: str, new_password: str):
        """
        Intenta cambiar la contraseña actual de la cuenta de correo electrónico asociada utilizando la contraseña actual
        y la nueva contraseña proporcionadas.

        :param old_password: Contraseña actual para la cuenta.
        :param new_password: Nueva contraseña para la cuenta.
        :raises TransferException: Si no se puede cambiar la contraseña de la cuenta de correo electrónico asociada.
        """

        # Obtención del token csrf requerido para esta acción
        response_get = self.__session.get(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.CHANGE_EMAIL_PASSWORD
            )
        )
        soup = BeautifulSoup(response_get.text, "html5lib")
        self.__find_errors(
            soup, Portal.USER, TransferException,
            "No se pudo cambiar la contraseña de la cuenta de correo electrónico asociada"
        )
        csrf = self.__get_csrf(soup)

        # Intento de cambio de contraseña de la cuenta de correo electrónico asociada
        response = self.__session.post(
            Portal.USER,
            self.__make_url(
                Portal.USER,
                Action.CHANGE_EMAIL_PASSWORD
            ),
            {
                "csrf": csrf,
                "old_password": old_password,
                "new_password": new_password,
                "repeat_new_password": new_password,
                "btn_submit": ""
            }
        )
        soup = BeautifulSoup(response.text, "html5lib")
        self.__find_errors(
            soup, Portal.USER, TransferException,
            "No se pudo cambiar la contraseña de la cuenta de correo electrónico asociada"
        )

    def get_connections_summary(self, year: int, month: int) -> ConnectionsSummary:
        """
        Este método devuelve un objeto de tipo ConnectionsSummary que contiene un resumen de conexiones para el año y
        mes dados.

        :param year: Un entero que representa el año.
        :param month: Un entero que representa el mes.
        :return: Un objeto de tipo ConnectionsSummary que contiene un resumen de conexiones para el año y mes dados.
        """
        summary_html = self.__get_summary_html_content(year, month, Action.GET_CONNECTIONS)
        return ConnectionsSummary(
            count=int(summary_html[0].select_one("input[name=count]").attrs["value"]),
            year_month_selected=summary_html[0].select_one("input[name=year_month_selected]").attrs["value"],
            total_time=time_string_to_seconds(summary_html[1].select_one('.card-stats-number').text.strip()),
            total_import=str_to_float(summary_html[2].select_one('.card-stats-number').text.strip()),
            uploaded=convert_to_bytes(summary_html[3].select_one('.card-stats-number').text.strip()),
            downloaded=convert_to_bytes(summary_html[4].select_one('.card-stats-number').text.strip()),
            total_traffic=convert_to_bytes(summary_html[5].select_one('.card-stats-number').text.strip())
        )

    def get_recharges_summary(self, year: int, month: int) -> RechargesSummary:
        """
        Este método devuelve un objeto de tipo RechargesSummary que contiene un resumen de recargas para el año y mes
        dados.

        :param year: Un entero que representa el año.
        :param month: Un entero que representa el mes.
        :return: Un objeto de tipo RechargesSummary que contiene un resumen de recargas para el año y mes dados.
        """
        summary_html = self.__get_summary_html_content(year, month, Action.GET_RECHARGES)
        return RechargesSummary(
            count=int(summary_html[0].select_one("input[name=count]").attrs["value"]),
            year_month_selected=summary_html[0].select_one("input[name=year_month_selected]").attrs["value"],
            total_import=str_to_float(summary_html[1].select_one('.card-stats-number').text.strip())
        )

    def get_transfers_summary(self, year: int, month: int) -> TransfersSummary:
        """
        Este método devuelve un objeto de tipo TransfersSummary que contiene un resumen de transferencias para el año y
        mes dados.

        :param year: Un entero que representa el año.
        :param month: Un entero que representa el mes.
        :return: Un objeto de tipo TransfersSummary que contiene un resumen de transferencias para el año y mes dados.
        """
        summary_html = self.__get_summary_html_content(year, month, Action.GET_TRANSFERS)
        return TransfersSummary(
            count=int(summary_html[0].select_one("input[name=count]").attrs["value"]),
            year_month_selected=summary_html[0].select_one("input[name=year_month_selected]").attrs["value"],
            total_import=str_to_float(summary_html[1].select_one('.card-stats-number').text.strip())
        )

    def get_quotes_paid_summary(self, year: int, month: int) -> QuotesPaidSummary:
        """
        Este método devuelve un objeto de tipo QuotesPaidSummary que contiene un resumen de cotizaciones pagadas para el
        año y mes dados.

        :param year: Un entero que representa el año.
        :param month: Un entero que representa el mes.
        :return: Un objeto de tipo QuotesPaidSummary que contiene un resumen de cotizaciones pagadas para el año y mes
        dados.
        """
        summary_html = self.__get_summary_html_content(year, month, Action.GET_QUOTES_PAID)
        return QuotesPaidSummary(
            count=int(summary_html[0].select_one("input[name=count]").attrs["value"]),
            year_month_selected=summary_html[0].select_one("input[name=year_month_selected]").attrs["value"],
            total_import=str_to_float(summary_html[1].select_one('.card-stats-number').text.strip())
        )

    def get_connections(
            self, year: int, month: int, summary: ConnectionsSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[Connection]:
        """
        Obtiene las conexiones a internet para un año y mes específicos.

        :param year: El año para el que se desea obtener las conexiones a internet.
        :param month: El mes para el que se desea obtener las conexiones a internet.
        :param summary: Un objeto ConnectionsSummary que contiene información resumida sobre las conexiones a internet
        para el año y mes seleccionados. Si no se especifica, se obtiene automáticamente con la función
        get_connections_summary().
        :param large: Un entero que indica el número máximo de conexiones a internet que se deben recuperar por página.
        El valor predeterminado es 0, lo que significa que se recuperarán todas las conexiones a internet.
        :param _reversed: Un booleano que indica si se deben devolver las conexiones a internet en orden inverso. El
        valor predeterminado es False.

        :return: Una lista de objetos Connection que representan las conexiones a internet para el año y mes
        seleccionados.

        :raises ValueError: Si el año o mes proporcionados no son válidos o si no se pueden obtener las conexiones a
        internet.
        """
        summary = self.get_connections_summary(year, month) if not summary else summary
        connections = []
        if summary.count != 0:
            rows = self.__get_action_per_page_as_row_html(
                Action.GET_CONNECTIONS, summary.year_month_selected, summary.count, large, _reversed
            )
            if rows:
                for row in rows:
                    connections.append(
                        Connection(
                            start_session=parse_datetime(row.select("td")[0].text.strip()),
                            end_session=parse_datetime(row.select("td")[1].text.strip()),
                            duration=time_string_to_seconds(row.select("td")[2].text.strip()),
                            uploaded=convert_to_bytes(row.select("td")[3].text.strip()),
                            downloaded=convert_to_bytes(row.select("td")[4].text.strip()),
                            import_=str_to_float(row.select("td")[5].text.strip())
                        )
                    )
        return connections

    def get_recharges(
            self, year: int, month: int, summary: RechargesSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[Recharge]:
        """
        Obtiene una lista de recargas realizadas en un año y mes específicos.

        :param year: El año para el que se desea obtener las recargas.
        :param month: El mes para el que se desea obtener las recargas.
        :param summary: Un objeto RechargesSummary que contiene información resumida sobre las recargas para el año y
        mes seleccionados. Si no se especifica, se obtiene automáticamente con la función get_recharges_summary().
        :param large: Un entero que indica el número máximo de recargas que se deben recuperar por página. El valor
        predeterminado es 0, lo que significa que se recuperarán todas las recargas.
        :param _reversed: Un booleano que indica si se deben devolver las recargas en orden inverso. El valor
        predeterminado es False.

        :return: Una lista de objetos Recharge que representan las recargas realizadas para el año y mes seleccionados.

        :raises ValueError: Si el año o mes proporcionados no son válidos o si no se pueden obtener las recargas.
        """
        summary = self.get_recharges_summary(year, month) if not summary else summary
        recharges = []
        if summary.count != 0:
            rows = self.__get_action_per_page_as_row_html(
                Action.GET_RECHARGES, summary.year_month_selected, summary.count, large, _reversed
            )
            if rows:
                for row in rows:
                    recharges.append(
                        Recharge(
                            date=parse_datetime(row.select("td")[0].text.strip()),
                            import_=str_to_float(row.select("td")[1].text.strip()),
                            channel=row.select("td")[2].text.strip(),
                            type_=row.select("td")[3].text.strip()
                        )
                    )
        return recharges

    def get_transfers(
            self, year: int, month: int, summary: TransfersSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[Transfer]:
        """
        Obtiene una lista de transferencias realizadas en un año y mes específicos.

        :param year: El año para el que se desea obtener las transferencias.
        :param month: El mes para el que se desea obtener las transferencias.
        :param summary: Un objeto TransfersSummary que contiene información resumida sobre las transferencias para el
        año y mes seleccionados. Si no se especifica, se obtiene automáticamente con la función get_transfers_summary().
        :param large: Un entero que indica el número máximo de transferencias que se deben recuperar por página. El
        valor predeterminado es 0, lo que significa que se recuperarán todas las transferencias.
        :param _reversed: Un booleano que indica si se deben devolver las transferencias en orden inverso. El valor
        predeterminado es False.

        :return: Una lista de objetos Transfer que representan las transferencias realizadas para el año y mes
        seleccionados.

        :raises ValueError: Si el año o mes proporcionados no son válidos o si no se pueden obtener las transferencias.
        """
        summary = self.get_transfers_summary(year, month) if not summary else summary
        transfers = []
        if summary.count != 0:
            rows = self.__get_action_per_page_as_row_html(
                Action.GET_TRANSFERS, summary.year_month_selected, summary.count, large, _reversed
            )
            if rows:
                for row in rows:
                    transfers.append(
                        Transfer(
                            date=parse_datetime(row.select("td")[0].text.strip()),
                            import_=str_to_float(row.select("td")[1].text.strip()),
                            destiny_account=row.select("td")[2].text.strip()
                        )
                    )
        return transfers

    def get_quotes_paid(
            self, year: int, month: int, summary: QuotesPaidSummary = None, large: int = 0, _reversed: bool = False
    ) -> list[QuotePaid]:
        """
        Obtiene una lista de cotizaciones pagadas realizadas en un año y mes específicos.

        :param year: El año para el que se desea obtener las cotizaciones pagadas.
        :param month: El mes para el que se desea obtener las cotizaciones pagadas.
        :param summary: Un objeto QuotesPaidSummary que contiene información resumida sobre las cotizaciones pagadas
        para el año y mes seleccionados. Si no se especifica, se obtiene automáticamente con la función
        get_quotes_paid_summary().
        :param large: Un entero que indica el número máximo de cotizaciones pagadas que se deben recuperar por página.
        El valor predeterminado es 0, lo que significa que se recuperarán todas las cotizaciones pagadas.
        :param _reversed: Un booleano que indica si se deben devolver las cotizaciones pagadas en orden inverso. El
        valor predeterminado es False.

        :return: Una lista de objetos QuotePaid que representan las cotizaciones pagadas realizadas para el año y mes
        seleccionados.

        :raises ValueError: Si el año o mes proporcionados no son válidos o si no se pueden obtener las cotizaciones
        pagadas.
        """
        summary = self.get_quotes_paid_summary(year, month) if not summary else summary
        quotes_paid = []
        if summary.count != 0:
            rows = self.__get_action_per_page_as_row_html(
                Action.GET_QUOTES_PAID, summary.year_month_selected, summary.count, large, _reversed
            )
            if rows:
                for row in rows:
                    quotes_paid.append(
                        QuotePaid(
                            date=parse_datetime(row.select("td")[0].text.strip()),
                            import_=str_to_float(row.select("td")[1].text.strip()),
                            channel=row.select("td")[2].text.strip(),
                            type_=row.select("td")[3].text.strip(),
                            office=row.select("td")[4].text.strip()
                        )
                    )
        return quotes_paid
