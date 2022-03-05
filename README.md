PyLibSuitETECSA
===========
## Una librería escrita en Python para SuitETECSA

PyLibSuitETECSA fue creada con el objetivo de ofrecer un api que interactúe con los servicios de ETECSA,
para facilitar el desarrollo de aplicaciones Python que faciliten y/o enriquezcan la gestión de los servicios
ofrecidos por portales como el [Portal de Usuario](https://www.portal.nauta.cu/) y el
[Portal Cautivo](https://secure.etecsa.net:8443/) de nauta, ahorrándoles tiempo, esfuerzos, neuronas y código a
los desarrolladores.

PyLibSuitETECSA está aún en fase de desarrollo activa por lo que no ofrece algunas funciones para el servicio
de Nauta Hogar en la implementación de la api encargada de gestionar los servicios ofrecidos por el [Portal de 
usuario de Nauta](https://www.portal.nauta.cu/) (UserPortal y UserPortalClient). Seria de gran ayuda cualquier
aportación de código en este sentido o en cualquier otro.

## Usando UserPortalClient
```python
from libsuitetecsa.api import UserPortalClient  # se importa el cliente para el portal de usuario de nauta

user_portal_cli = UserPortalClient(             # se instancia el cliente
    "usuario@nauta.com.cu",
    "Contraseña"
)

user_portal_cli.init_session()                  # se inicia la session donde se guardan las cookies y datos

with open("captcha_img.png", 'wb') as fp:
    fp.write(user_portal_cli.captcha_as_bytes)  # se guarda la imagen captcha

user_portal_cli.login(input("captcha_code: "))  # se inicia sesión en el portal

print(user_portal_cli.credit)                   # se imprime en pantalla el saldo de la cuenta logeada

```
## Funciones y propiedades de UserPortalClient
### Funciones
* init_session: Crea la session donde se guardan las cookies y datos
* login: Loguea al usuario en el portal y carga la información de la cuenta
* recharge: Recarga la cuenta logueada
* transfer: Transfiere saldo a otra cuenta nauta
* change_password: Cambia la contraseña de la cuenta logueada
* change_email_password: Cambia la contraseña de la cuenta de correo asociada a la cuenta logueada
* get_lasts: Devuelve las últimas `large` `action` realizadas, donde `large` es la cantidad Ej: 5 y `action` las operaciones realizadas Ej: "connections" (las `action` disponibles son: "connections", "recharges" y "transfers")
* get_connections: Devuelve las conexiones realizadas en el mes especificado incluyendo el año (`año-mes`: 2022-03)
* get_recharges: Devuelve las recargas realizadas en el mes especificado incluyendo el año (`año-mes`: 2022-03)
* get_transfers: Devuelve las transferencias realizadas en el mes especificado incluyendo el año (`año-mes`: 2022-03)
### Propiedades
* captcha_as_bytes: Imagen captcha en bytes
* block_date: Fecha de bloqueo
* delete_date: Fecha de eliminación
* account_type: Tipo de cuenta
* service_type: Tipo de servicio
* credit: Saldo
* time: Tiempo disponible
* mail_account: Cuenta de correo asociada

## Usando NautaClient
```python
import time

from libsuitetecsa.api import NautaClient   # se importa el cliente para el portal cautivo de nauta

nauta_ci = NautaClient(                     # se instancia el cliente
    "usuario@nauta.com.cu",
    "Contraseña"
)

nauta_ci.init_session()                     # se inicia la session donde se guardan las cookies y datos

with nauta_ci.login():                      # se inicia sesión en el portal y se mantiene abierta durante un minuto
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

Si te gusta el proyecto dale una estrella para que otros lo encuentren más facilmente.

## Dependencias
```text
requests~=2.27.1
beautifulsoup4~=4.10.0
```
