#  Copyright (c) 2023. Lesly Cintra Laza <a.k.a. lesclaz>
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

import datetime
from dataclasses import dataclass, fields

from suitetecsa_core.utils.nauta import str_to_date, str_to_float, time_string_to_seconds


@dataclass
class NautaUser:
    username: str
    blocking_date: datetime.date
    date_of_elimination: datetime.date
    account_type: str
    service_type: str
    credit: float
    time: int
    mail_account: str
    offer: str = None
    monthly_fee: float = None
    download_speeds: str = None
    upload_speeds: str = None
    phone: str = None
    link_identifiers: str = None
    link_status: str = None
    activation_date: datetime.date = None
    blocking_date_home: datetime.date = None
    date_of_elimination_home: datetime.date = None
    quote_paid: float = None
    voucher: float = None
    debt: float = None

    @classmethod
    def from_dict(cls, data):
        keys = [f.name for f in fields(cls)]
        normal_keys = {key: data[key] for key in data if key in keys}
        normal_keys['time'] = time_string_to_seconds(normal_keys["time"])
        for key in keys:
            if key in [
                "blocking_date", "date_of_elimination", "activation_date",
                "blocking_date_home", "date_of_elimination_home"
            ]:
                normal_keys[key] = str_to_date(normal_keys[key])
            elif key in [
                "credit", "monthly_fee", "quote_paid", "voucher", "debt"
            ]:
                normal_keys[key] = str_to_float(normal_keys[key])
        return cls(**normal_keys)
