from enum import Enum
from requests.utils import dict_from_cookiejar
import re

from py_suitetecsa_sdk.utils.humanize import naturalize, to_bytes


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
    GET_CONNECTIONS = 10
    GET_RECHARGES = 11
    GET_TRANSFERS = 12
    GET_QUOTES_PAID = 13
    CHECK_CONNECTION = 14


RE_SUCCESS_ACTION = re.compile(r"toastr\.success\('(?P<reason>[^']*?)'\)")

RE_DATETIME_FORMAT_ETECSA = re.compile(
    r"(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})"
    r"\s(?P<hour>\d{1,2}):\d{1,2}:\d{1,2}"
)

ATTR_TYPE = {
    "year_month_selected": "str",
    "channel": "str",
    "type_": "str",
    "office": "str",
    "destiny_account": "str",
    "status": "str",
    "message": "str",
    "count": "int",
    "phone": "int",
    "time": "seconds",
    "total_time": "seconds",
    "duration": "seconds",
    "remaining_time": "seconds",
    "uploaded": "bytes",
    "downloaded": "bytes",
    "total_traffic": "bytes",
    "download_speeds": "bytes",
    "upload_speeds": "bytes",
    "total_import": "float",
    "import_": "float",
    "credit": "float",
    "monthly_fee": "float",
    "quota_fund": "float",
    "voucher": "float",
    "debt": "float",
    "date": "datetime",
    "start_session": "datetime",
    "end_session": "datetime",
    "blocking_date": "datetime",
    "date_of_elimination": "datetime",
    "activation_date": "datetime",
    "blocking_date_home": "datetime",
    "date_of_elimination_home": "datetime"
}


def to_seconds(string: str) -> int:
    hours, minutes, seconds = string.split(':')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def time_from_seconds(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = ((seconds % 3600) % 60)

    return f'{hours:02}:{minutes:02}:{seconds:02}'


def api_response(func):
    def wrapper(*args, **kwargs):
        response = {'status': 'success'}
        session = args[0]
        use_api_response = session.use_api_response
        try:
            action, data = func(*args, **kwargs)
            if use_api_response:
                if not action and session.portal_manager == Portal.CONNECT:
                    response['login_action'] = session._NautaSession__login_action
                    response['CSRFHW'] = session._NautaSession__CSRFHW
                    response['wlanuserip'] = session._NautaSession__wlanuserip
                elif not action and session.portal_manager == Portal.USER:
                    response['csrf'] = session._NautaSession__csrf
                    response['cookies'] = dict_from_cookiejar(
                        session.session.cookies
                    )
                elif action == Action.LOGIN and session.portal_manager == Portal.CONNECT:
                    response['logged_in'] = session._NautaSession__logged_in
                    response['ATTRIBUTE_UUID'] = session._NautaSession__ATTRIBUTE_UUID
                elif action == Action.LOGOUT and session.portal_manager == Portal.CONNECT:
                    in_seconds = args[1]
                    if not in_seconds:
                        data.pop('remaining_seconds')
                return {
                    **response,
                    **data
                } if data else response
            elif action == Action.LOGOUT and session.portal_manager == Portal.CONNECT:
                in_seconds = args[1]
                data = data['remaining_seconds'] \
                    if in_seconds else data['remaining_time']
            return data
        except Exception as exc:
            if use_api_response:
                return {
                    'status': 'error',
                    'exception': exc.__class__.__name__,
                    'reason': exc.args[0]
                }
            else:
                raise exc
    return wrapper


def build_summary(action: Action, actions: list) -> dict:
    total_time = uploaded \
        = downloaded = total_traffic = 0
    total_import = 0
    for _import in actions:
        total_import += float(
            _import['import'].replace(',', '.').replace('$', '')
        )
    total_import = f'${total_import:.2f}'.replace('.', ',')

    match action:
        case Action.GET_CONNECTIONS:
            for _ in actions:
                total_time += to_seconds(_['duration'])
                uploaded += to_bytes(_['uploaded'])
                downloaded += to_bytes(_['downloaded'])
            total_traffic += uploaded + downloaded
            return {
                'count': len(actions),
                'total_time': time_from_seconds(total_time),
                'total_import': total_import,
                'uploaded': naturalize(uploaded),
                'downloaded': naturalize(downloaded),
                'total_traffic': naturalize(total_traffic)
            }
        case Action.GET_RECHARGES | Action.GET_QUOTES_PAID:
            return {
                'count': len(actions),
                'total_import': total_import
            }
