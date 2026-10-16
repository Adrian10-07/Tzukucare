import sys
# El motor de inferencia (TFLite / ONNX Runtime) se carga ANTES que PyQt5: en Windows, si Qt
# carga primero sus propias DLL de Visual C++, onnxruntime se cierra con "access violation".
import models.audio_classifier  # noqa: F401
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow
from models.firebase_service import FirebaseService
from models import settings_store
from controllers.audio_controller import AudioController
from controllers.firebase_worker import FirebaseWorker

def main():
    app = QApplication(sys.argv)

    # 1. Inicializar Servicios y cargar la configuración guardada
    firebase_service = FirebaseService()
    firebase_worker = FirebaseWorker(firebase_service)
    settings = settings_store.load_settings()

    # 2. Inicializar Vista y Controlador
    window = MainWindow(settings)
    audio_controller = AudioController(firebase_worker, settings)

    # 3. Conectar señales del Controlador a la Vista (Salida de datos)
    audio_controller.update_ui_signal.connect(window.update_status)
    audio_controller.log_signal.connect(window.append_log)
    audio_controller.calibration_done_signal.connect(window.on_calibration_done)
    firebase_worker.log_signal.connect(window.append_log)

    # 4. Conectar señales de la Vista al Controlador (Acciones del usuario)
    window.manual_alarm_signal.connect(audio_controller.trigger_manual_alarm)
    window.config_changed_signal.connect(audio_controller.update_configuration)
    window.calibration_requested_signal.connect(audio_controller.start_calibration)

    # 5. Mostrar Ventana e Iniciar hilos (Firebase y Captura de Audio)
    window.show()
    firebase_worker.start()
    audio_controller.start()

    exit_code = app.exec_()
    audio_controller.stop()
    firebase_worker.stop()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
