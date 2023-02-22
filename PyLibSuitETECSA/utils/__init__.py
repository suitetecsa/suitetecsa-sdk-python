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
import enum


class Action(enum.Enum):

    LOGIN = 8
    LOGOUT = 12
    LOAD_USER_INFO = 4
    RECHARGE = 6
    TRANSFER = 3
    NAUTA_HOGAR_PAID = 5
    CHANGE_PASSWORD = 2
    CHANGE_EMAIL_PASSWORD = 6
    GET_CONNECTIONS = 10
    GET_RECHARGES = 9
    GET_TRANSFERS = 11
    GET_QUOTES_FUND = 7


class Portal(enum.Enum):

    USER_PORTAL = 0
    NAUTA = 1


VARIOUS_ERRORS = "Se han detectado algunos errores."

# Un diccionario que contiene dos expresiones regulares. El primero se usa para
# encontrar el mensaje de error en el portal de usuario, y el segundo se usa
# para encontrar el mensaje de error en el portal Nauta.
RE_FAIL_REASON = {
    Portal.USER_PORTAL: re.compile(r"toastr\.error\('(?P<reason>[^']*?)'\)"),
    Portal.NAUTA: re.compile(r'alert\("(?P<reason>[^"]*?)"\)')
}
RE_SUCCESS_ACTION = re.compile(r"toastr\.success\('(?P<reason>[^']*?)'\)")

RE_DATETIME_FORMAT_ETECSA = re.compile(
    r"(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})"
    r"\s(?P<hour>\d{1,2}):\d{1,2}:\d{1,2}"
)

ATTR_TYPE = {
    "year_month_selected": "str",
    "channel": "str",
    "type_": "str",
    "office": "str",
    "destiny_account": "str",
    "status": "str",
    "message": "str",
    "count": "int",
    "phone": "int",
    "time": "seconds",
    "total_time": "seconds",
    "duration": "seconds",
    "remaining_time": "seconds",
    "uploaded": "bytes",
    "downloaded": "bytes",
    "total_traffic": "bytes",
    "download_speeds": "bytes",
    "upload_speeds": "bytes",
    "total_import": "float",
    "import_": "float",
    "credit": "float",
    "monthly_fee": "float",
    "quota_fund": "float",
    "voucher": "float",
    "debt": "float",
    "date": "datetime",
    "start_session": "datetime",
    "end_session": "datetime",
    "blocking_date": "datetime",
    "date_of_elimination": "datetime",
    "activation_date": "datetime",
    "blocking_date_home": "datetime",
    "date_of_elimination_home": "datetime"
}
