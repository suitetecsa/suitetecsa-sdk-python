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

import os
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from py_suitetecsa_sdk.utils import Action, Portal
from py_suitetecsa_sdk.core.session import NautaSession
from unittest.mock import patch, MagicMock
import pytest
import json


_assets_dir = os.path.join(
    os.path.dirname(__file__),
    "assets"
)


def read_asset(asset_name):
    with open(os.path.join(_assets_dir, asset_name)) as fp:
        return fp.read()


@pytest.fixture
def patcher():
    return patch("py_suitetecsa_sdk.core.session.Session")


@pytest.fixture
def user_session():
    user_session = NautaSession(
        portal_manager=Portal.CONNECT,
        use_api_response=True
    )
    return user_session


landing_html = read_asset('landing.html')
login_html = read_asset('login_page.html')
logged_in_html = read_asset('logged_in.html')
user_info_html = read_asset('user_info_connect.html')


post_responses = {
    'https://secure.etecsa.net:8443': login_html,
    'https://secure.etecsa.net:8443//LoginServlet': logged_in_html,
    'https://secure.etecsa.net:8443/EtecsaQueryServlet': user_info_html
}


def test_create_valid_session(patcher, user_session: NautaSession):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=landing_html,
        content=landing_html.encode("utf8")
    )
    mock_response_post = MagicMock(
        status_code=200,
        text=login_html
    )
    mock_request().get = MagicMock(return_value=mock_response_get)
    mock_request().post = MagicMock(return_value=mock_response_post)

    data_session = user_session.init()

    assert data_session['status'] == 'success'
    assert data_session['CSRFHW'] == '1fe3ee0634195096337177a0994723fb'
    assert data_session['wlanuserip'] == '10.190.20.96'


def test_login_seccess(patcher, user_session: NautaSession):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=landing_html,
        content=landing_html.encode("utf8")
    )
    mock_response_post = MagicMock(
        status_code=200,
        text='',
        url='http://secure.etecsa.net:8443/online.do?fooo'
    )
    def side_effect(url: str, data: dict = None):
        mock_response_post.text = post_responses[url]
        return mock_response_post
    mock_request().get = MagicMock(return_value=mock_response_get)
    mock_request().post = MagicMock(side_effect=side_effect)

    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'
    login_data = user_session.login()

    assert login_data['ATTRIBUTE_UUID'] == 'B2F6AAB9A9868BABC0BDC6B7A235ABE2'


def test_get_user_info_seccess(patcher, user_session: NautaSession):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=landing_html,
        content=landing_html.encode("utf8")
    )
    mock_response_post = MagicMock(
        status_code=200,
        text='',
        url='http://secure.etecsa.net:8443/online.do?fooo'
    )
    def side_effect(url: str, data: dict = None):
        mock_response_post.text = post_responses[url]
        return mock_response_post
    mock_request().get = MagicMock(return_value=mock_response_get)
    mock_request().post = MagicMock(side_effect=side_effect)

    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'
    user_session.login()
    user_information = user_session.get_user_information()

    with open(os.path.join(_assets_dir, 'user_info_connect.json'), 'r') as file:
        assert user_information == json.load(file)
