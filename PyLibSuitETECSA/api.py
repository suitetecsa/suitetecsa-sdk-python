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

from typing import Any

from requests import RequestException

from PyLibSuitETECSA.core.exception import LogoutException
from PyLibSuitETECSA.core.models import ActionResponse, Connection, Recharge, \
    Transfer, QuoteFund
from PyLibSuitETECSA.core.protocol import UserPortal, Nauta
from PyLibSuitETECSA.core.session import NautaSession
from PyLibSuitETECSA.utils import Action


class UserPortalClient:
    def __init__(self, username: str = None, password: str = None):
        self.username = username
        self.password = password
        self.session = None

    def init_session(self) -> None:
        """
        Crea una sesión.
        :return:
        """
        self.session = UserPortal.create_session()

    @property
    def captcha_as_bytes(self) -> bytes:
        """
        Si la sesión no está creada, la crea y devuelve la imagen captcha
        en formato de bytes.
        :return: bytes: imagen captcha
        """
        if not self.session:
            self.init_session()
        return UserPortal.get_captcha(self.session)

    def login(self, captcha_code: str):
        """
        Inicia sesión en el portal de usuario.
        :param captcha_code: Código captcha.
        :return: instancia de esta clase.
        """
        if not self.session:
            raise LogoutException(
                'Debe crear una sesión antes de loguearte.'
            )

        UserPortal.login(
            self.session,
            self.username,
            self.password,
            captcha_code
        )

        return self

    def recharge(self, recharge_code: str) -> ActionResponse:
        """
        Recarga el saldo de la cuenta registrada.
        :param recharge_code: Código de recarga.
        :return:
        """
        is_confirmed = UserPortal.recharge(
            self.session,
            recharge_code
        )
        return is_confirmed

    def transfer(
            self, mount_to_transfer: float | int | str,
            account_to_transfer: str
    ) -> ActionResponse:
        """
        Transfiere saldo a otra cuenta nauta.
        :param mount_to_transfer: Monto a transferir.
        :param account_to_transfer: Cuenta de destino.
        :return:
        """
        return UserPortal.transfer(
            self.session,
            mount_to_transfer,
            account_to_transfer,
            self.password
        )

    def pay_nauta_home(
        self, mount_to_transfer: float | int | str
    ) -> ActionResponse:
        return UserPortal.transfer(
            session=self.session,
            mount_to_transfer=mount_to_transfer,
            password=self.password,
            nauta_hogar_paid=True
        )

    def change_password(self, new_passwrd: str) -> ActionResponse:
        """
        Cambia la contraseña de acceso a internet de la cuenta registrada.
        :param new_passwrd: Nueva contraseña.
        :return:
        """
        return UserPortal.change_password(
            self.session,
            self.password,
            new_passwrd
        )

    def change_email_password(self, new_passwrd: str) -> ActionResponse:
        """
        Cambia la contraseña de la cuenta de correo asociada.
        :param new_passwrd: Nueva contraseña.
        :return:
        """
        return UserPortal.change_email_password(
            self.session,
            self.password,
            new_passwrd
        )

    def get_lasts(
            self, action: str = Action.GET_CONNECTIONS,
            large: int = 5
    ) -> list[Connection | Recharge | Transfer | QuoteFund] | None:
        """
        Devuelve las últimas `large` `action` realizadas por la cuenta.
        :param action: Acciones u operaciones que se requieren.
        :param large: Cantidad de action que se requieren.
        :return: Lista de (`Connection | Recharge | Transfer` según el valor de
        `action`).
        """
        return UserPortal.get_lasts(
            self.session,
            action,
            large
        )

    def get_connections(
            self, year: int,
            month: int
    ) -> list[Connection] | None:
        """
        Devuelve las conexiones realizadas en el periodo mes-año especificado.
        :param year: Año en el que buscar.
        :param month: Mes en el que buscar.
        :return: Lista de Connection en el periodo solicitado.
        """
        connections_summary = UserPortal.get_connections_summary(
            self.session, year, month
        )
        return UserPortal.get_connections(
            self.session, connections_summary
        )

    def get_recharges(
            self, year: int,
            month: int
    ) -> list[Recharge] | None:
        """
        Devuelve las recargas realizadas en el periodo mes-año especificado.
        :param year: Año en el que buscar.
        :param month: Mes en el que buscar.
        :return: Lista de Recharge en el periodo solicitado.
        """

        recharges_summary = UserPortal.get_recharges_summary(
            self.session, year, month
        )
        return UserPortal.get_recharges(
            self.session,
            recharges_summary
        )

    def get_transfers(
            self, year: int,
            month: int
    ) -> list[Transfer] | None:
        """
        Devuelve las transferencias realizadas en el periodo mes-año
        especificado.
        :param year: Año en el que buscar.
        :param month: Mes en el que buscar.
        :return: Lista de Transfer en el periodo solicitado.
        """

        transfers_summary = UserPortal.get_transfers_summary(
            self.session, year, month
        )
        return UserPortal.get_transfers(
            self.session,
            transfers_summary
        )

    def get_quotes_fund(
            self, year: int,
            month: int
    ) -> list[QuoteFund] | None:
        """
        Devuelve las recargas hechas al servicio nauta Hogar en el periodo
        mes-año especificado.
        :param year: Año en el que buscar.
        :param month: Mes en el que buscar.
        :return: Lista de NautaHomePaid en el periodo solicitado.
        """

        quotes_fund_summary = UserPortal.get_quotes_fund_summary(
            self.session, year, month
        )
        return UserPortal.get_quotes_fund(
            self.session,
            quotes_fund_summary
        )

    @property
    def is_nauta_home(self) -> bool:
        """
        :return: Si la cuentalogueada esta vinculada al servicio
        nauta hogar.
        """
        return self.session.is_nauta_home

    @property
    def blocking_date(self) -> datetime.datetime | None:
        """
        :return: Fecha de bloqueo de la cuenta registrada.
        """
        return self.session.blocking_date if self.session else None

    @property
    def date_of_elimination(self) -> datetime.datetime | None:
        """
        :return: Fecha de eliminación de la cuenta registrada.
        """
        return self.session.date_of_elimination if self.session else None

    @property
    def account_type(self) -> str | None:
        """
        :return: Tipo de cuenta de la cuenta registrada.
        """
        return self.session.account_type if self.session else None

    @property
    def service_type(self) -> str | None:
        """
        :return: Tipo de servicio de la cuenta registrada.
        """
        return self.session.service_type if self.session else None

    @property
    def credit(self) -> float | None:
        """
        :return: Saldo disponible de la cuenta registrada.
        """
        return self.session.credit if self.session else None

    @property
    def time(self) -> int | None:
        """
        :return: Tiempo disponible de la cuenta registrada.
        """
        return self.session.time if self.session else None

    @property
    def mail_account(self) -> str | None:
        """
        :return: Cuenta de correo asociada a la cuenta registrada.
        """
        return self.session.mail_account if self.session else None

    @property
    def offer(self) -> str | None:
        """
        :return: valor de oferta.
        """
        return self.session.offer if self.session else None

    @property
    def monthly_fee(self) -> float | None:
        """
        :return: valor cuota mensual.
        """
        return self.session.monthly_fee if self.session else None

    @property
    def download_speeds(self) -> int | None:
        """
        :return: valor velocidad de bajada.
        """
        return self.session.download_speeds if self.session else None

    @property
    def upload_speeds(self) -> str | None:
        """
        :return: valor velocidad de subida.
        """
        return self.session.upload_speeds if self.session else None

    @property
    def phone(self) -> str | None:
        """
        :return: valor teléfono.
        """
        return self.session.phone if self.session else None

    @property
    def link_identifiers(self) -> str | None:
        """
        :return: valor identificador del enlace.
        """
        return self.session.link_identifiers if self.session else None

    @property
    def link_status(self) -> str | None:
        """
        :return: valor estado del enlace.
        """
        return self.session.link_status if self.session else None

    @property
    def activation_date(self) -> str | None:
        """
        :return: valor fecha de activacion.
        """
        return self.session.activation_date if self.session else None

    @property
    def blocking_date_home(self) -> str | None:
        """
        :return: valor fecha de bloqueo (`nauta hogar`).
        """
        return self.session.blocking_date_home if self.session else None

    @property
    def date_of_elimination_home(self) -> str | None:
        """
        :return: valor fecha de eliminacion (`nauta hogar`).
        """
        return self.session.date_of_elimination_home if self.session else None

    @property
    def quota_fund(self) -> str | None:
        """
        :return: valor fondo de cuota.
        """
        return self.session.quota_fund if self.session else None

    @property
    def voucher(self) -> str | None:
        """
        :return: valor bono.
        """
        return self.session.voucher if self.session else None

    @property
    def debt(self) -> str | None:
        """
        :return: valor deuda.
        """
        return self.session.debt if self.session else None


class NautaClient(object):
    def __init__(self, user: str = None, password: str = None):
        self.user = user
        self.password = password
        self.session = None

    def init_session(self):
        """
        Crea una sesión.
        :return:
        """
        self.session = Nauta.create_session()

    def login(self):
        """
        Inicia sesión en internet.
        :return: Instancia de esta clase.
        """
        if not self.session:
            self.init_session()

        self.session.attribute_uuid = Nauta.login(
            self.session,
            self.user,
            self.password
        )

        return self

    @property
    def user_credit(self):
        """
        :return: Saldo disponible de la cuenta.
        """
        dispose_session = False
        try:
            if not self.session:
                dispose_session = True
                self.init_session()

            return Nauta.get_user_credit(
                session=self.session,
                username=self.user,
                password=self.password
            )
        finally:
            if self.session and dispose_session:
                self.session.dispose()
                self.session = None

    @property
    def remaining_time(self):
        """
        :return: Tiempo disponible de la cuenta registrada.
        """
        if not self.session:
            self.session = NautaSession()

        return Nauta.get_user_time(
            session=self.session,
            username=self.user,
        )

    def logout(self):
        """
        Cierra la sesión abierta.
        :return:
        """
        try:
            Nauta.logout(
                session=self.session,
                username=self.user,
            )
            self.session.dispose()
            self.session = None

            return
        except RequestException:
            raise LogoutException(
                "Hay problemas en la red y no se puede cerrar la session.\n"
                "Es posible que ya este desconectado."
            )

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
