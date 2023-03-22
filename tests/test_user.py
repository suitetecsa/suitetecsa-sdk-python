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

from suitetecsa_core.utils import Action, Portal
from suitetecsa_core.nauta.session import NautaSession
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
    return patch("suitetecsa_core.nauta.session.Session")


@pytest.fixture
def user_session():
    user_session = NautaSession(
        portal_manager=Portal.USER,
        use_api_response=True
    )
    return user_session


csrf_token_html = read_asset('csrf_token.html')

user_info_html = read_asset('user_info.html')

login_fail_captcha_html = read_asset('login_fail_captcha_code.html')
login_fail_user_or_password_html = read_asset('login_fail_user_or_password.html')

recharge_fail_html = read_asset('recharge_fail.html')

change_password_fail_html = read_asset('change_password_fail.html')

sd_summary = read_asset('sd_summary.html')
sdl_2023_03_47_html = read_asset('sdl_2023-03_47.html')
sdl_2023_03_2_html = read_asset('sdl_2023-03_2.html')
sdl_2023_03_3_html = read_asset('sdl_2023-03_3.html')
sdl_2023_03_4_html = read_asset('sdl_2023-03_4.html')

rd_summary = read_asset('rd_summary.html')
rdl_2023_03_2_html = read_asset('rdl_2023_03_2.html')

td_summary = read_asset('td_summary.html')

qp_summary = read_asset('qp_summary.html')
qpl_2023_03_1_html = read_asset('qpl_2023_03_1.html')


get_responses = {
    'https://www.portal.nauta.cu/user/login/es-es':
        csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/service_detail/":
        csrf_token_html,
    'https://www.portal.nauta.cu/useraaa/transfer_detail/':
        csrf_token_html,
    'https://www.portal.nauta.cu/useraaa/recharge_account':
        csrf_token_html,
    'https://www.portal.nauta.cu/useraaa/transfer_balance':
        csrf_token_html,
    'https://www.portal.nauta.cu/useraaa/change_password':
        csrf_token_html,
    'https://www.portal.nauta.cu/mail/change_password':
        csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47":
        sdl_2023_03_47_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47/2":
        sdl_2023_03_2_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47/3":
        sdl_2023_03_3_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47/4":
        sdl_2023_03_4_html,
    "https://www.portal.nauta.cu/useraaa/recharge_detail/":
        csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/recharge_detail_list/2023-03/2":
        rdl_2023_03_2_html,
    "https://www.portal.nauta.cu/useraaa/nautahogarpaid_detail/":
        csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/nautahogarpaid_detail_list/2023-03/1":
        qpl_2023_03_1_html
}


def test_create_valid_session(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=csrf_token_html)
    mock_request().get = MagicMock(return_value=mock_response)

    session_data = user_session.init()
    csrf_token = 'security6416bea61ad2b'

    patcher.stop()
    assert session_data['csrf'] == csrf_token


def test_login_success(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=user_info_html)
    mock_request().post = MagicMock(return_value=mock_response)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'

    user_information = user_session.login(captcha_code='captcha_code')
    patcher.stop()

    with open(os.path.join(_assets_dir, 'user_info.json'), 'r') as file:
        assert user_information == json.load(file)


def test_login_fail_for_captcha_code(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=login_fail_captcha_html)
    mock_request().post = MagicMock(return_value=mock_response)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'

    user_information = user_session.login(captcha_code='captcha_code')
    patcher.stop()

    with open(os.path.join(_assets_dir, 'login_fail_catpcha.json'), 'r') as file:
        assert user_information == json.load(file)


def test_login_fail_for_user_or_password(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=login_fail_user_or_password_html)
    mock_request().post = MagicMock(return_value=mock_response)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'

    user_information = user_session.login(captcha_code='captcha_code')
    patcher.stop()

    with open(os.path.join(_assets_dir, 'login_fail_cuser_or_password.json'), 'r') as file:
        assert user_information == json.load(file)


def test_rechage_success(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text='<div id="success"></div>')
    mock_request().post = MagicMock(return_value=mock_response)
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )
    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get
    mock_request().get = MagicMock(side_effect=side_effect)

    user_session.init()
    recharge_response = user_session.recharge('1234567890123456')

    with open(os.path.join(_assets_dir, 'action_success.json'), 'r') as file:
        assert recharge_response == json.load(file)


def test_rechage_fail(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=recharge_fail_html)
    mock_request().post = MagicMock(return_value=mock_response)
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )
    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get
    mock_request().get = MagicMock(side_effect=side_effect)

    user_session.init()
    recharge_response = user_session.recharge('1234567890123456')

    with open(os.path.join(_assets_dir, 'recharge_fail.json'), 'r') as file:
        assert recharge_response == json.load(file)


def test_transfer_success(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text='<div id="success"></div>')
    mock_request().post = MagicMock(return_value=mock_response)
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )
    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get
    mock_request().get = MagicMock(side_effect=side_effect)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'
    transfer_response = user_session.transfer(
        account_to_transfer='user.name@nauta.com.cu',
        mount_to_transfer=25
    )

    with open(os.path.join(_assets_dir, 'action_success.json'), 'r') as file:
        assert transfer_response == json.load(file)


def test_change_password_success(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text='<div id="success"></div>')
    mock_request().post = MagicMock(return_value=mock_response)
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )
    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get
    mock_request().get = MagicMock(side_effect=side_effect)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'
    change_password_response = user_session.change_password(
        new_password='new_password'
    )

    with open(os.path.join(_assets_dir, 'action_success.json'), 'r') as file:
        assert change_password_response == json.load(file)


def test_change_password_fail(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text=change_password_fail_html)
    mock_request().post = MagicMock(return_value=mock_response)
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )
    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get
    mock_request().get = MagicMock(side_effect=side_effect)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'
    change_password_response = user_session.change_password(
        new_password='new_password'
    )

    with open(os.path.join(_assets_dir, 'change_password_fail.json'), 'r') as file:
        assert change_password_response == json.load(file)


def test_change_email_password(patcher, user_session):
    mock_request = patcher.start()
    mock_response = MagicMock(status_code=200, text='<div id="success"></div>')
    mock_request().post = MagicMock(return_value=mock_response)
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )
    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get
    mock_request().get = MagicMock(side_effect=side_effect)

    user_session.init()
    user_session.credentials = 'user.name@nauta.com.cu', 'some_password'
    change_password_response = user_session.change_email_password(
        old_password='old_password',
        new_password='new_password'
    )

    with open(os.path.join(_assets_dir, 'action_success.json'), 'r') as file:
        assert change_password_response == json.load(file)


def test_get_valid_connections(patcher, user_session):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )

    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get

    mock_response_post = MagicMock(
        status_code=200,
        text=sd_summary
    )

    mock_request().get = MagicMock(side_effect=side_effect)
    mock_request().post = MagicMock(return_value=mock_response_post)

    user_session.init()
    conncets = user_session.get_connections(year=2023, month=3)
    lasts_conncet = user_session.get_lasts(
        action=Action.GET_CONNECTIONS,
        large=47
    )
    patcher.stop()

    with open(os.path.join(_assets_dir, 'connects_2023_03.json'), 'r') as file:
        assert conncets == json.load(file)
    with open(os.path.join(_assets_dir, 'lasts_connects.json'), 'r') as file:
        assert lasts_conncet == json.load(file)


def test_get_valid_recharges(patcher, user_session):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )

    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get

    mock_response_post = MagicMock(
        status_code=200,
        text=rd_summary
    )

    mock_request().get = MagicMock(side_effect=side_effect)
    mock_request().post = MagicMock(return_value=mock_response_post)

    user_session.init()
    conncets = user_session.get_recharges(year=2023, month=3)
    lasts_conncet = user_session.get_lasts(
        action=Action.GET_RECHARGES,
        large=2
    )
    patcher.stop()

    with open(os.path.join(_assets_dir, 'recharges_2023_03.json'), 'r') as file:
        assert conncets == json.load(file)
    with open(os.path.join(_assets_dir, 'lasts_recharges.json'), 'r') as file:
        assert lasts_conncet == json.load(file)


def test_get_valid_transfers(patcher, user_session):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )

    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get

    mock_response_post = MagicMock(
        status_code=200,
        text=td_summary
    )

    mock_request().get = MagicMock(side_effect=side_effect)
    mock_request().post = MagicMock(return_value=mock_response_post)

    user_session.init()
    conncets = user_session.get_transfers(year=2023, month=3)
    patcher.stop()

    with open(os.path.join(_assets_dir, 'td_2023_03.json'), 'r') as file:
        assert conncets == json.load(file)


def test_get_valid_quotes_paid(patcher, user_session):
    mock_request = patcher.start()
    mock_response_get = MagicMock(
        status_code=200,
        text=""
    )

    def side_effect(value: str):
        mock_response_get.text = get_responses[value]
        return mock_response_get

    mock_response_post = MagicMock(
        status_code=200,
        text=qp_summary
    )

    mock_request().get = MagicMock(side_effect=side_effect)
    mock_request().post = MagicMock(return_value=mock_response_post)

    user_session.init()
    conncets = user_session.get_quotes_paid(year=2023, month=3)
    lasts_conncet = user_session.get_lasts(
        action=Action.GET_QUOTES_PAID,
        large=1
    )
    patcher.stop()

    with open(os.path.join(_assets_dir, 'qp_2023_03.json'), 'r') as file:
        assert conncets == json.load(file)
    with open(os.path.join(_assets_dir, 'lasts_quotes_paid.json'), 'r') as file:
        assert lasts_conncet == json.load(file)
