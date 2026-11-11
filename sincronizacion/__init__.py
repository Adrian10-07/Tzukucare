"""Sincronización con la app móvil: vincula este dispositivo a una o varias cuentas.

La Pi tiene un id propio (dispositivo.json) y publica en Firestore un código de 6 dígitos
que cambia cada pocos minutos. En Configuración → pestaña "Vincular" se ve ese código y un QR;
la app lo escanea (o se escribe el código) y queda vinculada.
El primer usuario en vincularse es el administrador. Todo lo de los roles lo validan
las reglas de Firestore (ver firestore.rules).

Para quitarlo: borra esta carpeta. main.py lo detecta y la app sigue igual
(las alertas vuelven a ir sin dispositivo_id).
"""
import json
import os
import uuid

DIR = os.path.dirname(os.path.abspath(__file__))
IDENTIDAD_PATH = os.path.join(DIR, "dispositivo.json")

COLECCION_DISPOSITIVOS = "dispositivos"
COLECCION_CODIGOS = "codigos_vinculacion"
VIGENCIA_CODIGO_SEG = 10 * 60   # Cada cuánto cambia el código de vinculación
REFRESCO_SEG = 15               # Cada cuánto se lee el estado y se manda el latido
ESQUEMA_QR = "tzukucare://vincular"


def topic_de(dispositivo_id: str) -> str:
    """Tema FCM propio de este dispositivo (la app se suscribe a él al vincularse)."""
    return f"tzukucare_{dispositivo_id}"


def cargar_identidad(ruta: str = IDENTIDAD_PATH) -> dict:
    """Lee el id del dispositivo; si no existe lo crea una sola vez y lo guarda."""
    datos = {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        pass
    if not isinstance(datos, dict) or not datos.get("id"):
        datos = {"id": uuid.uuid4().hex[:20], "nombre": "TzukuCare"}
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
        except OSError:
            pass
    return datos


def crear_servicio(firebase_service):
    """Crea el servicio de sincronización (todavía sin arrancar)."""
    from .servicio import SyncService
    return SyncService(firebase_service, cargar_identidad())
