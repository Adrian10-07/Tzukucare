# views/config_dialog.py
from PyQt5.QtWidgets import (QDialog, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
                             QPushButton, QSpinBox, QTabWidget, QWidget, QComboBox,
                             QCheckBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent
from PyQt5.QtGui import QFont, QCursor, QIcon
from views import theme, alert_styles
from views.pixel_dog_widget import PixelDogWidget
import config


class ConfigDialog(QDialog):
    """Modal de configuración: ladridos y sensibilidad, alcance de detección y alertas extra."""
    calibration_requested = pyqtSignal()

    def __init__(self, settings: dict, parent=None, extra_tabs=None):
        super().__init__(parent)
        self._extra_tabs_factories = extra_tabs or []  # [API TZUKU] pestañas de servicios opcionales
        self._extra_tabs = []
        self.setWindowTitle("Configuración del Dispositivo")
        self.setModal(True)
        self.setMinimumWidth(700)
        self._umbral_calibrado = settings.get("umbral_calibrado_db")
        self._init_ui(settings)

    def _init_ui(self, settings: dict):
        self.setStyleSheet(theme.dialog_qss())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        lbl_title = QLabel("Configuración")
        lbl_title.setObjectName("dialog_title")
        lbl_title.setFont(theme.font(17, QFont.Bold))
        lbl_subtitle = QLabel("Ajusta cómo y cuándo TzukuCare envía alertas.")
        lbl_subtitle.setObjectName("muted")
        lbl_subtitle.setFont(theme.font(10))

        tabs = QTabWidget()
        tabs.addTab(self._build_tab_ladridos(settings), "Ladridos")
        tabs.addTab(self._build_tab_alcance(settings), "Alcance")
        tabs.addTab(self._build_tab_alertas(settings), "Otras alertas")
        for crear in self._extra_tabs_factories:  # [API TZUKU]
            tab = crear()
            tabs.addTab(tab, tab.titulo)
            self._extra_tabs.append(tab)

        # Botones
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cancel.setFont(theme.font(11, QFont.Bold))
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btn_primary")
        btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        btn_save.setFont(theme.font(11, QFont.Bold))
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_subtitle)
        layout.addSpacing(4)
        layout.addWidget(tabs, 1)
        layout.addLayout(buttons)

    def accept(self):
        for tab in self._extra_tabs:  # [API TZUKU] cada servicio guarda sus propios datos
            tab.aplicar()
        super().accept()

    # ---------- Pestaña: Ladridos ----------
    def _build_tab_ladridos(self, settings: dict) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)

        self.sb_ladridos = QSpinBox()
        self.sb_ladridos.setRange(1, 10)
        self.sb_ladridos.setValue(settings["ladridos"])

        self.sb_sensibilidad = QSpinBox()
        self.sb_sensibilidad.setRange(10, 90)
        self.sb_sensibilidad.setValue(settings["sensibilidad"])
        self.sb_sensibilidad.setSuffix("%")

        v.addWidget(self._build_field(
            "Ladridos para activar la alarma",
            "Ladridos seguidos necesarios para enviar la alerta.",
            self.sb_ladridos))
        v.addWidget(self._build_field(
            "Sensibilidad del umbral IA",
            "Qué tan seguro debe estar el modelo de que el sonido es un ladrido.",
            self.sb_sensibilidad))
        v.addStretch()
        return page

    # ---------- Pestaña: Alcance ----------
    def _build_tab_alcance(self, settings: dict) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)

        self.cb_alcance = QComboBox()
        for clave, (nombre, _) in config.ALCANCES.items():
            self.cb_alcance.addItem(nombre, clave)
        self._refresh_calibrado_item()
        idx = self.cb_alcance.findData(settings["alcance"])
        self.cb_alcance.setCurrentIndex(max(0, idx))
        self.cb_alcance.setMinimumWidth(150)

        v.addWidget(self._build_field(
            "Alcance de detección",
            "Ignora los sonidos que llegan muy bajos (lejanos). Es aproximado: depende del perro y del micrófono.",
            self.cb_alcance))

        # Calibración
        calib = QFrame()
        calib.setObjectName("field")
        row = QHBoxLayout(calib)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        lbl = QLabel("Calibrar con un ladrido real")
        lbl.setFont(theme.font(11, QFont.Bold))
        self.lbl_calibracion = QLabel(
            "Pulsa Calibrar y haz ladrar al perro desde el punto más lejano que quieras vigilar.")
        self.lbl_calibracion.setFont(theme.font(9))
        self.lbl_calibracion.setObjectName("muted")
        self.lbl_calibracion.setWordWrap(True)
        texts.addWidget(lbl)
        texts.addWidget(self.lbl_calibracion)

        self.btn_calibrar = QPushButton(f"Calibrar ({config.CALIBRACION_SEG} s)")
        self.btn_calibrar.setObjectName("btn_outline")
        self.btn_calibrar.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_calibrar.setFont(theme.font(11, QFont.Bold))
        self.btn_calibrar.clicked.connect(self._on_calibrate_clicked)

        row.addLayout(texts, 1)
        row.addWidget(self.btn_calibrar, alignment=Qt.AlignVCenter)
        v.addWidget(calib)
        v.addStretch()
        return page

    def _refresh_calibrado_item(self):
        idx = self.cb_alcance.findData("calibrado")
        if self._umbral_calibrado is None:
            self.cb_alcance.setItemText(idx, "Calibrado (sin calibrar)")
            self.cb_alcance.model().item(idx).setEnabled(False)
        else:
            self.cb_alcance.setItemText(idx, f"Calibrado ({self._umbral_calibrado:.0f} dBFS)")
            self.cb_alcance.model().item(idx).setEnabled(True)

    def _on_calibrate_clicked(self):
        self.btn_calibrar.setEnabled(False)
        self.btn_calibrar.setText("Escuchando…")
        self.lbl_calibracion.setText("Escuchando… haz ladrar al perro ahora.")
        self.lbl_calibracion.setStyleSheet(f"color: {theme.TEXTO}; font-weight: bold;")
        self.calibration_requested.emit()

    def set_calibration_result(self, nivel_max_db: float):
        self.btn_calibrar.setEnabled(True)
        self.btn_calibrar.setText(f"Calibrar ({config.CALIBRACION_SEG} s)")
        if nivel_max_db is None or nivel_max_db < -70:
            self.lbl_calibracion.setText("No se escuchó ningún sonido. Revisa el micrófono e inténtalo de nuevo.")
            self.lbl_calibracion.setStyleSheet(f"color: {theme.ALERTA_OSC}; font-weight: bold;")
            return
        self._umbral_calibrado = round(nivel_max_db - config.CALIBRACION_MARGEN_DB, 1)
        self._refresh_calibrado_item()
        self.cb_alcance.setCurrentIndex(self.cb_alcance.findData("calibrado"))
        self.lbl_calibracion.setStyleSheet(f"color: {theme.TURQUESA_OSC}; font-weight: bold;")
        self.lbl_calibracion.setText(
            f"Listo: ladrido medido a {nivel_max_db:.0f} dBFS. Pulsa Guardar para aplicarlo.")

    # ---------- Pestaña: Otras alertas ----------
    def _build_tab_alertas(self, settings: dict) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(6)

        lbl = QLabel(f"Elige hasta {config.MAX_ALERTAS_EXTRA} sonidos que también enviarán una alerta a la app. "
                     "Pasa el dedo o el ratón por uno para ver cómo se mostrará.")
        lbl.setFont(theme.font(10))
        lbl.setObjectName("muted")
        lbl.setWordWrap(True)
        v.addWidget(lbl)

        fila = QHBoxLayout()
        fila.setSpacing(10)

        box = QFrame()
        box.setObjectName("field")
        grid = QGridLayout(box)
        grid.setContentsMargins(10, 6, 10, 6)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(0)

        self.chk_alertas = {}
        for i, (clave, (nombre, _, _)) in enumerate(config.ALERTAS_EXTRA.items()):
            chk = QCheckBox(nombre)
            chk.setCursor(QCursor(Qt.PointingHandCursor))
            chk.setIcon(QIcon(PixelDogWidget.badge_pixmap(clave, 24)))
            chk.setIconSize(QSize(24, 24))
            chk.setChecked(clave in settings["alertas_extra"])
            if clave == "sirena":
                chk.setToolTip("YAMNet no distingue la alerta sísmica de otras sirenas (ambulancias, policía).")
            chk.toggled.connect(self._enforce_max_alertas)
            chk.toggled.connect(lambda _, c=clave: self._preview_alerta(c))
            chk.setProperty("alerta", clave)
            chk.installEventFilter(self)
            self.chk_alertas[clave] = chk
            grid.addWidget(chk, i // 2, i % 2)
        fila.addWidget(box, 1)
        fila.addWidget(self._build_preview_alerta())
        v.addLayout(fila)

        self.lbl_alertas_count = QLabel()
        self.lbl_alertas_count.setFont(theme.font(9))
        self.lbl_alertas_count.setObjectName("muted")
        v.addWidget(self.lbl_alertas_count)
        v.addStretch()
        self._enforce_max_alertas()
        activas = [k for k in config.ALERTAS_EXTRA if k in settings["alertas_extra"]]
        self._preview_alerta((activas or list(config.ALERTAS_EXTRA))[0])
        return page

    def _build_preview_alerta(self) -> QFrame:
        """Vista previa: el cachorro y el título que aparecerán en la pantalla principal."""
        preview = QFrame()
        preview.setObjectName("field")
        preview.setFixedWidth(150)
        lay = QVBoxLayout(preview)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        self.preview_dog = PixelDogWidget()
        self.preview_dog.setMinimumSize(110, 110)
        self.preview_dog.setFixedHeight(110)

        self.preview_titulo = QLabel()
        self.preview_titulo.setAlignment(Qt.AlignCenter)
        self.preview_titulo.setFont(theme.font(10, QFont.Black))
        self.preview_titulo.setWordWrap(True)
        self.preview_titulo.setFixedHeight(40)

        lay.addWidget(self.preview_dog)
        lay.addWidget(self.preview_titulo)
        lay.addStretch()
        return preview

    def _preview_alerta(self, clave: str):
        estilo = alert_styles.ESTILOS_ALERTA.get(clave)
        if estilo is None:
            return
        bg, fg, _, _ = estilo["colores"]
        self.preview_dog.set_alert(clave)
        self.preview_titulo.setText(estilo["titulo"])
        self.preview_titulo.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: 12px; padding: 2px 6px;")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter and obj.property("alerta"):
            self._preview_alerta(obj.property("alerta"))
        return super().eventFilter(obj, event)

    def _enforce_max_alertas(self):
        activas = sum(chk.isChecked() for chk in self.chk_alertas.values())
        lleno = activas >= config.MAX_ALERTAS_EXTRA
        for chk in self.chk_alertas.values():
            chk.setEnabled(chk.isChecked() or not lleno)
        nota = " La sirena también salta con ambulancias." if self.chk_alertas["sirena"].isChecked() else ""
        self.lbl_alertas_count.setText(f"{activas} de {config.MAX_ALERTAS_EXTRA} activas.{nota}")

    # ---------- Utilidades ----------
    def _build_field(self, title: str, hint: str, control: QWidget) -> QFrame:
        field = QFrame()
        field.setObjectName("field")
        row = QHBoxLayout(field)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        lbl = QLabel(title)
        lbl.setFont(theme.font(11, QFont.Bold))
        lbl_hint = QLabel(hint)
        lbl_hint.setFont(theme.font(9))
        lbl_hint.setObjectName("muted")
        lbl_hint.setWordWrap(True)
        texts.addWidget(lbl)
        texts.addWidget(lbl_hint)

        if isinstance(control, QSpinBox):
            control.setMinimumWidth(110)
            control.setAlignment(Qt.AlignCenter)

        row.addLayout(texts, 1)
        row.addWidget(control, alignment=Qt.AlignVCenter)
        return field

    def values(self) -> dict:
        return {
            "ladridos": self.sb_ladridos.value(),
            "sensibilidad": self.sb_sensibilidad.value(),
            "alcance": self.cb_alcance.currentData(),
            "umbral_calibrado_db": self._umbral_calibrado,
            "alertas_extra": [k for k, chk in self.chk_alertas.items() if chk.isChecked()],
        }
