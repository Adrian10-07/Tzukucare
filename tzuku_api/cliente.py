import time
from datetime import datetime, timedelta, timezone

import requests

TIPO_INFERENCIA = "barkaggression"


class TzukuApiError(Exception):
    pass


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _buscar_clave(datos, claves):
    """Busca la primera clave presente en datos o en datos["data"] (la doc no fija el formato)."""
    for nivel in (datos, datos.get("data") if isinstance(datos, dict) else None):
        if isinstance(nivel, dict):
            for k in claves:
                if nivel.get(k):
                    return nivel[k]
    return None


def _como_lista(datos):
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        for k in ("data", "results", "items", "inferences"):
            if isinstance(datos.get(k), list):
                return datos[k]
            if isinstance(datos.get(k), dict):
                return _como_lista(datos[k])
    return []


def id_resultado(r: dict) -> str:
    return str(r.get("_id") or r.get("id") or r.get("createdAt") or sorted(r.items()))


class TzukuApiClient:
    def __init__(self, base_url: str, email: str, password: str, timeout: float = 30):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self._token = None

    # ---------- autenticación ----------
    def login(self) -> None:
        r = self.session.post(f"{self.base_url}/auth/login", timeout=self.timeout,
                              json={"email": self.email, "password": self.password})
        if r.status_code >= 400:
            raise TzukuApiError(f"login rechazado (HTTP {r.status_code})")
        token = _buscar_clave(r.json(), ("token", "accessToken", "access_token", "jwt"))
        if not token:
            raise TzukuApiError("el login no devolvió un token")
        self._token = token

    def _request(self, metodo: str, ruta: str, **kwargs):
        """Hace la petición con el token; si caduca (401) vuelve a iniciar sesión una vez."""
        for intento in range(2):
            if self._token is None:
                self.login()
            r = self.session.request(metodo, f"{self.base_url}{ruta}", timeout=self.timeout,
                                     headers={"Authorization": f"Bearer {self._token}"}, **kwargs)
            if r.status_code == 401 and intento == 0:
                self._token = None
                continue
            if r.status_code >= 400:
                raise TzukuApiError(f"{metodo} {ruta} -> HTTP {r.status_code}: {r.text[:200]}")
            return r
        raise TzukuApiError("no autorizado")

    # ---------- endpoints ----------
    def subir_audio(self, wav_bytes: bytes, pet_id: str, collar_id: str, nombre: str = "clip.wav"):
        r = self._request("POST", "/collar-raw-media",
                          files={"file": (nombre, wav_bytes, "audio/wav")},
                          data={"typeFile": "audio", "petId": pet_id, "collarId": collar_id})
        try:
            return r.json()
        except ValueError:
            return {}

    def consultar_resultados(self, collar_id: str, desde: datetime = None, hasta: datetime = None):
        params = {"collarId": collar_id}
        if desde:
            params["from"] = _iso(desde)
        if hasta:
            params["to"] = _iso(hasta)
        r = self._request("GET", "/inference", params=params)
        return [x for x in _como_lista(r.json())
                if isinstance(x, dict) and x.get("inferenceType") == TIPO_INFERENCIA]

    def analizar(self, wav_bytes: bytes, pet_id: str, collar_id: str, vistos: set = None,
                 consultar_cada: float = 3, espera_maxima: float = 90, nombre: str = "clip.wav"):
        """Sube el clip y espera su resultado. Devuelve el resultado (dict) o None si no llegó a tiempo."""
        vistos = vistos if vistos is not None else set()
        # Margen por si el reloj de la Pi y el del servidor no coinciden exactamente
        desde = datetime.now(timezone.utc) - timedelta(seconds=10)
        self.subir_audio(wav_bytes, pet_id, collar_id, nombre)

        limite = time.monotonic() + espera_maxima
        while time.monotonic() < limite:
            time.sleep(consultar_cada)
            nuevos = [r for r in self.consultar_resultados(collar_id, desde)
                      if id_resultado(r) not in vistos]
            if nuevos:
                nuevos.sort(key=lambda r: str(r.get("createdAt", "")))
                resultado = nuevos[-1]
                vistos.update(id_resultado(r) for r in nuevos)
                return resultado
        return None
