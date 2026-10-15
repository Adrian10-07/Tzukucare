# views/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QVBoxLayout,
                             QHBoxLayout, QWidget, QTextEdit, QFrame, QPushButton,
                             QSpinBox, QDoubleSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from views.pixel_dog_widget import PixelDogWidget
import config

class MainWindow(QMainWindow):
    # Señales enviadas hacia el controlador
    manual_alarm_signal = pyqtSignal()
    config_changed_signal = pyqtSignal(int, float)  # (ladridos, sensibilidad_porcentaje)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Detección Canina - RPi UI")
        self.setMinimumSize(720, 480)
        self._init_ui()

    def _init_ui(self):
        screen = QApplication.primaryScreen().availableGeometry()
        is_small_screen = screen.height() < 550
        font_title_size = 11 if is_small_screen else 13
        font_status_size = 14 if is_small_screen else 18

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {config.FONDO_ARRIBA}, stop:1 {config.FONDO_ABAJO});
            }}
            QFrame#card {{
                background-color: #FFFFFF;
                border-radius: 18px;
                border: 2px solid #BFE6F2;
            }}
            QFrame#header {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {config.TURQUESA}, stop:1 #4FB3D9);
                border-radius: 14px;
            }}
            QLabel {{ color: {config.TEXTO}; background: transparent; }}
            QTextEdit {{
                background-color: {config.FONDO_ABAJO};
                color: {config.TEXTO};
                border: 2px solid {config.CELESTE_CLARO};
                border-radius: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 6px;
            }}
            QPushButton#btn_emergency {{
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton#btn_emergency:hover {{
                background-color: #DC2626;
            }}
            QPushButton#btn_save {{
                background-color: {config.TURQUESA};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                padding: 6px;
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {config.CELESTE_CLARO};
                border: 1px solid {config.CELESTE};
                border-radius: 8px;
                padding: 4px;
                font-weight: bold;
                color: {config.TEXTO};
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 8, 10, 10)
        main_layout.setSpacing(8)

        # Encabezado
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 6, 14, 6)

        lbl_logo = QLabel("TzukuCare")
        lbl_logo.setFont(QFont("Segoe UI", 15 if is_small_screen else 18, QFont.Bold))
        lbl_logo.setStyleSheet("color: #FFFFFF;")

        lbl_sub = QLabel("Monitoreo canino en tiempo real")
        lbl_sub.setFont(QFont("Segoe UI", 10))
        lbl_sub.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_sub.setStyleSheet(f"color: {config.AMARILLO_SUAVE};")

        header_layout.addWidget(lbl_logo)
        header_layout.addStretch()
        header_layout.addWidget(lbl_sub)

        # Layout Principal
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # CARD IZQUIERDA (Estado, Perro, Botón Alarma Manual)
        self.left_card = QFrame()
        self.left_card.setObjectName("card")
        left_layout = QVBoxLayout(self.left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        self.lbl_estado = QLabel("REPOSO")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setFont(QFont("Segoe UI", font_status_size, QFont.Bold))
        self.lbl_estado.setStyleSheet(
            f"background-color: {config.TURQUESA}; color: #FFFFFF; border-radius: 14px; padding: 6px;"
        )

        self.pixel_dog = PixelDogWidget()
        self.lbl_clase = QLabel("Detección: Esperando audio...")
        self.lbl_clase.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        self.lbl_clase.setAlignment(Qt.AlignCenter)
        self.lbl_clase.setStyleSheet(
            f"color: {config.TEXTO}; background-color: {config.CELESTE_CLARO}; border-radius: 10px; padding: 4px;"
        )

        # 🚨 Botón Alarma Manual de Emergencia
        self.btn_emergencia = QPushButton("🚨 ACTIVAR ALARMA MANUAL")
        self.btn_emergencia.setObjectName("btn_emergency")
        self.btn_emergencia.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_emergencia.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_emergencia.clicked.connect(self._on_manual_alarm_clicked)

        left_layout.addWidget(self.lbl_estado)
        left_layout.addWidget(self.pixel_dog, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.lbl_clase)
        left_layout.addWidget(self.btn_emergencia)

        # CARD DERECHA (Registro de Eventos + Panel de Configuración)
        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        lbl_historial_title = QLabel(" Registro de Eventos")
        lbl_historial_title.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        lbl_historial_title.setStyleSheet(f"color: {config.TURQUESA_OSC};")

        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)

        # ⚙️ SECCIÓN DE CONFIGURACIÓN
        config_box = QFrame()
        config_box.setStyleSheet(f"background-color: {config.CELESTE_CLARO}; border-radius: 10px; padding: 6px;")
        config_layout = QVBoxLayout(config_box)
        config_layout.setSpacing(6)

        lbl_cfg_title = QLabel("⚙️ Configuración del Dispositivo")
        lbl_cfg_title.setFont(QFont("Segoe UI", 10, QFont.Bold))

        controls_layout = QHBoxLayout()

        # SpinBox: Cantidad de ladridos
        vbox_ladridos = QVBoxLayout()
        lbl_ladridos = QLabel("Ladridos p/ Alarma:")
        lbl_ladridos.setFont(QFont("Segoe UI", 9))
        self.sb_ladridos = QSpinBox()
        self.sb_ladridos.setRange(1, 10)
        self.sb_ladridos.setValue(3)
        vbox_ladridos.addWidget(lbl_ladridos)
        vbox_ladridos.addWidget(self.sb_ladridos)

        # SpinBox: Sensibilidad IA (%)
        vbox_sensibilidad = QVBoxLayout()
        lbl_sensibilidad = QLabel("Sensibilidad IA (%):")
        lbl_sensibilidad.setFont(QFont("Segoe UI", 9))
        self.sb_sensibilidad = QSpinBox()
        self.sb_sensibilidad.setRange(10, 90)
        self.sb_sensibilidad.setValue(40)
        self.sb_sensibilidad.setSuffix("%")
        vbox_sensibilidad.addWidget(lbl_sensibilidad)
        vbox_sensibilidad.addWidget(self.sb_sensibilidad)

        # Botón para aplicar cambios
        btn_apply = QPushButton("Guardar")
        btn_apply.setObjectName("btn_save")
        btn_apply.setCursor(QCursor(Qt.PointingHandCursor))
        btn_apply.clicked.connect(self._on_config_apply_clicked)

        controls_layout.addLayout(vbox_ladridos)
        controls_layout.addLayout(vbox_sensibilidad)
        controls_layout.addWidget(btn_apply, alignment=Qt.AlignBottom)

        config_layout.addWidget(lbl_cfg_title)
        config_layout.addLayout(controls_layout)

        right_layout.addWidget(lbl_historial_title)
        right_layout.addWidget(self.log_txt)
        right_layout.addWidget(config_box)

        content_layout.addWidget(self.left_card, 45)
        content_layout.addWidget(right_card, 55)

        main_layout.addWidget(header)
        main_layout.addLayout(content_layout, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.showMaximized()

    def _on_manual_alarm_clicked(self):
        self.manual_alarm_signal.emit()

    def _on_config_apply_clicked(self):
        ladridos = self.sb_ladridos.value()
        sensibilidad = float(self.sb_sensibilidad.value())
        self.config_changed_signal.emit(ladridos, sensibilidad)

    def update_status(self, estado: str, clase: str):
        bg, fg, _, borde = config.ESTILOS_ESTADO.get(estado, config.ESTILOS_ESTADO["REPOSO"])
        self.lbl_estado.setText(estado)
        self.lbl_estado.setStyleSheet(f"background-color: {bg}; color: {fg}; border-radius: 14px; padding: 6px;")
        self.left_card.setStyleSheet(f"QFrame#card {{ background-color: #FFFFFF; border-radius: 18px; border: 3px solid {borde}; }}")
        self.pixel_dog.set_state(estado)
        self.lbl_clase.setText(f"Sonido actual: {clase}")

    def append_log(self, text: str):
        self.log_txt.append(text)