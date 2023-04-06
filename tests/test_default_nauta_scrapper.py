#  Copyright (c) 2023. Lesly Cintra Laza <a.k.a. lesclaz>.
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
import json
import os
import sys
from unittest.mock import MagicMock, patch

from suitetecsa_core.domain.model import NautaUser, ConnectionsSummary, Connection, RechargesSummary, Recharge, \
    TransfersSummary, Transfer, QuotesPaidSummary, QuotePaid
from suitetecsa_core.repository.session_provider import DefaultNautaSession

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import unittest

from bs4 import BeautifulSoup

from suitetecsa_core.repository.scrapper_provider import DefaultNautaScrapper

_assets_dir = os.path.join(
    os.path.dirname(__file__),
    "assets"
)


def read_asset(asset_name):
    with open(os.path.join(_assets_dir, asset_name)) as fp:
        return fp.read()


# html content files for Portal.CONNECT
landing_html = read_asset("landing.html")
login_html = read_asset("login_page.html")
logged_in_html = read_asset("logged_in.html")
connect_info_html = read_asset("user_info_connect.html")

# html content files for Portal.USER
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

post_responses = {
    "https://secure.etecsa.net:8443": login_html,
    "https://secure.etecsa.net:8443//LoginServlet": logged_in_html,
    "https://secure.etecsa.net:8443/EtecsaQueryServlet": connect_info_html,
    "https://www.portal.nauta.cu/user/login/es-es": user_info_html,
    "https://www.portal.nauta.cu/useraaa/recharge_account": "<div id=\"success\"></div>",
    "https://www.portal.nauta.cu/useraaa/transfer_balance": "<div id=\"success\"></div>",
    "https://www.portal.nauta.cu/useraaa/change_password": "<div id=\"success\"></div>",
    "https://www.portal.nauta.cu/mail/change_password": "<div id=\"success\"></div>",
    "https://www.portal.nauta.cu/useraaa/service_detail_summary/": sd_summary,
    "https://www.portal.nauta.cu/useraaa/recharge_detail_summary/": rd_summary,
    "https://www.portal.nauta.cu/useraaa/transfer_detail_summary/": td_summary,
    "https://www.portal.nauta.cu/useraaa/nautahogarpaid_detail_summary/": qp_summary
}

get_responses = {
    "http://www.cubadebate.cu/": landing_html,
    "https://secure.etecsa.net:8443": login_html,
    "https://www.portal.nauta.cu/user/login/es-es": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/service_detail/": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/transfer_detail/": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/recharge_account": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/transfer_balance": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/change_password": csrf_token_html,
    "https://www.portal.nauta.cu/mail/change_password": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47": sdl_2023_03_47_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47/2": sdl_2023_03_2_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47/3": sdl_2023_03_3_html,
    "https://www.portal.nauta.cu/useraaa/service_detail_list/2023-03/47/4": sdl_2023_03_4_html,
    "https://www.portal.nauta.cu/useraaa/recharge_detail/": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/recharge_detail_list/2023-03/2": rdl_2023_03_2_html,
    "https://www.portal.nauta.cu/useraaa/nautahogarpaid_detail/": csrf_token_html,
    "https://www.portal.nauta.cu/useraaa/nautahogarpaid_detail_list/2023-03/1": qpl_2023_03_1_html
}


class TestDefaultNautaScrapper(unittest.TestCase):

    @patch('requests.Session')
    def setUp(self, MockSession):
        # Simulando comportamiento de la clase Session()
        session = MockSession()
        response_post = MagicMock(status_code=200, text="", url="http://secure.etecsa.net:8443/online.do?fooo")
        response_get = MagicMock(status_code=200, text="", url="https://secure.etecsa.net:8443")

        def post_side_effect(url: str, data: dict = None):
            response_post.text = post_responses[url]
            return response_post

        def get_side_effect(url: str, data: dict = None):
            response_get.text = get_responses[url]
            return response_get

        session.post = MagicMock(side_effect=post_side_effect)
        session.get = MagicMock(side_effect=get_side_effect)

        nauta_session = DefaultNautaSession(session)
        scrapper = BeautifulSoup()
        self.nauta_scrapper = DefaultNautaScrapper(scrapper, nauta_session)

        self.form_html = '<form><input type="text" name="username" value="John"><input type="password" ' \
                         'name="password"></form>'
        self.form_soup = BeautifulSoup(self.form_html, 'html.parser')
        self.html = '<html><head></head><body><form><input type="hidden" name="csrf" value="abc123"></form></body>' \
                    '</html>'
        self.soup = BeautifulSoup(self.html, 'html.parser')

    def test_get_inputs(self):
        expected_result = {'username': 'John', 'password': None}
        result = DefaultNautaScrapper._DefaultNautaScrapper__get_inputs(self.form_soup)
        self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_get_csrf(self):
        expected_result = "abc123"
        result = DefaultNautaScrapper._DefaultNautaScrapper__get_csrf(self.soup)
        self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_connect_session_init(self):
        expected_result = "1fe3ee0634195096337177a0994723fb"
        self.nauta_scrapper._DefaultNautaScrapper__connect_session_init()
        result = self.nauta_scrapper._DefaultNautaScrapper__session._csrf_hw
        self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_user_session_init(self):
        expected_result = "security6416bea61ad2b"
        self.nauta_scrapper._DefaultNautaScrapper__user_session_init()
        result = self.nauta_scrapper._DefaultNautaScrapper__session._csrf
        self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_connect_success(self):
        expected_result = "B2F6AAB9A9868BABC0BDC6B7A235ABE2"
        self.nauta_scrapper.connect("user.name@nauta.com.cu", "some_password")
        result = self.nauta_scrapper.data_session["ATTRIBUTE_UUID"]
        self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_login_success(self):
        result = self.nauta_scrapper.login("user.name@nauta.com.cu", "some_password", "some_captcha_code")
        with open(os.path.join(_assets_dir, "user_info.json"), "r") as file:
            self.assertEqual(result, NautaUser.from_dict(json.load(file)), "El resultado no es el esperado.")

    def test_get_connect_information_success(self):
        result = self.nauta_scrapper.get_connect_information("user.name@nauta.com.cu", "some_password")
        with open(os.path.join(_assets_dir, 'user_info_connect.json'), 'r') as file:
            self.assertEqual(result, json.load(file), "El resultado no es el esperado.")

    def test_get_user_information_success(self):
        soup = BeautifulSoup(user_info_html, "html5lib")
        result = self.nauta_scrapper._DefaultNautaScrapper__get_information_user(soup)
        with open(os.path.join(_assets_dir, "user_info.json"), "r") as file:
            self.assertEqual(result, NautaUser.from_dict(json.load(file)), "El resultado no es el esperado.")

    def test_to_up_success(self):
        self.nauta_scrapper.to_up("1234567890123456")

    def test_transfer_success(self):
        self.nauta_scrapper.transfer(25.0, "some_password", "user_two.name@nauta.com.cu")

    def test_change_password_success(self):
        self.nauta_scrapper.change_password("old_password", "new_password")

    def test_change_password_email_success(self):
        self.nauta_scrapper.change_email_password("old_password", "new_password")

    def test_get_connections_summary_success(self):
        result = self.nauta_scrapper.get_connections_summary(2023, 3)
        with open(os.path.join(_assets_dir, "connects_summary_2023_03.json"), "r") as file:
            self.assertEqual(result, ConnectionsSummary.from_dict(json.load(file)), "El resultado no es el esperado.")

    def test_get_connections_success(self):
        result = self.nauta_scrapper.get_connections(2023, 3)
        with open(os.path.join(_assets_dir, "connects_2023_03.json"), "r") as file:
            expected_result = [Connection.from_dict(connection_dict) for connection_dict in json.load(file)]
            self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_get_recharges_summary_success(self):
        result = self.nauta_scrapper.get_recharges_summary(2023, 3)
        with open(os.path.join(_assets_dir, "recharges_summary_2023_03.json"), "r") as file:
            self.assertEqual(result, RechargesSummary.from_dict(json.load(file)), "El resultado no es el esperado.")

    def test_get_recharges_success(self):
        result = self.nauta_scrapper.get_recharges(2023, 3)
        with open(os.path.join(_assets_dir, "recharges_2023_03.json"), "r") as file:
            expected_result = [Recharge.from_dict(recharge_dict) for recharge_dict in json.load(file)]
            self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_get_transfers_summary_success(self):
        result = self.nauta_scrapper.get_transfers_summary(2023, 3)
        with open(os.path.join(_assets_dir, "transfers_summary_2023_03.json"), "r") as file:
            self.assertEqual(result, TransfersSummary.from_dict(json.load(file)), "El resultado no es el esperado.")

    def test_get_transfers_success(self):
        result = self.nauta_scrapper.get_transfers(2023, 3)
        with open(os.path.join(_assets_dir, "transfers_2023_03.json"), "r") as file:
            expected_result = [Transfer.from_dict(transfer_dict) for transfer_dict in json.load(file)]
            self.assertEqual(result, expected_result, "El resultado no es el esperado.")

    def test_get_quotes_paid_summary_success(self):
        result = self.nauta_scrapper.get_quotes_paid_summary(2023, 3)
        with open(os.path.join(_assets_dir, "quotes_paid_summary_2023_03.json"), "r") as file:
            self.assertEqual(result, QuotesPaidSummary.from_dict(json.load(file)), "El resultado no es el esperado.")

    def test_get_quotes_paid_success(self):
        result = self.nauta_scrapper.get_quotes_paid(2023, 3)
        with open(os.path.join(_assets_dir, "quotes_paid_2023_03.json"), "r") as file:
            expected_result = [QuotePaid.from_dict(quote_paid_dict) for quote_paid_dict in json.load(file)]
            self.assertEqual(result, expected_result, "El resultado no es el esperado.")


if __name__ == '__main__':
    unittest.main()
