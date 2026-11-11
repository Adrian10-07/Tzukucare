import threading

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
                             QLineEdit, QCheckBox, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor

from views import theme
from .cliente import TzukuApiClient

CAMPOS = (  # clave en config.json, etiqueta, oculto
    ("email", "Correo", False),
    ("password", "Contraseña", True),
    ("pet_id", "ID de mascota", False),
    ("collar_id", "ID de collar", False),
)


class PanelApi(QWidget):
    titulo = "API"
    _prueba_terminada = pyqtSignal(bool, str)

    def __init__(self, addon, parent=None):
        super().__init__(parent)
        self.addon = addon
        self._prueba_terminada.connect(self._on_prueba_terminada)
        self._init_ui(addon.cfg)

    def _init_ui(self, cfg: dict):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.FONDO_ABAJO};
                border: 2px solid {theme.CELESTE_CLARO};
                border-radius: 10px;
                padding: 4px 10px;
                color: {theme.TEXTO};
                min-height: 24px;
                selection-background-color: {theme.TURQUESA};
            }}
            QLineEdit:focus {{ border-color: {theme.TURQUESA}; }}
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(8)

        lbl = QLabel("Servicio opcional: envía el audio de cada alarma a la API de TZUKU y muestra "
                     "en el registro si el ladrido es agresivo. Sin activarlo, TzukuCare funciona igual.")
        lbl.setFont(theme.font(10))
        lbl.setObjectName("muted")
        lbl.setWordWrap(True)
        v.addWidget(lbl)

        self.chk_activo = QCheckBox("Activar análisis por API")
        self.chk_activo.setFont(theme.font(11, QFont.Bold))
        self.chk_activo.setCursor(QCursor(Qt.PointingHandCursor))
        self.chk_activo.setChecked(bool(cfg.get("activo")))
        v.addWidget(self.chk_activo)

        box = QFrame()
        box.setObjectName("field")
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 10, 14, 10)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        self.inputs = {}
        for fila, (clave, etiqueta, oculto) in enumerate(CAMPOS):
            l = QLabel(etiqueta)
            l.setFont(theme.font(10, QFont.Bold))
            e = QLineEdit(str(cfg.get(clave) or ""))
            e.setFont(theme.font(10))
            if oculto:
                e.setEchoMode(QLineEdit.Password)
            self.inputs[clave] = e
            grid.addWidget(l, fila, 0)
            grid.addWidget(e, fila, 1)
        v.addWidget(box)

        self.chk_firebase = QCheckBox("Avisar también a la app móvil si es agresivo")
        self.chk_firebase.setCursor(QCursor(Qt.PointingHandCursor))
        self.chk_firebase.setChecked(bool(cfg.get("reenviar_a_firebase")))
        v.addWidget(self.chk_firebase)

        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.btn_probar = QPushButton("Probar conexión")
        self.btn_probar.setObjectName("btn_outline")
        self.btn_probar.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_probar.setFont(theme.font(10, QFont.Bold))
        self.btn_probar.clicked.connect(self._on_probar)
        self.lbl_estado = QLabel("Los cambios se aplican al pulsar Guardar.")
        self.lbl_estado.setFont(theme.font(9))
        self.lbl_estado.setObjectName("muted")
        self.lbl_estado.setWordWrap(True)
        fila.addWidget(self.btn_probar)
        fila.addWidget(self.lbl_estado, 1)
        v.addLayout(fila)
        v.addStretch()

    def _valores(self) -> dict:
        cfg = dict(self.addon.cfg)
        cfg.update({k: e.text().strip() for k, e in self.inputs.items()})
        cfg["activo"] = self.chk_activo.isChecked()
        cfg["reenviar_a_firebase"] = self.chk_firebase.isChecked()
        return cfg

    def aplicar(self):
        """Lo llama el modal al pulsar Guardar."""
        self.addon.aplicar_config(self._valores())

    # ---------- Probar conexión (en un hilo para no congelar el modal) ----------
    def _on_probar(self):
        cfg = self._valores()
        if not cfg["email"] or not cfg["password"]:
            self._mostrar(False, "Escribe el correo y la contraseña.")
            return
        self.btn_probar.setEnabled(False)
        self._mostrar(None, "Probando…")
        threading.Thread(target=self._probar, args=(cfg,), daemon=True).start()

    def _probar(self, cfg: dict):
        try:
            cliente = TzukuApiClient(cfg["base_url"], cfg["email"], cfg["password"], timeout=15)
            cliente.login()
            if cfg["collar_id"]:
                cliente.consultar_resultados(cfg["collar_id"])
                ok, msg = True, "Conexión correcta: sesión iniciada y collar accesible."
            else:
                ok, msg = True, "Sesión iniciada. Falta el ID de collar."
        except Exception as e:  # cualquier fallo de red o de la API se muestra tal cual
            ok, msg = False, f"No se pudo conectar: {e}"
        try:
            self._prueba_terminada.emit(ok, msg)
        except RuntimeError:  # el modal ya se cerró
            pass

    def _on_prueba_terminada(self, ok: bool, msg: str):
        self.btn_probar.setEnabled(True)
        self._mostrar(ok, msg)

    def _mostrar(self, ok, msg: str):
        color = {True: theme.TURQUESA_OSC, False: theme.ALERTA_OSC}.get(ok, theme.TEXTO)
        self.lbl_estado.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.lbl_estado.setText(msg)
