# suitetecsa_core

`suitetecsa_core` es una librería de Python que permite interactuar de manera sencilla con algunos servicios ofrecidos por ETECSA, el proveedor de servicios de telecomunicaciones en Cuba. La librería incluye un conjunto de módulos y herramientas que facilitan el acceso a estos servicios a través de técnicas de scrapping.

Con `suitetecsa_core`, puedes obtener datos de manera rápida y eficiente a partir de dos portales web: el [portal de acceso a internet](https://secure.etecsa.net:8443/) y el [portal de usuario](https://www.portal.nauta.cu/) de Nauta. La librería te permite devolver los datos en formato JSON como si fuera una API REST y realizar algunas operaciones comunes, como consultar el saldo de una cuenta Nauta o conectarte a internet.

Además, `suitetecsa_core` incluye métodos que agregan funcionalidades útiles, como la generación de contraseñas y la compartición de sesión. Con `suitetecsa_core`, puedes automatizar tareas comunes y ahorrar tiempo al interactuar con los servicios de ETECSA.

La librería es fácil de usar y está diseñada para ser extensible y personalizable, lo que te permite adaptarla a tus necesidades específicas. Además, se está trabajando para agregar más portales para agregar más servicios que se puedan gestionar con `suitetecsa_core`.

### Portales de ETECSA que gestiona `suitetecsa_core` y funciones implementadas

- [x] [Secure Etecsa](https://secure.etecsa.net:8443/)
  
  - [x] Iniciar sesión.
  - [x] Cerrar sesión.
  - [x] Obtener el tiempo disponible en la cuenta.
  - [x] Obtener la informacion de la cuenta.

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

- [ ] [Servicios en Linea](https://www.tienda.etecsa.cu/)

- [ ] [Portal Nauta](https://www.nauta.cu/)



# Uso

### Gestiona los servicios `Nauta` con NautaSession

NautaSession es la clase encargada de interactuar con los servicios de nauta que gestiona `suitetecsa_core`. Los portales con los que interactúa son: [Secure Etcsa](https://secure.etecsa.net:8443/) y [Portal de Usuario](https://www.portal.nauta.cu/). A continuación se muestra como iniciar una sesión con cuarquiera de estos dos portales.

```python
from suitetecsa_core import NautaSession, Portal


# se instancia la clase nautasession, encargada de gestionar la sesión
nauta_session = NautaSession(
    portal_manager = Portal.CONNECT,
    use_api_response = True
)
```

Aquí lo que hicimos fue importar la clase NautaSession que es la encargada de gestionar la sesión que crearemos con el portal, luego instanciamos la clase pasándole dos parámetros, el primero hace referencia al portal que queremos gestionar, en este caso es Portal.CONNECT que hace referencia a [Secure Etcsa](https://secure.etecsa.net:8443/), la otra opción es Portal.USER que hace referencia a [Portal de Usuario](https://www.portal.nauta.cu/). El segundo parámetro que le pasamos a NautaSession afecta la forma en la que los métodos de la clase retorna los valores.

```python
# se inicializa la sesión en el portal
session_data = nauta_session.init()
print(session_data)
```

__Salida por consola__

```bash
{
    'status': 'success',
    'login_action': 'https://secure.etecsa.net:8443//LoginServle',
    'CSRFHW': '1fe3ee0634195096337177a0994723fb',
    'wlanuserip': '10.190.20.96'
}
```

Como puedes ver, el método init nos ha devuelto un `diccionario Python` o `JSON` con los parámetros importantes de la sesión simulando a una verdadera API Rest, si el parémetro `use_api_response` fuera `False` (valor por defecto) el método no hubiese retornado nada. Y ya de paso; así es como se inicializa una sesión con los portales gestionados por `suitetecsa_core`.

Ahora es necesario proporcionar las credenciales para poder gestionar nuestra cuenta de usuario en el portal. Hay dos maneras de hacerlo y da igual la que elijas ya que no refleja ningún cambio en el comportamiento de la clase o sus métodos.

```python
# la primera manera de proporcionarle las credenciales a la clase
# es hacerlo por separado.
nauta_session.username = "user.name@nauta.com.cu"
nauta_session.password = "some_password"

# la otra manera de hacerlo es pasandole las credenciales en un sol
# linea de código
nauta_session.credentials = "user.name@nauta.com.cu", "some_password"
```

Ya tenemos la sesión inicializada, ya le proporcionamos las credenciales a la clase, ahora toca iniciar sesión.

```python
# si a portal_manager de diste como valor Portal.COONECT
login_data = nauta_session.login()

# si el valor fue Portal.USER necesitas descargar la imagen captcha
# para poder proporcionar el código que aparece en dicha imagen
with open("captcha_image.png", "wb") as file:
    file.write(nauta_session.get_captcha())
login_data = nauta_session.login(input("Captcha code: "))
```

## Métodos de la clase NautaSession

| Método                | Parámetros                                                                                | Secure Etecsa | Portal de Usuario | Descripción                                                        |
| ---------------------:|:-----------------------------------------------------------------------------------------:|:-------------:|:-----------------:|:------------------------------------------------------------------ |
| init                  | -                                                                                         | si            | si                | Inicializa la sesión en el portal..                                |
| get_captcha           | -                                                                                         | no            | si                | devuelve la imagen captcha en formato de bytes.                    |
| login                 | captcha_code: `str` (opcional)                                                            | si            | si                | loggea al usuario en el portal.                                    |
| get_remaining_time    | -                                                                                         | si            | no                | obtiene el tiempo diponible de la cuenta.                          |
| get_user_information  | -                                                                                         | si            | si                | obtine la informacion de la cuenta.                                |
| recharge              | recharge_code: `str`                                                                      | no            | si                | recarga el saldo de la cuenta.                                     |
| transfer              | mount_to_transfer: `int`, account_to_transfer: `str` (opcional), nauta_hogar_paid: `bool` | no            | si                | transfiere saldo a otra cuenta nauta o paga nauta hogar.           |
| change_password       | new_password: `str`                                                                       | no            | si                | cambia la contrase;a de acceso.                                    |
| change_email_password | old_password: `str`, new_password: `str`                                                  | no            | si                | cambia la contrase;a de la cuenta de correo asociada.              |
| get_connections       | year: `int`, month: `int`                                                                 | no            | si                | obtiene las conecciones realizadas en el periodo `a;o-mes`.        |
| get_recharges         | year: `int`, month: `int`                                                                 | no            | si                | obtiene las recargas realizadas en el periodo `a;o-mes`.           |
| get_transfers         | year: `int`, month: `int`                                                                 | no            | si                | obtiene las transferencias realizadas en el periodo `a;o-mes`.     |
| get_quotes_paid       | year: `int`, month: `int`                                                                 | no            | si                | obtiene los pagos realizado a nauta hogar en el periodo `a;o-mes`. |
| get_lasts             | action: `Action`, large: `int` (Opcional)                                                 | no            | si                | obtiene las ultimas `large` `action`s.                             |
| logout                | -                                                                                         | si            | si                | cierra la sesion del portal                                        |



## Método get_lasts

Ya que este es un método un poco confuso de usar sin documentación, decidí mostrar un ejemplo de su uso y dar una breve explicación.

```python
#importamos el enum Action
from suitetecsa_core import Action

# obtenemos las ultimas 2 recargas realizadas
lasts_recharges = nauta_session.get_lasts(
    action = Action.GET_RECHARGES,
    large = 2
) 
print(lasts_recharges)
```

__Salida por consola__

```bash
{
    "status": "success",
    "recharges_summary": {
        "count": 2,
        "total_import": "$450,00"
    },
    "recharges": [
        {
            "date": "10/03/2023 12:12:33",
            "import": "$200,00",
            "channel": "PV ETECSA",
            "type": "Efectivo"
        },
        {
            "date": "16/03/2023 19:41:35",
            "import": "$250,00",
            "channel": "Transferm\u00f3vil",
            "type": "Efectivo"
        }
    ]
}
```

get_lasts obtiene y devuelve las últimas `large` `action`s, donde `large` es la cantidad y `action` que va a intentar obtener. Las `action`s que se le pueden pasar como parametro a get_lasts son: Action.**GET_CONNECTIONS**, Action.**GET_RECHARGES**, Action.**GET_TRANSFERS** y Action.**GET_QUOTES_PAID**, que hacen referencia a las **conexiones**, **recargas**, **transferencias** y **pagos de cuotas a nauta hogar** realizadas por la cuenta, respectivamente. Por otra parte, `large` es de tipo entero y es un parámetro opcional ya que tiene un valor asignado por defecto, este valor es 5, o sea, que si se hace una llamada al método get_lasts y unicamente se le pasa una Action como parámetro, este nos devuelve las últimas **5** `action`s realizadas por la cuenta en sesión.

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
