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


class Action:
    LOGIN = "login_action"
    LOGOUT = "logout_action"
    LOAD_USER_INFO = "load_user_info_action"
    RECHARGE = "recharge_action"
    TRANSFER = "transfer_action"
    NAUTA_HOGAR_PAID = "nauta_hogar_paid"
    CHANGE_PASSWORD = "change_password_action"
    CHANGE_EMAIL_PASSWORD = "change_email_password_action"
    GET_CONNECTIONS = "get_connections_action"
    GET_RECHARGES = "get_recharges_action"
    GET_TRANSFERS = "get_transfers_action"
    GET_QUOTES_FUND = "get_quotes_fund_action"


class Portal:
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
    "total_time": "seconds",
    "uploaded": "bytes",
    "downloaded": "bytes",
    "total_traffic": "bytes",
    "duration": "seconds",
    "remaining_time": "seconds",
    "total_import": "float",
    "import_": "float",
    "date": "datetime",
    "start_session": "datetime",
    "end_session": "datetime"
}
