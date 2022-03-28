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

class PreLoginException(Exception):
    pass


class LoginException(Exception):
    pass


class LogoutException(Exception):
    pass


class RechargeException(Exception):
    pass


class TransferException(Exception):
    pass


class ConnectionException(Exception):
    pass


class ChangePasswordException(Exception):
    pass


class GetInfoException(Exception):
    pass


class NautaException(Exception):
    pass


class NotLoggedIn(Exception):
    pass


class NotNautaHomeAccount(Exception):
    pass
