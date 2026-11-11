import io
import queue
import time
import wave
from collections import deque
from math import ceil, gcd

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from scipy.signal import resample_poly

import config as app_config
from . import faltantes, guardar_config
from .cliente import TzukuApiClient, TzukuApiError

ETIQUETAS = {
    "others": "Normal / otro",
    "aggressive": "Agresivo",
    "very_aggressive": "Muy agresivo",
    "unsure": "Incierto",
}


def chunks_a_wav(chunks, rate_in: int, rate_out: int) -> bytes:
    """Une bloques int16 mono del micrófono y los guarda como WAV a rate_out."""
    audio = np.frombuffer(b"".join(chunks), dtype=np.int16)
    if rate_out != rate_in:
        g = gcd(rate_in, rate_out)
        audio = resample_poly(audio.astype(np.float32), rate_out // g, rate_in // g)
        audio = np.clip(audio, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate_out)
        w.writeframes(audio.tobytes())
    return buf.getvalue()


class TzukuApiAddon(QThread):
    log_signal = pyqtSignal(str)
    resultado_signal = pyqtSignal(dict)   # payload completo de la API, por si la vista lo quiere usar

    def __init__(self, config: dict, firebase_worker=None):
        super().__init__()
        self.firebase_worker = firebase_worker
        self.activo = False
        self._cola = queue.Queue()
        self._ultimo_envio = 0.0
        self._vistos = set()
        self.cfg = config
        self.aplicar_config(config, guardar=False, avisar=False)

    def aplicar_config(self, config: dict, guardar: bool = True, avisar: bool = True):
        """Activa, desactiva o cambia credenciales en caliente (se llama desde el panel)."""
        if guardar and not guardar_config(config):
            self.log_signal.emit("⚠️ API TZUKU: no se pudo guardar tzuku_api/config.json")
        faltan = faltantes(config)
        activar = bool(config.get("activo")) and not faltan

        self.cfg = config
        self.cliente = TzukuApiClient(config["base_url"], config["email"], config["password"],
                                      timeout=config["timeout_http_seg"])
        seg_por_chunk = app_config.CHUNK_SIZE / app_config.SAMPLE_RATE_IN
        self._buffer = deque(maxlen=max(1, ceil(config["segundos_clip"] / seg_por_chunk)))
        self.activo = activar

        if avisar:
            hora = time.strftime("%H:%M:%S")
            if activar:
                self.log_signal.emit(f"[{hora}] 🌐 Análisis API TZUKU activado")
            elif config.get("activo"):
                self.log_signal.emit(f"[{hora}] ⚠️ Análisis API TZUKU sin activar: faltan {', '.join(faltan)}")
            else:
                self.log_signal.emit(f"[{hora}] Análisis API TZUKU desactivado")

    # ---------- llamadas desde el hilo de audio (deben ser rápidas) ----------
    def feed(self, data: bytes):
        if self.activo:
            self._buffer.append(data)

    def on_alarm(self):
        if not self.activo:
            return
        ahora = time.monotonic()
        if ahora - self._ultimo_envio < self.cfg["enfriamiento_seg"]:
            return
        self._ultimo_envio = ahora
        self._cola.put(list(self._buffer))

    # ---------- hilo propio ----------
    def run(self):
        if self.activo:
            hora = time.strftime("%H:%M:%S")
            self.log_signal.emit(f"[{hora}] 🌐 Análisis API TZUKU activo (clips de {self.cfg['segundos_clip']} s)")
        while True:
            chunks = self._cola.get()
            if chunks is None:
                break
            if self.activo:   # si lo apagaron mientras esperaba en la cola, no se envía
                self._procesar(chunks)

    def _procesar(self, chunks):
        hora = time.strftime("%H:%M:%S")
        try:
            wav = chunks_a_wav(chunks, app_config.SAMPLE_RATE_IN, self.cfg["sample_rate_wav"])
            self.log_signal.emit(f"[{hora}] 🌐 Enviando clip a la API TZUKU ({len(wav) // 1024} KB)...")
            resultado = self.cliente.analizar(
                wav, self.cfg["pet_id"], self.cfg["collar_id"], self._vistos,
                consultar_cada=self.cfg["consultar_cada_seg"],
                espera_maxima=self.cfg["espera_maxima_seg"],
                nombre=f"tzukucare_{time.strftime('%Y%m%d_%H%M%S')}.wav")
        except (TzukuApiError, OSError, ValueError) as e:   # requests.RequestException hereda de OSError
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] ❌ API TZUKU: {e}")
            return

        hora = time.strftime("%H:%M:%S")
        if resultado is None:
            self.log_signal.emit(f"[{hora}] ⏳ API TZUKU: sin resultado tras {self.cfg['espera_maxima_seg']} s")
            return

        payload = resultado.get("payload") or {}
        label = payload.get("label", "?")
        conf = payload.get("confidence")
        conf_txt = f" ({conf:.0%})" if isinstance(conf, (int, float)) else ""
        metr = payload.get("metrics") or {}
        bpm = metr.get("barks_per_minute")
        extra = f" | {bpm:.0f} ladridos/min" if isinstance(bpm, (int, float)) else ""
        self.log_signal.emit(f"[{hora}] 🐕 API TZUKU: {ETIQUETAS.get(label, label)}{conf_txt}{extra}")
        self.resultado_signal.emit(resultado)

        if (self.cfg["reenviar_a_firebase"] and self.firebase_worker is not None
                and label in self.cfg["reenviar_etiquetas"]):
            nombre = ETIQUETAS.get(label, label)
            self.firebase_worker.enqueue(
                label, tipo="agresividad",
                nivel="Crítico" if label == "very_aggressive" else "Advertencia",
                mensaje=f"Ladrido {nombre.lower()}{conf_txt}",
                titulo=f"¡TzukuCare: ladrido {nombre.lower()}!",
                cuerpo=f"El análisis de la API clasificó los ladridos como {nombre.lower()}{conf_txt}.")

    def crear_panel(self):
        """Pestaña para el modal de Configuración (ver tzuku_api/panel.py)."""
        from .panel import PanelApi
        return PanelApi(self)

    def stop(self):
        self._cola.put(None)
        self.wait(5000)   # no bloquea el cierre si una petición está colgada
