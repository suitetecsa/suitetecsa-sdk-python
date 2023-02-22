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
from datetime import date
from typing import List, Any, Union

import bs4
import requests
from PyLibSuitETECSA.core import USER_PORTAL_ATTRS

from PyLibSuitETECSA.core.exception import GetInfoException, \
    TransferException, ChangePasswordException, LoginException, \
    RechargeException, PreLoginException, NotNautaHomeAccount, \
    LogoutException, NautaException, ConnectionException
from PyLibSuitETECSA.core.models import Connection, ConnectionsSummary, \
    QuotePaid, QuotesPaidSummary, Recharge, RechargesSummary, Transfer, \
    ActionResponse, TransfersSummary
from PyLibSuitETECSA.core.session import UserPortalSession, NautaSession
from PyLibSuitETECSA.utils import RE_SUCCESS_ACTION, Action, Portal
from PyLibSuitETECSA.utils.parser import parse_errors


class UserPortal:
    # La URL base del portal.
    BASE_URL = "https://www.portal.nauta.cu/"

    # Un diccionario que contiene las URL de las acciones que se pueden
    # realizar en el portal.
    __url = {
        Action.LOGIN: f"user/login/es-es",
        Action.LOAD_USER_INFO: f"useraaa/user_info",
        Action.RECHARGE: f"useraaa/recharge_account",
        Action.TRANSFER: f"useraaa/transfer_balance",
        Action.NAUTA_HOGAR_PAID: f"useraaa/transfer_nautahogarpaid",
        Action.CHANGE_PASSWORD: f"useraaa/change_password",
        Action.CHANGE_EMAIL_PASSWORD: f"mail/change_password",
        Action.GET_CONNECTIONS: {
            "base": f"useraaa/service_detail/",
            "summary": f"useraaa/service_detail_summary/",
            "list": f"useraaa/service_detail_list/"
        },
        Action.GET_RECHARGES: {
            "base": f"useraaa/recharge_detail/",
            "summary": f"useraaa/recharge_detail_summary/",
            "list": f"useraaa/recharge_detail_list/"
        },
        Action.GET_TRANSFERS: {
            "base": f"useraaa/transfer_detail/",
            "summary": f"useraaa/transfer_detail_summary/",
            "list": f"useraaa/transfer_detail_list/",
        },
        Action.GET_QUOTES_FUND: {
            "base": f"useraaa/nautahogarpaid_detail/",
            "summary": f"useraaa/nautahogarpaid_detail_summary/",
            "list": f"useraaa/nautahogarpaid_detail_list/"
        },
        Action.LOGOUT: f"user/logout"
    }

    @classmethod
    def __build_url(
        cls, action: int,
        get_action: bool = False,
        sub_action: str = None,
        year_month_selected: str = None,
        count_or_page: int = None
    ) -> str | None:
        """
        Construye una url en dependecia de los parametros pasados.

        :param cls: la clase desde la que se llama el metodo.
        :param action: La acción que desea realizar
        :type action: int
        :param get_action: confirma o no la recuperacion de una lista
        :type get_action: bool
        :param sub_action: paso en la recuperacion de la lista
        :type sub_action: str
        :param year_month_selected: mes-anno a consultar
        :type year_month_selected: str
        :param count_or_page: cantidad de resultados o paginas a consultar
        :type count_or_page: int

        :return: La url creada
        """
        if not get_action:
            return f'{cls.BASE_URL}{cls.__url[action]}'
        elif get_action and sub_action:
            url = f'{cls.BASE_URL}{cls.__url[action][sub_action]}'
            match sub_action:
                case "base" | "summary":
                    return url
                case "list":
                    if not year_month_selected:
                        raise AttributeError(
                            'Atributo year_month_selected no definido'
                        )
                    if not count_or_page:
                        raise AttributeError(
                            'Atributo count_or_page no definido'
                        )
                    else:
                        return f'{url}{year_month_selected}/{count_or_page}'

    @classmethod
    def __get_csrf(
            cls, action: Action,
            session: UserPortalSession = None,
            url: str = None,
            soup: bs4.BeautifulSoup = None
    ) -> str:
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
                url = cls.__build_url(action)
            r = session.requests_session.get(url)
            soup = cls.__raise_if_error(
                r,
                ConnectionException,
                "Error al obtener el token 'csrf'"
            )
        return soup.select_one('input[name=csrf]').attrs["value"]

    @classmethod
    def __raise_if_error(
            cls, r: requests.Response,
            exception: Exception,
            message: str,
            find_error: bool = True
    ) -> bs4.BeautifulSoup:
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
            raise exception(
                f"{message}: {r.status_code} :: {r.reason}"
            )

        if find_error:
            soup = bs4.BeautifulSoup(r.text, 'html5lib')
            error = parse_errors(soup, Portal.USER_PORTAL)
            if error:
                raise exception(error)
            else:
                return soup

    @classmethod
    def __update_session_parameters(
        cls, session: UserPortalSession,
        soup: bs4.BeautifulSoup
    ) -> None:
        """
        Actualiza la session con la informacion tomada del portal

        :param cls: La clase a la que se llama el método
        :param session: session actual
        :type session: UserPortalSession
        :param soup: pagina consultada
        :type soup: bs4.BeautifulSoup
        """

        parameters = soup.select_one('.z-depth-1').select('.m6')

        for _, parameter in enumerate(parameters):
            session.__setattr__(
                USER_PORTAL_ATTRS[_],
                parameter.select_one('p').text
            )

    @staticmethod
    def get_captcha(session: UserPortalSession) -> bytes:
        """
        Obtiene la imagen captcha del portal.

        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :return: La imagen captcha.
        """
        r = session.requests_session.get(
            "https://www.portal.nauta.cu/captcha/?"
        )
        UserPortal.__raise_if_error(
            r,
            ConnectionException,
            "Error al Obtener la imagen Captcha",
            find_error=False
        )
        return r.content

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

        r = session.requests_session.get(
            cls.__build_url(Action.LOGIN)
        )

        soup = cls.__raise_if_error(
            r,
            PreLoginException,
            "Fallo al crear la sesión"
        )

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

        soup = cls.__raise_if_error(
            r,
            LoginException,
            "Falló el inicio de sesión"
        )

        cls.__update_session_parameters(session, soup)

    @classmethod
    def load_user_info(cls, session: UserPortalSession) -> None:
        """
        Toma el objeto `UserPortalSession` y actualiza sus atributos con la
        información del portal del usuario

        :param cls: la clase a la que se llama el método
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        """
        r = session.requests_session.get(
            cls.__build_url(Action.LOAD_USER_INFO)
        )

        soup = cls.__raise_if_error(
            r,
            GetInfoException,
            "Fallo al recuperar la info de la cuenta"
        )

        cls.__update_session_parameters(session, soup)

    @classmethod
    def recharge(
        cls, session: UserPortalSession,
        recharge_code: str
    ) -> ActionResponse:
        """
        Recarga la cuenta asociada a la session

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

        r = cls.__post_action(session, data, action)

        soup = cls.__raise_if_error(
            r,
            RechargeException,
            "Error al recargar la cuenta"
        )

        return cls.__get_response(soup)

    @classmethod
    def transfer(
            cls, session: UserPortalSession, mount_to_transfer: float,
            account_to_transfer: str, password: str,
            nauta_hogar_paid: bool = False
    ) -> ActionResponse:
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
            "csrf": cls.__get_csrf(action, session),
            "transfer": f'{mount_to_transfer:.2f}'.replace('.', ','),
            "password_user": password,
            "action": "checkdata"
        }
        if not nauta_hogar_paid:
            data["id_cuenta"] = account_to_transfer

        r = cls.__post_action(session, data, action)

        soup = cls.__raise_if_error(
            r,
            TransferException,
            "Error al transferir el saldo"
        )

        return cls.__get_response(soup)

    @classmethod
    def change_password(
            cls, session: UserPortalSession, old_password: str,
            new_password: str
    ) -> ActionResponse:
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

        r = cls.__post_action(session, data, action)

        soup = cls.__raise_if_error(
            r,
            ChangePasswordException,
            "Error al cambiar la contraseña"
        )

        return cls.__get_response(soup)

    @classmethod
    def change_email_password(
            cls, session: UserPortalSession, old_password: str,
            new_password: str
    ) -> ActionResponse:
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

        r = cls.__post_action(session, data, action)

        soup = cls.__raise_if_error(
            r,
            ChangePasswordException,
            "Error al cambiar la contraseña"
        )

        return cls.__get_response(soup)

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
            url = cls.__build_url(action)
        r = session.requests_session.post(
            url,
            param
        )

        return r

    @classmethod
    def get_lasts(
            cls, session: UserPortalSession,
            action: str = Action.GET_CONNECTIONS, large: int = 5
    ) -> List[Any]:
        """
        Obtiene las últimas (large) acciones de un determinado tipo
        (conexiones, recargas, transferencias, cuotas pagadas) del portal
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
            Action.GET_QUOTES_FUND: cls.get_quotes_paid
        }
        actions_summary = {
            Action.GET_CONNECTIONS: cls.get_connections_summary,
            Action.GET_RECHARGES: cls.get_recharges_summary,
            Action.GET_TRANSFERS: cls.get_transfers_summary,
            Action.GET_QUOTES_FUND: cls.get_quotes_fund_summary
        }

        year = date.today().year
        month = date.today().month

        lasts = []
        _action_summary = actions_summary[action](
            session, year, month
        )
        _actions = actions[action](session, _action_summary)
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
        list_type = {
            Action.GET_CONNECTIONS: "service_detail",
            Action.GET_RECHARGES: "recharge_detail",
            Action.GET_QUOTES_FUND: "nautahogarpaid_detail",
            Action.GET_TRANSFERS: "transfer_detail"
        }

        message_action = {
            Action.GET_CONNECTIONS:
            "Error al obtener la lista de conexiones",
            Action.GET_RECHARGES:
            "Error al obtener la lista de recargas",
            Action.GET_QUOTES_FUND:
            "Error al obtener la lista de fondos de cuotas",
            Action.GET_TRANSFERS:
            "Error al obtener la lista de transferencias"
        }

        year_month = f'{year}-{month:02}'
        r = cls.__post_action(
            session,
            {
                "csrf": cls.__get_csrf(
                    action,
                    session,
                    cls.__build_url(
                        action,
                        True,
                        "base"
                    )
                ),
                "year_month": year_month,
                "list_type": list_type[action]
            },
            action,
            cls.__build_url(
                action,
                True,
                "summary"
            )
        )
        soup = cls.__raise_if_error(
            r,
            GetInfoException,
            message_action[action]
        )

        return soup.select_one('#content').select('.card-content')

    @classmethod
    def __get_response(cls, soup: bs4.BeautifulSoup) -> ActionResponse | None:
        """
        Busca un mensaje de accion exitosa y de existir, lo devuelve
        junto a un estado success dentro de un objeto ActionResponse.

        :param cls: la clase que está llamando al método
        :param soup: html devuelto tras la accion realizada
        :type soup: bs4.BeautifulSoup

        :return: resultado de la accion realizada
        """
        script_text = soup.find_all("script")[-1].contents[0].strip()
        match_ = RE_SUCCESS_ACTION.match(script_text)
        if match_:
            soup = bs4.BeautifulSoup(match_.group("reason"), "html5lib")
            return ActionResponse(
                "success",
                soup.select_one('li:is(.msg_message)').text
            )

    @classmethod
    def get_connections_summary(
        cls, session: UserPortalSession, year: int, month: int
    ) -> ConnectionsSummary:
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
            connections,
            total_time,
            total_import,
            uploaded,
            downloaded,
            total_traffic
        ] = cls.__get_action(session, year, month, Action.GET_CONNECTIONS)
        return ConnectionsSummary(
            count=connections.select_one('input[name=count]').attrs['value'],
            year_month_selected=connections.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            total_time=total_time.select_one('.card-stats-number').text,
            total_import=total_import.select_one('.card-stats-number').text,
            uploaded=uploaded.select_one('.card-stats-number').text,
            downloaded=downloaded.select_one('.card-stats-number').text,
            total_traffic=total_traffic.select_one('.card-stats-number').text
        )

    @classmethod
    def get_connections(
            cls, session: UserPortalSession,
            connections_summary: ConnectionsSummary
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

        rows = cls.__parse_action_rows(
            session,
            Action.GET_CONNECTIONS,
            connections_summary.year_month_selected,
            connections_summary.count
        )

        if rows:
            connections_list = []
            for row in rows:
                [
                    start_session_tag,
                    end_session_tag,
                    duration_tag,
                    upload_tag,
                    download_tag,
                    import_tag
                ] = row.select('td')
                connections_list.append(
                    Connection(
                        start_session=start_session_tag.text,
                        end_session=end_session_tag.text,
                        duration=duration_tag.text,
                        uploaded=upload_tag.text,
                        downloaded=download_tag.text,
                        import_=import_tag.text
                    )
                )
            return connections_list

    @classmethod
    def get_recharges_summary(
        cls, session: UserPortalSession, year: int, month: int
    ) -> RechargesSummary:

        """
        Obtiene los datos interesantes del sumario de recargas

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto RechargesSummary con la informacion interesante
        del sumario de recargas
        """

        recharges, total_import = cls.__get_action(
            session, year, month, Action.GET_RECHARGES
        )
        return RechargesSummary(
            count=recharges.select_one('input[name=count]').attrs['value'],
            year_month_selected=recharges.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            total_import=total_import.select_one('.card-stats-number').text
        )

    @classmethod
    def get_recharges(
            cls,
            session: UserPortalSession,
            recharges_summary: RechargesSummary
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

        rows = cls.__parse_action_rows(
            session,
            Action.GET_RECHARGES,
            recharges_summary.year_month_selected,
            recharges_summary.count
        )

        if rows:
            recharges_list = []
            for row in rows:
                date, import_, channel, type_ = row

                recharges_list.append(
                    Recharge(
                        date=date.text,
                        import_=import_.text,
                        channel=channel.text,
                        type_=type_.text
                    )
                )
            return recharges_list

    @classmethod
    def get_transfers_summary(
        cls, session: UserPortalSession, year: int, month: int
    ) -> TransfersSummary:

        """
        Obtiene los datos interesantes del sumario de transferencias

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto TransfersSummary con la informacion interesante
        del sumario de transferencias
        """

        transfers, total_import = cls.__get_action(
            session, year, month, Action.GET_TRANSFERS
        )
        return TransfersSummary(
            count=transfers.select_one('input[name=count]').attrs['value'],
            year_month_selected=transfers.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            total_import=total_import.select_one('.card-stats-number').text
        )

    @classmethod
    def get_transfers(
            cls, session: UserPortalSession,
            transfers_summary: TransfersSummary
    ) -> list[Transfer] | None:
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

        rows = cls.__parse_action_rows(
            session,
            Action.GET_TRANSFERS,
            transfers_summary.year_month_selected,
            transfers_summary.count
        )

        if rows:
            transfers_list = []
            for row in rows:
                date, import_, destiny_account = row

                transfers_list.append(
                    Transfer(
                        date=date.text,
                        import_=import_.text,
                        destiny_account=destiny_account.text
                    )
                )
            return transfers_list

    @classmethod
    def get_quotes_fund_summary(
        cls, session: UserPortalSession,
        year: int, month: int
    ) -> QuotesPaidSummary:

        """
        Obtiene los datos interesantes del sumario de cuotas pagadas

        :param cls: la clase que está llamando al método
        :param session: la sesion actual
        :type session: UserPortalSession
        :param year: anno a consultar
        :type year: int
        :param month: mes del anno a consultar
        :type month: int

        :return: objeto QuotesPaidSummary con la informacion interesante
        del sumario de cuotas pagadas
        """

        quotes_fund, total_import = cls.__get_action(
            session, year, month, Action.GET_QUOTES_FUND
        )
        return QuotesPaidSummary(
            count=quotes_fund.select_one('input[name=count]').attrs['value'],
            year_month_selected=quotes_fund.select_one(
                'input[name=year_month_selected]'
            ).attrs['value'],
            total_import=total_import.select_one('.card-stats-number').text
        )

    @classmethod
    def get_quotes_paid(
            cls, session: UserPortalSession,
            quotes_fund_summary: QuotesPaidSummary
    ) -> list[QuotePaid] | None:
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

        rows = cls.__parse_action_rows(
            session,
            Action.GET_QUOTES_FUND,
            quotes_fund_summary.year_month_selected,
            quotes_fund_summary.count
        )

        if rows:
            quotes_fund_list = []
            for row in rows:
                date, import_, channel, type_, office = row

                quotes_fund_list.append(
                    QuotePaid(
                        date=date.text,
                        import_=import_.text,
                        channel=channel.text,
                        type_=type_.text,
                        office=office.text
                    )
                )
            return quotes_fund_list

    @classmethod
    def __parse_action_rows(
        cls,
        session: UserPortalSession,
        action: int,
        year_month_selected: str,
        count: int,
    ) -> list[bs4.Tag] | None:

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

        rows_list = []

        pages = (
            count // 14 + 1
            if count / 14 > count // 14
            else count // 14
        ) if count > 14 else 1

        for page in range(1, pages + 1):
            suffix = page if page != 1 else count
            url = cls.__build_url(
                action,
                True,
                'list',
                year_month_selected,
                suffix
            )
            tbody = cls.__get_tbody(
                session,
                url
            )
            if tbody:
                rows_list.extend(
                    tbody.select("tr")
                )
        return rows_list

    @classmethod
    def __get_tbody(
        cls,
        session: UserPortalSession,
        url: str
    ) -> bs4.Tag | None:

        """
        obtiene y devuelve la seccion tbody de la tabla html

        :param cls: La clase en sí
        :param session: Sesión de portal de usuario
        :type session: UserPortalSession
        :param url: url de la consulta
        :type url: str

        :return: un objeto bs4.Tag (seccion tbody de la tabla)
        """

        r = session.requests_session.get(
            url
        )
        soup = cls.__raise_if_error(
            r,
            GetInfoException,
            "Error al obtener la información."
        )
        return soup.select_one(
            '.responsive-table > tbody'
        )


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
            error = parse_errors(soup, Portal.NAUTA)
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
