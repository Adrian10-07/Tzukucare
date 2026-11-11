"""Pestaña "Vincular" del modal de Configuración: QR, código y usuarios vinculados."""
from datetime import datetime, timezone

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QCursor, QPixmap, QPainter, QColor

from views import theme

try:
    import qrcode
except ImportError:  # sin la librería se muestra solo el código
    qrcode = None


def qr_pixmap(texto: str, lado: int) -> QPixmap:
    """Dibuja el QR con QPainter (sin PIL): cada módulo es un cuadro."""
    pix = QPixmap(lado, lado)
    pix.fill(QColor("#FFFFFF"))
    if qrcode is None or not texto:
        return pix
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    matriz = qr.get_matrix()
    n = len(matriz)
    celda = lado // n
    margen = (lado - celda * n) // 2
    p = QPainter(pix)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(theme.TEXTO))
    for y, fila in enumerate(matriz):
        for x, negro in enumerate(fila):
            if negro:
                p.drawRect(margen + x * celda, margen + y * celda, celda, celda)
    p.end()
    return pix


class PanelVincular(QWidget):
    titulo = "Vincular"
    LADO_QR = 170

    def __init__(self, servicio, parent=None):
        super().__init__(parent)
        self.servicio = servicio
        self._qr_actual = None
        self._init_ui()
        servicio.estado_signal.connect(self._on_estado)
        self._reloj = QTimer(self)
        self._reloj.timeout.connect(self._actualizar_cuenta)
        self._reloj.start(1000)
        self._on_estado(dict(servicio.estado))

    def _init_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(8)

        lbl = QLabel("En la app TzukuCare toca \"Vincular dispositivo\" y escanea el QR, "
                     "o escribe el código. El primero en vincularse será el administrador.")
        lbl.setFont(theme.font(10))
        lbl.setObjectName("muted")
        lbl.setWordWrap(True)
        v.addWidget(lbl)

        caja = QFrame()
        caja.setObjectName("field")
        h = QHBoxLayout(caja)
        h.setContentsMargins(14, 10, 14, 10)
        h.setSpacing(16)

        self.lbl_qr = QLabel()
        self.lbl_qr.setFixedSize(self.LADO_QR, self.LADO_QR)
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        h.addWidget(self.lbl_qr)

        der = QVBoxLayout()
        der.setSpacing(4)
        t = QLabel("Código de vinculación")
        t.setFont(theme.font(10, QFont.Bold))
        t.setObjectName("muted")
        self.lbl_codigo = QLabel("— — —")
        self.lbl_codigo.setFont(theme.font(26, QFont.Bold))
        self.lbl_codigo.setObjectName("dialog_title")
        self.lbl_codigo.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_cuenta = QLabel("")
        self.lbl_cuenta.setFont(theme.font(9))
        self.lbl_cuenta.setObjectName("muted")
        self.lbl_miembros = QLabel("")
        self.lbl_miembros.setFont(theme.font(10))
        self.lbl_miembros.setWordWrap(True)
        self.lbl_miembros.setObjectName("dialog_title")
        der.addWidget(t)
        der.addWidget(self.lbl_codigo)
        der.addWidget(self.lbl_cuenta)
        der.addSpacing(6)
        der.addWidget(self.lbl_miembros)
        der.addStretch()
        h.addLayout(der, 1)
        v.addWidget(caja)

        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.btn_nuevo = QPushButton("Nuevo código")
        self.btn_nuevo.setObjectName("btn_outline")
        self.btn_nuevo.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_nuevo.setFont(theme.font(10, QFont.Bold))
        self.btn_nuevo.clicked.connect(self.servicio.nuevo_codigo)
        self.btn_quitar = QPushButton("Quitar a todos")
        self.btn_quitar.setObjectName("btn_outline")
        self.btn_quitar.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_quitar.setFont(theme.font(10, QFont.Bold))
        self.btn_quitar.clicked.connect(self._on_quitar)
        self.lbl_estado = QLabel("")
        self.lbl_estado.setFont(theme.font(9))
        self.lbl_estado.setWordWrap(True)
        fila.addWidget(self.btn_nuevo)
        fila.addWidget(self.btn_quitar)
        fila.addWidget(self.lbl_estado, 1)
        v.addLayout(fila)
        v.addStretch()

    def aplicar(self):
        """Lo llama el modal al pulsar Guardar. Aquí no hay nada que guardar."""

    # ---------- Estado ----------
    @pyqtSlot(dict)  # como slot, Qt lo desconecta solo al cerrar el modal
    def _on_estado(self, estado: dict):
        self._estado = estado
        codigo = estado.get("codigo")
        if not estado.get("conectado") and not codigo:
            self.lbl_codigo.setText("— — —")
            self.lbl_estado.setObjectName("status_warn")
            self.lbl_estado.setText("Sin conexión a Firebase. Revisa internet y firebase_credentials.json.")
        else:
            self.lbl_codigo.setText(f"{codigo[:3]} {codigo[3:]}" if codigo else "…")
            self.lbl_estado.setObjectName("status_ok" if estado.get("conectado") else "status_warn")
            self.lbl_estado.setText("Conectado" if estado.get("conectado") else "Reconectando…")
        self.lbl_estado.style().polish(self.lbl_estado)

        texto_qr = self.servicio.qr_texto() if codigo else ""
        if texto_qr != self._qr_actual:
            self._qr_actual = texto_qr
            self.lbl_qr.setPixmap(qr_pixmap(texto_qr, self.LADO_QR))
            if qrcode is None and codigo:
                self.lbl_qr.setText("Instala 'qrcode'\npara ver el QR")

        miembros = estado.get("miembros") or []
        if not miembros:
            self.lbl_miembros.setText("Aún no hay usuarios vinculados.")
        else:
            admin = estado.get("admin")
            quien = (admin.get("nombre") or admin.get("email")) if admin else "—"
            self.lbl_miembros.setText(f"Usuarios vinculados: {len(miembros)}\nAdministrador: {quien}")
        self.btn_quitar.setEnabled(bool(miembros))
        self._actualizar_cuenta()

    def _actualizar_cuenta(self):
        expira = getattr(self, "_estado", {}).get("expira")
        if not expira:
            self.lbl_cuenta.setText("")
            return
        seg = int((expira - datetime.now(timezone.utc)).total_seconds())
        if seg <= 0:
            self.lbl_cuenta.setText("Renovando código…")
        else:
            self.lbl_cuenta.setText(f"Cambia en {seg // 60}:{seg % 60:02d}")

    def _on_quitar(self):
        r = QMessageBox.question(
            self, "Quitar a todos",
            "Se desvincularán todos los teléfonos y dejarán de recibir alertas de este equipo.\n"
            "El próximo en vincularse será el nuevo administrador. ¿Continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r == QMessageBox.Yes:
            self.servicio.quitar_todos()
            self.lbl_estado.setText("Quitando usuarios…")
