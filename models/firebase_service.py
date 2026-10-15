import firebase_admin
from firebase_admin import credentials, messaging, firestore
import config

class FirebaseService:
    def __init__(self):
        self.db = None
        self.is_connected = False
        self._initialize()

    def _initialize(self):
        try:
            cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.is_connected = True
            print("Firebase y Firestore conectados con éxito.")
        except Exception as e:
            print(f"Error al conectar con Firebase: {e}")

    def save_alert(self, clase: str):
        """Guarda un registro de alerta en Firestore."""
        if not self.is_connected or not self.db:
            return False, "Firebase no está conectado"

        try:
            datos_alerta = {
                "mensaje": f"Ladridos detectados ({clase})",
                "nivel": "Crítico",
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            self.db.collection(config.FIRESTORE_COLLECTION).add(datos_alerta)
            return True, "Guardado en Firestore exitoso."
        except Exception as e:
            return False, f"Error en Firestore: {e}"

    def send_push_notification(self, clase: str):
        """Envía notificación Push a través de FCM."""
        if not self.is_connected:
            return False, "Firebase no está conectado"

        try:
            mensaje_push = messaging.Message(
                notification=messaging.Notification(
                    title="¡TzukuCare Alerta!",
                    body=f"Se detectaron ladridos continuos ({clase})."
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='sonido_alerta',
                        channel_id='tzukucare_alerts'
                    )
                ),
                topic=config.FCM_TOPIC
            )
            response = messaging.send(mensaje_push)
            return True, f"Push enviado con éxito: {response}"
        except Exception as e:
            return False, f"Error enviando Push: {e}"