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


def to_seconds(string: str) -> int:
    hours, minutes, seconds = string.split(':')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def to_float(string: str) -> int:
    return float(string.replace('$', '').replace(',', '.')\
        .replace(' CUP', ''))


def to_bytes(string: str) -> int:
    units = {
        "tb": 4,
        "gb": 3,
        "mb": 2,
        "kb": 1
    }
    import_, unit = string.replace(',', '.')\
        .replace('ps', '').lower().split(' ')
    to_multiply = 1024 ** units[unit] if unit != "bytes" else 1
    return int(float(import_) * to_multiply)
