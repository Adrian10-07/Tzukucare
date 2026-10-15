from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QVBoxLayout,
                             QHBoxLayout, QWidget, QTextEdit, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from views.pixel_dog_widget import PixelDogWidget
import config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Detección Canina - RPi UI")
        self.setMinimumSize(720, 400)
        self._init_ui()

    def _init_ui(self):
        screen = QApplication.primaryScreen().availableGeometry()
        is_small_screen = screen.height() < 550
        font_title_size = 12 if is_small_screen else 14
        font_status_size = 14 if is_small_screen else 18

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {config.FONDO_ARRIBA}, stop:1 {config.FONDO_ABAJO});
            }}
            QFrame#card {{
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #BFE6F2;
            }}
            QFrame#header {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {config.TURQUESA}, stop:1 #4FB3D9);
                border-radius: 16px;
            }}
            QLabel {{ color: {config.TEXTO}; background: transparent; }}
            QTextEdit {{
                background-color: {config.FONDO_ABAJO};
                color: {config.TEXTO};
                border: 2px solid {config.CELESTE_CLARO};
                border-radius: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {12 if is_small_screen else 14}px;
                padding: 8px;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 12px; margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {config.CELESTE}; border-radius: 5px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 10, 12, 12)
        main_layout.setSpacing(10)

        # Encabezado
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
        lbl_sub.setStyleSheet(f"color: {config.AMARILLO_SUAVE}; background: transparent;")

        header_layout.addWidget(lbl_logo)
        header_layout.addStretch()
        header_layout.addWidget(lbl_sub)

        # Contenido Principal
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
            f"background-color: {config.TURQUESA}; color: #FFFFFF; border-radius: 16px; padding: 8px;"
        )

        self.pixel_dog = PixelDogWidget()
        self.lbl_clase = QLabel("Detección: Esperando audio...")
        self.lbl_clase.setFont(QFont("Segoe UI", font_title_size, QFont.Bold))
        self.lbl_clase.setAlignment(Qt.AlignCenter)
        self.lbl_clase.setStyleSheet(
            f"color: {config.TEXTO}; background-color: {config.CELESTE_CLARO}; border-radius: 12px; padding: 6px;"
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
        lbl_historial_title.setStyleSheet(f"color: {config.TURQUESA_OSC}; background: transparent;")

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

    def update_status(self, estado: str, clase: str):
        """Actualiza los componentes visuales de la vista."""
        bg, fg, _, borde = config.ESTILOS_ESTADO.get(estado, config.ESTILOS_ESTADO["REPOSO"])

        self.lbl_estado.setText(estado)
        self.lbl_estado.setStyleSheet(f"background-color: {bg}; color: {fg}; border-radius: 16px; padding: 10px;")
        self.left_card.setStyleSheet(f"QFrame#card {{ background-color: #FFFFFF; border-radius: 20px; border: 3px solid {borde}; }}")
        self.pixel_dog.set_state(estado)
        self.lbl_clase.setText(f"Sonido actual: {clase}")

    def append_log(self, text: str):
        """Añade una línea al registro de eventos."""
        self.log_txt.append(text)