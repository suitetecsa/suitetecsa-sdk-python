#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import logging
import math
import re
from typing import Type, Any

import bs4
import requests
from bs4 import ResultSet, Tag
from requests import Session
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

from suitetecsa_core import Action, Portal
from suitetecsa_core.exceptions import ChangePasswordException, ConnectionException, \
    GetInfoException, LoginException, LogoutException, InvalidMethod, NotLoggedIn, PreLoginException, \
    RechargeException, SessionLoadException, TransferException
from suitetecsa_core.utils import api_response, make_actions_summary
from suitetecsa_core.utils.parser import parse_errors
from suitetecsa_core.utils.nauta import verify_session_data

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

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s :: %(levelname)s :: %(message)s"
)
logger = logging.getLogger()


class NautaCore:
    _headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                  'image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'es-419,es;q=0.6',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    _connect_domain: bytes = b'secure.etecsa.net'
    _base_url: dict = {
        Portal.CONNECT: f'https://{_connect_domain.decode()}:8443/',
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

    _session: Session
    _portal_manager: Portal
    _use_api_response: bool
    _login_action: str
    _username: str
    _password: str
    _csrf: str = None
    _wlanuserip: str = None
    _CSRFHW: str = None
    _ATTRIBUTE_UUID: str = None
    _logged_in: bool = False

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value) -> None:
        self._username = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value) -> None:
        self._password = value

    @property
    def credentials(self) -> tuple[str, str]:
        return self._username, self._password

    @credentials.setter
    def credentials(self, value: tuple[str, str]) -> None:
        self._username, self._password = value

    def _make_url(
            self, action: Action,
            get_action: bool = False,
            sub_action: str = None,
            year_month_selected: str = None,
            count: int = None,
            page: int = None
    ) -> str:
        if action == Action.CHECK_CONNECTION:
            return self._portals_urls[self._portal_manager][action]
        elif not get_action:
            return f'{self._base_url[self._portal_manager]}' \
                   f'{self._portals_urls[self._portal_manager][action]}'
        else:
            url = f'{self._base_url[self._portal_manager]}' \
                  f'{self._portals_urls[self._portal_manager][action][sub_action]}'
            match sub_action:
                case 'base' | 'summary':
                    return url
                case 'list':
                    if not year_month_selected:
                        pass
                    if not count:
                        pass
                    else:
                        return f'{url}{year_month_selected}/{count}' \
                            if not page \
                            else f'{url}{year_month_selected}/{count}/{page}'

    def _check_errors(
            self, response: requests.Response,
            exc: Type[Exception],
            msg: str,
            find_errors: bool = True
    ) -> bs4.BeautifulSoup:
        if not response.ok:
            raise exc(
                f"{msg}: {response.status_code} :: {response.reason}"
            )

        soup = bs4.BeautifulSoup(response.text, 'html5lib')

        if find_errors:
            error = parse_errors(soup, self._portal_manager)
            if error:
                raise exc(
                    f'{msg} :: {error}'
                )

        return soup

    @staticmethod
    def _get_inputs(form_soup: bs4.Tag) -> dict:
        return {
            _["name"]: _.get("value", default=None)
            for _ in form_soup.select("input[name]")
        }

    @staticmethod
    def _get_csrf(soup: bs4.BeautifulSoup) -> str:
        return soup.select_one('input[name=csrf]').attrs["value"]

    def _get_information_user(self, soup: bs4.BeautifulSoup) -> dict:
        keys = [
            'username', 'blocking_date', 'date_of_elimination',
            'account_type', 'service_type', 'credit', 'time',
            'mail_account', 'offer', 'monthly_fee', 'download_speeds',
            'upload_speeds', 'phone', 'link_identifiers',
            'link_status', 'activation_date', 'blocking_date_home',
            'date_of_elimination_home', 'quote_paid', 'voucher', 'debt'
        ]
        if not self._logged_in:
            raise GetInfoException(
                'This session is not logged in'
            )
        user_info = {}
        for _index, attr in enumerate(
                soup.select_one('.z-depth-1').select('.m6')
        ):
            user_info = {
                **user_info,
                keys[_index]: attr.select_one('p').text.strip()
            }
        return {'user_information': user_info} \
            if self._use_api_response \
            else user_info

    @staticmethod
    def _get_information_connect(soup: bs4.BeautifulSoup) -> dict:
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

    @property
    def session_data(self) -> dict:
        if not self._logged_in:
            raise NotLoggedIn(
                'This session is not logged_in'
            )
        if self._portal_manager != Portal.CONNECT:
            raise InvalidMethod(
                'This method is not valid for this portal'
            )
        return {
            'username': self._username,
            'cookies': dict_from_cookiejar(self._session.cookies),
            'wlanuserip': self._wlanuserip,
            'CSRFHW': self._CSRFHW,
            'ATTRIBUTE_UUID': self._ATTRIBUTE_UUID
        }

    @session_data.setter
    def session_data(self, value: dict) -> None:
        if self._portal_manager != Portal.CONNECT:
            raise InvalidMethod(
                'This method is not valid for this portal'
            )
        if self._logged_in:
            raise SessionLoadException(
                'You are logged_in'
            )

        verify_session_data(data=value)

        self._username = value["username"]
        self._session.cookies = cookiejar_from_dict(value['cookies'])
        self._wlanuserip = value['wlanuserip']
        self._CSRFHW = value['CSRFHW']
        self._ATTRIBUTE_UUID = value['ATTRIBUTE_UUID']
        self._logged_in = True


class NautaSession(NautaCore):

    def __init__(
            self,
            portal_manager: Portal = Portal.CONNECT,
            use_api_response: bool = False
    ) -> None:
        self._portal_manager = portal_manager
        self._use_api_response = use_api_response

    def __post_action(
            self, data: dict,
            action: Action,
            url: str = None
    ) -> requests.Response | None:
        if not url:
            url = self._make_url(action=action)
        logger.info(f'post action to {url}')
        return self._session.post(url, data=data)

    def is_connected(self) -> bool:
        r = requests.get(
            self._make_url(action=Action.CHECK_CONNECTION)
        )
        return self._connect_domain not in r.content

    def get_captcha(self) -> bytes:
        logger.debug('Obtaining the captcha image')
        response = self._session.get(
            'https://www.portal.nauta.cu/captcha/?'
        )
        self._check_errors(
            response=response,
            exc=ConnectionException,
            msg='Fail to obtain the captcha image',
            find_errors=False
        )
        logger.debug('Obtained the captcha image')
        return response.content

    def __init_connect(self) -> tuple[None, None]:
        logger.debug(
            f'Action get to {self._make_url(Action.CHECK_CONNECTION)}'
        )
        soup = self._check_errors(
            response=self._session.get(
                self._make_url(Action.CHECK_CONNECTION)
            ),
            exc=PreLoginException,
            msg='Fail to create session',
            find_errors=False
        )
        action = soup.form["action"]
        data = self._get_inputs(soup)

        logger.debug(f'Action post to {action}')
        soup = self._check_errors(
            response=self._session.post(action, data),
            exc=PreLoginException,
            msg='Fail to create session',
            find_errors=False
        )
        form_soup = soup.select_one("#formulario")
        self._login_action = form_soup["action"]
        data = self._get_inputs(form_soup)

        self._CSRFHW = data["CSRFHW"]
        logger.debug(f'Obtained the csrfhw token: {self._CSRFHW}')
        self._wlanuserip = data["wlanuserip"]
        logger.debug(f'Obtained the wlanuserip parameter: {self._wlanuserip}')

        return None, None

    def __init_user(self) -> tuple[None, None]:
        self._session.headers = self._headers
        logger.debug(
            f'Action get to {self._make_url(Action.LOGIN)}'
        )
        soup = self._check_errors(
            response=self._session.get(
                self._make_url(Action.LOGIN)
            ),
            exc=PreLoginException,
            msg='Fail to create session'
        )

        self._csrf = self._get_csrf(
            soup=soup
        )
        logger.debug(f'Obtained csrf token: {self._csrf}')

        return None, None

    @api_response
    def init(self) -> tuple[None, None]:
        self._session = Session()
        match self._portal_manager:
            case Portal.CONNECT:
                return self.__init_connect()
            case Portal.USER:
                return self.__init_user()
            case _:
                raise PreLoginException

    @api_response
    def get_user_information(self) -> tuple[Action, dict]:
        data = self._get_information_connect(
            soup=self._check_errors(
                response=self.__post_action(
                    data={
                        'username': self._username,
                        'password': self._password,
                        'wlanuserip': self._wlanuserip,
                        'CSRFHW': self._CSRFHW,
                        'lang': ''
                    },
                    action=Action.LOAD_USER_INFORMATION
                ),
                exc=GetInfoException,
                msg='Fail to obtain user information'
            )
        ) if self._portal_manager == Portal.CONNECT \
            else self._get_information_user(
            soup=self._check_errors(
                response=self._session.get(
                    self._make_url(
                        action=Action.LOAD_USER_INFORMATION
                    )
                ),
                exc=GetInfoException,
                msg='Fail to obtain user information'
            )
        )
        return Action.LOAD_USER_INFORMATION, data

    def __connect(self) -> None:
        if not self._CSRFHW or not self._wlanuserip:
            self.init()
        if not self._username or not self._password:
            pass
        r = self._session.post(
            self._login_action,
            {
                "CSRFHW": self._CSRFHW,
                "wlanuserip": self._wlanuserip,
                "username": self._username,
                "password": self._password
            }
        )
        if not r.ok:
            pass
        if "online.do" not in r.url:
            pass
        self._ATTRIBUTE_UUID = re.search(
            r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', r.text).group(1)
        self._logged_in = True

    def __login(self, captcha_code: str) -> dict:
        if not captcha_code:
            raise LoginException(
                'Captca code is required'
            )
        soup = self._check_errors(
            response=self.__post_action(
                {
                    'csrf': self._csrf,
                    'login_user': self._username,
                    'password_user': self._password,
                    'captcha': captcha_code.upper(),
                    'btn_submit': ''
                },
                Action.LOGIN
            ),
            exc=LoginException,
            msg='Fail to login'
        )
        self._logged_in = True
        return {
            'logged_in': True,
            **self._get_information_user(soup)
        }

    @api_response
    def login(self, captcha_code: str = None) -> tuple[Action, dict | None]:
        data = self.__connect() \
            if self._portal_manager == Portal.CONNECT \
            else self.__login(captcha_code)
        return Action.LOGIN, data

    @api_response
    def recharge(self, recharge_code: str) -> tuple[Action, None]:
        data = {
            'csrf': self._get_csrf(
                soup=self._check_errors(
                    response=self._session.get(
                        url=self._make_url(
                            action=Action.RECHARGE
                        )
                    ),
                    exc=RechargeException,
                    msg='Fail to recharge the account balance'
                )
            ),
            'recharge_code': recharge_code,
            'btn_submit': ''
        }
        self._check_errors(
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
            self, mount_to_transfer: float,
            account_to_transfer: str = None,
            nauta_hogar_paid: bool = False
    ) -> tuple[Action, None]:
        action = Action.TRANSFER if not nauta_hogar_paid \
            else Action.NAUTA_HOGAR_PAID
        data = {
            'csrf': self._get_csrf(
                soup=self._check_errors(
                    response=self._session.get(
                        url=self._make_url(
                            action=action
                        )
                    ),
                    exc=TransferException,
                    msg='Fail to transfer balance'
                )
            ),
            'transfer': f'{mount_to_transfer:.2f}'.replace('.', ','),
            'password_user': self._password,
            'action': 'checkdata'
        }
        if not nauta_hogar_paid:
            data["id_cuenta"] = account_to_transfer

        self._check_errors(
            response=self.__post_action(
                data=data,
                action=action
            ),
            exc=TransferException,
            msg='Fail to transfer'
        )
        return Action.TRANSFER, None

    @api_response
    def change_password(self, new_password: str) -> tuple[Action, None]:
        data = {
            'csrf': self._get_csrf(
                soup=self._check_errors(
                    response=self._session.get(
                        url=self._make_url(
                            action=Action.CHANGE_PASSWORD
                        )
                    ),
                    exc=ChangePasswordException,
                    msg="Fail to change password"
                )
            ),
            'old_password': self._password,
            'new_password': new_password,
            'repeat_new_password': new_password,
            'btn_submit': ''
        }
        self._check_errors(
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
    ) -> tuple[Action, None]:
        data = {
            'csrf': self._get_csrf(
                soup=self._check_errors(
                    response=self._session.get(
                        url=self._make_url(
                            action=Action.CHANGE_EMAIL_PASSWORD
                        )
                    ),
                    exc=ChangePasswordException,
                    msg="Fail to change password"
                )
            ),
            'old_password': old_password,
            'new_password': new_password,
            'repeat_new_password': new_password,
            'btn_submit': ''
        }
        self._check_errors(
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
    ) -> ResultSet[Tag]:
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

        soup = self._check_errors(
            response=self.__post_action(
                data={
                    'csrf': self._get_csrf(
                        soup=self._check_errors(
                            response=self._session.get(
                                url=self._make_url(
                                    action=action,
                                    get_action=True,
                                    sub_action='base'
                                )
                            ),
                            exc=GetInfoException,
                            msg=__err_msgs[action]
                        )
                    ),
                    'year_month': __year_month,
                    'list_type': __lists[action]
                },
                action=action,
                url=self._make_url(
                    action=action,
                    get_action=True,
                    sub_action='summary'
                )
            ),
            exc=GetInfoException,
            msg=__err_msgs[action]
        )
        return soup.select_one('#content').select('.card-content')

    def __get_t_body(self, url: str) -> bs4.Tag:
        soup = self._check_errors(
            response=self._session.get(
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
            count: int,
            large: int = 0,
            _reversed: bool = False
    ) -> list[bs4.Tag]:
        row_list = []
        totals_pages = math.ceil(count / 14)
        current_page = totals_pages if _reversed else 1
        if large == 0:
            large = count

        while len(row_list) < large and current_page >= 1:
            page = current_page if current_page != 1 else None
            url = self._make_url(
                action=action,
                get_action=True,
                sub_action='list',
                year_month_selected=year_month_selected,
                count=count,
                page=page
            )
            logger.info(f'post action to {url}')
            t_body = self.__get_t_body(url=url)
            if t_body:
                rows_page = [row for row in reversed(t_body.select('tr'))] \
                    if _reversed else \
                    [row for row in t_body.select('tr')]
                row_list.extend(
                    rows_page[:abs(large) - len(row_list)]
                )
            current_page += -1 if _reversed else 1
        return row_list

    @api_response
    def _get_connections_summary(
            self, year: int,
            month: int
    ) -> tuple[Action, dict[str, dict[str, Any]]]:
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
            if self._use_api_response \
            else __summary
        return Action.GET_CONNECTIONS, __data

    @api_response
    def get_connections(
            self, year: int, month: int, summary: dict = None, large: int = 0, _reversed: bool = False
    ) -> tuple[Action, dict[str, tuple[Action, dict[str, dict[str, Any]]]]]:

        __summary = self._get_connections_summary(
            year=year,
            month=month
        ) if not summary else summary
        __summary = __summary['connections_summary'] \
            if self._use_api_response and not summary else __summary
        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_CONNECTIONS,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count'],
                large=large,
                _reversed=_reversed
            )
            data = None
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
                data = {
                    'connections_summary': __summary,
                    'connections': __connections
                }
        else:
            data = {
                'connections_summary': __summary,
                'connections': []
            }
        return Action.GET_CONNECTIONS, data

    @api_response
    def _get_recharges_summary(
            self, year: int,
            month: int
    ) -> tuple[Action, dict[str, dict[str, Any]]]:
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

        data = {'recharges_summary': __summary} \
            if self._use_api_response \
            else __summary
        return Action.GET_RECHARGES, data

    @api_response
    def get_recharges(
            self, year: int, month: int, summary: dict = None, large: int = 0, _reversed: bool = False
    ) -> tuple[Action, dict[str, list[dict[str, Any]]]]:
        __summary = self._get_recharges_summary(
            year=year,
            month=month
        ) if not summary else summary
        __summary = __summary['recharges_summary'] \
            if self._use_api_response and not summary else __summary
        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_RECHARGES,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count'],
                large=large,
                _reversed=_reversed
            )

            data = None
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
                data = {
                    'recharges_summary': __summary,
                    'recharges': __recharges
                }
        else:
            data = {
                'recharges_summary': __summary,
                'recharges': []
            }

        return Action.GET_RECHARGES, data

    @api_response
    def _get_transfers_summary(
            self, year: int,
            month: int
    ) -> tuple[Action, dict[str, dict[str, Any]]]:
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

        data = {'transfers_summary': __summary} \
            if self._use_api_response \
            else __summary
        return Action.GET_TRANSFERS, data

    @api_response
    def get_transfers(
            self, year: int, month: int, summary: dict = None, large: int = 0, _reversed: bool = False
    ) -> tuple[Action, Any]:
        __summary = self._get_transfers_summary(
            year=year,
            month=month
        ) if not summary else summary
        __summary = __summary['transfers_summary'] \
            if self._use_api_response and not summary else __summary
        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_TRANSFERS,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count'],
                large=large,
                _reversed=_reversed
            )

            data = None
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
                data = {
                    'transfers_summary': __summary,
                    'transfers': __transfers
                }
        else:
            data = {
                'transfers_summary': __summary,
                'transfers': []
            }

        return Action.GET_TRANSFERS, data

    @api_response
    def _get_quotes_paid_summary(
            self, year: int,
            month: int
    ) -> tuple[Action, dict[str, dict[str, Any]]]:
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

        data = {'quotes_paid_summary': __summary} \
            if self._use_api_response \
            else __summary
        return Action.GET_QUOTES_PAID, data

    @api_response
    def get_quotes_paid(
            self, year: int,
            month: int,
            summary: dict = None,
            large: int = 0,
            _reversed: bool = False
    ) -> tuple[Action, Any]:
        __summary = self._get_quotes_paid_summary(
            year=year,
            month=month
        ) if not summary else summary
        __summary = __summary['quotes_paid_summary'] \
            if self._use_api_response and not summary else __summary

        if __summary['count'] != 0:
            __rows = self.__parse_action_rows(
                action=Action.GET_QUOTES_PAID,
                year_month_selected=__summary['year_month_selected'],
                count=__summary['count'],
                large=large,
                _reversed=_reversed
            )

            data = None
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
                data = {
                    'quotes_paid_summary': __summary,
                    'quotes_paid': __quotes_paid
                }
        else:
            data = {
                'quotes_paid_summary': __summary,
                'quotes_paid': []
            }

        return Action.GET_QUOTES_PAID, data

    @api_response
    def get_lasts(self, action: Action, large: int = 5) -> tuple[Action, dict[Any, Any]]:

        def get_current_year_month():
            """
            Returns a generator that yields the current year and month, and then the previous months in each
            subsequent call.

            :return: a tuple with two integers representing the year and month respectively
            """
            now = datetime.datetime.now()
            while True:
                yield now.year, now.month
                now = now.replace(day=1) - datetime.timedelta(days=1)

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

        total_count = 0
        retrieved_count = 0
        actions = []
        __summaries = []
        generator = get_current_year_month()
        while total_count < large:
            year, month = next(generator)
            current_summary = getattr(self, f'_get_{action.value}_summary')(year=year, month=month)
            if self.use_api_response:
                current_summary = current_summary[f'{action.value}_summary']
            total_count += current_summary["count"]
            __summaries.append(current_summary)
        for summary in __summaries:
            count = large - retrieved_count if retrieved_count + summary["count"] > large else 0
            retrieved_actions: list = getattr(self, f'get_{action.value}')(
                year=0,
                month=0,
                summary=summary,
                large=count,
                _reversed=True
            )
            if self.use_api_response:
                retrieved_actions = retrieved_actions[action.value]
            actions.extend(reversed(retrieved_actions) if count == 0 else retrieved_actions)

        return action, {
            __summary_keys[action]: make_actions_summary(
                action_type=action,
                actions=actions
            ),
            __actions_keys[action]: actions
        }

    def disconnect(self) -> dict[str, Any] | None:
        if not self._logged_in:
            if self._use_api_response:
                return {
                    "status": "error",
                    "reason": "reason"
                }
            else:
                pass

        r = self._session.get(
            url=self._make_url(
                action=Action.LOGOUT
            ),
            params={
                'username': self._username,
                'wlanuserip': self._wlanuserip,
                'CSRFHW': self._CSRFHW,
                'ATTRIBUTE_UUID': self._ATTRIBUTE_UUID
            }
        )

        if not r.ok:
            if self._use_api_response:
                return {
                    "status": "error",
                    "status_code": r.status_code,
                    "reason": r.reason
                }
            else:
                pass
        if "SUCCESS" not in r.text:
            if self._use_api_response:
                return {
                    "status": "error",
                    "reason": "reason"
                }
            else:
                pass

        self._logged_in = False
        self._ATTRIBUTE_UUID = str()

        return {
            "status": "success",
            "logged_in": False
        } if self._use_api_response else None

    @api_response
    def get_remaining_time(self, in_seconds: bool = False) -> tuple[Action, dict[str, Any]]:
        __remaining_seconds: int
        soup = self._check_errors(
            response=self._session.post(
                self._make_url(action=Action.LOAD_USER_INFORMATION),
                {
                    'op': 'getLeftTime',
                    'username': self._username,
                    'wlanuserip': self._wlanuserip,
                    'CSRFHW': self._CSRFHW,
                    'ATTRIBUTE_UUID': self._ATTRIBUTE_UUID
                }
            ),
            exc=LogoutException,
            msg='Fail to logout',
            find_errors=False
        )

        hours, minutes, seconds = [int(number)
                                   for number in soup.text.strip().split(':')]
        remaining_time = soup.text.strip()
        __remaining_seconds = hours * 3600 + minutes * 60 + seconds \
            if in_seconds else None

        return Action.LOGOUT, {
            'remaining_time': remaining_time,
            'remaining_seconds': __remaining_seconds
        }

    @property
    def use_api_response(self):
        return self._use_api_response

    @property
    def portal_manager(self):
        return self._portal_manager

    @property
    def login_action(self):
        return self._login_action

    @property
    def csrfhw(self):
        return self._CSRFHW

    @property
    def wlanuserip(self):
        return self._wlanuserip

    @property
    def csrf(self):
        return self._csrf

    @property
    def session(self):
        return self._session

    @property
    def logged_in(self):
        return self._logged_in

    @property
    def attribute_uuid(self):
        return self._ATTRIBUTE_UUID
