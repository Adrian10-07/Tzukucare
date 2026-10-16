import queue
import time
from PyQt5.QtCore import QThread, pyqtSignal
from models.firebase_service import FirebaseService


class FirebaseWorker(QThread):
    """Envía las alertas a Firebase en su propio hilo para no bloquear la interfaz ni el micrófono."""
    log_signal = pyqtSignal(str)

    def __init__(self, firebase_service: FirebaseService):
        super().__init__()
        self.firebase = firebase_service
        self._cola = queue.Queue()

    def enqueue(self, clase: str, tipo: str = "ladrido", mensaje: str = None,
                nivel: str = "Crítico", titulo: str = None, cuerpo: str = None):
        """Pone una alerta en la cola. Vuelve de inmediato; se puede llamar desde cualquier hilo."""
        self._cola.put({"clase": clase, "tipo": tipo, "mensaje": mensaje, "nivel": nivel,
                        "titulo": titulo, "cuerpo": cuerpo})

    def run(self):
        while True:
            evento = self._cola.get()
            if evento is None:
                break
            hora = time.strftime("%H:%M:%S")

            # 1. Guardar en Firestore
            success_db, msg_db = self.firebase.save_alert(
                evento["clase"], tipo=evento["tipo"], mensaje=evento["mensaje"], nivel=evento["nivel"])
            self.log_signal.emit(f"[{hora}] {msg_db}")

            # 2. Enviar Notificación Push FCM
            success_push, msg_push = self.firebase.send_push_notification(
                evento["clase"], titulo=evento["titulo"], cuerpo=evento["cuerpo"], tipo=evento["tipo"])
            self.log_signal.emit(f"[{hora}] {msg_push}")

    def stop(self):
        self._cola.put(None)
        self.wait()
