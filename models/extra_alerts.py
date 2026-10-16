import time
import config


class ExtraAlertMonitor:
    """Decide cuándo enviar las alertas extra (disparos, cristal, etc.) con enfriamiento por tipo."""

    def __init__(self, activas=None, enfriamiento: float = config.ENFRIAMIENTO_ALERTA_SEG):
        self.activas = set(activas or [])
        self.enfriamiento = enfriamiento
        self._ultimo_envio = {}

    def set_activas(self, activas):
        self.activas = set(activas or [])

    def update(self, detectadas: dict, ahora: float = None) -> list:
        """Recibe {clave: (clase, puntuación)} y devuelve las claves que deben dispararse ahora."""
        ahora = time.monotonic() if ahora is None else ahora
        disparar = []
        for clave in detectadas:
            if clave not in self.activas:
                continue
            ultimo = self._ultimo_envio.get(clave)
            if ultimo is not None and ahora - ultimo < self.enfriamiento:
                continue
            self._ultimo_envio[clave] = ahora
            disparar.append(clave)
        return disparar
