class DetectionStateMachine:
    def __init__(self, umbral_alarma: int = 3):
        self.okgoogle = 0
        self.ladridos_seguidos = 0
        self.ladridos_total_escucha = 0
        self.umbral_alarma = umbral_alarma

    def set_umbral_alarma(self, nuevo_umbral: int):
        """Actualiza dinámicamente cuántos ladridos activan la alarma."""
        self.umbral_alarma = max(1, nuevo_umbral)

    def force_alarm(self) -> str:
        """Fuerza manualmente el estado de Alarma para emergencias."""
        self.ladridos_total_escucha = 0
        self.okgoogle = 0
        self.ladridos_seguidos = 0
        return "¡¡ ALARMA ACTIVADA !!"

    def update(self, es_ladrido: bool) -> str:
        """Evalúa las transiciones de estado según la detección de ladridos."""
        estado_texto = "REPOSO"

        if es_ladrido:
            self.ladridos_seguidos += 1
            if self.ladridos_seguidos >= 2 or self.okgoogle == 1:
                self.okgoogle = 1
                estado_texto = "ESCUCHA ACTIVA"
                self.ladridos_total_escucha += 1

        if self.ladridos_total_escucha >= self.umbral_alarma:
            estado_texto = "¡¡ ALARMA ACTIVADA !!"
            self.ladridos_total_escucha = 0
            self.okgoogle = 0
            self.ladridos_seguidos = 0

        return estado_texto