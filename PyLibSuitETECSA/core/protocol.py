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
from datetime import date
from typing import List, Any, Union

import bs4
import requests

from PyLibSuitETECSA.core.exception import GetInfoException, \
    TransferException, ChangePasswordException, LoginException, \
    RechargeException, PreLoginException, NotNautaHomeAccount, \
    LogoutException, NautaException
from PyLibSuitETECSA.core.models import Connection, Recharge, Transfer, \
    QuotePaid
from PyLibSuitETECSA.core.session import UserPortalSession, NautaSession
from PyLibSuitETECSA.core.utils import Action, find_errors, Portal


class UserPortal:
    # La URL base del portal.
    BASE_URL = "https://www.portal.nauta.cu/"

    # Un diccionario que contiene las URL de las acciones que se pueden
    # realizar en el portal.
    __url = {
        Action.LOGIN: f"{BASE_URL}user/login/es-es",
        Action.LOAD_USER_INFO: f"{BASE_URL}useraaa/user_info",
        Action.RECHARGE: f"{BASE_URL}useraaa/recharge_account",
        Action.CHANGE_PASSWORD: f"{BASE_URL}useraaa/change_password",
        Action.CHANGE_EMAIL_PASSWORD: f"{BASE_URL}email/change_password",
        Action.GET_CONNECTIONS: {
            "base": f"{BASE_URL}useraaa/service_detail/",
            "summary": f"{BASE_URL}useraaa/service_detail_summary/",
            "list": f"{BASE_URL}useraaa/service_detail_list/"
        },
        Action.GET_RECHARGES: {
            "base": f"{BASE_URL}useraaa/recharge_detail/",
            "summary": f"{BASE_URL}useraaa/recharge_detail_summary/",
            "list": f"{BASE_URL}useraaa/recharge_detail_list/"
        },
        Action.GET_TRANSFERS: {
            "base": f"{BASE_URL}useraaa/transfer_detail/",
            "summary": f"{BASE_URL}useraaa/transfer_detail_summary/",
            "list": f"{BASE_URL}useraaa/transfer_detail_list/",
        },
        Action.GET_QUOTES_FUND: {
            "base": f"{BASE_URL}useraaa/nautahogarpaid_detail/",
            "summary": f"{BASE_URL}useraaa/nautahogarpaid_detail_summary/",
            "list": f"{BASE_URL}useraaa/nautahogarpaid_detail_list/"
        },
        Action.LOGOUT: f"{BASE_URL}user/logout"
    }

    # Un diccionario que contiene las excepciones que se pueden generar
    # cuando se produce un error en el portal.
    __up_exceptions = {
        Action.LOAD_USER_INFO: GetInfoException,
        Action.RECHARGE: RechargeException,
        Action.TRANSFER: TransferException,
        Action.GET_CONNECTIONS: GetInfoException,
        Action.GET_RECHARGES: GetInfoException,
        Action.GET_QUOTES_FUND: GetInfoException,
        Action.GET_TRANSFERS: GetInfoException,
        Action.CHANGE_PASSWORD: ChangePasswordException,
        Action.CHANGE_EMAIL_PASSWORD: ChangePasswordException,
        Action.LOGIN: LoginException
    }

    # Un diccionario que contiene los atributos de la cuenta del usuario.
    __attrs = {
        "username": "usuario",
        "account_type": "tipo de cuenta",
        "service_type": "tipo de servicio",
        "credit": "saldo disponible",
        "time": "tiempo disponible de la cuenta",
        "mail_account": "cuenta de correo",
        "offer": "oferta",
        "monthly_fee": "cuota mensual",
        "download_speeds": "velocidad de bajada",
        "upload_speeds": "velocidad de subida",
        "phone": "teléfono",
        "link_identifiers": "identificador del enlace",
        "link_status": "estado del enlace",
        "activation_date": "fecha de activación",
        "blocking_date": "fecha de bloqueo",
        "date_of_elimination": "fecha de eliminación",
        "blocking_date_home": "fecha de bloqueo",
        "date_of_elimination_home": "fecha de eliminación",
        "quota_fund": "fondo de cuota",
        "voucher": "bono",
        "debt": "deuda"
    }

    @classmethod
    def __get_csrf(
            cls, action: str,
            session: UserPortalSession = None,
            url: str = None,
            soup: bs4.BeautifulSoup = None
    ):
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
        if session:
            if not url:
                url = cls.__url[action]
            r = session.requests_session.get(url)
            cls.__raise_if_error(r, action)
            soup = bs4.BeautifulSoup(r.text, 'html.parser')
        return soup.find("input", {"name": "csrf"}).attrs["value"]

    @classmethod
    def __raise_if_error(
            cls, r: requests.Response,
            action: str
    ):
        """
        Comprueba si la solicitud fue exitosa y si hay algún error en la
        respuesta.

        :param cls: La clase a la que se llama el método
        :param r: solicitudes.Respuesta
        :type r: requests.Response
        :param action: La acción a realizar
        :type action: str
        """
        if not r.ok:
            raise cls.__up_exceptions[action](
                f"Fallo al realizar la operación: {r.status_code} - {r.reason}"
            )

        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        errors = find_errors(soup, Portal.USER_PORTAL)
        if errors:
            raise cls.__up_exceptions[action](errors)

    @staticmethod
    def get_captcha(session: UserPortalSession) -> bytes:
        """
        Obtiene la imagen captcha del portal.

        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :return: La imagen captcha.
        """
        return session.requests_session.get(
            "https://www.portal.nauta.cu/captcha/?").content

    @classmethod
    def create_session(cls) -> UserPortalSession:
        """
        Cree una nueva sesión haciendo una solicitud GET a la página de
        inicio de sesión, luego extrae el token CSRF de la respuesta y
        lo agrega a la nueva sesión

        :param cls: La clase que está llamando al método
        :return: Un objeto UserPortalSession
        """
        session = UserPortalSession()

        resp = session.requests_session.get(
            cls.__url[Action.LOGIN]
        )

        if not resp.ok:
            raise PreLoginException("Failed to create session")

        soup = bs4.BeautifulSoup(resp.text, 'html.parser')
        session.csrf = cls.__get_csrf(Action.LOGIN, soup=soup)

        return session

    @classmethod
    def login(
            cls, session: UserPortalSession, username: str, password: str,
            captcha_code: str
    ) -> None:
        """
        Inicia sesión en el portal de usuario.

        :param cls: La clase a la que se llama el método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param username: Su nombre de usuario
        :type username: str
        :param password: La contraseña que desea utilizar para iniciar sesión
        :type password: str
        :param captcha_code: El código captcha que obtienes de la imagen
        captcha
        :type captcha_code: str
        """
        r = cls.__post_action(
            session,
            {
                "csrf": session.csrf,
                "login_user": username,
                "password_user": password,
                "captcha": captcha_code,
                "btn_submit": ""
            },
            Action.LOGIN
        )

        if not r.ok:
            raise LoginException(
                f"Fallo el inicio de sesión: {r.status_code} - {r.reason}")
        cls.__raise_if_error(r, Action.LOGIN)

        soup = bs4.BeautifulSoup(r.text, "html.parser")

        session.__dict__.update(
            **{
                key: cls.__get_attr__(
                    key,
                    soup
                )
                for key in cls.__attrs.keys()}
        )

    @classmethod
    def load_user_info(cls, session: UserPortalSession) -> None:
        """
        Toma un objeto `UserPortalSession` y actualiza sus atributos con la
        información del portal del usuario

        :param cls: la clase a la que se llama el método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        """
        action = Action.LOAD_USER_INFO
        r = session.requests_session.get(
            cls.__url[action]
        )
        cls.__raise_if_error(r, action)

        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        session.__dict__.update(
            **{
                key: cls.__get_attr__(
                    key,
                    soup
                )
                for key in cls.__attrs.keys()}
        )

    @classmethod
    def recharge(cls, session: UserPortalSession, recharge_code: str) -> None:
        """
        Recarga la cuenta

        :param cls: La clase en sí
        :param session: El objeto de sesión que creó anteriormente
        :type session: UserPortalSession
        :param recharge_code: El código de recarga que desea utilizar
        :type recharge_code: str
        """
        action = Action.RECHARGE
        data = {
            "csrf": cls.__get_csrf(action, session),
            "recharge_code": recharge_code,
            "btn_submit": ""
        }
        cls.__post_action(session, data, action)

    @classmethod
    def transfer(
            cls, session: UserPortalSession, mount_to_transfer: str,
            account_to_transfer: str, password: str
    ) -> None:
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
        action = Action.TRANSFER
        data = {
            "csrf": cls.__get_csrf(action, session),
            "transfer": mount_to_transfer,
            "password_user": password,
            "id_cuenta": account_to_transfer,
            "action": "checkdata"
        }
        cls.__post_action(session, data, action)

    @classmethod
    def change_password(
            cls, session: UserPortalSession, old_password: str,
            new_password: str
    ) -> None:
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
        action = Action.CHANGE_PASSWORD
        data = {
            "csrf": cls.__get_csrf(action, session),
            "old_password": old_password,
            "new_password": new_password,
            "repeat_new_password": new_password,
            "btn_submit": ""
        }
        cls.__post_action(session, data, action)

    @classmethod
    def change_email_password(
            cls, session: UserPortalSession, old_password: str,
            new_password: str
    ) -> None:
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
        action = Action.CHANGE_EMAIL_PASSWORD
        data = {
            "csrf": cls.__get_csrf(action, session),
            "old_password": old_password,
            "new_password": new_password,
            "repeat_new_password": new_password,
            "btn_submit": ""
        }
        cls.__post_action(session, data, action)

    @classmethod
    def __post_action(
            cls, session: UserPortalSession, param: dict, action: str,
            url: str = None
    ) -> requests.Response:
        """
        Realiza una petición POST y devuelve la respuesta o genera un
        error si la respuesta no es correcta.

        :param cls: la clase desde la que se llama al método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param param: los parámetros a enviar al servidor
        :type param: dict
        :param action: La acción a realizar
        :type action: str
        :param url: La URL para publicar
        :type url: str
        :return: Un objeto de respuesta.
        """
        if not url:
            url = cls.__url[action]
        r = session.requests_session.post(
            url,
            param
        )
        cls.__raise_if_error(r, action)

        return r

    @classmethod
    def get_lasts(
            cls, session: UserPortalSession,
            action: str = Action.GET_CONNECTIONS, large: int = 5
    ) -> List[Any]:
        """
        Obtiene las últimas (large) acciones de un determinado tipo
        (conexiones, recargas, transferencias, cotizaciones_fondo) del portal
        del usuario

        :param cls: la clase que está llamando al método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param action: La acción a realizar
        :type action: str
        :param large: el número de registros a devolver, defaults to 5
        :type large: int (optional)
        :return: Una lista de las últimas 5 acciones del usuario.
        """
        actions = {
            Action.GET_CONNECTIONS: cls.get_connections,
            Action.GET_RECHARGES: cls.get_recharges,
            Action.GET_TRANSFERS: cls.get_transfers,
            Action.GET_QUOTES_FUND: cls.get_quotes_fund
        }

        year = date.today().year
        month = date.today().month

        lasts = []
        _actions = actions[action](session, year, month)
        if _actions:
            lasts.extend(_actions)

        while len(lasts) < large:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
            _actions = actions[action](session, year, month)
            if _actions:
                lasts.extend(_actions)

        return lasts[:large]

    @classmethod
    def __get_action(
            cls, session: UserPortalSession, year: int, month: int, action: str
    ):
        """
        Según el valor del parámetro (action) recupera las filas de una tabla
        html de (conexiones, recargas, transferencias, cotizaciones_fondo) y
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
        list_type = {
            Action.GET_CONNECTIONS: "service_detail",
            Action.GET_RECHARGES: "recharge_detail",
            Action.GET_QUOTES_FUND: "nautahogarpaid_detail",
            Action.GET_TRANSFERS: "transfer_detail"
        }

        year_month = f'{year}-{month:02}'
        r = cls.__post_action(
            session,
            {
                "csrf": cls.__get_csrf(
                    action,
                    session,
                    cls.__url[action]["base"]
                ),
                "year_month": year_month,
                "list_type": list_type[action]
            },
            action,
            cls.__url[action]["list"]
        )
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        table = soup.find(
            "table",
            {
                "class": "striped bordered highlight responsive-table"
            }
        )
        if table:
            trs = soup.find_all("tr")
            trs.pop(0)
            return trs

    @classmethod
    def get_connections(
            cls, session: UserPortalSession, year: int, month: int
    ) -> Union[List[Connection], None]:
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
        trs = cls.__get_action(session, year, month, Action.GET_CONNECTIONS)
        if trs:
            return [Connection(start_session=tr.find_all("td")[0].text,
                               end_session=tr.find_all("td")[1].text,
                               duration=tr.find_all("td")[2].text,
                               upload=tr.find_all("td")[3].text,
                               download=tr.find_all("td")[4].text,
                               import_=tr.find_all("td")[5].text) for tr in
                    trs]

    @classmethod
    def get_recharges(
            cls, session: UserPortalSession, year: int, month: int
    ) -> Union[List[Recharge], None]:
        """
        Obtiene las recargas del usuario en un mes y año dado

        :param cls: la clase misma
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del mes del que quieres recibir las recargas
        :type year: int
        :param month: En t
        :type month: int
        :return: Una lista de objetos de recarga.
        """
        trs = cls.__get_action(session, year, month, Action.GET_RECHARGES)
        if trs:
            return [Recharge(date=tr.find_all("td")[0].text,
                             import_=tr.find_all("td")[1].text,
                             channel=tr.find_all("td")[2].text,
                             type_=tr.find_all("td")[3].text) for tr in trs]

    @classmethod
    def get_transfers(
            cls, session: UserPortalSession, year: int, month: int
    ) -> Union[List[Transfer], None]:
        """
        Obtiene las transferencias del usuario en un mes y año dado

        :param cls: la clase misma
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: El año del estado de cuenta que desea obtener
        :type year: int
        :param month: En t
        :type month: int
        :return: Una lista de objetos de transferencia.
        """
        trs = cls.__get_action(session, year, month, Action.GET_TRANSFERS)
        if trs:
            return [
                Transfer(date=tr.find_all("td")[0].text,
                         import_=tr.find_all("td")[1].text,
                         destiny_account=tr.find_all("td")[2].text)
                for tr in trs
            ]

    @classmethod
    def get_quotes_fund(
            cls, session: UserPortalSession, year: int, month: int
    ) -> Union[List[QuotePaid], None]:
        """
        Esta función devuelve una lista de objetos QuotePaid, que son las
        cotizaciones pagadas por el usuario en el mes y año dados

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param year: En t
        :type year: int
        :param month: En t
        :type month: int
        :return: Una lista de objetos QuotePaid.
        """
        if not session.is_nauta_home:
            raise NotNautaHomeAccount(
                "Esta cuenta no esta asociada al servicio Nauta Hogar."
            )

        trs = cls.__get_action(session, year, month, Action.GET_QUOTES_FUND)
        if trs:
            return [
                QuotePaid(date=tr.find_all("td")[0].text,
                          import_=tr.find_all("td")[1].text,
                          channel=tr.find_all("td")[2].text,
                          office=tr.find_all("td")[3].text,
                          type_=tr.find_all("td")[4].text) for tr in trs
            ]

    @classmethod
    def __get_attr__(cls, attr: str, soup: bs4.BeautifulSoup) -> str:
        """
        Extrae el atributo pedido del html proporcionado

        :param cls: La clase desde la que se llama al método
        :param attr: El atributo que queremos obtener de la página
        :type attr: str
        :param soup: el objeto BeautifulSoup
        :type soup: bs4.BeautifulSoup
        :return: El valor del atributo.
        """
        if attr == "blocking_date_home" or attr == "date_of_elimination_home":
            index = 1
        else:
            index = 0
        count = 0
        for div in soup.find_all("div", {"class": "col s12 m6"}):
            if div.find("h5").text.strip().lower() == cls.__attrs[attr]:
                if index == 1 and count == 0:
                    count = 1
                    continue
                return div.find("p").text


class Nauta:

    CHECK_PAGE = "http://www.cubadebate.cu"
    LOGIN_DOMAIN = b"secure.etecsa.net"

    @classmethod
    def _get_inputs(cls, form_soup):
        return {
            _["name"]: _.get("value", default=None)
            for _ in form_soup.select("input[name]")
        }

    @classmethod
    def is_connected(cls):
        r = requests.get(cls.CHECK_PAGE)
        return cls.LOGIN_DOMAIN not in r.content

    @classmethod
    def create_session(cls) -> NautaSession:
        if cls.is_connected():
            raise PreLoginException("Hay una conexión activa")

        session = NautaSession()

        resp = session.requests_session.get(cls.CHECK_PAGE)
        if not resp.ok:
            raise PreLoginException("Failed to create session")

        soup = bs4.BeautifulSoup(resp.text, 'html.parser')
        action = soup.form["action"]
        data = cls._get_inputs(soup)

        # Now go to the login page
        resp = session.requests_session.post(action, data)
        soup = bs4.BeautifulSoup(resp.text, 'html.parser')
        form_soup = soup.find("form", id="formulario")

        session.login_action = form_soup["action"]
        data = cls._get_inputs(form_soup)

        session.csrfhw = data['CSRFHW']
        session.wlanuserip = data['wlanuserip']

        return session

    @classmethod
    def login(cls, session, username, password):

        r = session.requests_session.post(
            session.login_action,
            {
                "CSRFHW": session.csrfhw,
                "wlanuserip": session.wlanuserip,
                "username": username,
                "password": password
            }
        )

        if not r.ok:
            raise LoginException(
                "Fallo el inicio de sesión: {} - {}".format(
                    r.status_code,
                    r.reason
                )
            )

        if "online.do" not in r.url:
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            error = find_errors(soup, Portal.NAUTA)
            if error:
                raise LoginException(error)

        m = re.search(r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', r.text)

        return m.group(1) if m \
            else None

    @classmethod
    def logout(cls, session, username=None):
        response = session.requests_session.get(
            "https://secure.etecsa.net:8443/LogoutServlet",
            {
                "CSRFHW": session.csrfhw,
                "username": username,
                "ATTRIBUTE_UUID": session.attribute_uuid,
                "wlanuserip": session.wlanuserip
            }
        )
        if not response.ok:
            raise LogoutException(
                "Fallo al cerrar la sesión: {} - {}".format(
                    response.status_code,
                    response.reason
                )
            )

        if "SUCCESS" not in response.text.upper():
            raise LogoutException(
                "Fallo al cerrar la sesión: {}".format(
                    response.text[:100]
                )
            )

    @classmethod
    def get_user_time(cls, session, username):

        r = session.requests_session.post(
            "https://secure.etecsa.net:8443/EtecsaQueryServlet",
            {
                "op": "getLeftTime",
                "ATTRIBUTE_UUID": session.attribute_uuid,
                "CSRFHW": session.csrfhw,
                "wlanuserip": session.wlanuserip,
                "username": username,
            }
        )

        return r.text

    @classmethod
    def get_user_credit(cls, session, username, password):

        r = session.requests_session.post(
            "https://secure.etecsa.net:8443/EtecsaQueryServlet",
            {
                "CSRFHW": session.csrfhw,
                "wlanuserip": session.wlanuserip,
                "username": username,
                "password": password
            }
        )

        if not r.ok:
            raise NautaException(
                "Fallo al obtener la información del usuario: {} - {}"
                .format(
                    r.status_code,
                    r.reason
                )
            )

        if "secure.etecsa.net" not in r.url:
            raise NautaException(
                "No se puede obtener el crédito del usuario mientras esta "
                "online"
            )

        soup = bs4.BeautifulSoup(r.text, "html.parser")
        credit_tag = soup.select_one(
            "#sessioninfo > tbody:nth-child(1) > tr:nth-child(2) > "
            "td:nth-child(2)")

        if not credit_tag:
            raise NautaException(
                "Fallo al obtener el crédito del usuario: no se encontró la "
                "información"
            )

        return credit_tag.get_text().strip()
