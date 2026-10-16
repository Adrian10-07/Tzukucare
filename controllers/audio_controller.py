import time
import pyaudio
from PyQt5.QtCore import QThread, pyqtSignal
from models.audio_classifier import AudioClassifier
from models.state_machine import DetectionStateMachine
from models.extra_alerts import ExtraAlertMonitor
from models import settings_store
from controllers.firebase_worker import FirebaseWorker
import config

class AudioController(QThread):
    update_ui_signal = pyqtSignal(str, str)  # (estado, clase)
    log_signal = pyqtSignal(str)             # (mensaje_log)
    calibration_done_signal = pyqtSignal(float)  # nivel máximo medido (dBFS)

    def __init__(self, firebase_worker: FirebaseWorker, settings: dict = None):
        super().__init__()
        self.classifier = AudioClassifier()
        self.state_machine = DetectionStateMachine()
        self.extra_alerts = ExtraAlertMonitor()
        self.firebase_worker = firebase_worker
        self.is_running = True
        self._calibrando_hasta = None
        self._calibracion_max = None
        self._ultimo_ui = None
        self._apply_settings(settings or settings_store.load_settings())

    def _apply_settings(self, settings: dict):
        self.state_machine.set_umbral_alarma(settings["ladridos"])
        self.classifier.set_umbral_confianza(settings["sensibilidad"] / 100.0)
        self.classifier.set_umbral_db(settings_store.umbral_db(settings))
        self.extra_alerts.set_activas(settings["alertas_extra"])

    def trigger_manual_alarm(self):
        """Dispara inmediatamente la alarma manual de emergencia."""
        hora = time.strftime("%H:%M:%S")
        estado_texto = self.state_machine.force_alarm()
        
        self._ultimo_ui = None  # fuerza que el hilo de audio vuelva a refrescar la interfaz después
        self.update_ui_signal.emit(estado_texto, "Alarma Manual")
        self.log_signal.emit(f"[{hora}] 🚨 ALARMA MANUAL ACTIVADA POR USUARIO")

        # Firestore + Push en el hilo de Firebase (no congela la interfaz)
        self.firebase_worker.enqueue("ACTIVACIÓN MANUAL DE EMERGENCIA", tipo="manual",
                                     mensaje="Ladridos detectados (ACTIVACIÓN MANUAL DE EMERGENCIA)")

    def update_configuration(self, settings: dict):
        """Aplica y guarda la configuración (ladridos, sensibilidad, alcance y alertas extra)."""
        hora = time.strftime("%H:%M:%S")
        settings = settings_store.sanitize(settings)
        self._apply_settings(settings)
        guardado = settings_store.save_settings(settings)

        umbral = settings_store.umbral_db(settings)
        alcance = "sin límite" if umbral is None else f"{umbral:.0f} dBFS"
        self.log_signal.emit(
            f"[{hora}] ⚙️ Configuración actualizada: {settings['ladridos']} ladridos | "
            f"Sensibilidad: {settings['sensibilidad']}% | Alcance: {alcance} | "
            f"Alertas extra: {', '.join(settings['alertas_extra']) or 'ninguna'}"
            + ("" if guardado else " (no se pudo guardar en disco)")
        )

    def start_calibration(self):
        """Mide el volumen máximo durante unos segundos para fijar el alcance."""
        self._calibracion_max = None
        self._calibrando_hasta = time.monotonic() + config.CALIBRACION_SEG

    def _update_calibration(self, nivel_db: float):
        if self._calibrando_hasta is None:
            return
        if self._calibracion_max is None or nivel_db > self._calibracion_max:
            self._calibracion_max = nivel_db
        if time.monotonic() >= self._calibrando_hasta:
            self._calibrando_hasta = None
            self.calibration_done_signal.emit(self._calibracion_max)

    def _send_extra_alerts(self, detectadas: dict):
        hora = time.strftime("%H:%M:%S")
        for clave in self.extra_alerts.update(detectadas):
            nombre, _, nivel = config.ALERTAS_EXTRA[clave]
            clase, score = detectadas[clave]
            self.log_signal.emit(f"[{hora}] 🔔 ALERTA: {nombre} ({clase}, {score:.2f})")
            self.firebase_worker.enqueue(
                clase, tipo=clave, nivel=nivel,
                mensaje=f"{nombre} detectado ({clase})",
                titulo=f"¡TzukuCare: {nombre}!",
                cuerpo=f"Se detectó un posible sonido de {nombre.lower()} ({clase}).",
            )

    def run(self):
        p = pyaudio.PyAudio()

        input_device_index = None
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels', 0) > 0:
                input_device_index = i
                break

        if input_device_index is None:
            self.log_signal.emit("❌ Error: No se encontró micrófono disponible.")
            p.terminate()
            return

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=config.CHANNELS,
                rate=config.SAMPLE_RATE_IN,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=config.CHUNK_SIZE
            )
        except Exception as e:
            self.log_signal.emit(f"❌ Error al abrir micrófono: {e}")
            p.terminate()
            return

        while self.is_running:
            try:
                data = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
            except Exception:
                continue

            resultado = self.classifier.process_and_classify(data)
            top_class = resultado["top_class"]
            self._update_calibration(resultado["nivel_db"])

            estado_texto = self.state_machine.update(resultado["es_ladrido"])

            # Solo repinta la interfaz cuando algo cambia
            if (estado_texto, top_class) != self._ultimo_ui:
                self._ultimo_ui = (estado_texto, top_class)
                self.update_ui_signal.emit(estado_texto, top_class)

            if resultado["alertas"]:
                self._send_extra_alerts(resultado["alertas"])

            if estado_texto in ["ESCUCHA ACTIVA", "¡¡ ALARMA ACTIVADA !!"]:
                hora = time.strftime("%H:%M:%S")

                if estado_texto == "ESCUCHA ACTIVA":
                    self.log_signal.emit(f"[{hora}] Ladrido detectado ({top_class})")

                elif estado_texto == "¡¡ ALARMA ACTIVADA !!":
                    self.log_signal.emit(f"[{hora}] ¡¡ ALARMA ACTIVADA !! - Ladridos continuos")

                    # Firestore + Push en el hilo de Firebase (el micrófono sigue escuchando)
                    self.firebase_worker.enqueue(top_class, tipo="ladrido")

        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.is_running = False
        self.wait()