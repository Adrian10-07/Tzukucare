
class DetectionStateMachine:
    def __init__(self):
        self.okgoogle = 0
        self.ladridos_seguidos = 0
        self.ladridos_total_escucha = 0

    def update(self, es_ladrido: bool):
        """Evalúa las transiciones de estado según la detección de ladridos."""
        estado_texto = "REPOSO"

        if es_ladrido:
            self.ladridos_seguidos += 1
            if self.ladridos_seguidos >= 2 or self.okgoogle == 1:
                self.okgoogle = 1
                estado_texto = "ESCUCHA ACTIVA"
                self.ladridos_total_escucha += 1

        if self.ladridos_total_escucha >= 3:
            estado_texto = "¡¡ ALARMA ACTIVADA !!"
            # Resetear contadores tras la activación de la alarma
            self.ladridos_total_escucha = 0
            self.okgoogle = 0
            self.ladridos_seguidos = 0

        return estado_texto