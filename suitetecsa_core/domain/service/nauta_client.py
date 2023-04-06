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
from suitetecsa_core.core.exceptions import NautaException, NotLoggedIn
from suitetecsa_core.domain.model import NautaUser, ConnectionsSummary, RechargesSummary, TransfersSummary, \
    QuotesPaidSummary
from suitetecsa_core.repository.scrapper_provider import NautaScrapper
from suitetecsa_core.utils.nauta import time_string_to_seconds


class NautaClient:

    _username: str = None
    _password: str = None

    def __init__(self, scrapper: NautaScrapper) -> None:
        self.__scrapper = scrapper

    @property
    def credentials(self) -> tuple[str, str]:
        return self._username, self._password

    @credentials.setter
    def credentials(self, value) -> None:
        self._username, self._password = value

    @property
    def is_connected(self) -> bool:
        return self.__scrapper.is_connected

    @property
    def user_information(self) -> NautaUser:
        return self.__scrapper.user_information

    @property
    def connect_information(self) -> dict:
        if not self._username or not self._password:
            raise ValueError("username and password are required")
        if not self.check_portal_access():
            raise NautaException("There is no access to the portal")
        return self.__scrapper.get_connect_information(self._username, self._password)

    @property
    def data_session(self) -> dict[str, str]:
        if not self.__scrapper.is_logged_in:
            raise NotLoggedIn("You are not logged in")
        return self.__scrapper.data_session

    @data_session.setter
    def data_session(self, value) -> None:
        self.__scrapper.data_session = value

    @property
    def captcha_image(self) -> bytes:
        return self.__scrapper.captcha_image

    @property
    def remaining_time(self) -> int:
        return time_string_to_seconds(self.__scrapper.remaining_time)

    def check_portal_access(self) -> bool:
        return self.__scrapper.check_portal_access()

    def connect(self) -> None:
        if not self._username or not self._password:
            raise ValueError("username and password are required")
        if not self.check_portal_access():
            raise NautaException("There is no access to the portal")
        self.__scrapper.connect(self._username, self._password)

    def disconnect(self) -> None:
        if not self.__scrapper.is_logged_in:
            raise NotLoggedIn("You are not logged in")
        self.__scrapper.disconnect()

    def login(self, captcha_code: str) -> NautaUser:
        if not self._username or not self._password or not captcha_code:
            raise ValueError("username and password are required")
        if not self.check_portal_access():
            raise NautaException("There is no access to the portal")
        return self.__scrapper.login(self._username, self._password, captcha_code)

    def logout(self):
        if not self.__scrapper.is_user_logged_in:
            raise NotLoggedIn("You are not logged in")
        self.__scrapper.logout()

    def to_up(self, recharge_code: str) -> None:
        self.__scrapper.to_up(recharge_code)

    def transfer(self, amount: float, destination_account: str) -> None:
        self.__scrapper.transfer(amount, self._password, destination_account)

    def pay_nauta_home(self, amount: float) -> None:
        if not self.__scrapper.is_nauta_home:
            raise NautaException("Operation not allowed for this account")
        self.__scrapper.transfer(amount, self._password)

    def change_password(self, new_password: str) -> None:
        self.__scrapper.change_password(self._password, new_password)

    def change_email_password(self, old_password: str, new_password: str) -> None:
        self.__scrapper.change_email_password(old_password, new_password)

    def get_connections_summary(self, year: int, month: int) -> ConnectionsSummary:
        return self.__scrapper.get_connections_summary(year, month)

    def get_recharges_summary(self, year: int, month: int) -> RechargesSummary:
        return self.__scrapper.get_recharges_summary(year, month)

    def get_transfers_summary(self, year: int, month: int) -> TransfersSummary:
        return self.__scrapper.get_transfers_summary(year, month)

    def get_quotes_paid_summary(self, year: int, month: int) -> QuotesPaidSummary:
        return self.__scrapper.get_quotes_paid_summary(year, month)

    def get_connections(
            self, year: int, month: int, summary: ConnectionsSummary = None, large: int = 0, _reversed: bool = False
    ):
        return self.__scrapper.get_connections(year, month, summary, large, _reversed)

    def get_recharges(
            self, year: int, month: int, summary: RechargesSummary = None, large: int = 0, _reversed: bool = False
    ):
        return self.__scrapper.get_recharges(year, month, summary, large, _reversed)

    def get_transfers(
            self, year: int, month: int, summary: TransfersSummary = None, large: int = 0, _reversed: bool = False
    ):
        return self.__scrapper.get_transfers(year, month, summary, large, _reversed)

    def get_quotes_paid(
            self, year: int, month: int, summary: QuotesPaidSummary = None, large: int = 0, _reversed: bool = False
    ):
        return self.__scrapper.get_quotes_paid(year, month, summary, large, _reversed)
