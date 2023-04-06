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

from suitetecsa_core.utils.nauta import str_to_float, parse_datetime, convert_to_bytes, time_string_to_seconds


@dataclass
class Connection:

    start_session: datetime.datetime
    end_session: datetime.datetime
    duration: int
    uploaded: int
    downloaded: int
    import_: float

    @classmethod
    def from_dict(cls, data):
        keys = [f.name for f in fields(cls)]
        normal_keys = {key: data[key] for key in data if key in keys}
        normal_keys["start_session"] = parse_datetime(normal_keys["start_session"])
        normal_keys["end_session"] = parse_datetime(normal_keys["end_session"])
        normal_keys["import_"] = str_to_float(normal_keys["import_"])
        normal_keys["duration"] = time_string_to_seconds(normal_keys["duration"])
        for key in keys:
            if key in ["uploaded", "downloaded"]:
                normal_keys[key] = convert_to_bytes(normal_keys[key])
        return cls(**normal_keys)
