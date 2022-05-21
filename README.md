PyLibSuitETECSA
===========
## Una librería escrita en Python para SuitETECSA

PyLibSuitETECSA fue creada con el objetivo de ofrecer una API que interactúe con los servicios ofrecidos 
por [ETECSA](https://www.etecsa.cu/), para facilitar el desarrollo de aplicaciones Python dedicadas a la 
gestión de estos mediante los portales [de usuario](https://www.portal.nauta.cu/) 
y [cautivo](https://secure.etecsa.net:8443/) de nauta, ahorrándoles tiempo, esfuerzos, neuronas 
y código a los desarrolladores.

PyLibSuitETECSA está aún en fase de desarrollo activa, por lo que aún no implementa algunas funciones
necesarias para la gestión de cuentas asociadas al servicio Nauta Hogar. Se me ha hecho difícil la 
implementación de dichas funciones, ya que no poseo este servicio.

## Usando UserPortalClient

```python
from PyLibSuitETECSA.api import UserPortalClient  # se importa el cliente para el portal de usuario de nauta

user_portal_cli = UserPortalClient(  # se instancia el cliente
    "usuario@nauta.com.cu",
    "Contraseña"
)

user_portal_cli.init_session()  # se inicia la session donde se guardan las cookies y datos

with open("captcha_img.png", 'wb') as fp:
    fp.write(user_portal_cli.captcha_as_bytes)  # se guarda la imagen captcha

user_portal_cli.login(input("captcha_code: "))  # se inicia sesión en el portal

print(
    user_portal_cli.credit)  # se imprime en pantalla el saldo de la cuenta logueada

```
## Métodos y propiedades de UserPortalClient
### Métodos

<details>
<summary>Nauta</summary>
<table>
<thead>
<tr>
<td>Método</td>
<td>Función</td>
</tr>
</thead>
<tr>
<td>init_session</td>
<td>Crea la sesión donde se guardan las cookies y datos</td>
</tr>
<tr>
<td>login</td>
<td>Loguea al usuario en el portal y carga la información de la cuenta</td>
</tr>
<tr>
<td>recharge</td>
<td>Recarga la cuenta logueada</td>
</tr>
<tr>
<td>transfer</td>
<td>Transfiere saldo a otra cuenta nauta</td>
</tr>
<tr>
<td>change_password</td>
<td>Cambia la contraseña de la cuenta logueada</td>
</tr>
<tr>
<td>change_email_password</td>
<td>Cambia la contraseña de la cuenta de correo asociada a la cuenta logueada</td>
</tr>
<tr>
<td>get_lasts</td>
<td>Devuelve las últimas <b>large</b> <b>action</b> realizadas, donde <b>large</b> es la cantidad Ex: 5 y <b>action</b> las operaciones realizadas Ex: <b>UserPortal.ACTION_CONNECTIONS</b> (las <b>action</b> disponibles son: <b>UserPortal.ACTION_CONNECTIONS</b>, <b>UserPortal.ACTION_RECHARGES</b>, <b>UserPortal.ACTION_TRANSFER</b> y <b>UserPortal.ACTION_QUOTE_FUNDS</b>, esta última solo para nauta hogar)</td>
</tr>
<tr>
<td>get_connections</td>
<td>Devuelve las conexiones realizadas en el mes especificado incluyendo el año (<b>año-mes</b>: 2022-03)</td>
</tr>
<tr>
<td>get_recharges</td>
<td>Devuelve las recargas realizadas en el mes especificado incluyendo el año (<b>año-mes</b>: 2022-03)</td>
</tr>
<tr>
<td>get_transfers</td>
<td>Devuelve las transferencias realizadas en el mes especificado incluyendo el año (<b>año-mes</b>: 2022-03)</td>
</tr>
</table>
</details>

<details>
<summary>Nauta Hogar</summary>
<table>
<thead>
<tr>
<td>Método</td>
<td>Función</td>
</tr>
</thead>
<tr>
<td>transfer_to_quote</td>
<td>Transfiere saldo a la cuota de nauta hogar (<b>aún sin implementar</b>)</td>
</tr>
<tr>
<td>pay_to_debt_with_credit</td>
<td>Paga deuda de nauta hogar con saldo (<b>aún sin implementar</b>)</td>
</tr>
<tr>
<td>pay_to_debt_with_quote_fund</td>
<td>Paga deuda de nauta hogar con fondo de cuota (<b>aún sin implementar</b>)</td>
</tr>
<tr>
<td>get_quotes_fund</td>
<td>Devuelve los fondos de cuota realizados en el mes especificado incluyendo el año (<b>año-mes</b>: 2022-03)</td>
</tr>
</table>
</details>

### Propiedades

<details>
    <summary>Nauta</summary>
    <table>
        <thead>
            <tr>
                <td>Propiedad</td>
                <td>Dato devuelto</td>
            </tr>
        </thead>
        <tr>
            <td>captcha_as_bytes</td>
            <td>Imagen captcha en bytes.</td>
        </tr>
        <tr>
            <td>blocking_date</td>
            <td>Fecha de bloqueo.</td>
        </tr>
        <tr>
            <td>date_of_elimination</td>
            <td>Fecha de eliminación.</td>
        </tr>
        <tr>
            <td>account_type</td>
            <td>Tipo de cuenta.</td>
        </tr>
        <tr>
            <td>service_type</td>
            <td>Tipo de servicio.</td>
        </tr>
        <tr>
            <td>credit</td>
            <td>Saldo.</td>
        </tr>
        <tr>
            <td>time</td>
            <td>Tiempo disponible.</td>
        </tr>
        <tr>
            <td>mail_account</td>
            <td>Cuenta de correo asociada.</td>
        </tr>
    </table>
</details>

<details>
    <summary>Nauta Hogar</summary>
    <table>
        <thead>
            <tr>
                <td>Propiedad</td>
                <td>Dato devuelto</td>
            </tr>
        </thead>
        <tr>
            <td>offer</td>
            <td>Oferta</td>
        </tr>
        <tr>
            <td>monthly_fee</td>
            <td>Cuota mensual</td>
        </tr>
        <tr>
            <td>download_speeds</td>
            <td>Velocidad de bajada</td>
        </tr>
        <tr>
            <td>upload_speeds</td>
            <td>Velocidad de subida</td>
        </tr>
        <tr>
            <td>phone</td>
            <td>Teléfono</td>
        </tr>
        <tr>
            <td>link_identifiers</td>
            <td>Identificador del enlace</td>
        </tr>
        <tr>
            <td>link_status</td>
            <td>Estado del enlace</td>
        </tr>
        <tr>
            <td>activation_date</td>
            <td>Fecha de activación</td>
        </tr>
        <tr>
            <td>blocking_date_home</td>
            <td>Fecha de bloqueo</td>
        </tr>
        <tr>
            <td>date_of_elimination_home</td>
            <td>Fecha de eliminación</td>
        </tr>
        <tr>
            <td>quota_fund</td>
            <td>Fondo de cuota</td>
        </tr>
        <tr>
            <td>voucher</td>
            <td>Bono</td>
        </tr>
        <tr>
            <td>debt</td>
            <td>Deuda</td>
        </tr>
    </table>
</details>

__Nota__: Los `métodos` y `propiedades` disponibles para `Nauta` también lo están para `Nauta Hogar`.

## Usando NautaClient

```python
import time

from PyLibSuitETECSA.api import NautaClient  # se importa el cliente para el portal cautivo de nauta

nauta_ci = NautaClient(  # se instancia el cliente
    "usuario@nauta.com.cu",
    "Contraseña"
)

nauta_ci.init_session()  # se inicia la session donde se guardan las cookies y datos

with nauta_ci.login():  # se inicia sesión en el portal y se mantiene abierta durante un minuto
    print(nauta_ci.remaining_time)
    time.sleep(60)

```
## Funciones y propiedades de UserPortalClient
### Funciones
* init_session: Crea la session donde se guardan las cookies y datos
* login: Loguea al usuario en el portal
* logout: Cierra la sesión abierta
* load_last_session: Carga la última session creada
### Propiedades
* is_logged_in: Si se está loagueado en el portal
* user_credit: Saldo de la cuenta
* remaining_time: Tiempo restante

## Contribuir
__IMPORTANTE__: PyLibSuitETESA necesita compatibilidad con nauta hogar.

Todas las contribuciones son bienvenidas. Puedes ayudar trabajando en uno de los issues existentes. 
Clona el repo, crea una rama para el issue que estés trabajando y cuando estés listo crea un Pull Request.

También puedes contribuir difundiendo esta herramienta entre tus amigos y en tus redes. Mientras
más grande sea la comunidad más sólido será el proyecto. 

Si te gusta el proyecto dale una estrella para que otros lo encuentren más fácilmente.

## Dependencias
```text
requests~=2.27.1
beautifulsoup4~=4.10.0
pytest~=7.1.2
setuptools~=60.2.0
```
