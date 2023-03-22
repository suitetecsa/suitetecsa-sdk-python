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

from datetime import date
import os
import re
import bs4
import requests
import logging

from requests import Session
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from json import dump, load
from py_suitetecsa_sdk.core.exceptions import ChangePasswordException, ConnectionException,\
    GetInfoException, LoginException, LogoutException, InvalidMethod, NotLoggedIn, PreLoginException, RechargeException, SessionLoadException, TransferException

from py_suitetecsa_sdk.utils import Action, Portal, api_response, build_summary
from py_suitetecsa_sdk.utils.parser import parse_errors


logging.basicConfig(
    level=logging.INFO,
    format="%(name)s :: %(levelname)s :: %(message)s"
)
logger = logging.getLogger()


class NautaSession:

    __headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'es-419,es;q=0.6',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    __domain: str = b'secure.etecsa.net'
    __base_url: dict = {
        Portal.CONNECT: f'https://{__domain.decode()}:8443/',
        Portal.USER: 'https://www.portal.nauta.cu/'
    }
    __portals_urls = {
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

    __logged_in: bool = False
    __user_information: dict = None
    __login_action: str
    session: Session
    __username: str
    __password: str
    __wlanuserip: str = None
    __CSRFHW: str = None
    __csrf: str = None
    __ATTRIBUTE_UUID: str

    def __init__(
            self,
            portal_manager: Portal = Portal.CONNECT,
            use_api_response: bool = False
    ) -> None:
        self.portal_manager = portal_manager
        self.use_api_response = use_api_response
        # self.session.headers = self.__headers

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, value) -> None:
        self.__username = value

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value) -> None:
        self.__password = value

    @property
    def credentials(self) -> tuple[str]:
        return self.__username, self.__password

    @credentials.setter
    def credentials(self, value: tuple[str]) -> None:
        self.__username, self.__password = value

    def __build_url(
        self, action: Action,
        get_action: bool = False,
        sub_action: str = None,
        year_month_selected: str = None,
        count: int = None,
        page: int = None
    ) -> str | None:
        """
        Construye una url en dependecia de los parametros pasados.

        :param action: Acción a realizar
        :type action: Action
        :param get_action: confirma o no la recuperacion de una lista
        :type get_action: bool
        :param sub_action: paso en la recuperacion de la lista
        :type sub_action: str
        :param year_month_selected: mes-anno a consultar
        :type year_month_selected: str
        :param count_or_page: cantidad de resultados o paginas a consultar
        :type count_or_page: int

        :return: La url creada
        :type: str
        """
        if action == Action.CHECK_CONNECTION:
            return self.__portals_urls[self.portal_manager][action]
        elif not get_action:
            return f'{self.__base_url[self.portal_manager]}'\
                   f'{self.__portals_urls[self.portal_manager][action]}'
        else:
            url = f'{self.__base_url[self.portal_manager]}'\
                  f'{self.__portals_urls[self.portal_manager][action][sub_action]}'
            match sub_action:
                case 'base' | 'summary':
                    return url
                case 'list':
                    if not year_month_selected:
                        pass
                    if not count:
                        pass
                    else:
                        return f'{url}{year_month_selected}/{count}'\
                            if not page \
                            else f'{url}{year_month_selected}/{count}/{page}'

    def __check_errors(
            self, response: requests.Response,
            exc: Exception,
            msg: str,
            find_errors: bool = True
    ) -> bs4.BeautifulSoup | None:
        """
        Comprueba si la solicitud fue exitosa y si hay algún error en la
        respuesta.

        :param response: respuesta de la solicitud http
        :type response: requests.Response
        :param action: Acción a realizar
        :type action: str
        """
        if not response.ok:
            raise exc(
                f"{msg}: {response.status_code} :: {response.reason}"
            )

        soup = bs4.BeautifulSoup(response.text, 'html5lib')

        if find_errors:
            error = parse_errors(soup, self.portal_manager)
            if error:
                raise exc(
                    f'{msg} :: {error}'
                )

        return soup

    def __post_action(
            self, data: dict,
            action: Action,
            url: str = None
    ) -> requests.Response | None:
        if not url:
            url = self.__build_url(action)
        logger.info(f'post action to {url}')
        return self.session.post(url, data=data)

    def _get_inputs(self, form_soup: bs4.Tag) -> dict:
        """
        Crea un dictado `name`: `value` de cada atributo
        del formulario html

        :param form_soup: Formulario HTML
        :type form_soup: bs4.Tag

        :return: El dictado creado
        :type: dict
        """
        return {
            _["name"]: _.get("value", default=None)
            for _ in form_soup.select("input[name]")
        }

    def is_connected(self) -> bool:
        """
        Comprueba si ya existe una conexion a internet

        :return: Resultado de la comprobacion
        :type: bool
        """
        r = requests.get(
            self.__build_url(Action.CHECK_CONNECTION)
        )
        return self.__domain not in r.content

    def __get_csrf(
            self, action: Action,
            url: str = None,
            soup: bs4.BeautifulSoup = None
    ) -> str | None:
        """
        Obtiene el token CSRF de la página

        :param cls: la clase desde la que se llama al método
        :param action: La acción que desea realizar
        :type action: str
        :param session: UserPortalSession = Ninguno
        :type session: UserPortalSession
        :param url: La URL a la que enviar la solicitud
        :type url: str
        :param soup: bs4.BeautifulSoup = Ninguno
        :type soup: bs4.BeautifulSoup
        :return: El token csrf
        """
        if not url:
            url = self.__build_url(action)
        r = self.session.get(url)
        soup = self.__check_errors(
            r,
            ConnectionException,
            'Fail to obtain csrf token'
        )
        return soup.select_one('input[name=csrf]').attrs["value"]

    def get_captcha(self) -> bytes | None:
        """
        Obtiene la imagen captcha del portal.

        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :return: La imagen captcha.
        """
        logger.debug('Obtaining the captcha image')
        response = self.session.get(
            'https://www.portal.nauta.cu/captcha/?'
        )
        self.__check_errors(
            response=response,
            exc=ConnectionException,
            msg='Fail to obtain the captcha image',
            find_errors=False
        )
        logger.debug('Obtained the captcha image')
        return response.content

    def __init_connect(self) -> dict | None:
        """
        Inicializa la session con el portal cautivo de nauta

        :return: Atributos esenciales para la sesion o None
        :type: dict | None
        """
        logger.debug(
            f'Action get to {self.__build_url(Action.CHECK_CONNECTION)}'
        )
        soup = self.__check_errors(
            response=self.session.get(
                self.__build_url(Action.CHECK_CONNECTION)
            ),
            exc=PreLoginException,
            msg='Fail to create session',
            find_errors=False
        )
        action = soup.form["action"]
        data = self._get_inputs(soup)

        logger.debug(f'Action post to {action}')
        soup = self.__check_errors(
            response=self.session.post(action, data),
            exc=PreLoginException,
            msg='Fail to create session',
            find_errors=False
        )
        form_soup = soup.select_one("#formulario")
        self.__login_action = form_soup["action"]
        data = self._get_inputs(form_soup)

        self.__CSRFHW = data["CSRFHW"]
        logger.debug(f'Obtained the csrfhw token: {self.__CSRFHW}')
        self.__wlanuserip = data["wlanuserip"]
        logger.debug(f'Obtained the wlanuserip parameter: {self.__wlanuserip}')

        return None, None

    def __init_user(self) -> dict | None:
        self.session.headers = self.__headers
        logger.debug(
            f'Action get to {self.__build_url(Action.LOGIN)}'
        )
        soup = self.__check_errors(
            response=self.session.get(
                self.__build_url(Action.LOGIN)
            ),
            exc=PreLoginException,
            msg='Fail to create session'
        )

        self.__csrf = self.__get_csrf(
            action=Action.LOGIN,
            soup=soup
        )
        logger.debug(f'Obtained csrf token: {self.__csrf}')

        return None, None

    @api_response
    def init(self) -> dict | None:
        self.session = Session()
        match self.portal_manager:
            case Portal.CONNECT:
                return self.__init_connect()
            case Portal.USER:
                return self.__init_user()
            case _:
                raise PreLoginException

    def __get_information_connect(self) -> tuple[Action, dict]:
        """
        Obtiene la informacion de la cuenta ofrecida por
        el protal cautivo

        :return: informacion obtenida
        :type: dict
        """
        if not self.__CSRFHW or not self.__wlanuserip:
            self.init()
        soup = self.__check_errors(
            response=self.session.post(
                self.__build_url(
                    action=Action.LOAD_USER_INFORMATION
                ),
                {
                    'username': self.__username,
                    'password': self.__password,
                    'wlanuserip': self.__wlanuserip,
                    'CSRFHW': self.__CSRFHW,
                    'lang': ''
                }
            ),
            exc=GetInfoException,
            msg='Fail to obtain user information'
        )
        keys = [
            "account_status",
            "credit",
            "expiration_date",
            "access_areas",
            "from",
            "to",
            "time"
        ]
        __data = {
            'account_info': {
                keys[count]: value.text.strip()
                for count, value in enumerate(soup.select(
                    '#sessioninfo > tbody > tr > :not(td.key)'
                ))
            },
            'lasts_connections': [
                {
                    keys[count+4]: value.text.strip()
                    for count, value in enumerate(tr.select(
                        'td'
                    ))
                } for tr in soup.select(
                    '#sesiontraza > tbody > tr'
                )
            ]
        }
        return Action.LOAD_USER_INFORMATION, __data

    def __get_information_user(
            self, soup: bs4.BeautifulSoup = None
    ) -> tuple[Action, dict]:
        keys = [
            'username', 'blocking_date', 'date_of_elimination',
            'account_type', 'service_type', 'credit', 'time',
            'mail_account', 'offer', 'monthly_fee', 'download_speeds',
            'upload_speeds', 'phone', 'link_identifiers',
            'link_status', 'activation_date', 'blocking_date_home',
            'date_of_elimination_home', 'quote_paid', 'voucher', 'debt'
        ]
        if not self.__logged_in:
            raise GetInfoException(
                'This session is not logged in'
            )
        if not soup:
            soup = self.__check_errors(
                response=self.session.get(
                    self.__build_url(Action.LOAD_USER_INFORMATION)
                ), exc=GetInfoException,
                msg='Fail to get information'
            )
        __user_information = {}
        for _index, attr in enumerate(
            soup.select_one('.z-depth-1').select('.m6')
        ):
            __user_information = {
                **__user_information,
                keys[_index]: attr.select_one('p').text.strip()
            }
        __data = {'user_information': __user_information} \
            if self.use_api_response \
            else __user_information
        return Action.LOAD_USER_INFORMATION, __data

    @api_response
    def get_user_information(self) -> dict:
        match self.portal_manager:
            case Portal.CONNECT:
                return self.__get_information_connect()
            case Portal.USER:
                return self.__get_information_user()

    def __connect(self) -> tuple[Action, None]:
        """
        Inicia la conexion a internet

        :return: Dictado que contiene el atributo `ATTRIBUTE_UUID`
        necesario para desconectar la cuenta or None
        :type: dict | None
        """
        if not self.__CSRFHW or not self.__wlanuserip:
            self.init()
        if not self.__username or not self.__password:
            pass
        r = self.session.post(
            self.__login_action,
            {
                "CSRFHW": self.__CSRFHW,
                "wlanuserip": self.__wlanuserip,
                "username": self.__username,
                "password": self.__password
            }
        )
        if not r.ok:
            pass
        if "online.do" not in r.url:
            pass
        self.__ATTRIBUTE_UUID = re.search(
            r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', r.text).group(1)
        self.__logged_in = True
        return Action.LOGIN, None

    def __login(self, captcha_code: str) -> tuple[Action, dict]:
        if not captcha_code:
            raise LoginException(
                'Captca code is required'
            )
        soup = self.__check_errors(
            response=self.__post_action(
                {
                    'csrf': self.__csrf,
                    'login_user': self.__username,
                    'password_user': self.__password,
                    'captcha': captcha_code.upper(),
                    'btn_submit': ''
                },
                Action.LOGIN
            ),
            exc=LoginException,
            msg='Fail to login'
        )
        self.__logged_in = True
        __data = {
            'logged_in': True,
            **self.__get_information_user(soup)[1]
        }
        return Action.LOGIN, __data

    @api_response
    def login(self, captcha_code: str = None) -> dict:
        match self.portal_manager:
            case Portal.CONNECT:
                return self.__connect()
            case Portal.USER:
                return self.__login(captcha_code)

    @api_response
    def recharge(self, recharge_code: str) -> dict | None:
        """
        Recarga el saldo de la cuenta asociada a la session

        :param cls: La clase en sí
        :param session: El objeto de sesión que creó anteriormente
        :type session: UserPortalSession
        :param recharge_code: El código de recarga que desea utilizar
        :type recharge_code: str
        """
        data = {
            'csrf': self.__get_csrf(Action.RECHARGE),
            'recharge_code': recharge_code,
            'btn_submit': ''
        }
        soup = self.__check_errors(
            response=self.__post_action(
                data=data,
                action=Action.RECHARGE
            ),
            exc=RechargeException,
            msg='Fail to recharge the account credit'
        )
        return Action.RECHARGE, None

    @api_response
    def transfer(
            self, account_to_transfer: str,
            mount_to_transfer: float,
            nauta_hogar_paid: bool = False
    ) -> dict | None:
        """
        Transfiere una cantidad de dinero de una cuenta a otra

        :param cls: La clase que está llamando al método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param mount_to_transfer: La cantidad de dinero a transferir
        :type mount_to_transfer: str
        :param account_to_transfer: La cuenta a la que transferir el dinero
        :type account_to_transfer: str
        :param password: La contraseña de la cuenta para transferir el monto
        :type password: str
        """
        action = Action.TRANSFER if not nauta_hogar_paid \
            else Action.NAUTA_HOGAR_PAID
        data = {
            'csrf': self.__get_csrf(action=action),
            'transfer': f'{mount_to_transfer:.2f}'.replace('.', ','),
            'password_user': self.__password,
            'action': 'checkdata'
        }
        if not nauta_hogar_paid:
            data["id_cuenta"] = account_to_transfer

        soup = self.__check_errors(
            response=self.__post_action(
                data=data,
                action=action
            ),
            exc=TransferException,
            msg='Fail to transfer'
        )
        return Action.TRANSFER, None

    @api_response
    def change_password(self, new_password: str) -> dict | None:
        """
        Cambia la contraseña del usuario

        :param cls: La clase desde la que se llama al método
        :param session: El objeto de sesión que creó cuando inició sesión
        :type session: UserPortalSession
        :param old_password: la vieja contraseña
        :type old_password: str
        :param new_password: La nueva contraseña que desea establecer
        :type new_password: str
        """
        data = {
            'csrf': self.__get_csrf(action=Action.CHANGE_PASSWORD),
            'old_password': self.__password,
            'new_password': new_password,
            'repeat_new_password': new_password,
            'btn_submit': ''
        }
        soup = self.__check_errors(
            response=self.__post_action(
                data=data,
                action=Action.CHANGE_PASSWORD
            ),
            exc=ChangePasswordException,
            msg='Fail to change password'
        )
        return Action.CHANGE_PASSWORD, None

    @api_response
    def change_email_password(
            self, old_password: str,
            new_password: str
    ) -> dict | None:
        """
        Cambia la contraseña de la cuenta de correo electrónico asociada con la
        cuenta del usuario

        :param cls: La clase desde la que se llama al método
        :param session: El objeto de sesión que creó cuando inició sesión
        :type session: UserPortalSession
        :param old_password: La contraseña actual de la cuenta de correo
        electrónico
        :type old_password: str
        :param new_password: La nueva contraseña que desea establecer
        :type new_password: str
        """
        data = {
            'csrf': self.__get_csrf(action=Action.CHANGE_EMAIL_PASSWORD),
            'old_password': old_password,
            'new_password': new_password,
            'repeat_new_password': new_password,
            'btn_submit': ''
        }
        soup = self.__check_errors(
            response=self.__post_action(
                data=data,
                action=Action.CHANGE_EMAIL_PASSWORD
            ),
            exc=ChangePasswordException,
            msg='Fail to change password'
        )
        return Action.CHANGE_EMAIL_PASSWORD, None

    def __get_action(
            self, year: int,
            month: int,
            action: Action
    ) -> bs4.Tag:
        """
        Según el valor del parámetro (action) recupera las filas de una tabla
        html de (conexiones, recargas, transferencias, cuotas pagadas) y
        la devuelve si existe

        :param cls: la clase que está llamando al método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del mes del que desea obtener los datos
        :type year: int
        :param month: El mes del que desea obtener los datos
        :type month: int
        :param action: La acción a realizar
        :type action: str
        :return: Una lista de trs
        """
        __lists = {
            Action.GET_CONNECTIONS: 'service_detail',
            Action.GET_RECHARGES: 'recharge_detail',
            Action.GET_QUOTES_PAID: 'nautahogarpaid_detail',
            Action.GET_TRANSFERS: 'transfer_detail'
        }
        __err_msgs = {
            Action.GET_CONNECTIONS:
            'Fail to obtain connections list',
            Action.GET_RECHARGES:
            'Fail to obtain recharges list',
            Action.GET_QUOTES_PAID:
            'Fail to obtain quotes paid list',
            Action.GET_TRANSFERS:
            'Fail to obtain transfers list'
        }
        __year_month = f'{year}-{month:02}'

        soup = self.__check_errors(
            response=self.__post_action(
                data={
                    'csrf': self.__get_csrf(
                        action=action,
                        url=self.__build_url(
                            action=action,
                            get_action=True,
                            sub_action='base'
                        )
                    ),
                    'year_month': __year_month,
                    'list_type': __lists[action]
                },
                action=action,
                url=self.__build_url(
                    action=action,
                    get_action=True,
                    sub_action='summary'
                )
            ),
            exc=GetInfoException,
            msg=__err_msgs[action]
        )
        return soup.select_one('#content').select('.card-content')

    def __get_tbody(self, url: str) -> bs4.Tag:
        """
        obtiene y devuelve la seccion tbody de la tabla html

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param url: url de la consulta
        :type url: str

        :return: un objeto bs4.Tag (seccion tbody de la tabla)
        """
        soup = self.__check_errors(
            response=self.session.get(
                url
            ),
            exc=GetInfoException,
            msg='Fail to obtain information'
        )
        return soup.select_one(
            '.responsive-table > tbody'
        )

    def __parse_action_rows(
            self, action: Action,
            year_month_selected: str,
            count: int
    ) -> list[bs4.Tag]:
        """
        obtiene una tabla y devuelve una lista de objetos bs4.Tag;
        uno por cada fila de la tabla

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param action: acciones a consultar
        :type action: int
        :param year_month_selected: mes y anno seleccionados
        :type year_month_selected: str
        :param count: cantidad de acciones resultantes de la consulta
        :type count: int

        :return: lista de objetos bs4.Tag (filas de la tabla)
        """
        __row_list = []
        __pages = (
            count // 14 + 1
            if count / 14 > count // 14
            else count // 14
        ) if count > 14 else 1

        for __page in range(1, __pages + 1):
            page = __page if __page != 1 else None
            __url = self.__build_url(
                action=action,
                get_action=True,
                sub_action='list',
                year_month_selected=year_month_selected,
                count=count,
                page=page
            )
            logger.info(f'post action to {__url}')
            __tbody = self.__get_tbody(url=__url)
            if __tbody:
                __row_list.extend(
                    __tbody.select('tr')
                )
        return __row_list

    @api_response
    def __get_connections_summary(
            self, year: int,
            month: int
    ) -> dict:
        """
        Obtiene los datos interesantes del sumario de conexiones

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto ConnectionsSummary con la informacion interesante
        del sumario de conexiones
        """
        [
            __connections, __total_time, __total_import,
            __uploaded, __downloaded, __total_traffic
        ] = self.__get_action(year=year, month=month, action=Action.GET_CONNECTIONS)

        __summary = {
            'count': int(__connections.select_one('input[name=count]').attrs['value']),
            'year_month_selected': __connections.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            'total_time': __total_time.select_one('.card-stats-number').text.strip(),
            'total_import': __total_import.select_one('.card-stats-number').text.strip(),
            'uploaded': __uploaded.select_one('.card-stats-number').text.strip(),
            'downloaded': __downloaded.select_one('.card-stats-number').text.strip(),
            'total_traffic': __total_traffic.select_one('.card-stats-number').text.strip()
        }

        __data = {'connections_summary': __summary} \
            if self.use_api_response \
            else __summary
        return Action.GET_CONNECTIONS, __data

    @api_response
    def get_connections(
            self, year: int, month: int
    ) -> dict:
        """
        Obtiene las conexiones del usuario en un mes y año dado

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del que desea obtener los datos
        :type year: int
        :param month: int: el mes del que desea obtener los datos
        :type month: int
        :return: Una lista de objetos de conexión.
        """
        __summary = self.__get_connections_summary(
            year=year,
            month=month
        )
        __summary = __summary['connections_summary'] \
            if self.use_api_response else __summary
        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_CONNECTIONS,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count']
            )
            __data = None
            if __rows:
                __connections = []
                for __row in __rows:
                    [
                        start_session_tag, end_session_tag, duration_tag,
                        upload_tag, download_tag, import_tag
                    ] = __row.select('td')
                    __connections.append(
                        {
                            'start_session': start_session_tag.text.strip(),
                            'end_session': end_session_tag.text.strip(),
                            'duration': duration_tag.text.strip(),
                            'uploaded': upload_tag.text.strip(),
                            'downloaded': download_tag.text.strip(),
                            'import': import_tag.text.strip()
                        }
                    )
                __data = {
                    'connections_summary': __summary,
                    'connections': __connections
                }
        else:
            __data = {
                'connections_summary': __summary,
                'connections': []
            }

        return Action.GET_CONNECTIONS, __data

    @api_response
    def __get_recharges_summary(
            self, year: int,
            month: int
    ) -> dict:
        """
        Obtiene los datos interesantes del sumario de conexiones

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto ConnectionsSummary con la informacion interesante
        del sumario de conexiones
        """
        __recharges, __total_import = self.__get_action(
            year=year,
            month=month,
            action=Action.GET_RECHARGES
        )

        __summary = {
            'count': int(__recharges.select_one('input[name=count]').attrs['value']),
            'year_month_selected': __recharges.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            'total_import': __total_import.select_one(
                '.card-stats-number'
            ).text.strip()
        }

        __data = {'recharges_summary': __summary} \
            if self.use_api_response \
            else __summary
        return Action.GET_RECHARGES, __data

    @api_response
    def get_recharges(
            self, year: int, month: int
    ) -> dict:
        """
        Obtiene las conexiones del usuario en un mes y año dado

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del que desea obtener los datos
        :type year: int
        :param month: int: el mes del que desea obtener los datos
        :type month: int
        :return: Una lista de objetos de conexión.
        """
        __summary = self.__get_recharges_summary(
            year=year,
            month=month
        )
        __summary = __summary['recharges_summary'] \
            if self.use_api_response else __summary
        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_RECHARGES,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count']
            )

            if __rows:
                __recharges = []
                for __row in __rows:
                    __date, __import, __channel, __type = __row.select('td')
                    __recharges.append(
                        {
                            'date': __date.text.strip(),
                            'import': __import.text.strip(),
                            'channel': __channel.text.strip(),
                            'type': __type.text.strip()
                        }
                    )
                __data = {
                    'recharges_summary': __summary,
                    'recharges': __recharges
                }
        else:
            __data = {
                'recharges_summary': __summary,
                'recharges': []
            }

        return Action.GET_RECHARGES, __data

    @api_response
    def __get_transfers_summary(
            self, year: int,
            month: int
    ) -> dict:
        """
        Obtiene los datos interesantes del sumario de conexiones

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto ConnectionsSummary con la informacion interesante
        del sumario de conexiones
        """
        __transfers, __total_import = self.__get_action(
            year=year,
            month=month,
            action=Action.GET_TRANSFERS
        )

        __summary = {
            'count': int(__transfers.select_one('input[name=count]').attrs['value']),
            'year_month_selected': __transfers.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            'total_import': __total_import.select_one(
                '.card-stats-number'
            ).text.strip()
        }

        __data = {'transfers_summary': __summary} \
            if self.use_api_response \
            else __summary
        return Action.GET_TRANSFERS, __data

    @api_response
    def get_transfers(
            self, year: int, month: int
    ) -> dict:
        """
        Obtiene las conexiones del usuario en un mes y año dado

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del que desea obtener los datos
        :type year: int
        :param month: int: el mes del que desea obtener los datos
        :type month: int
        :return: Una lista de objetos de conexión.
        """
        __summary = self.__get_transfers_summary(
            year=year,
            month=month
        )
        __summary = __summary['transfers_summary'] \
            if self.use_api_response else __summary
        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_TRANSFERS,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count']
            )

            if __rows:
                __transfers = []
                for __row in __rows:
                    __date, __import, __destiny_account = __row.select('td')
                    __transfers.append(
                        {
                            'date': __date.text.strip(),
                            'import': __import.text.strip(),
                            'destiny_account': __destiny_account.text.strip()
                        }
                    )
                __data = {
                    'transfers_summary': __summary,
                    'transfers': __transfers
                }
        else:
            __data = {
                'transfers_summary': __summary,
                'transfers': []
            }

        return Action.GET_TRANSFERS, __data

    @api_response
    def __get_quotes_paid_summary(
            self, year: int,
            month: int
    ) -> dict:
        """
        Obtiene los datos interesantes del sumario de conexiones

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto ConnectionsSummary con la informacion interesante
        del sumario de conexiones
        """
        __quotes_paid, __total_import = self.__get_action(
            year=year,
            month=month,
            action=Action.GET_QUOTES_PAID
        )

        __summary = {
            'count': int(__quotes_paid.select_one('input[name=count]').attrs['value']),
            'year_month_selected': __quotes_paid.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            'total_import': __total_import.select_one(
                '.card-stats-number'
            ).text.strip()
        }

        __data = {'quotes_paid_summary': __summary} \
            if self.use_api_response \
            else __summary
        return Action.GET_QUOTES_PAID, __data

    @api_response
    def get_quotes_paid(
            self, year: int, month: int
    ) -> dict:
        """
        Obtiene las conexiones del usuario en un mes y año dado

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del que desea obtener los datos
        :type year: int
        :param month: int: el mes del que desea obtener los datos
        :type month: int
        :return: Una lista de objetos de conexión.
        """
        __summary = self.__get_quotes_paid_summary(
            year=year,
            month=month
        )
        __summary = __summary['quotes_paid_summary'] \
            if self.use_api_response else __summary

        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_QUOTES_PAID,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count']
            )

            if __rows:
                __quotes_paid = []
                for __row in __rows:
                    __date, __import, __channel, __type, __office = __row.select(
                        'td')
                    __quotes_paid.append(
                        {
                            'date': __date.text.strip(),
                            'import': __import.text.strip(),
                            'channel': __channel.text.strip(),
                            'type': __type.text.strip(),
                            'office': __office.text.strip()
                        }
                    )
                __data = {
                    'quotes_paid_summary': __summary,
                    'quotes_paid': __quotes_paid
                }
        else:
            __data = {
                'quotes_paid_summary': __summary,
                'quotes_paid': []
            }

        return Action.GET_QUOTES_PAID, __data

    @api_response
    def get_lasts(self, action: Action, large: int = 5) -> dict:
        __actions = {
            Action.GET_CONNECTIONS: self.get_connections,
            Action.GET_RECHARGES: self.get_recharges,
            Action.GET_TRANSFERS: self.get_transfers,
            Action.GET_QUOTES_PAID: self.get_quotes_paid
        }
        __actions_keys = {
            Action.GET_CONNECTIONS: 'connections',
            Action.GET_RECHARGES: 'recharges',
            Action.GET_TRANSFERS: 'transfers',
            Action.GET_QUOTES_PAID: 'quotes_paid'
        }
        __summary_keys = {
            Action.GET_CONNECTIONS: 'connections_summary',
            Action.GET_RECHARGES: 'recharges_summary',
            Action.GET_TRANSFERS: 'transfers_summary',
            Action.GET_QUOTES_PAID: 'quotes_paid_summary'
        }
        __year = date.today().year
        __month = date.today().month
        __lasts = []
        actions = __actions[action](year=__year, month=__month)[
            __actions_keys[action]]
        if actions:
            __lasts.extend(actions)
        while len(__lasts) < large:
            if __month == 1:
                __month = 12
                __year -= 1
            else:
                __month -= 1
            actions = __actions[action](year=__year, month=__month)[
                __actions_keys[action]]
            if actions:
                __lasts.extend(actions)
        return action, {
            __summary_keys[action]: build_summary(
                action=action,
                actions=__lasts[:large]
            ),
            __actions_keys[action]: __lasts[:large]
        }

    def disconnect(self) -> None:
        """
        Desconecta la cuenta de internet

        :return: Dictado con la info de estado de la operacion
        or None
        :type: dict | None
        """
        if not self.__logged_in:
            if self.use_api_response:
                return {
                    "status": "error",
                    "reason": "reason"
                }
            else:
                pass

        r = self.session.get(
            f'{self.__logout_url}',
            params={
                'username': self.__username,
                'wlanuserip': self.__wlanuserip,
                'CSRFHW': self.__CSRFHW,
                'ATTRIBUTE_UUID': self.__ATTRIBUTE_UUID
            }
        )

        if not r.ok:
            if self.use_api_response:
                return {
                    "status": "error",
                    "status_code": r.status_code,
                    "reason": r.reason
                }
            else:
                pass
        if "SUCCESS" not in r.text:
            if self.use_api_response:
                return {
                    "status": "error",
                    "reason": "reason"
                }
            else:
                pass

        self.__logged_in = False
        self.__ATTRIBUTE_UUID = str()

        return {
            "status": "success",
            "logged_in": False
        } if self.use_api_response else None

    @api_response
    def get_remaining_time(self, in_seconds: bool = False) -> dict | str | int:
        """
        Obtiene el tiempo restante de la cuenta conectada

        :param in_seconds: Define si el tiempo restante se devolvera
        en formato `hh:MM:ss` (str) o segundos (int)
        :type in_seconds: bool

        :return: Un dictado con el tiempo restante de la cuenta y otra
        informacion util o solo el tiempo restante en formato de string
        o integer
        :type: dict | str | int
        """
        __remainig_seconds: int
        soup = self.__check_errors(
            response=self.session.post(
                self.__query_url,
                {
                    'op': 'getLeftTime',
                    'username': self.__username,
                    'wlanuserip': self.__wlanuserip,
                    'CSRFHW': self.__CSRFHW,
                    'ATTRIBUTE_UUID': self.__ATTRIBUTE_UUID
                }
            ),
            exc=LogoutException,
            msg='Fail to logout',
            find_errors=False
        )

        hours, minutes, seconds = [int(number)
                                   for number in soup.text.strip().split(':')]
        remainig_time = soup.text.strip()
        __remainig_seconds = hours * 3600 + minutes * 60 + seconds \
            if in_seconds else None

        return Action.LOGOUT, {
            'remaining_time': remainig_time,
            'remaining_seconds': __remainig_seconds
        }

    @property
    def session_data(self) -> dict:
        if not self.__logged_in:
            raise NotLoggedIn(
                'This session is not logged_in'
            )
        if self.portal_manager != Portal.CONNECT:
            raise InvalidMethod(
                'This method is not valid for this portal'
            )
        return {
            'username': self.__username,
            'cookies': dict_from_cookiejar(self.session.cookies),
            'wlanuserip': self.__wlanuserip,
            'CSRFHW': self.__CSRFHW,
            'ATTRIBUTE_UUID': self.__ATTRIBUTE_UUID
        }

    @session_data.setter
    def session_data(self, value: dict) -> None:
        if self.portal_manager != Portal.CONNECT:
            raise InvalidMethod(
                'This method is not valid for this portal'
            )
        if self.__logged_in:
            raise SessionLoadException(
                'You are logged_in'
            )

        required_keys = [
            'username', 'cookies', 'wlanuserip', 'CSRFHW', 'ATTRIBUTE_UUID'
        ]
        for key in required_keys:
            if key not in value.keys():
                raise SessionLoadException(
                    f'Parameter {key} is required'
                )

        self.__username = value["username"]
        self.session.cookies = cookiejar_from_dict(value['cookies'])
        self.__wlanuserip = value['wlanuserip']
        self.__CSRFHW = value['CSRFHW']
        self.__ATTRIBUTE_UUID = value['ATTRIBUTE_UUID']
        self.__logged_in = True

    @api_response
    def save_connect_data_to_file(self, file_path: str) -> None:
        if os.path.exists(os.path.dirname(file_path)):
            with open(file_path, 'w') as file:
                dump(self.get_session_data(), file)
        return True, None

    def load_connect_data_from_file(self, file_path: str) -> None:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = load(file)
                self.set_connect_data(data)
        return True, None
