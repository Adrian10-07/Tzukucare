# main.py
import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow
from models.firebase_service import FirebaseService
from controllers.audio_controller import AudioController

def main():
    app = QApplication(sys.argv)

    # 1. Inicializar Servicios
    firebase_service = FirebaseService()

    # 2. Inicializar Vista y Controlador
    window = MainWindow()
    audio_controller = AudioController(firebase_service)

    # 3. Conectar señales del Controlador a la Vista (Salida de datos)
    audio_controller.update_ui_signal.connect(window.update_status)
    audio_controller.log_signal.connect(window.append_log)

    # 4. Conectar señales de la Vista al Controlador (Acciones del usuario)
    window.manual_alarm_signal.connect(audio_controller.trigger_manual_alarm)
    window.config_changed_signal.connect(audio_controller.update_configuration)

    # 5. Mostrar Ventana e Iniciar Captura de Audio
    window.show()
    audio_controller.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()