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
import os, sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import datetime
from unittest.mock import patch, MagicMock

import pytest
from PyLibSuitETECSA.api import UserPortalClient

from PyLibSuitETECSA.core.exception import LoginException, RechargeException, \
    TransferException, ChangePasswordException
from PyLibSuitETECSA.core.protocol import UserPortal
from PyLibSuitETECSA.core.session import UserPortalSession

_assets_dir = os.path.join(
    os.path.dirname(__file__),
    "assets"
)


def read_asset(asset_name):
    with open(os.path.join(_assets_dir, asset_name)) as fp:
        return fp.read()


@pytest.fixture
def patcher():
    return patch("PyLibSuitETECSA.core.session.requests")


@pytest.fixture
def user_portal_cli():
    user_portal_cli = UserPortalClient()
    return user_portal_cli


LOGIN_PAGE_HTML = read_asset("login_page.html")
LOGIN_ACTION_FAIL_HTML = read_asset("login_action_fail.html")
LOGIN_ACTION_FAIL_BAD_ACCOUNT_HTML = read_asset(
    "login_action_fail_bad_account.html"
)
SERVICE_DETAIL_HTML = read_asset("service_detail.html")
CONNECTONS_SUMMARY_HTML = read_asset("connections_summary.html")
CONNECTONS_LIST_PAGE1_HTML = read_asset("connection_list_page1.html")
CONNECTONS_LIST_PAGE2_HTML = read_asset("connection_list_page2.html")
CONNECTONS_LIST_PAGE3_HTML = read_asset("connection_list_page3.html")
CONNECTONS_LIST_PAGE4_HTML = read_asset("connection_list_page4.html")
USER_INFO_HTML = read_asset("user_info.html")
RECHARGE_HTML = read_asset("recharge_action.html")
RECHARGE_SUCCESS_HTML = read_asset("recharge_action_successful.html")
RECHARGE_FAIL_HTML = read_asset("recharge_action_fail.html")
TRANSFER_HTML = read_asset("transfer_action.html")
TRANSFER_SUCCESS_HTML = read_asset("transfer_action_success.html")
TRANSFER_FAIL_HTML = read_asset("transfer_action_fail.html")
CHANGE_PASSWORD_HTML = read_asset("change_password_action.html")
CHANGE_PASSWORD_SUCCESS_HTML = read_asset(
    "change_password_action_success.html"
)
CHANGE_PASSWORD_FAIL_HTML = read_asset("change_password_action_fail.html")


def test_create_valid_session(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=LOGIN_PAGE_HTML)
    mock_request.Session().get = MagicMock(return_value=mock_response)

    user_portal_cli.init_session()
    session = user_portal_cli.session

    csrf_token = 'security628645155dcb3'

    patcher.stop()
    assert session.csrf == csrf_token


def test_login_successful(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=USER_INFO_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)

    user_portal_cli.session = UserPortalSession()

    user_portal_cli.username = "pepito.perez@nauta.com.cu"
    user_portal_cli.password = "SomePassword"

    user_portal_cli.login("captcha")
    user_info = user_portal_cli.session

    patcher.stop()

    assert user_info.account_type == 'Prepago recargable'
    assert user_info.date_of_elimination == '31/12/2037'
    assert user_info.credit == '$147,61 CUP'
    assert user_info.time == '11:48:31'
    assert user_info.offer == 'NH RESIDENCIAL 1024/512 (40h) - RP'
    assert user_info.upload_speeds == '512 kbps'
    assert user_info.link_identifiers == 'H ED######'
    assert user_info.activation_date == '25/02/2021'
    assert user_info.date_of_elimination_home == '07/03/2023'
    assert user_info.monthly_fee == '$300,00 CUP'


def test_login_action_fail(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=LOGIN_ACTION_FAIL_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)

    user_portal_cli.session = UserPortalSession()

    user_portal_cli.username = "pepito.perez@nauta.com.cu"
    user_portal_cli.password = "SomePassword"

    with pytest.raises(LoginException) as e:
        user_portal_cli.login("captcha")
    
    patcher.stop()

    assert "['Olvidó llenar el campo usuario', " \
           "'Olvidó llenar el campo contraseña', " \
           "'Olvidó llenar el campo Código Captcha']" == str(e.value)


def test_login_action_fail_for_bad_account(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(
        status_code=200,
        text=LOGIN_ACTION_FAIL_BAD_ACCOUNT_HTML
    )
    mock_request.Session().post = MagicMock(return_value=mock_response)

    user_portal_cli.session = UserPortalSession()

    user_portal_cli.username = "pepito.perez@nauta.com.cu"
    user_portal_cli.password = "SomePassword"

    with pytest.raises(LoginException) as e:
        user_portal_cli.login("captcha")

    patcher.stop()

    assert "Usuario desconocido o contraseña incorrecta" == str(e.value)


def test_get_valid_user_info(patcher):
    mock_request = patcher.start()
    mock_response = MagicMock(
        status_code=200,
        text=USER_INFO_HTML,
        url="https://www.portal.nauta.cu/useraaa/user_info"
    )
    mock_request.Session().get = MagicMock(return_value=mock_response)

    session = UserPortalSession()
    UserPortal.load_user_info(session)
    user_info = session

    patcher.stop()

    assert user_info.account_type == 'Prepago recargable'
    assert user_info.date_of_elimination == '31/12/2037'
    assert user_info.credit == '$147,61 CUP'
    assert user_info.time == '11:48:31'
    assert user_info.offer == 'NH RESIDENCIAL 1024/512 (40h) - RP'
    assert user_info.upload_speeds == '512 kbps'
    assert user_info.link_identifiers == 'H ED######'
    assert user_info.activation_date == '25/02/2021'
    assert user_info.date_of_elimination_home == '07/03/2023'
    assert user_info.monthly_fee == '$300,00 CUP'


def test_recharge_action_successful(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=RECHARGE_SUCCESS_HTML)
    mock_response_get = MagicMock(status_code=200, text=RECHARGE_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    is_confirmed = user_portal_cli.recharge("01234567890123456")
    assert is_confirmed.status == 'success'


def test_recharge_action_fail(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=RECHARGE_FAIL_HTML)
    mock_response_get = MagicMock(status_code=200, text=RECHARGE_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    with pytest.raises(RechargeException) as e:
        user_portal_cli.recharge("01234567890123456")

    patcher.stop()

    assert "El código de recarga es incorrecto." == str(e.value)


def test_transfer_action_successful(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=TRANSFER_SUCCESS_HTML)
    mock_response_get = MagicMock(status_code=200, text=TRANSFER_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    is_confirmed = user_portal_cli.transfer(24, "pepita@nauta.com.cu")
    assert is_confirmed.status == 'success'


def test_transfer_action_fail(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=TRANSFER_FAIL_HTML)
    mock_response_get = MagicMock(status_code=200, text=TRANSFER_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    with pytest.raises(TransferException) as e:
        user_portal_cli.transfer(24, "pepita@nauta.com.cu")

    patcher.stop()

    assert "['El campo saldo a transferir debe ser menor o igual que 1318']" \
           == str(e.value)


def test_change_password_action_successful(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(
        status_code=200,
        text=CHANGE_PASSWORD_SUCCESS_HTML
    )
    mock_response_get = MagicMock(status_code=200, text=CHANGE_PASSWORD_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    is_confirmed = user_portal_cli.change_password("some_password")
    assert is_confirmed.status == 'success'


def test_change_password_action_fail(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=CHANGE_PASSWORD_FAIL_HTML)
    mock_response_get = MagicMock(status_code=200, text=CHANGE_PASSWORD_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    with pytest.raises(ChangePasswordException) as e:
        user_portal_cli.change_password("some_password")

    patcher.stop()

    assert "Se han detectado algunos errores de validación de la " \
           "información.El campo nueva contraseña no es una contraseña " \
           "fuerte. Debe tener números, caracteres especiales, mayúsculas, " \
           "minúsculas y una longitud mínima de 8 caracteres y máxima de 20." \
           == str(e.value)


def test_change_email_password_action_successful(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(
        status_code=200,
        text=CHANGE_PASSWORD_SUCCESS_HTML
    )
    mock_response_get = MagicMock(status_code=200, text=CHANGE_PASSWORD_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    is_confirmed = user_portal_cli.change_email_password("some_password")
    assert is_confirmed.status == 'success'


def test_change_email_password_action_fail(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=CHANGE_PASSWORD_FAIL_HTML)
    mock_response_get = MagicMock(status_code=200, text=CHANGE_PASSWORD_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)
    mock_request.Session().get = MagicMock(return_value=mock_response_get)

    user_portal_cli.session = UserPortalSession()
    with pytest.raises(ChangePasswordException) as e:
        user_portal_cli.change_email_password("some_password")

    patcher.stop()

    assert "Se han detectado algunos errores de validación de la " \
           "información.El campo nueva contraseña no es una contraseña " \
           "fuerte. Debe tener números, caracteres especiales, mayúsculas, " \
           "minúsculas y una longitud mínima de 8 caracteres y máxima de 20." \
           == str(e.value)


def test_get_valid_connections(patcher, user_portal_cli):

    texts = {
        "https://www.portal.nauta.cu/useraaa/service_detail/":
        SERVICE_DETAIL_HTML,
        "https://www.portal.nauta.cu/useraaa/service_detail_list/2022-12/47":
        CONNECTONS_LIST_PAGE1_HTML,
        "https://www.portal.nauta.cu/useraaa/service_detail_list/2022-12/2":
        CONNECTONS_LIST_PAGE2_HTML,
        "https://www.portal.nauta.cu/useraaa/service_detail_list/2022-12/3":
        CONNECTONS_LIST_PAGE3_HTML,
        "https://www.portal.nauta.cu/useraaa/service_detail_list/2022-12/4":
        CONNECTONS_LIST_PAGE4_HTML,
    }

    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )

    def side_effect(value: str):
        mock_response_get.text = texts[value]
        return mock_response_get

    mock_response_post = MagicMock(
        status_code=200,
        text=CONNECTONS_SUMMARY_HTML
    )
    mock_request.Session().get = MagicMock(side_effect=side_effect)
    mock_request.Session().post = MagicMock(return_value=mock_response_post)

    user_portal_cli.session = UserPortalSession()
    connection = user_portal_cli.get_connections(2022, 12)[-1]

    print(connection.start_session)

    patcher.stop()

    assert type(connection.start_session) == datetime.datetime
