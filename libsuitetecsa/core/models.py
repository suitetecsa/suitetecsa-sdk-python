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

from datetime import datetime


class Connection(object):

    def __init__(self, **kwargs):
        self.start_session = None
        self.end_session = None
        self.duration = None
        self.upload = None
        self.download = None
        self.import_ = None
        self.__dict__.update(kwargs)

    @property
    def start_session_as_dt(self):
        if self.start_session:
            date_ = self.start_session.split(" ")[0]
            time_ = self.start_session.split(" ")[1]

            day = date_.split("/")[0]
            month = date_.split("/")[1]
            year = date_.split("/")[2]

            hours = time_.split(":")[0]
            minutes = time_.split(":")[1]
            seconds = time_.split(":")[2]

            return datetime(int(year), int(month), int(day),
                            int(hours), int(minutes), int(seconds))


class Recharge(object):

    def __init__(self, **kwargs):
        self.date = None
        self.import_ = None
        self.channel = None
        self.type_ = None
        self.__dict__.update(kwargs)

    @property
    def date_as_dt(self):
        date_ = self.date.split(" ")[0]
        time_ = self.date.split(" ")[1]

        day = date_.split("/")[0]
        month = date_.split("/")[1]
        year = date_.split("/")[2]

        hours = time_.split(":")[0]
        minutes = time_.split(":")[1]
        seconds = time_.split(":")[2]

        return datetime(int(year), int(month), int(day),
                        int(hours), int(minutes), int(seconds))


class QuotePaid(Recharge):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.office = None
        self.__dict__.update(kwargs)


class Transfer(object):

    def __init__(self, **kwargs):
        self.date = None
        self.import_ = None
        self.destiny_account = None
        self.__dict__.update(kwargs)

    @property
    def date_as_dt(self):
        date_ = self.date.split(" ")[0]
        time_ = self.date.split(" ")[1]

        day = date_.split("/")[0]
        month = date_.split("/")[1]
        year = date_.split("/")[2]

        hours = time_.split(":")[0]
        minutes = time_.split(":")[1]
        seconds = time_.split(":")[2]

        return datetime(int(year), int(month), int(day),
                        int(hours), int(minutes), int(seconds))


class User:

    def __init__(self, **kwargs):
        self.username = None
        self.block_date = None
        self.delete_date = None
        self.account_type = None
        self.service_type = None
        self.credit = None
        self.remaining_time = None
        self.mail_account = None
        self.__dict__.update(kwargs)
