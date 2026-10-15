# main.py
import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow
from models.firebase_service import FirebaseService
from controllers.audio_controller import AudioController

def main():
    app = QApplication(sys.argv)

    # 1. Inicializar Servicios (Modelos)
    firebase_service = FirebaseService()

    # 2. Inicializar la Interfaz Gráfica (Vista)
    window = MainWindow()

    # 3. Inicializar el Controlador
    audio_controller = AudioController(firebase_service)

    # 4. Conectar señales del Controlador a la Vista
    audio_controller.update_ui_signal.connect(window.update_status)
    audio_controller.log_signal.connect(window.append_log)

    # 5. Mostrar Ventana e Iniciar Captura
    window.show()
    audio_controller.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()