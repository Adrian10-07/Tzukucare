import sys, time, re
import numpy as np
import pyaudio
# Nuevas importaciones para Firebase
import firebase_admin
from firebase_admin import credentials, messaging

# Inicializar Firebase con el archivo JSON
try:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase conectado con éxito.")
except Exception as e:
    print(f"❌ Error al conectar con Firebase: {e}")

# Soporte para TensorFlow completo en Laptop o TFLite Runtime
try:
    import tensorflow.lite as tflite
except ImportError:
    import tflite_runtime.interpreter as tflite

import yamnet as yamnet_model

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QHBoxLayout, QWidget, QTextEdit, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor

# ==========================================
# WIDGET ANIMADO EN PIXEL ART (PERRO)
# ==========================================
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

# ==========================================
# HILO DE CAPTURA Y PROCESAMIENTO
# ==========================================
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
            rate=16000,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=15600
        )

        okgoogle = 0
        ladridosSeguidos = 0
        ladridosTotalEscucha = 0

        while True:
            try:
                data = stream.read(15600, exception_on_overflow=False)
            except Exception:
                continue

            audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

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
            color = "#10B981" # Verde

            if es_ladrido:
                ladridosSeguidos += 1
                if ladridosSeguidos >= 2 or okgoogle == 1:
                    okgoogle = 1
                    estado_texto = "ESCUCHA ACTIVA"
                    color = "#F59E0B" # Amarillo
                    ladridosTotalEscucha += 1

            if ladridosTotalEscucha >= 3:
                estado_texto = "¡¡ ALARMA ACTIVADA !!"
                color = "#EF4444" # Rojo
                ladridosTotalEscucha = 0
                okgoogle = 0
                ladridosSeguidos = 0

            self.update_signal.emit(top_class, top_score, estado_texto, color)

# ==========================================
# VENTANA PRINCIPAL (DASHBOARD MODERN 7")
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Detección Canina - RPi UI")
        
        # --- DETECCIÓN AUTOMÁTICA DE PANTALLA ---
        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()

        # Permitir un tamaño mínimo flexible para pantallas de 800x480 o 1024x600
        self.setMinimumSize(720, 400)
        
        # Si la pantalla es pequeña (menor a 600px de alto), adaptar fuentes
        is_small_screen = screen_h < 550
        font_title_size = 12 if is_small_screen else 14
        font_status_size = 14 if is_small_screen else 18

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #0F172A;
            }}
            QFrame#card {{
                background-color: #1E293B;
                border-radius: 12px;
                border: 1px solid #334155;
            }}
            QLabel {{
                color: #F8FAFC;
            }}
            QTextEdit {{
                background-color: #020617;
                color: #F8FAFC;
                border: 1px solid #1E293B;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {12 if is_small_screen else 14}px;
                padding: 8px;
            }}
        """)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Panel Izquierdo (Estado y Perro)
        left_card = QFrame()
        left_card.setObjectName("card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)

        self.lbl_estado = QLabel("REPOSO")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setFont(QFont("Segoe UI", font_status_size, QFont.Bold))
        self.lbl_estado.setStyleSheet("""
            background-color: #10B981;
            color: #FFFFFF;
            border-radius: 8px;
            padding: 8px;
        """)

        self.pixel_dog = PixelDogWidget()

        self.lbl_clase = QLabel("Detección: Esperando audio...")
        self.lbl_clase.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        self.lbl_clase.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(self.lbl_estado)
        left_layout.addWidget(self.pixel_dog, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.lbl_clase)

        # Panel Derecho (Historial)
        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)

        lbl_historial_title = QLabel(" Registro de Eventos")
        lbl_historial_title.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        
        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)

        right_layout.addWidget(lbl_historial_title)
        right_layout.addWidget(self.log_txt)

        main_layout.addWidget(left_card, 45)
        main_layout.addWidget(right_card, 55)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- MODO DE VISUALIZACIÓN ---
        # Abre la ventana maximizada ocupando el espacio disponible sin salirse de la pantalla
        self.showMaximized()

        # Hilo de audio e interconexión
        self.thread = AudioThread()
        self.thread.update_signal.connect(self.actualizar_ui)
        self.thread.start()

    def actualizar_ui(self, clase, confianza, estado, color):
            # Actualizar banner y animación
            self.lbl_estado.setText(estado)
            self.lbl_estado.setStyleSheet(f"background-color: {color}; color: #FFFFFF; border-radius: 8px; padding: 10px;")
            self.pixel_dog.set_state(estado)

            self.lbl_clase.setText(f"Sonido actual: {clase}")

            # SOLO guardar en el historial si es alerta amarilla o roja
            if estado in ["ESCUCHA ACTIVA", "¡¡ ALARMA ACTIVADA !!"]:
                hora = time.strftime("%H:%M:%S")
                
                if estado == "ESCUCHA ACTIVA":
                    icono = ""
                    mensaje = f"Ladrido detectado ({clase})"
                    log_entry = f"[{hora}] {icono} {mensaje}"
                    self.log_txt.append(log_entry)
                    
                else: # ALARMA ACTIVADA
                    icono = ""
                    mensaje = "¡¡ ALARMA ACTIVADA !! - Ladridos continuos"
                    log_entry = f"[{hora}] {icono} {mensaje}"
                    self.log_txt.append(log_entry)
                    
                    # --- NUEVO: ENVIAR NOTIFICACIÓN PUSH ---
                    try:
                        mensaje_push = messaging.Message(
                            notification=messaging.Notification(
                                title="¡TzukuCare Alerta!",
                                body=f"Se detectaron ladridos continuos ({clase})."
                            ),
                            android=messaging.AndroidConfig(
                                priority='high',
                                notification=messaging.AndroidNotification(
                                    sound='sonido_alerta', # El mismo nombre de tu .mp3 en Flutter
                                    channel_id='tzukucare_alerts'
                                )
                            ),
                            topic='alertas_tzukucare'
                        )
                        response = messaging.send(mensaje_push)
                        self.log_txt.append(f"[{hora}]  Push enviado con éxito: {response}")
                    except Exception as e:
                        self.log_txt.append(f"[{hora}]  Error enviando Push: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())