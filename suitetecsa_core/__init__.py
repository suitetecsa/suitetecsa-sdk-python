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

from enum import Enum


class Portal(Enum):
    CONNECT = 0
    USER = 1


class Action(Enum):
    LOGIN = 2
    LOGOUT = 3
    LOAD_USER_INFORMATION = 4
    RECHARGE = 5
    TRANSFER = 6
    NAUTA_HOGAR_PAID = 7
    CHANGE_PASSWORD = 8
    CHANGE_EMAIL_PASSWORD = 9
    GET_CONNECTIONS = "connections"
    GET_RECHARGES = "recharges"
    GET_TRANSFERS = "transfers"
    GET_QUOTES_PAID = "quotes_paid"
    CHECK_CONNECTION = 14


from suitetecsa_core.nauta import NautaSession

__all__ = ['NautaSession', 'Portal', 'Action']
