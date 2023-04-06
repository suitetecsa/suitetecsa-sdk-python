# suitetecsa-sdk-python

`suitetecsa-sdk-python` es una librería Python que permite interactuar de manera sencilla con algunos servicios ofrecidos por ETECSA, el proveedor de servicios de telecomunicaciones en Cuba. La librería incluye un conjunto de módulos y herramientas que facilitan el acceso a estos servicios a través de técnicas de scrapping.

Con `suitetecsa-sdk-python`, puedes obtener datos de manera rápida y eficiente a partir de dos portales web: el [portal de acceso a internet](https://secure.etecsa.net:8443/) y el [portal de usuario](https://www.portal.nauta.cu/) de Nauta. La librería te permite realizar algunas operaciones comunes, como consultar el saldo de una cuenta Nauta o conectarte a internet.

Además, `suitetecsa-sdk-python` incluye métodos que agregan funcionalidades útiles, como la generación de contraseñas y la compartición de sesión. Con `suitetecsa-sdk-python`, puedes automatizar tareas comunes y ahorrar tiempo al interactuar con los servicios de ETECSA.

La librería es fácil de usar y está diseñada para ser extensible y personalizable, lo que te permite adaptarla a tus necesidades específicas. Además, se está trabajando para agregar más portales para agregar más servicios que se puedan gestionar con `suitetecsa-sdk-python`.

### Portales de ETECSA que gestiona `suitetecsa-sdk-python` y funciones implementadas

- [x] [Secure Etecsa](https://secure.etecsa.net:8443/)
  
  - [x] Iniciar sesión.
  - [x] Cerrar sesión.
  - [x] Obtener el tiempo disponible en la cuenta.
  - [x] Obtener la información de la cuenta.

- [x] [Portal de Usuario](https://www.portal.nauta.cu/)
  
  - [x] Iniciar sesión.
  
  - [x] Obtener información de la cuenta.
  
  - [x] Recargar la cuenta.
  
  - [x] Transferir saldo a otra cuenta nauta.
  
  - [x] Transferir saldo para pago de cuota (`solo para cuentas Nauta Hogar`).
  
  - [x] Cambiar la contraseña de la cuenta de acceso.
  
  - [x] Cambiar la contraseña de la cuenta de correo asociada.
  
  - [x] Obtener las conexiones realizadas en el periódo `año-mes` especificado.
  
  - [x] Obtener las recargas realizadas en el periódo `año-mes` especificado.
  
  - [x] Obtener las transferencias realizadas en el periódo `año-mes` especificado.
  
  - [x] Obtener los pagos de cuotas realizados en el periódo `año-mes` especificado (`solo para cuentas Nauta Hogar`).
  
  - [x] Obtener las útimas (`la cantidad puede ser definida por el desarrollador que use la librería; por defecto es 5`) operaciones (`las antes mencionadas`).

- [ ] [Portal Etecsa](https://www.etecsa.cu/)

- [ ] [Servicios en Línea](https://www.tienda.etecsa.cu/)

- [ ] [Portal Nauta](https://www.nauta.cu/)

# Uso

### Gestiona los servicios `Nauta` con NautaClient

La clase `NautaClient` es la encargada de interactuar con los servicios de Nauta que gestiona `suitetecsa-sdk-python`. Esta clase permite la conexión a dos portales diferentes: [Secure Etcsa](https://secure.etecsa.net:8443/) y [Portal de Usuario](https://www.portal.nauta.cu/). La interacción con uno u otro portal dependerá del método que se utilice en cada caso. Por ejemplo, para conectarse a internet a través del portal cautivo, se utiliza el método `connect`, mientras que para iniciar sesión en el portal de usuario se utiliza el método `login`.

A continuación, se muestran ejemplos de cómo conectarse a cada portal, obtener información y cerrar la sesión:

```python
import time
from bs4 import BeautifulSoup
from requests import Session
from suitetecsa_core import NautaClient, DefaultNautaSession, DefaultNautaScrapper


if __name__ == '__main__':
    session = Session()
    nauta_session = DefaultNautaSession(session)
    scrapper = BeautifulSoup()
    nauta_scrapper = DefaultNautaScrapper(scrapper, nauta_session)
    client = NautaClient(nauta_scrapper)

    # Estableciendo credenciales para el inicio de sesión
    client.credentials = "user.name@nauta.com.cu", "some_password"

    # Iniciando sesión en el portal cautivo
    client.connect()
    # Imprimiendo tiempo restante de la cuenta
    print(client.remaining_time)
    # Esperando 30 segundos
    time.sleep(30)
    # Imprimiendo tiempo restante de la cuenta
    print(client.remaining_time)
    # Cerrando sesión
    client.disconnect()

    # Iniciando sesión en el portal de usuario

    # Obteniendo imagen captcha
    with open("captcha_image.png", "wb") as file:
        file.write(client.captcha_image)

    # Iniciando sesión
    user = client.login("some_captcha_code")

    # Imprimiendo saldo y tiempo disponibles de la cuenta
    print(f"{user.credit} :: {user.time}")

    # Cerrando sesión
    client.logout()
```

El por qué de tantas instancias se debe a que he tratado de cumplir con los principios SOLID en esta última versión de `suitetecsa-sdk-python`, aplicando el principio de inversión de dependencias.

## Métodos de la clase NautaClient

| Método                  | Parámetros                                                                                                                 | Descripción                                                                                                                                            |
| -----------------------:|:--------------------------------------------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------ |
| login                   | captcha_code: `str`                                                                                                        | Inicia sesión en el portal de usuario de Nauta utilizando el código captcha        proporcionado.                                                      |
| connect                 | -                                                                                                                          | inicia sesion en el portal cautivo de nauta                                                                                                            |
| to_up                   | recharge_code: `str`                                                                                                       | Intenta recargar el saldo de la cuenta utilizando el código de recarga proporcionado.                                                                  |
| transfer                | amount: `float`, destination_account: `str`                                                                                | Intenta transferir una cantidad de saldo especificada a una cuenta de destino.                                                                         |
| pay_nauta_home          | amount: `float`                                                                                                            | Intenta pagar nauta hogar con la cantidad de saldo especificada.                                                                                       |
| change_password         | new_password: `str`                                                                                                        | Intenta cambiar la contraseña actual por una nueva utilizando la nueva contraseña        proporcionadas.                                               |
| change_email_password   | old_password: `str`, new_password: `str`                                                                                   | Intenta cambiar la contraseña actual de la cuenta de correo electrónico asociada utilizando la contraseña actual y la nueva contraseña proporcionadas. |
| get_connections_summary | year: `int`, month:`int`                                                                                                   | Este método devuelve un objeto de tipo ConnectionsSummary que contiene un resumen de conexiones para el año y<br/>        mes dados.                   |
| get_connections         | year: `int`, month: `int`, summary: `ConnectionsSummary` (Opcional), large: `int` (Opcional), _reversed: `bool` (Opcional) | Obtiene las conexiones a internet para un año y mes específicos.                                                                                       |
| get_recharges_summary   | year: `int`, month:`int`                                                                                                   | Este método devuelve un objeto de tipo RechargesSummary que contiene un resumen de recargas para el año y mes<br/>        dados.                       |
| get_recharges           | year: `int`, month: `int`, summary: `RechargesSummary` (Opcional), large: `int` (Opcional), _reversed: `bool` (Opcional)   | Obtiene una lista de recargas realizadas en un año y mes específicos.                                                                                  |
| get_transfers_summary   | year: `int`, month:`int`                                                                                                   | Este método devuelve un objeto de tipo TransfersSummary que contiene un resumen de transferencias para el año y<br/>        mes dados.                 |
| get_transfers           | year: `int`, month: `int`, summary: `TransfersSummary` (Opcional), large: `int` (Opcional), _reversed: `bool` (Opcional)   | Obtiene una lista de transferencias realizadas en un año y mes específicos.                                                                            |
| get_quotes_paid_summary | year: `int`, month:`int`                                                                                                   | Este método devuelve un objeto de tipo QuotesPaidSummary que contiene un resumen de cotizaciones pagadas para el año y mes dados.                      |
| get_quotes_paid         | year: `int`, month: `int`, summary: `QuotesPaidSummary` (Opcional), large: `int` (Opcional), _reversed: `bool` (Opcional)  | Obtiene una lista de cotizaciones pagadas realizadas en un año y mes específicos.                                                                      |
| logout                  | -                                                                                                                          | Cierra la sesión en el portal de usuario de Nauta eliminando las cookies y el token CSRF de la sesión.                                                 |
| disconnect              | -                                                                                                                          | Cierra la sesión en el portal cautivo.                                                                                                                 |

# 

# Contribución

¡Gracias por tu interés en colaborar con nuestro proyecto! Nos encanta recibir contribuciones de la comunidad y valoramos mucho tu tiempo y esfuerzo.  

## Cómo contribuir

Si estás interesado en contribuir, por favor sigue los siguientes pasos:  

1. Revisa las issues abiertas para ver si hay alguna tarea en la que puedas ayudar.  
2. Si no encuentras ninguna issue que te interese, por favor abre una nueva issue explicando el problema o la funcionalidad que te gustaría implementar. Asegúrate de incluir toda la información necesaria para que otros puedan entender el problema o la funcionalidad que estás proponiendo.  
3. Si ya tienes una issue asignada o si has decidido trabajar en una tarea existente, por favor crea un fork del repositorio y trabaja en una nueva rama (`git checkout -b nombre-de-mi-rama`).  
4. Cuando hayas terminado de trabajar en la tarea, crea un pull request explicando los cambios que has realizado y asegurándote de que el código cumple con nuestras directrices de estilo y calidad.  
5. Espera a que uno de nuestros colaboradores revise el pull request y lo apruebe o sugiera cambios adicionales.  

## Directrices de contribución

Por favor, asegúrate de seguir nuestras directrices de contribución para que podamos revisar y aprobar tus cambios de manera efectiva:  

- Sigue los estándares de codificación y estilo de nuestro proyecto.  
- Asegúrate de que el código nuevo esté cubierto por pruebas unitarias.  
- Documenta cualquier cambio que hagas en la documentación del proyecto.  

¡Gracias de nuevo por tu interés en contribuir! Si tienes alguna pregunta o necesitas ayuda, no dudes en ponerte en contacto con nosotros en la sección de issues o enviándonos un mensaje directo.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Esto significa que tienes permiso para utilizar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del software, y para permitir que las personas a las que se les proporcione el software lo hagan, con sujeción a las siguientes condiciones:

- Se debe incluir una copia de la licencia en todas las copias o partes sustanciales del software.
- El software se proporciona "tal cual", sin garantía de ningún tipo, expresa o implícita, incluyendo pero no limitado a garantías de comerciabilidad, aptitud para un propósito particular y no infracción. En ningún caso los autores o titulares de la licencia serán responsables de cualquier reclamo, daño u otra responsabilidad, ya sea en una acción de contrato, agravio o de otra manera, que surja de, fuera de o en conexión con el software o el uso u otros tratos en el software.

Puedes encontrar una copia completa de la Licencia MIT en el archivo LICENSE que se incluye en este repositorio.

## Contacto

Si tienes alguna pregunta o comentario sobre el proyecto, no dudes en ponerte en contacto conmigo a través de los siguientes medios:

- Correo electrónico: lesclaz95@gmail.com
- Twitter: [@lesclaz](https://twitter.com/lesclaz)
- Telegram: [@lesclaz](https://t.me/lesclaz)

Estaré encantado de escuchar tus comentarios y responder tus preguntas. ¡Gracias por tu interés en mi proyecto!
