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
import requests

from PyLibSuitETECSA.utils import ATTR_TYPE
from PyLibSuitETECSA.utils.from_str import to_bytes, to_datetime, to_float, to_seconds


class SessionObject(object):
    headers_ = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'es-419,es;q=0.6',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    def __init__(self):
        self.requests_session = self.__class__._create_requests_session()

    @classmethod
    def _create_requests_session(cls):
        requests_session = requests.Session()
        requests_session.headers = cls.headers_
        return requests_session

    def __setattr__(self, __name: str, __value: Any) -> None:
        if type(__value) == str and __name in ATTR_TYPE:
            match ATTR_TYPE[__name]:
                case "str":
                    self.__dict__[__name] = __value
                case "int":
                    self.__dict__[__name] = int(__value)
                case "float":
                    self.__dict__[__name] = to_float(__value)
                case "seconds":
                    self.__dict__[__name] = to_seconds(__value)
                case "bytes":
                    self.__dict__[__name] = to_bytes(__value)
                case "datetime":
                    self.__dict__[__name] = to_datetime(__value)
                case _:
                    raise AttributeError
        else:
            self.__dict__[__name] = __value


class NautaSession(SessionObject):

    def __init__(self, login_action=None, csrfhw=None, wlanuserip=None,
                 attribute_uuid=None):
        super().__init__()
        self.login_action = login_action
        self.csrfhw = csrfhw
        self.wlanuserip = wlanuserip
        self.attribute_uuid = attribute_uuid


class UserPortalSession(SessionObject):

    def __init__(self, csrf=None):
        super().__init__()
        self.csrf = csrf

        # Attrs for normal nauta account
        self.blocking_date = None
        self.date_of_elimination = None
        self.account_type = None
        self.service_type = None
        self.credit = None
        self.time = None
        self.mail_account = None

        # Attrs for nauta home account
        self.offer = None
        self.monthly_fee = None
        self.download_speeds = None
        self.upload_speeds = None
        self.phone = None
        self.link_identifiers = None
        self.link_status = None
        self.activation_date = None
        self.blocking_date_home = None
        self.date_of_elimination_home = None
        self.quota_fund = None
        self.voucher = None
        self.debt = None

    @property
    def is_nauta_home(self):
        return bool(self.offer)
