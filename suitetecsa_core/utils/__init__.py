from typing import Any, Dict, List

from requests.utils import dict_from_cookiejar

from suitetecsa_core import Action, Portal
from suitetecsa_core.utils.nauta import convert_to_bytes, seconds_to_time_string, time_string_to_seconds, \
    convert_from_bytes


def api_response(func):
    def wrapper(*args, **kwargs):
        response = {'status': 'success'}
        session = args[0]
        use_api_response = session.use_api_response
        try:
            action, data = func(*args, **kwargs)
            if use_api_response:
                if not action and session.portal_manager == Portal.CONNECT:
                    response['login_action'] = session.login_action
                    response['CSRFHW'] = session.csrfhw
                    response['wlanuserip'] = session.wlanuserip
                elif not action and session.portal_manager == Portal.USER:
                    response['csrf'] = session.csrf
                    response['cookies'] = dict_from_cookiejar(
                        session.session.cookies
                    )
                elif action == Action.LOGIN and session.portal_manager == Portal.CONNECT:
                    response['logged_in'] = session.logged_in
                    response['ATTRIBUTE_UUID'] = session.attribute_uuid
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


def make_actions_summary(actions: List[Dict[str, str]], action_type: Action) -> Dict[str, Any]:
    """
    Crea un resumen de las acciones realizadas por un usuario.

    Parámetros:
    - actions: lista de acciones llevadas a cabo por el usuario.
    - action_type: tipo de acción a resumir, puede ser 'get_connections', 'get_recharges' o 'get_quotes_paid'.

    Retorna un diccionario que contiene un resumen de las acciones ejecutadas, con las siguientes claves:
    - 'count': cantidad de acciones efectuadas.
    - 'total_time': tiempo total invertido en las acciones (solo para 'get_connections').
    - 'total_import': importe total de las acciones (en formato '$#,##').
    - 'uploaded': cantidad total de datos subidos (en formato legible, como '1.2 MB').
    - 'downloaded': cantidad total de datos descargados (en formato legible, como '1.2 GB').
    - 'total_traffic': cantidad total de datos transferidos (en formato legible, como '1.2 TB').

    Lanza una excepción ValueError si el tipo de acción es inválido.
    """
    if action_type == Action.GET_CONNECTIONS:
        total_time = sum(time_string_to_seconds(_['duration']) for _ in actions)
        uploaded = sum(convert_to_bytes(_['uploaded']) for _ in actions)
        downloaded = sum(convert_to_bytes(_['downloaded']) for _ in actions)
        total_traffic = uploaded + downloaded
        return {
            'count': len(actions),
            'total_time': seconds_to_time_string(total_time),
            'total_import': f"${sum(float(_['import'].replace(',', '.').replace('$', '')) for _ in actions):,.2f}"
            .replace(".", ","),
            'uploaded': convert_from_bytes(uploaded),
            'downloaded': convert_from_bytes(downloaded),
            'total_traffic': convert_from_bytes(total_traffic)
        }
    elif action_type in (Action.GET_RECHARGES, Action.GET_QUOTES_PAID):
        return {
            'count': len(actions),
            'total_import': f"${sum(float(_['import'].replace(',', '.').replace('$', '')) for _ in actions):,.2f}"
            .replace(".", ",")
        }
    else:
        raise ValueError("Invalid action type")
