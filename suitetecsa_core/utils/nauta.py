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

import json
import os
import random
import re
import select
import socket
import string
import threading
import netifaces
import datetime


def time_string_to_seconds(time_string: str) -> int:
    """
    Convierte una cadena de tiempo en formato "HH:MM:SS" a segundos.

    Parámetros:
    - time_string: cadena de tiempo en formato "HH:MM:SS".

    Retorna la cantidad total de segundos en la cadena de tiempo.

    Lanza una excepción ValueError si el formato de tiempo es inválido.
    """
    try:
        # Verificar que la cadena de tiempo tenga el formato "HH:MM:SS"
        datetime.datetime.strptime(time_string, '%H:%M:%S')
    except ValueError:
        raise ValueError("Invalid time format. The format should be HH:MM:SS.")

    # Devolver la cantidad total de segundos utilizando una expresión generadora y la función sum()
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(time_string.split(":"))))


def seconds_to_time_string(seconds: int) -> str:
    """
    Convierte una cantidad de segundos en formato entero en una cadena de tiempo en formato "HH:MM:SS".

    Parámetros:
    - seconds: cantidad de segundos en formato entero.

    Retorna una cadena de tiempo en formato "HH:MM:SS".
    """
    # Calcular la cantidad de horas, minutos y segundos
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Devolver la cadena de tiempo en formato "HH:MM:SS"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def convert_from_bytes(size: int) -> str:
    """
    Esta función recibe una cantidad de datos en bytes y la convierte a un formato legible para el usuario,
    en unidades de "Bytes", "KB", "MB", "GB" o "TB".

    Parámetros:
    size (int): La cantidad de datos en bytes.

    Retorna:
    str: La cantidad de datos en un formato legible para el usuario, en unidades de "Bytes", "KB", "MB", "GB" o "TB".

    Ejemplos de uso:
    >>> convert_from_bytes(5242880)
    '5 MB'

    >>> convert_from_bytes(26843545600)
    '25 GB'

    >>> convert_from_bytes(555008)
    '542.47 KB'
    """
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(units)-1:
        size /= 1024
        i += 1
    size_str = f"{size:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{size_str} {units[i]}"


def convert_to_bytes(size: str) -> int:
    """
    Esta función recibe una cantidad de datos en formato de "X unidad" y la convierte a bytes.

    Parámetros:
    size (str): La cantidad de datos en formato de "X unidad". La unidad puede ser "bytes", "kb", "mb", "gb" o "tb".

    Retorna:
    int: La cantidad de datos en bytes.

    Lanza:
    ValueError: Si el formato del parámetro size es incorrecto.

    Ejemplos de uso:
    >>> convert_to_bytes("5 MB")
    5242880

    >>> convert_to_bytes("25 GB")
    26843545600

    >>> convert_to_bytes("542.47 KB")
    555008
    """
    units = {"bytes": 1, "kb": 1024, "mb": 1024 **
             2, "gb": 1024**3, "tb": 1024**4}
    size = size.split()
    try:
        return int(float(size[0].replace(",", ".")) * units[size[1].lower()])
    except (IndexError, KeyError, ValueError):
        raise ValueError(
            "El formato del parámetro size es incorrecto. Debe ser en formato 'X unidad', donde unidad puede ser "
            "'bytes', 'kb', 'mb', 'gb' o 'tb'."
        )


def verify_session_data(data: dict) -> None:
    """
    Verifica que los datos de sesión cumplan con los parámetros requeridos.

    Parámetros:
    - data: diccionario con los datos de sesión.

    Lanza una excepción ValueError si no se cumplen los parámetros requeridos.
    """
    required_keys = [
        'username', 'cookies', 'wlanuserip', 'CSRFHW', 'ATTRIBUTE_UUID'
    ]
    if not all(key in data for key in required_keys):
        raise ValueError(f'Parameters {required_keys} are required')


def save_data_to_file(data: dict, file_path: str) -> None:
    """
    Guarda los datos de sesión en un archivo JSON.

    Parámetros:
    - data: diccionario con los datos de sesión.
    - file_path: ruta del archivo donde se guardarán los datos.

    Lanza una excepción ValueError si los datos de sesión no cumplen con los parámetros requeridos.
    """
    verify_session_data(data=data)
    if os.path.exists(os.path.dirname(file_path)):
        with open(file_path, 'w') as file:
            json.dump(data, file)


def load_data_from_file(file_path: str) -> dict:
    """
    Carga los datos de sesión desde un archivo JSON.

    Parámetros:
    - file_path: ruta del archivo donde se encuentran los datos.

    Retorna un diccionario con los datos de sesión.

    Lanza una excepción ValueError si los datos de sesión no cumplen con los parámetros requeridos.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            verify_session_data(data=data)
            return data


def share_session(data: dict) -> tuple:
    """
    Comparte la sesión actual entre dos dispositivos mediante una conexión TCP/IP.

    Parameters:
        data (dict): los datos a compartir.

    Returns:
        tuple: un objeto `Thread` y un código de compartición.

    Raises:
        ValueError: Si el parámetro `data` no tiene las claves `wlanuserip`, `CSRFHW` y `ATTRIBUTE_UUID`.

    """

    # Verificar que el parámetro `data` tenga las claves 'username', 'cookies',
    # 'wlanuserip', 'CSRFHW' y `ATTRIBUTE_UUID`
    verify_session_data(data=data)

    def run_socket(session_data: dict, secret_phrase: str, timeout: int = 30) -> None:
        """
        Función auxiliar que corre en un hilo separado y maneja la conexión TCP/IP.

        Parameters:
            session_data (dict): los datos a compartir.
            secret_phrase (str): el código de compartición.
            timeout (int): el tiempo máximo de espera en segundos.

        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', 8024))
        s.listen(1)
        print("Escuchando en el puerto 8024...")
        ready, _, _ = select.select([s], [], [], timeout)
        if ready:
            conn, addr = s.accept()
            print(f"Conexión establecida desde {addr}")
            # Recibir el código de compartición enviado por el cliente
            received_share_code = conn.recv(1024).decode()
            if received_share_code == secret_phrase:
                # Enviar los datos y el código de compartición al cliente
                conn.sendall(json.dumps(session_data).encode())
                conn.close()
                print("La conexión se ha cerrado.")
            else:
                # Enviar un mensaje de error al cliente si el código de compartición es incorrecto
                conn.sendall("Invalid secret".encode())
                conn.close()
        else:
            print("Se ha agotado el tiempo de espera para recibir una conexión.")
            s.close()

    # Generar la parte aleatoria del código de compartición
    secret = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=4))

    # Obtener la dirección IP del dispositivo
    interface = netifaces.gateways()['default'][netifaces.AF_INET][1]
    ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']

    # Obtener los últimos tres dígitos de la dirección IP
    ip_suffix = ip.split(".")[-1].zfill(3)

    # Unir los últimos tres dígitos de la dirección IP con la parte aleatoria del código de compartición
    share_code = f"{ip_suffix}-{secret}"

    # Crear un hilo para manejar la conexión TCP/IP
    thread = threading.Thread(target=run_socket, args=(data, secret))

    # Iniciar el hilo
    thread.start()

    # Devolver el objeto Thread y el código de compartición
    return thread, share_code


def join_session(share_code: str) -> dict[str, str]:
    """
    Establece una conexión con un servidor remoto utilizando un código de sesión compartido.

    Args:
    - share_code (str): Código de sesión compartido con el que se establecerá la conexión.

    Returns:
    - session_data (dict): Diccionario con los datos de la sesión obtenidos del servidor remoto.

    Raises: - ValueError: Si el código de sesión no tiene el formato correcto o si los datos de la sesión recibidos
    no son correctos. - ConnectionRefusedError: Si no se puede establecer la conexión con el servidor remoto. -
    json.JSONDecodeError: Si se produce un error al decodificar el JSON recibido del servidor remoto.

    """
    # Verificamos que el código tenga el formato "XXX-XXXX"
    pattern = r'^\d{3}-[A-Z\d]{4}$'
    if not re.match(pattern, share_code):
        raise ValueError('El código no tiene el formato correcto')

    # Obtenemos los primeros tres números de la dirección IP de la máquina en la red local
    ip_range = '.'.join(netifaces.ifaddresses(netifaces.interfaces()[0])[
                        netifaces.AF_INET][0]['addr'].split('.')[:3])

    # Unimos los primeros tres caracteres de share_code con ip_range
    dest_ip = ip_range + '.' + str(int(share_code[:3]))

    # Guardamos los últimos cuatro caracteres de share_code en la variable secret
    secret = share_code[-4:]

    try:
        # Creamos un socket y nos conectamos a dest_ip en el puerto 8024
        with socket.create_connection((dest_ip, 8024)) as s:
            # Enviamos el valor de secret al servidor
            s.sendall(secret.encode('utf-8'))

            # Esperamos recibir el diccionario JSON
            data = s.recv(1024)

        # Decodificamos el JSON y lo guardamos en la variable session_data
        session_data = json.loads(data.decode('utf-8'))

    except json.JSONDecodeError:
        # Si se produce un error al decodificar el JSON, comprobamos si recibimos un mensaje de error en formato string
        if data.decode('utf-8').strip() == 'Invalid secret':
            raise ValueError('El código secreto es inválido')
        else:
            raise ValueError('Error al recibir los datos de la sesión')

    # Verificar que el parámetro `data` tenga las claves 'username', 'cookies',
    # 'wlanuserip', 'CSRFHW' y `ATTRIBUTE_UUID`
    verify_session_data(data=session_data)

    # Devolvemos el diccionario recibido
    return session_data
