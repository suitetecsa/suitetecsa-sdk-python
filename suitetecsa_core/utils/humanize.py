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

__suffixes = {
    'decimal': ('KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
    'binary': ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    'gnu':  'KMBTPEZY'
}


def naturalize(value: int, binary: bool = False, gnu: bool = False, format: str = '%.2f') -> str:
    if gnu:
        suffix = __suffixes['gnu']
    elif binary:
        suffix = __suffixes['binary']
    else:
        suffix = __suffixes['decimal']

    __base = 1024 if (gnu or binary) else 1000
    __bytes = float(value)
    abs_bytes = abs(__bytes)

    if abs_bytes == 1 and not gnu:
        return '%d Byte' % __bytes
    elif abs_bytes < __base and not gnu:
        return '%d Bytes' % __bytes
    elif abs_bytes < __base and gnu:
        return '%dB' % __bytes

    for i, s in enumerate(suffix):
        unit = __base ** (i + 2)
        if abs_bytes < unit and not gnu:
            return ((format + ' %s') % ((__base * __bytes / unit), s)).replace('.', ',')
        elif abs_bytes < unit and gnu:
            return ((format + '%s') % ((__base * __bytes / unit), s)).replace('.', ',')
    if gnu:
        return ((format + '%s') % ((__base * __bytes / unit), s)).replace('.', ',')
    return ((format + ' %s') % ((__base * __bytes / unit), s)).replace('.', ',')


def to_bytes(value: str):
    unit = value.split(' ')[-1]
    __value = float(value.replace(f' {unit}', '').replace(',', '.').replace(' ', ''))
    suffix = __suffixes['decimal']

    for i, s in enumerate(suffix):
        if s == unit:
            return int(__value * (1000 ** (i + 1)))
