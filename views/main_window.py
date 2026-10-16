from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QVBoxLayout,
                             QHBoxLayout, QWidget, QFrame, QPushButton,
                             QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import (QFont, QCursor, QPixmap, QPainter, QColor,
                         QPainterPath, QPen)
from views.pixel_dog_widget import PixelDogWidget
from views.config_dialog import ConfigDialog
from views import theme
import config


# Texto secundario que acompaña a cada estado
DESCRIPCION_ESTADO = {
    "REPOSO": "Todo tranquilo. Escuchando el entorno.",
    "ESCUCHA ACTIVA": "Se detectaron ladridos. Prestando atención…",
    "¡¡ ALARMA ACTIVADA !!": "Ladridos continuos o alarma manual.",
}


def _emergency_pixmap(size: int) -> QPixmap:
    """Triángulo de advertencia blanco con '!' (dibujado, no depende de fuentes emoji)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    m = size * 0.08
    tri = QPainterPath()
    tri.moveTo(QPointF(size / 2, m))
    tri.lineTo(QPointF(size - m, size - m * 1.4))
    tri.lineTo(QPointF(m, size - m * 1.4))
    tri.closeSubpath()
    pen = QPen(QColor("#FFFFFF"), size * 0.08)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(QColor("#FFFFFF"))
    p.drawPath(tri)

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(theme.ALERTA_OSC))
    w = size * 0.11
    p.drawRoundedRect(int(size / 2 - w / 2), int(size * 0.33), int(w), int(size * 0.31), w / 2, w / 2)
    r = size * 0.065
    p.drawEllipse(QPointF(size / 2, size * 0.75), r, r)
    p.end()
    return pix


class EmergencyButton(QPushButton):
    """Botón grande de emergencia: icono + título + subtítulo."""

    def __init__(self, small: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("btn_emergency")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAccessibleName("Activar alarma de emergencia")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(6 if small else 10)
        lay.addStretch()

        icon = QLabel()
        icon.setPixmap(_emergency_pixmap(76 if small else 112))
        icon.setAlignment(Qt.AlignCenter)

        title = QLabel("EMERGENCIA")
        title.setObjectName("emergency_title")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(theme.font(20 if small else 26, QFont.Black))

        subtitle = QLabel("Toca para enviar una alerta a la app")
        subtitle.setObjectName("emergency_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setFont(theme.font(10 if small else 12, QFont.DemiBold))

        for w in (icon, title, subtitle):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay.addWidget(w)
        lay.addStretch()

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(28)
        sombra.setOffset(0, 6)
        sombra.setColor(QColor(239, 107, 107, 110))
        self.setGraphicsEffect(sombra)


class MainWindow(QMainWindow):
    # Señales enviadas hacia el controlador
    manual_alarm_signal = pyqtSignal()
    config_changed_signal = pyqtSignal(dict)  # configuración completa (ver config.SETTINGS_DEFAULT)
    calibration_requested_signal = pyqtSignal()

    def __init__(self, settings: dict = None):
        super().__init__()
        self.setWindowTitle("TzukuCare - Monitoreo canino")
        self.setMinimumSize(720, 480)
        # Estilo "Fusion": los controles se ven igual en Windows y en la Raspberry Pi
        QApplication.setStyle("Fusion")
        # Valores actuales mostrados en el modal de configuración
        self._settings = dict(settings or config.SETTINGS_DEFAULT)
        self._config_dialog = None
        self._init_ui()

    def _init_ui(self):
        small = self._is_small_screen()
        self._small = small

        self.setStyleSheet(theme.main_window_qss(small))

        root = QVBoxLayout()
        root.setContentsMargins(12, 10, 12, 12) if small else root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(10 if small else 16)

        root.addWidget(self._build_header(small))

        content = QHBoxLayout()
        content.setSpacing(10 if small else 16)
        content.addWidget(self._build_status_card(small), 1)
        content.addWidget(self._build_emergency_card(small), 1)
        root.addLayout(content, 1)

        container = QWidget()
        container.setObjectName("root")
        container.setLayout(root)
        self.setCentralWidget(container)
        self.showMaximized()

    @staticmethod
    def _is_small_screen() -> bool:
        # Pantallas de 7" (800x480 / 1024x600) usan tamaños compactos
        return QApplication.primaryScreen().availableGeometry().height() < 550

    # ---------- Encabezado ----------
    def _build_header(self, small: bool) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        lay = QHBoxLayout(header)
        lay.setContentsMargins(16, 8, 10, 8) if small else lay.setContentsMargins(22, 12, 14, 12)
        lay.setSpacing(12)

        badge = QLabel("TC")
        badge.setObjectName("logo_badge")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(34, 34) if small else badge.setFixedSize(42, 42)
        badge.setFont(theme.font(12 if small else 14, QFont.Black))

        textos = QVBoxLayout()
        textos.setSpacing(0)
        lbl_logo = QLabel("TzukuCare")
        lbl_logo.setObjectName("logo")
        lbl_logo.setFont(theme.font(15 if small else 19, QFont.Bold))
        lbl_sub = QLabel("Monitoreo canino en tiempo real")
        lbl_sub.setObjectName("logo_sub")
        lbl_sub.setFont(theme.font(9 if small else 10))
        textos.addWidget(lbl_logo)
        textos.addWidget(lbl_sub)

        # ⚙️ Botón que abre el modal de configuración
        self.btn_config = QPushButton("⚙  Configuración")
        self.btn_config.setObjectName("btn_config")
        self.btn_config.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_config.setFont(theme.font(10 if small else 11, QFont.Bold))
        self.btn_config.setFixedHeight(34 if small else 40)
        self.btn_config.clicked.connect(self._on_config_button_clicked)

        lay.addWidget(badge)
        lay.addLayout(textos)
        lay.addStretch()
        lay.addWidget(self.btn_config, alignment=Qt.AlignVCenter)
        return header

    # ---------- Tarjeta de estado ----------
    def _build_status_card(self, small: bool) -> QFrame:
        self.left_card = QFrame()
        self.left_card.setObjectName("card")
        lay = QVBoxLayout(self.left_card)
        lay.setContentsMargins(14, 12, 14, 12) if small else lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(6 if small else 10)

        caption = QLabel("ESTADO DEL MONITOR")
        caption.setObjectName("caption")
        caption.setFont(theme.font(9, QFont.Bold))

        self.lbl_estado = QLabel("REPOSO")
        self.lbl_estado.setObjectName("status_pill")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setFont(theme.font(15 if small else 19, QFont.Black))
        self._pill_h = 40 if small else 54
        self.lbl_estado.setFixedHeight(self._pill_h)

        self.lbl_estado_desc = QLabel(DESCRIPCION_ESTADO["REPOSO"])
        self.lbl_estado_desc.setObjectName("muted")
        self.lbl_estado_desc.setAlignment(Qt.AlignCenter)
        self.lbl_estado_desc.setFont(theme.font(9 if small else 11))

        self.pixel_dog = PixelDogWidget()
        self.pixel_dog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pixel_dog.setMinimumSize(110, 110) if small else self.pixel_dog.setMinimumSize(150, 150)

        # Fila inferior: solo el sonido detectado, en una línea compacta
        info = QFrame()
        info.setObjectName("info_box")
        info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        info_lay = QHBoxLayout(info)
        info_lay.setContentsMargins(12, 6, 12, 6) if small else info_lay.setContentsMargins(16, 8, 16, 8)
        info_lay.setSpacing(8)

        lbl_sonido_cap = QLabel("SONIDO DETECTADO")
        lbl_sonido_cap.setObjectName("caption")
        lbl_sonido_cap.setFont(theme.font(8 if small else 9, QFont.Bold))
        self.lbl_clase = QLabel("Esperando audio…")
        self.lbl_clase.setObjectName("sound_value")
        self.lbl_clase.setFont(theme.font(12 if small else 14, QFont.Bold))
        self.lbl_clase.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        info_lay.addWidget(lbl_sonido_cap)
        info_lay.addStretch()
        info_lay.addWidget(self.lbl_clase)

        lay.addWidget(caption)
        lay.addWidget(self.lbl_estado)
        lay.addWidget(self.lbl_estado_desc)
        lay.addWidget(self.pixel_dog, 1)
        lay.addWidget(info)
        self._apply_state_style("REPOSO")
        return self.left_card

    # ---------- Tarjeta de emergencia ----------
    def _build_emergency_card(self, small: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 14) if small else lay.setContentsMargins(22, 18, 22, 22)
        lay.setSpacing(6 if small else 10)

        caption = QLabel("EMERGENCIA MANUAL")
        caption.setObjectName("caption")
        caption.setFont(theme.font(9, QFont.Bold))

        hint = QLabel("Envía una alerta inmediata a la app móvil.")
        hint.setObjectName("muted")
        hint.setFont(theme.font(9 if small else 11))
        hint.setWordWrap(True)

        # 🚨 Botón grande de alarma manual
        self.btn_emergencia = EmergencyButton(small)
        self.btn_emergencia.clicked.connect(self._on_manual_alarm_clicked)

        lay.addWidget(caption)
        lay.addWidget(hint)
        lay.addSpacing(2 if small else 6)
        lay.addWidget(self.btn_emergencia, 1)
        return card

    # ---------- Acciones ----------
    def _on_manual_alarm_clicked(self):
        self.manual_alarm_signal.emit()

    def _on_config_button_clicked(self):
        dialog = ConfigDialog(self._settings, self)
        dialog.calibration_requested.connect(self.calibration_requested_signal.emit)
        self._config_dialog = dialog
        try:
            if dialog.exec_() == ConfigDialog.Accepted:
                self._settings = dialog.values()
                self.config_changed_signal.emit(dict(self._settings))
        finally:
            self._config_dialog = None

    def on_calibration_done(self, nivel_max_db: float):
        if self._config_dialog is not None:
            self._config_dialog.set_calibration_result(nivel_max_db)

    # ---------- Actualización desde el controlador ----------
    def update_status(self, estado: str, clase: str):
        self.lbl_estado.setText(estado)
        self.lbl_estado_desc.setText(DESCRIPCION_ESTADO.get(estado, ""))
        self._apply_state_style(estado)
        self.pixel_dog.set_state(estado)
        self.lbl_clase.setText(clase)

    def _apply_state_style(self, estado: str):
        bg, fg, _, borde = config.ESTILOS_ESTADO.get(estado, config.ESTILOS_ESTADO["REPOSO"])
        self.lbl_estado.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: {self._pill_h // 2}px;")
        self.left_card.setStyleSheet(f"QFrame#card {{ border: 2px solid {borde}; }}")

    def append_log(self, text: str):
        # El historial ya no se muestra en pantalla; los eventos se envían a la consola.
        print(text, flush=True)
