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
from typing import Union

import bs4
import requests

from libsuitetecsa.core.exception import GetInfoException, TransferException, \
    ChangePasswordException, RechargeException, PreLoginException, \
    LoginException, NautaException, LogoutException, NotNautaHomeAccount
from libsuitetecsa.core.models import Transfer, Connection, Recharge, \
    QuotePaid
from libsuitetecsa.core.session import UserPortalSession, NautaSession
from libsuitetecsa.core.utils import USER_PORTAL, find_errors


class UserPortal:
    
    # Url base del portal de usuario de nauta.
    BASE_URL = "https://www.portal.nauta.cu/"

    # Constantes
    ACTION_CONNECTIONS = "connections"
    ACTION_RECHARGES = "recharges"
    ACTION_TRANSFERS = "transfers"
    ACTION_QUOTES_FUNDS = "quotes_funds"

    # Lista de urls del portal de nsuario de nauta.
    __url = {"login": "user/login/es-es",
             "user_info": "useraaa/user_info",
             "recharge": "useraaa/recharge_account",
             "change_password": "useraaa/change_password",
             "change_email_password": "email/change_password",
             "service_detail": "useraaa/service_detail/",
             "service_detail_summary": "useraaa/service_detail_summary/",
             "recharge_detail": "useraaa/recharge_detail/",
             "recharge_detail_summary": "useraaa/recharge_detail_summary/",
             "recharge_detail_list": "useraaa/recharge_detail_list/",
             "nautahogarpaid_detail": "useraaa/nautahogarpaid_detail/",
             "nautahogarpaid_detail_summary":
                 "useraaa/nautahogarpaid_detail_summary/",
             "nautahogarpaid_detail_list":
                 "useraaa/nautahogarpaid_detail_list/",
             "transfer_detail": "useraaa/transfer_detail/",
             "transfer_detail_summary": "useraaa/transfer_detail_summary/",
             "transfer_detail_list": "useraaa/transfer_detail_list/",
             "service_detail_list": "useraaa/service_detail_list/",
             "logout": "user/logout"}
    
    # Excepciones disparadas por esta clase.
    __up_exceptions = {"user_info": GetInfoException,
                       "recharge": RechargeException,
                       "transfer": TransferException,
                       "service_detail": GetInfoException,
                       "recharge_detail": GetInfoException,
                       "nautahogarpaid_detail": GetInfoException,
                       "transfer_detail": GetInfoException,
                       "change_password": ChangePasswordException,
                       "change_email_password": ChangePasswordException,
                       "login": LoginException}
    
    # Diccionario usado para extraer información de la cuenta logueada.
    __attrs = {"username": "usuario",
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
               "debt": "deuda"}

    @classmethod
    def __raise_if_error(cls, r: requests.Response, action: str) -> None:
        if not r.ok:
            raise cls.__up_exceptions[action](
                f"Fallo al realizar la operación: {r.status_code} - {r.reason}"
            )

        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        errors = find_errors(soup, USER_PORTAL)
        if errors:
            raise cls.__up_exceptions[action](errors)

    @classmethod
    def __get_csrf_(cls, session: UserPortalSession, action: str) -> str:
        r = session.requests_session.get(cls.BASE_URL + cls.__url[action])
        cls.__raise_if_error(r, action)
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        return cls.__get_csrf(soup)

    @staticmethod
    def get_captcha(session: UserPortalSession) -> bytes:
        return session.requests_session.get(
            "https://www.portal.nauta.cu/captcha/?").content

    @staticmethod
    def __get_csrf(soup: bs4.BeautifulSoup) -> str:
        return soup.find("input", {"name": "csrf"}).attrs["value"]

    @classmethod
    def create_session(cls) -> UserPortalSession:
        session = UserPortalSession()

        resp = session.requests_session.get(f'{cls.BASE_URL}user/login/es-es')

        if not resp.ok:
            raise PreLoginException("Failed to create session")

        soup = bs4.BeautifulSoup(resp.text, 'html.parser')
        session.csrf = cls.__get_csrf(soup)

        return session

    @classmethod
    def login(
            cls, session: UserPortalSession,
            username: str,
            password: str,
            captcha_code: str
    ) -> None:
        r = session.requests_session.post(
            f'{cls.BASE_URL}user/login/es-es',
            {
                "csrf": session.csrf,
                "login_user": username,
                "password_user": password,
                "captcha": captcha_code,
                "btn_submit": ""
            }
        )

        cls.__raise_if_error(r, "login")

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
    def load_user_info(cls, session: UserPortalSession):
        action = "user_info"
        r = session.requests_session.get(
            cls.BASE_URL + cls.__url[action]
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
    def __post_action(cls, session: UserPortalSession, data: dict, action: str):
        r = session.requests_session.post(
            cls.BASE_URL + cls.__url[action],
            json=data
        )
        cls.__raise_if_error(r, action)
    
    @classmethod
    def recharge(cls, session: UserPortalSession, recharge_code: str):
        action = "recharge"
        data = {
            "csrf": cls.__get_csrf_(session, action),
            "recharge_code": recharge_code,
            "btn_submit": ""
        }
        cls.__post_action(session, data, action)
        
    @classmethod
    def transfer(
            cls, session: UserPortalSession,
            mount_to_transfer: str,
            account_to_transfer: str,
            password: str
    ):
        action = "up_transfer"
        data = {
            "csrf": cls.__get_csrf_(session, action),
            "transfer": mount_to_transfer,
            "password_user": password,
            "id_cuenta": account_to_transfer,
            "action": "checkdata"
        }
        cls.__post_action(session, data, action)

    @classmethod
    def change_password(
            cls, session: UserPortalSession,
            old_password: str,
            new_password: str
    ):
        action = "change_password"
        data = {
            "csrf": cls.__get_csrf_(session, action),
            "old_password": old_password,
            "new_password": new_password,
            "repeat_new_password": new_password,
            "btn_submit": ""
        }
        cls.__post_action(session, data, action)

    @classmethod
    def change_email_password(
            cls, session: UserPortalSession,
            old_password: str,
            new_password: str
    ):
        action = "change_email_password"
        data = {
            "csrf": cls.__get_csrf_(session, action),
            "old_password": old_password,
            "new_password": new_password,
            "repeat_new_password": new_password,
            "btn_submit": ""
        }
        cls.__post_action(session, data, action)

    @classmethod
    def get_lasts(
            cls, session: UserPortalSession,
            action: str = ACTION_CONNECTIONS,
            large: int = 5
    ):
        actions = {
            cls.ACTION_CONNECTIONS: cls.get_connections,
            cls.ACTION_RECHARGES: cls.get_recharges,
            cls.ACTION_TRANSFERS: cls.get_transfers,
            cls.ACTION_QUOTES_FUNDS: cls.get_quotes_fund
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
        cls, session: UserPortalSession,
        year: int,
        month: int,
        action: str
    ) -> Union[bs4.ResultSet, None]:
        actions = {
            cls.ACTION_CONNECTIONS: {
                "base": "service_detail",
                "list": "service_detail_list",
                "summary": "service_detail_summary"
            },
            cls.ACTION_RECHARGES: {
                "base": "recharge_detail",
                "list": "recharge_detail_list",
                "summary": "recharge_detail_summary"
            },
            cls.ACTION_QUOTES_FUNDS: {
                "base": "nautahogarpaid_detail",
                "list": "nautahogarpaid_detail_list",
                "summary": "nautahogarpaid_detail_summary"
            },
            cls.ACTION_TRANSFERS: {
                "base": "transfer_detail",
                "list": "transfer_detail_list",
                "summary": "transfer_detail_summary"
            }
        }

        year_month = f'{year}-{month:02}'
        r = session.requests_session.post(
            cls.BASE_URL + cls.__url[actions[action]["list"]] + year_month,
            {
                "csrf": cls.__get_csrf_(session, actions[action]["base"]),
                "year_month": year_month,
                "list_type": actions[action]["base"]
            }
        )
        if not r.ok:
            raise cls.__up_exceptions[actions[action]["base"]](
                f"Fallo al realizar la operación: {r.status_code} - {r.reason}"
            )
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        if cls.__url[actions[action]["list"]] not in r.url:
            raise cls.__up_exceptions[actions[action]["base"]](
                find_errors(soup, USER_PORTAL)
            )
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
            cls, session: UserPortalSession,
            year: int,
            month: int
    ):
        trs = cls.__get_action(session, year, month, "connections")
        if trs:
            return [Connection(start_session=tr.find_all("td")[0].text,
                               end_session=tr.find_all("td")[1].text,
                               duration=tr.find_all("td")[2].text,
                               upload=tr.find_all("td")[3].text,
                               download=tr.find_all("td")[4].text,
                               import_=tr.find_all("td")[5].text) for tr in
                    trs]

    @classmethod
    def get_recharges(cls, session: UserPortalSession, year: int, month: int):
        trs = cls.__get_action(session, year, month, "recharges")
        if trs:
            return [Recharge(date=tr.find_all("td")[0].text,
                             import_=tr.find_all("td")[1].text,
                             channel=tr.find_all("td")[2].text,
                             type_=tr.find_all("td")[3].text) for tr in trs]

    @classmethod
    def get_quotes_fund(
            cls, session: UserPortalSession,
            year: int,
            month: int
    ):
        if not session.is_nauta_home:
            raise NotNautaHomeAccount(
                "Esta cuenta no esta asociada al servicio Nauta Hogar."
            )

        trs = cls.__get_action(session, year, month, "quotes_funds")
        if trs:
            return [
                QuotePaid(date=tr.find_all("td")[0].text,
                          import_=tr.find_all("td")[1].text,
                          channel=tr.find_all("td")[2].text,
                          office=tr.find_all("td")[3].text,
                          type_=tr.find_all("td")[4].text) for tr in trs
            ]

    @classmethod
    def get_transfers(cls, session: UserPortalSession, year: int, month: int):
        trs = cls.__get_action(session, year, month, "transfers")
        if trs:
            return [
                Transfer(date=tr.find_all("td")[0].text,
                         import_=tr.find_all("td")[1].text,
                         destiny_account=tr.find_all("td")[2].text)
                for tr in trs
            ]

    @staticmethod
    def __get_attr__(attr: str, soup: bs4.BeautifulSoup) -> str:
        if attr == "blocking_date_home" or attr == "date_of_elimination_home":
            index = 1
        else:
            index = 0
        count = 0
        for div in soup.find_all("div", {"class": "col s12 m6"}):
            if div.find("h5").text.strip().lower() == UserPortal.__attrs[attr]:
                if index == 1 and count == 0:
                    count = 1
                    continue
                return div.find("p").text


class Nauta(object):
    """Protocol Layer (Interface)

    Abstracts the details of dealing with nauta server
    This is the lower layer of the application. API client must
    use this instead of directly talk with nauta server

    """

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
            if NautaSession.is_logged_in():
                raise PreLoginException("Hay una session abierta")
            else:
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
            script_text = soup.find_all("script")[-1].get_text().strip()

            match = cls._re_login_fail_reason.match(script_text)
            raise LoginException(
                "Fallo el inicio de sesión: {}".format(
                    match.group("reason")
                )
            )

        m = re.search(r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', r.text)

        return m.group(1) if m \
            else None

    @classmethod
    def logout(cls, session, username=None):
        logout_url = \
            (
                    "https://secure.etecsa.net:8443/LogoutServlet?" +
                    "CSRFHW={}&" +
                    "username={}&" +
                    "ATTRIBUTE_UUID={}&" +
                    "wlanuserip={}"
            ).format(
                session.csrfhw,
                username,
                session.attribute_uuid,
                session.wlanuserip
            )

        response = session.requests_session.get(logout_url)
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
                "Fallo al obtener la información del usuario: {} - {}".format(
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
