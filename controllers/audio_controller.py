import time
import pyaudio
from PyQt5.QtCore import QThread, pyqtSignal
from models.audio_classifier import AudioClassifier
from models.state_machine import DetectionStateMachine
from models.firebase_service import FirebaseService
import config

class AudioController(QThread):
    update_ui_signal = pyqtSignal(str, str)  # (estado, clase)
    log_signal = pyqtSignal(str)             # (mensaje_log)

    def __init__(self, firebase_service: FirebaseService):
        super().__init__()
        self.classifier = AudioClassifier()
        self.state_machine = DetectionStateMachine()
        self.firebase = firebase_service
        self.is_running = True

    def trigger_manual_alarm(self):
        """Dispara inmediatamente la alarma manual de emergencia."""
        hora = time.strftime("%H:%M:%S")
        estado_texto = self.state_machine.force_alarm()
        
        self.update_ui_signal.emit(estado_texto, "Alarma Manual")
        self.log_signal.emit(f"[{hora}] 🚨 ALARMA MANUAL ACTIVADA POR USUARIO")

        # 1. Guardar en Firestore
        success_db, msg_db = self.firebase.save_alert("ACTIVACIÓN MANUAL DE EMERGENCIA")
        self.log_signal.emit(f"[{hora}] {msg_db}")

        # 2. Enviar Notificación Push FCM
        success_push, msg_push = self.firebase.send_push_notification("ACTIVACIÓN MANUAL DE EMERGENCIA")
        self.log_signal.emit(f"[{hora}] {msg_push}")

    def update_configuration(self, ladridos: int, sensibilidad_pct: float):
        """Actualiza la sensibilidad del clasificador y el umbral de ladridos."""
        hora = time.strftime("%H:%M:%S")
        umbral_confianza = sensibilidad_pct / 100.0

        self.state_machine.set_umbral_alarma(ladridos)
        self.classifier.set_umbral_confianza(umbral_confianza)

        self.log_signal.emit(
            f"[{hora}] ⚙️ Configuración actualizada: {ladridos} ladridos | Sensibilidad: {sensibilidad_pct:.0f}%"
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
            return

        while self.is_running:
            try:
                data = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
            except Exception:
                continue

            top_class, top_score, es_ladrido = self.classifier.process_and_classify(data)
            estado_texto = self.state_machine.update(es_ladrido)

            self.update_ui_signal.emit(estado_texto, top_class)

            if estado_texto in ["ESCUCHA ACTIVA", "¡¡ ALARMA ACTIVADA !!"]:
                hora = time.strftime("%H:%M:%S")

                if estado_texto == "ESCUCHA ACTIVA":
                    self.log_signal.emit(f"[{hora}] Ladrido detectado ({top_class})")

                elif estado_texto == "¡¡ ALARMA ACTIVADA !!":
                    self.log_signal.emit(f"[{hora}] ¡¡ ALARMA ACTIVADA !! - Ladridos continuos")

                    success_db, msg_db = self.firebase.save_alert(top_class)
                    self.log_signal.emit(f"[{hora}] {msg_db}")

                    success_push, msg_push = self.firebase.send_push_notification(top_class)
                    self.log_signal.emit(f"[{hora}] {msg_push}")

        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.is_running = False
        self.wait()