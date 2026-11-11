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
    audio_controller.extra_alert_signal.connect(window.show_extra_alert)  # [ALERTAS UI]
    firebase_worker.log_signal.connect(window.append_log)

    # [API TZUKU] Servicio opcional (apagado por defecto; se activa en Configuración → pestaña API).
    # Para quitarlo: borra la carpeta tzuku_api/ (o este bloque).
    api_addon = None
    try:
        from tzuku_api import crear_complemento
        api_addon = crear_complemento(firebase_worker)
        api_addon.log_signal.connect(window.append_log)
        audio_controller.api_addon = api_addon
        window.extra_config_tabs.append(api_addon.crear_panel)
    except ImportError as e:  # carpeta borrada: se ignora; otra dependencia faltante: se avisa
        if e.name != "tzuku_api":
            window.append_log(f"API TZUKU no disponible: {e}")

    # [SINCRONIZACIÓN] Vincula la Pi con la app móvil (pestaña "Vincular" en Configuración).
    # Para quitarlo: borra la carpeta sincronizacion/ (o este bloque).
    sync = None
    try:
        from sincronizacion import crear_servicio
        sync = crear_servicio(firebase_service)
        firebase_service.dispositivo_id = sync.dispositivo_id
        sync.log_signal.connect(window.append_log)
        window.extra_config_tabs.insert(0, sync.crear_panel)
        if api_addon:  # el admin escribe el petId/collarId en la app y llegan aquí solos
            def _usar_mascota(pet, collar):
                if pet and collar and (pet, collar) != (api_addon.cfg.get("pet_id"), api_addon.cfg.get("collar_id")):
                    api_addon.aplicar_config({**api_addon.cfg, "pet_id": pet, "collar_id": collar})
            sync.mascota_signal.connect(_usar_mascota)
    except ImportError as e:
        if e.name != "sincronizacion":
            window.append_log(f"Sincronización no disponible: {e}")

    # 4. Conectar señales de la Vista al Controlador (Acciones del usuario)
    window.manual_alarm_signal.connect(audio_controller.trigger_manual_alarm)
    window.config_changed_signal.connect(audio_controller.update_configuration)
    window.calibration_requested_signal.connect(audio_controller.start_calibration)

    # 5. Mostrar Ventana e Iniciar hilos (Firebase y Captura de Audio)
    window.show()
    firebase_worker.start()
    audio_controller.start()
    if sync:  # [SINCRONIZACIÓN]
        sync.start()
    if api_addon:  # [API TZUKU]
        api_addon.start()

    exit_code = app.exec_()
    audio_controller.stop()
    if api_addon:  # [API TZUKU]
        api_addon.stop()
    if sync:  # [SINCRONIZACIÓN]
        sync.stop()
    firebase_worker.stop()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
