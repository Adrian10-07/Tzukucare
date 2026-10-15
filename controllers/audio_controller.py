import time
import pyaudio
from PyQt5.QtCore import QThread, pyqtSignal
from models.audio_classifier import AudioClassifier
from models.state_machine import DetectionStateMachine
from models.firebase_service import FirebaseService
import config

class AudioController(QThread):
    # Señales enviadas hacia la vista
    update_ui_signal = pyqtSignal(str, str)  # (estado, clase)
    log_signal = pyqtSignal(str)             # (mensaje_log)

    def __init__(self, firebase_service: FirebaseService):
        super().__init__()
        self.classifier = AudioClassifier()
        self.state_machine = DetectionStateMachine()
        self.firebase = firebase_service
        self.is_running = True

    def run(self):
        p = pyaudio.PyAudio()

        input_device_index = None
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels', 0) > 0:
                input_device_index = i
                break

        if input_device_index is None:
            self.log_signal.emit("Error: No se encontró micrófono disponible.")
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
            self.log_signal.emit(f"Error al abrir micrófono: {e}")
            return

        while self.is_running:
            try:
                data = stream.read(config.CHUNK_SIZE, exception_on_overflow=False)
            except Exception:
                continue

            # 1. Procesar audio con el Modelo de Inferencia
            top_class, top_score, es_ladrido = self.classifier.process_and_classify(data)

            # 2. Actualizar el Modelo de Estado
            estado_texto = self.state_machine.update(es_ladrido)

            # 3. Notificar a la Vista para actualizar la UI
            self.update_ui_signal.emit(estado_texto, top_class)

            # 4. Manejo de eventos de registro y dispatch de Firebase
            if estado_texto in ["ESCUCHA ACTIVA", "¡¡ ALARMA ACTIVADA !!"]:
                hora = time.strftime("%H:%M:%S")

                if estado_texto == "ESCUCHA ACTIVA":
                    self.log_signal.emit(f"[{hora}] Ladrido detectado ({top_class})")

                elif estado_texto == "¡¡ ALARMA ACTIVADA !!":
                    self.log_signal.emit(f"[{hora}] ¡¡ ALARMA ACTIVADA !! - Ladridos continuos")

                    # Disparo a Firestore
                    success_db, msg_db = self.firebase.save_alert(top_class)
                    self.log_signal.emit(f"[{hora}] {msg_db}")

                    # Disparo Push FCM
                    success_push, msg_push = self.firebase.send_push_notification(top_class)
                    self.log_signal.emit(f"[{hora}] {msg_push}")

        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.is_running = False
        self.wait()