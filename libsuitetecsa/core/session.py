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

import json
import os
from http import cookiejar

import requests

from libsuitetecsa import appdata_path


class SessionObject(object):
    SESSION_FILE = None
    headers_ = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'es-MX,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0'}

    @classmethod
    def _create_requests_session(cls):
        requests_session = requests.Session()
        requests_session.cookies = cookiejar.MozillaCookieJar(cls.SESSION_FILE)
        requests_session.headers = cls.headers_
        return requests_session

    def save(self):
        self.requests_session.cookies.save()

        data = {**self.__dict__}
        data.pop("requests_session")

        with open(self.__class__.SESSION_FILE, "w") as fp:
            json.dump(data, fp)

    @classmethod
    def load(cls):
        inst = object.__new__(cls)
        inst.requests_session = cls._create_requests_session()

        with open(cls.SESSION_FILE, 'r') as fp:
            inst.__dict__.update(
                json.load(fp)
            )

        return inst

    def dispose(self):
        self.requests_session.cookies.clear()
        self.requests_session.cookies.save()
        try:
            os.remove(self.__class__.SESSION_FILE)
        except:
            pass

    @classmethod
    def is_logged_in(cls):
        return os.path.exists(cls.SESSION_FILE)


class NautaSession(SessionObject):
    SESSION_FILE = os.path.join(appdata_path, "nauta-session")

    def __init__(self,  login_action=None, csrfhw=None, wlanuserip=None, attribute_uuid=None):
        self.requests_session = self.__class__._create_requests_session()

        self.login_action = login_action
        self.csrfhw = csrfhw
        self.wlanuserip = wlanuserip
        self.attribute_uuid = attribute_uuid


class UserPortalSession(SessionObject):
    SESSION_FILE = os.path.join(appdata_path, "user-portal-session")

    def __init__(self, csrf=None):
        self.requests_session = self.__class__._create_requests_session()

        self.csrf = csrf

        self.block_date = None
        self.delete_date = None
        self.account_type = None
        self.service_type = None
        self.credit = None
        self.time = None
        self.mail_account = None
