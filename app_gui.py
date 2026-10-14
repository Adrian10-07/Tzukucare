import sys, time, re
import numpy as np
import pyaudio
import firebase_admin
from firebase_admin import credentials, messaging, firestore
import yamnet as yamnet_model
import tensorflow.lite as tflite
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor

# Inicializar Firebase con el archivo JSON y Firestore
try:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client() # <-- 2. Base de datos inicializada
    print("Firebase y Firestore conectados con éxito.")
except Exception as e:
    print(f"Error al conectar con Firebase: {e}")


# ==========================================================
# PALETA VISUAL (turquesa, celeste y amarillos suaves)
# Solo afecta el diseño; no interviene en la lógica.
# ==========================================================
TURQUESA = "#2EC4B6"
TURQUESA_OSC = "#168F89"
CELESTE = "#8ECAE6"
CELESTE_CLARO = "#E0F4FB"
FONDO_ARRIBA = "#CFF0F7"
FONDO_ABAJO = "#F6FCFE"
AMARILLO = "#FFD97D"
AMARILLO_SUAVE = "#FFF3C9"
TEXTO = "#1F3A4D"
TEXTO_SUAVE = "#6B8798"
ALERTA = "#EF6B6B"
ALERTA_SUAVE = "#FFE6E6"

# Estilo visual por estado: (fondo de la píldora, texto, fondo del perrito, borde de la tarjeta)
ESTILOS_ESTADO = {
    "REPOSO":                (TURQUESA,  "#FFFFFF", CELESTE_CLARO,  "#BFE6F2"),
    "ESCUCHA ACTIVA":        (AMARILLO,  TEXTO,     AMARILLO_SUAVE, AMARILLO),
    "¡¡ ALARMA ACTIVADA !!": (ALERTA,    "#FFFFFF", ALERTA_SUAVE,   ALERTA),
}


# WIDGET ANIMADO EN PIXEL ART (PERRO)
class PixelDogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.state = "REPOSO"
        self.frame = 0
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._next_frame)
        self.anim_timer.start(200)

        self.colors = {
            '.': QColor(0, 0, 0, 0),         # Transparente
            'K': QColor(26, 26, 26),          # Negro / Delineado
            'B': QColor(140, 80, 40),         # Café Oscuro
            'L': QColor(200, 130, 70),        # Café Claro
            'W': QColor(245, 245, 245),       # Blanco
            'R': QColor(220, 50, 50),         # Rojo
            'Y': QColor(255, 200, 0),         # Amarillo
            'P': QColor(255, 150, 180)        # Rosado
        }

        self.matrix_sit_1 = [
            "................",
            ".....KKKK.......",
            "....KLLLLKK.....",
            "...KLLKBLLLK....",
            "...KLLLLLLLK....",
            "...KLLLLLRK.....",
            "....KLLLLK......",
            "....KBBBLLK.....",
            "...KBBBBBBBKK...",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KWWK...KWWK...",
            ".KWWWK...KWWWK..",
            "................"
        ]

        self.matrix_sit_2 = [
            "................",
            ".....KKKK.......",
            "....KLLLLKK.....",
            "...KLLKKLLLK....",
            "...KLLLLLLLK....",
            "...KLLLLLRK.....",
            "....KLLLLK......",
            "....KBBBLLK.....",
            "...KBBBBBBBKK...",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KWWK...KWWK...",
            ".KWWWK...KWWWK..",
            "................"
        ]

        self.matrix_bark_1 = [
            "....KK...KK.....",
            "...KLLK.KLLK....",
            "...KLLLKLLLK....",
            "...KLLKBLLLK....",
            "...KLLLLLLLK....",
            "...KLLLRRRK.....",
            "....KLLRPPK.....",
            "....KBBBLLK.....",
            "...KBBBBBBBKK...",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..",
            "..KWWK...KWWK...",
            ".KWWWK...KWWWK..",
            "................"
        ]

        self.matrix_alarm_1 = [
            "YY...KK...KK....",
            ".YY.KLLK.KLLK...",
            "..Y.KLLLKLLLK...",
            "...KLLKBLLLK....",
            "...KLLLLLLLK....",
            "..KLLLRRRRRKYY..",
            "..KLLLRPRPRK.YY.",
            "...KBBBLLKK...Y.",
            "..KBBBBBBBKK....",
            ".KBBBBBBBBBBK...",
            ".KBBBBBBBBBBK...",
            ".KBBBBBBBBBBK...",
            ".KBBBBBBBBBBK...",
            ".KWWK...KWWK....",
            "KWWWK...KWWWK...",
            "................"
        ]

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            if self.state == "¡¡ ALARMA ACTIVADA !!":
                self.anim_timer.setInterval(100)
            else:
                self.anim_timer.setInterval(200)
            self.update()

    def _next_frame(self):
        self.frame = (self.frame + 1) % 4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        if self.state == "REPOSO":
            grid = self.matrix_sit_2 if (self.frame % 2 == 0) else self.matrix_sit_1
        elif self.state == "ESCUCHA ACTIVA":
            grid = self.matrix_bark_1 if (self.frame % 2 == 0) else self.matrix_sit_1
        else:
            grid = self.matrix_alarm_1 if (self.frame % 2 == 0) else self.matrix_bark_1

        pixel_size = min(self.width(), self.height()) // 16
        offset_x = (self.width() - (pixel_size * 16)) // 2
        offset_y = (self.height() - (pixel_size * 16)) // 2

        # --- Fondo suave detrás del perrito (solo diseño) ---
        fondo = ESTILOS_ESTADO.get(self.state, ESTILOS_ESTADO["REPOSO"])[2]
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(fondo))
        painter.drawRoundedRect(
            offset_x, offset_y, pixel_size * 16, pixel_size * 16, 28, 28
        )
        painter.setRenderHint(QPainter.Antialiasing, False)

        for r in range(16):
            for c in range(16):
                char = grid[r][c]
                color = self.colors.get(char, self.colors['.'])
                if color.alpha() > 0:
                    painter.fillRect(
                        offset_x + (c * pixel_size),
                        offset_y + (r * pixel_size),
                        pixel_size, pixel_size, color
                    )

# HILO DE CAPTURA Y PROCESAMIENTO
class AudioThread(QThread):
    update_signal = pyqtSignal(str, float, str, str)

    def run(self):
        interpreter = tflite.Interpreter(model_path="./lite-model_yamnet_classification_tflite_1.tflite")
        interpreter.allocate_tensors()
        inputs = interpreter.get_input_details()
        outputs = interpreter.get_output_details()
        yamnet_classes = yamnet_model.class_names('./yamnet_class_map.csv')

        p = pyaudio.PyAudio()

        input_device_index = None
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels', 0) > 0:
                input_device_index = i
                break

        if input_device_index is None:
            return

        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=46800
        )

        okgoogle = 0
        ladridosSeguidos = 0
        ladridosTotalEscucha = 0

        while True:
            try:
                data = stream.read(46800, exception_on_overflow=False)
            except Exception:
                continue

            audio_hd = np.frombuffer(data, dtype=np.int16)
            audio_16k = audio_hd[::3]
            audio_array = audio_16k.astype(np.float32) / 32768.0

            interpreter.set_tensor(inputs[0]['index'], audio_array)
            interpreter.invoke()
            scores = interpreter.get_tensor(outputs[0]['index'])
            prediction = np.mean(scores, axis=0)

            top5_i = np.argsort(prediction)[::-1][:5]
            top_class = yamnet_classes[top5_i[0]]
            top_score = float(prediction[top5_i[0]])
            
            resultado = ''.join(' {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i]) for i in top5_i)
            es_ladrido = re.search('Bark', resultado) or re.search('Bow-wow', resultado)

            estado_texto = "REPOSO"
            color = "#10B981"

            if es_ladrido:
                ladridosSeguidos += 1
                if ladridosSeguidos >= 2 or okgoogle == 1:
                    okgoogle = 1
                    estado_texto = "ESCUCHA ACTIVA"
                    color = "#F59E0B"
                    ladridosTotalEscucha += 1

            if ladridosTotalEscucha >= 3:
                estado_texto = "¡¡ ALARMA ACTIVADA !!"
                color = "#EF4444"
                ladridosTotalEscucha = 0
                okgoogle = 0
                ladridosSeguidos = 0

            self.update_signal.emit(top_class, top_score, estado_texto, color)

# VENTANA PRINCIPAL
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Detección Canina - RPi UI")
        
        screen = QApplication.primaryScreen().availableGeometry()
        screen_h = screen.height()

        self.setMinimumSize(720, 400)
        
        is_small_screen = screen_h < 550
        font_title_size = 12 if is_small_screen else 14
        font_status_size = 14 if is_small_screen else 18

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {FONDO_ARRIBA}, stop:1 {FONDO_ABAJO});
            }}
            QFrame#card {{
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #BFE6F2;
            }}
            QFrame#header {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {TURQUESA}, stop:1 #4FB3D9);
                border-radius: 16px;
            }}
            QLabel {{ color: {TEXTO}; background: transparent; }}
            QTextEdit {{
                background-color: {FONDO_ABAJO};
                color: {TEXTO};
                border: 2px solid {CELESTE_CLARO};
                border-radius: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {12 if is_small_screen else 14}px;
                padding: 8px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 12px;
                margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {CELESTE};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 10, 12, 12)
        main_layout.setSpacing(10)

        # --- Encabezado ---
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 6 if is_small_screen else 10, 16, 6 if is_small_screen else 10)

        lbl_logo = QLabel("TzukuCare")
        lbl_logo.setFont(QFont("Segoe UI", 16 if is_small_screen else 20, QFont.Bold))
        lbl_logo.setStyleSheet("color: #FFFFFF; background: transparent;")

        lbl_sub = QLabel("Monitoreo canino en tiempo real")
        lbl_sub.setFont(QFont("Segoe UI", 10 if is_small_screen else 12))
        lbl_sub.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_sub.setStyleSheet(f"color: {AMARILLO_SUAVE}; background: transparent;")

        header_layout.addWidget(lbl_logo)
        header_layout.addStretch()
        header_layout.addWidget(lbl_sub)

        #  Contenido principal 
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        self.left_card = QFrame()
        self.left_card.setObjectName("card")
        left_layout = QVBoxLayout(self.left_card)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(8)
        
        self.lbl_estado = QLabel("REPOSO")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setFont(QFont("Segoe UI", font_status_size, QFont.Bold))
        self.lbl_estado.setStyleSheet(
            f"background-color: {TURQUESA}; color: #FFFFFF; border-radius: 16px; padding: 8px;"
        )

        self.pixel_dog = PixelDogWidget()
        self.lbl_clase = QLabel("Detección: Esperando audio...")
        self.lbl_clase.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        self.lbl_clase.setAlignment(Qt.AlignCenter)
        self.lbl_clase.setStyleSheet(
            f"color: {TEXTO}; background-color: {CELESTE_CLARO}; border-radius: 12px; padding: 6px;"
        )

        left_layout.addWidget(self.lbl_estado)
        left_layout.addWidget(self.pixel_dog, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.lbl_clase)

        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(8)
        
        lbl_historial_title = QLabel(" Registro de Eventos")
        lbl_historial_title.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        lbl_historial_title.setStyleSheet(f"color: {TURQUESA_OSC}; background: transparent;")
        
        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)

        right_layout.addWidget(lbl_historial_title)
        right_layout.addWidget(self.log_txt)

        content_layout.addWidget(self.left_card, 45)
        content_layout.addWidget(right_card, 55)

        main_layout.addWidget(header)
        main_layout.addLayout(content_layout, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.showMaximized()

        self.thread = AudioThread()
        self.thread.update_signal.connect(self.actualizar_ui)
        self.thread.start()

    def actualizar_ui(self, clase, confianza, estado, color):
        # Colores visuales según el estado (el parámetro `color` del hilo ya no se usa para el diseño)
        bg, fg, _, borde = ESTILOS_ESTADO.get(estado, ESTILOS_ESTADO["REPOSO"])

        self.lbl_estado.setText(estado)
        self.lbl_estado.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: 16px; padding: 10px;"
        )
        self.left_card.setStyleSheet(
            f"QFrame#card {{ background-color: #FFFFFF; border-radius: 20px; border: 3px solid {borde}; }}"
        )
        self.pixel_dog.set_state(estado)
        self.lbl_clase.setText(f"Sonido actual: {clase}")

        if estado in ["ESCUCHA ACTIVA", "¡¡ ALARMA ACTIVADA !!"]:
            hora = time.strftime("%H:%M:%S")
            
            if estado == "ESCUCHA ACTIVA":
                mensaje = f"Ladrido detectado ({clase})"
                self.log_txt.append(f"[{hora}] {mensaje}")
                
            else: # ALARMA ACTIVADA
                mensaje = "¡¡ ALARMA ACTIVADA !! - Ladridos continuos"
                self.log_txt.append(f"[{hora}] {mensaje}")
                
                # 1: GUARDAR HISTORIAL EN FIRESTORE 
                try:
                    datos_alerta = {
                        "mensaje": f"Ladridos detectados ({clase})",
                        "nivel": "Crítico",
                        "timestamp": firestore.SERVER_TIMESTAMP 
                    }
                    db.collection("alertas_tzukucare").add(datos_alerta)
                    self.log_txt.append(f"[{hora}] Guardado en Firestore exitoso.")
                except Exception as e:
                    self.log_txt.append(f"[{hora}] Error en Firestore: {e}")

                # 2: ENVIAR NOTIFICACIÓN PUSH 
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
                        topic='alertas_tzukucare'
                    )
                    response = messaging.send(mensaje_push)
                    self.log_txt.append(f"[{hora}] Push enviado con éxito: {response}")
                except Exception as e:
                    self.log_txt.append(f"[{hora}] Error enviando Push: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())