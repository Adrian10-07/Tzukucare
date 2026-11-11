"""Servicio opcional: análisis de agresividad en ladridos con la API de TZUKU.

Viene APAGADO. Se activa y se configura desde Configuración → pestaña "API"
(o editando tzuku_api/config.json). Para quitarlo del proyecto basta con borrar esta
carpeta: main.py lo detecta y la app sigue igual.
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Valores por defecto (las credenciales NO tienen valor por defecto: se escriben desde la app)
DEFAULTS = {
    "activo": False,
    "base_url": "https://multimodal-ai-lab.cicese.mx/api",
    "email": "",
    "password": "",
    "pet_id": "",
    "collar_id": "",
    "segundos_clip": 15,
    "sample_rate_wav": 16000,
    "enfriamiento_seg": 60,
    "consultar_cada_seg": 3,
    "espera_maxima_seg": 90,
    "timeout_http_seg": 30,
    "reenviar_a_firebase": False,
    "reenviar_etiquetas": ["aggressive", "very_aggressive"],
}
OBLIGATORIOS = ("email", "password", "pet_id", "collar_id")


def cargar_config(ruta: str = CONFIG_PATH) -> dict:
    """Lee config.json sobre los valores por defecto. Si no existe o está dañado, devuelve los defaults."""
    datos = {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        pass
    config = {**DEFAULTS, **(datos if isinstance(datos, dict) else {})}
    # Permite no guardar la contraseña en disco: la variable de entorno tiene prioridad
    if os.environ.get("TZUKU_API_PASSWORD"):
        config["password"] = os.environ["TZUKU_API_PASSWORD"]
    return config


def guardar_config(config: dict, ruta: str = CONFIG_PATH) -> bool:
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def faltantes(config: dict) -> list:
    """Campos obligatorios vacíos o con el texto de ejemplo."""
    return [k for k in OBLIGATORIOS
            if not str(config.get(k) or "").strip() or str(config[k]).startswith(("TU_", "ID_"))]


def crear_complemento(firebase_worker=None):
    """Crea el servicio. Siempre devuelve el objeto: si está apagado no hace nada hasta que se active."""
    from .complemento import TzukuApiAddon
    return TzukuApiAddon(cargar_config(), firebase_worker)
