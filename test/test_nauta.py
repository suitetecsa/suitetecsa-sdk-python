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

from PyLibSuitETECSA.api import NautaClient
from PyLibSuitETECSA.core.exception import PreLoginException
from PyLibSuitETECSA.core.session import NautaSession

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
def nauta_cli():
    nauta_cli = NautaClient()
    return nauta_cli


LANDING_HTML = read_asset("landing.html")
LOGIN_HTML = read_asset("login_page_nauta.html")
LOGGED_IN_HTML = read_asset("logged_in.html")
USER_CREDIT_HTML = read_asset("user_credit.html")


def test_create_valid_session(patcher, nauta_cli):
    patcher_two = patch("PyLibSuitETECSA.core.protocol.requests")
    mock_request_too = patcher_two.start()
    mock_response = MagicMock(
        status_code=200, text=LANDING_HTML, content=LANDING_HTML.encode("utf8")
    )
    mock_response_post = MagicMock(status_code=200, text=LOGIN_HTML)
    mock_request_too.get = MagicMock(return_value=mock_response)
    mock_request = patcher.start()
    mock_request.Session().get = MagicMock(return_value=mock_response)
    mock_request.Session().post = MagicMock(return_value=mock_response_post)

    nauta_cli.init_session()
    session = nauta_cli.session.__dict__
    session.pop("requests_session")
    session_expected = {
        "login_action": "https://secure.etecsa.net:8443//LoginServlet",
        "csrfhw": "1fe3ee0634195096337177a0994723fb",
        "wlanuserip": "10.190.20.96",
        "attribute_uuid": None
    }

    patcher.stop()
    assert session == session_expected


def test_create_session_raises_when_connected(nauta_cli):
    patcher = patch("PyLibSuitETECSA.core.protocol.requests")
    mock_request = patcher.start()
    mock_response_get = MagicMock(status_code=200, text="LALALA")
    mock_request.get = MagicMock(return_value=mock_response_get)

    with pytest.raises(PreLoginException) as e:
        nauta_cli.init_session()

    patcher.stop()

    assert "Hay una conexión activa" == str(e.value)


def test_action_login_successful(patcher, nauta_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(
        status_code=200,
        text=LOGGED_IN_HTML,
        url="http://secure.etecsa.net:8443/online.do?fooo"
    )
    mock_request.Session().post = MagicMock(return_value=mock_response)
    nauta_cli.session = NautaSession()
    nauta_cli.login()

    patcher.stop()

    assert nauta_cli.session.attribute_uuid == "B2F6AAB9A9868BABC0BDC6B7" \
                                               "A235ABE2"


def test_get_user_credit(patcher, nauta_cli):
    mock_request = patcher.start()
    mock_response = MagicMock(
        status_code=200,
        text=USER_CREDIT_HTML,
        url="https://secure.etecsa.net:8443/EtecsaQueryServlet"
    )
    mock_request.Session().post = MagicMock(return_value=mock_response)
    nauta_cli.session = NautaSession()
    credit = nauta_cli.user_credit

    patcher.stop()

    assert credit == "37.82 CUP"
