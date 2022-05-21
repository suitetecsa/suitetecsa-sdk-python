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
import os
from unittest.mock import patch, MagicMock

import pytest
from PyLibSuitETECSA.api import UserPortalClient

from PyLibSuitETECSA.core.exception import LoginException
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
SERVICE_DETAIL_LIST_HTML = read_asset("service_detail_list.html")
USER_INFO_HTML = read_asset("user_info.html")


def test_create_valid_session(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=LOGIN_PAGE_HTML)
    mock_request.Session().get = MagicMock(return_value=mock_response)

    user_portal_cli.init_session()
    session = user_portal_cli.session.__dict__
    session.pop("requests_session")

    session_expected = {
        'csrf': 'security628645155dcb3', 'blocking_date': None,
        'date_of_elimination': None, 'account_type': None,
        'service_type': None, 'credit': None, 'time': None,
        'mail_account': None, 'offer': None, 'monthly_fee': None,
        'download_speeds': None, 'upload_speeds': None, 'phone': None,
        'link_identifiers': None, 'link_status': None,
        'activation_date': None, 'blocking_date_home': None,
        'date_of_elimination_home': None, 'quota_fund': None, 'voucher': None,
        'debt': None
    }

    patcher.stop()
    assert session == session_expected


def test_login_successful(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=USER_INFO_HTML)
    mock_request.Session().post = MagicMock(return_value=mock_response)

    user_portal_cli.session = UserPortalSession()

    user_portal_cli.username = "pepito.perez@nauta.com.cu"
    user_portal_cli.password = "SomePassword"

    user_portal_cli.login("captcha")
    user_info = user_portal_cli.session.__dict__
    user_info.pop("requests_session")

    user_info_expected = {
        'csrf': None, 'blocking_date': '30/11/2037',
        'date_of_elimination': '31/12/2037',
        'account_type': 'Prepago recargable',
        'service_type': 'Navegación Internacional con Correo Internacional',
        'credit': '$0,00 CUP', 'time': '00:00:00',
        'mail_account': 'pepito@nauta.cu', 'offer': None,
        'monthly_fee': None, 'download_speeds': None,
        'upload_speeds': None, 'phone': None,
        'link_identifiers': None, 'link_status': None,
        'activation_date': None, 'blocking_date_home': None,
        'date_of_elimination_home': None, 'quota_fund': None,
        'voucher': None, 'debt': None,
        'username': 'pepito.perez@nauta.com.cu'
    }

    patcher.stop()

    assert user_info == user_info_expected


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
    user_info = session.__dict__
    user_info.pop("requests_session")

    user_info_expected = {
        'csrf': None, 'blocking_date': '30/11/2037',
        'date_of_elimination': '31/12/2037',
        'account_type': 'Prepago recargable',
        'service_type': 'Navegación Internacional con Correo Internacional',
        'credit': '$0,00 CUP', 'time': '00:00:00',
        'mail_account': 'pepito@nauta.cu', 'offer': None,
        'monthly_fee': None, 'download_speeds': None,
        'upload_speeds': None, 'phone': None,
        'link_identifiers': None, 'link_status': None,
        'activation_date': None, 'blocking_date_home': None,
        'date_of_elimination_home': None, 'quota_fund': None,
        'voucher': None, 'debt': None,
        'username': 'pepito.perez@nauta.com.cu'
    }

    patcher.stop()

    assert user_info == user_info_expected


def test_get_valid_connections(patcher, user_portal_cli):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=SERVICE_DETAIL_HTML,
        url="https://www.portal.nauta.cu/useraaa/service_detail/"
    )
    mock_response_post = MagicMock(
        status_code=200,
        text=SERVICE_DETAIL_LIST_HTML,
        url="https://www.portal.nauta.cu/useraaa/service_detail_list/"
    )
    mock_request.Session().get = MagicMock(return_value=mock_response_get)
    mock_request.Session().post = MagicMock(return_value=mock_response_post)

    user_portal_cli.session = UserPortalSession()
    connection = user_portal_cli.get_connections(2022, 5)[0].__dict__

    connection_expected = {
        'start_session': '30/04/2022 22:06:07',
        'end_session': '01/05/2022 02:16:05', 'duration': '04:09:58',
        'upload': '116,35 MB', 'download': '1,28 GB', 'import_': '$50,00'
    }

    patcher.stop()

    assert connection == connection_expected
