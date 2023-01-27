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


from datetime import datetime

from dataclasses import dataclass
from typing import Any

from PyLibSuitETECSA.utils import ATTR_TYPE
from PyLibSuitETECSA.utils.from_str import to_bytes, to_datetime, to_float, to_seconds


class DataModel:

    def __setattr__(self, __name: str, __value: Any) -> None:
        if type(__value) == str and __name in ATTR_TYPE:
            match ATTR_TYPE[__name]:
                case "str":
                    self.__dict__[__name] = __value
                case "int":
                    self.__dict__[__name] = int(__value)
                case "float":
                    self.__dict__[__name] = to_float(__value)
                case "seconds":
                    self.__dict__[__name] = to_seconds(__value)
                case "bytes":
                    self.__dict__[__name] = to_bytes(__value)
                case "datetime":
                    self.__dict__[__name] = to_datetime(__value)
                case _:
                    raise AttributeError


@dataclass
class ConnectionsSummary(DataModel):

    count: (str | int)
    year_month_selected: str
    total_time: (str | int)
    total_import: (str | float)
    uploaded: (str | int)
    downloaded: (str | int)
    total_traffic: (str | int)


@dataclass
class Connection(DataModel):

    start_session: (str | datetime)
    end_session: (str | datetime)
    duration: (str | int)
    uploaded: (str | int)
    downloaded: (str | int)
    import_: (str | float)


@dataclass
class RechargesSummary(DataModel):

    count: (str | int)
    year_month_selected: str
    total_import: (str | float)


@dataclass
class Recharge(DataModel):

    date: (str | datetime)
    import_: (str | float)
    channel: str
    type_: str


@dataclass
class QuotesFundSummary(RechargesSummary):
    pass


@dataclass
class QuoteFund(Recharge):

    office: str


@dataclass
class TransfersSummary(RechargesSummary):
    pass


@dataclass
class Transfer(DataModel):

    date: (str | datetime)
    import_: (str | float)
    destiny_account: str


@dataclass
class ActionResponse:

    status: str
    message: str
