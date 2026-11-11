# views/theme.py
"""Tokens visuales y hojas de estilo compartidas, basadas en la paleta de config.py."""
import os
import tempfile
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QFont, QPixmap, QPainter, QPen, QColor, QPainterPath
import config

# Paleta (config.py) + dos tonos derivados para estados de pulsación
TURQUESA = config.TURQUESA
TURQUESA_OSC = config.TURQUESA_OSC
CELESTE = config.CELESTE
CELESTE_CLARO = config.CELESTE_CLARO
FONDO_ARRIBA = config.FONDO_ARRIBA
FONDO_ABAJO = config.FONDO_ABAJO
AMARILLO = config.AMARILLO
AMARILLO_SUAVE = config.AMARILLO_SUAVE
TEXTO = config.TEXTO
TEXTO_SUAVE = config.TEXTO_SUAVE
ALERTA = config.ALERTA
ALERTA_SUAVE = config.ALERTA_SUAVE
ALERTA_OSC = "#D94F4F"      # ALERTA oscurecido
BORDE = "#D3ECF4"           # entre CELESTE_CLARO y CELESTE

FAMILIAS = ["Segoe UI", "Noto Sans", "DejaVu Sans", "Arial"]


def font(size: int, weight: int = QFont.Normal) -> QFont:
    f = QFont(FAMILIAS[0], size, weight)
    try:
        f.setFamilies(FAMILIAS)  # Qt >= 5.13: usa la primera fuente instalada
    except AttributeError:
        pass
    return f


def _icon_path(nombre: str, color: str) -> str:
    """Dibuja (una sola vez) iconos pequeños para la hoja de estilo: check y flechas."""
    carpeta = os.path.join(tempfile.gettempdir(), "tzukucare_ui")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}_{color.strip('#')}.png")
    if not os.path.exists(ruta):
        size = 32
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color), 4.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        path = QPainterPath()
        if nombre == "check":
            path.moveTo(QPointF(7, 17)); path.lineTo(QPointF(13, 23)); path.lineTo(QPointF(25, 9))
        elif nombre == "up":
            path.moveTo(QPointF(8, 20)); path.lineTo(QPointF(16, 12)); path.lineTo(QPointF(24, 20))
        else:  # down
            path.moveTo(QPointF(8, 12)); path.lineTo(QPointF(16, 20)); path.lineTo(QPointF(24, 12))
        p.drawPath(path)
        p.end()
        pix.save(ruta, "PNG")
    return ruta.replace("\\", "/")  # QSS necesita barras normales (Windows)


def main_window_qss(small: bool) -> str:
    radio_card = 18 if small else 24
    return f"""
        QWidget#root {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {FONDO_ARRIBA}, stop:1 {FONDO_ABAJO});
        }}
        QLabel {{ color: {TEXTO}; background: transparent; }}

        QFrame#header {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {TURQUESA_OSC}, stop:1 {TURQUESA});
            border-radius: {radio_card - 4}px;
        }}
        QLabel#logo {{ color: #FFFFFF; }}
        QLabel#logo_sub {{ color: {AMARILLO_SUAVE}; }}
        QLabel#logo_badge {{
            background-color: {AMARILLO};
            color: {TEXTO};
            border-radius: {9 if small else 12}px;
        }}
        QPushButton#btn_config {{
            background-color: #FFFFFF;
            color: {TURQUESA_OSC};
            border: none;
            border-radius: {16 if small else 19}px;
            padding: 0px {14 if small else 20}px;
        }}
        QPushButton#btn_config:hover {{ background-color: {AMARILLO_SUAVE}; }}
        QPushButton#btn_config:pressed {{ background-color: {AMARILLO}; }}

        QFrame#card {{
            background-color: #FFFFFF;
            border: 2px solid {BORDE};
            border-radius: {radio_card}px;
        }}
        QLabel#caption {{ color: {TEXTO_SUAVE}; }}
        QLabel#muted {{ color: {TEXTO_SUAVE}; }}
        QLabel#sound_value {{ color: {TEXTO}; }}
        QFrame#info_box {{
            background-color: {CELESTE_CLARO};
            border: none;
            border-radius: {12 if small else 16}px;
        }}

        QPushButton#btn_emergency {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {ALERTA}, stop:1 {ALERTA_OSC});
            border: none;
            border-radius: {radio_card + 4}px;
        }}
        QPushButton#btn_emergency:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #F27C7C, stop:1 {ALERTA});
        }}
        QPushButton#btn_emergency:pressed {{ background-color: {ALERTA_OSC}; }}
        QLabel#emergency_title {{ color: #FFFFFF; }}
        QLabel#emergency_subtitle {{ color: {ALERTA_SUAVE}; }}
    """


def dialog_qss() -> str:
    check = _icon_path("check", "#FFFFFF")
    up = _icon_path("up", TURQUESA_OSC)
    down = _icon_path("down", TURQUESA_OSC)
    return f"""
        QDialog {{ background-color: {FONDO_ABAJO}; }}
        QLabel {{ color: {TEXTO}; background: transparent; }}
        QLabel#dialog_title {{ color: {TEXTO}; }}
        QLabel#muted {{ color: {TEXTO_SUAVE}; }}
        QLabel#status_ok {{ color: {TURQUESA_OSC}; }}
        QLabel#status_warn {{ color: {ALERTA_OSC}; }}

        QFrame#field {{
            background-color: #FFFFFF;
            border: 1px solid {BORDE};
            border-radius: 14px;
        }}

        /* Pestañas tipo control segmentado */
        QTabWidget::pane {{ border: none; }}
        QTabWidget::tab-bar {{ alignment: left; }}
        QTabBar {{ background: transparent; }}
        QTabBar::tab {{
            background: {CELESTE_CLARO};
            color: {TEXTO_SUAVE};
            padding: 8px 18px;
            margin-right: 6px;
            border-radius: 15px;
            font-weight: bold;
        }}
        QTabBar::tab:hover {{ color: {TEXTO}; }}
        QTabBar::tab:selected {{ background: {TURQUESA}; color: #FFFFFF; }}

        QSpinBox, QComboBox {{
            background-color: {FONDO_ABAJO};
            border: 2px solid {CELESTE_CLARO};
            border-radius: 12px;
            padding: 6px 10px;
            font-size: 16px;
            font-weight: bold;
            color: {TEXTO};
            min-height: 30px;
            selection-background-color: {TURQUESA};
        }}
        QSpinBox:focus, QComboBox:focus, QComboBox:on {{ border-color: {TURQUESA}; }}
        QSpinBox::up-button, QSpinBox::down-button {{
            width: 28px;
            border: none;
            background: {CELESTE_CLARO};
        }}
        QSpinBox::up-button {{ border-top-right-radius: 10px; }}
        QSpinBox::down-button {{ border-bottom-right-radius: 10px; }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {CELESTE}; }}
        QSpinBox::up-arrow {{ image: url("{up}"); width: 14px; height: 14px; }}
        QSpinBox::down-arrow {{ image: url("{down}"); width: 14px; height: 14px; }}
        QComboBox::drop-down {{ border: none; width: 34px; }}
        QComboBox::down-arrow {{ image: url("{down}"); width: 16px; height: 16px; }}
        QComboBox QAbstractItemView {{
            background: #FFFFFF;
            color: {TEXTO};
            border: 1px solid {BORDE};
            selection-background-color: {CELESTE_CLARO};
            selection-color: {TEXTO};
            outline: none;
            padding: 4px;
        }}

        QCheckBox {{
            color: {TEXTO};
            font-size: 13px;
            spacing: 10px;
            padding: 7px 4px;
        }}
        QCheckBox:disabled {{ color: {CELESTE}; }}
        QCheckBox::indicator {{
            width: 20px; height: 20px;
            border-radius: 6px;
            border: 2px solid {CELESTE};
            background: #FFFFFF;
        }}
        QCheckBox::indicator:hover {{ border-color: {TURQUESA}; }}
        QCheckBox::indicator:checked {{
            background: {TURQUESA};
            border-color: {TURQUESA};
            image: url("{check}");
        }}
        QCheckBox::indicator:disabled {{ background: {FONDO_ABAJO}; border-color: {CELESTE_CLARO}; }}

        QPushButton {{
            border: none;
            border-radius: 14px;
            font-weight: bold;
            padding: 9px 20px;
            min-height: 22px;
        }}
        QPushButton#btn_primary {{ background-color: {TURQUESA}; color: #FFFFFF; }}
        QPushButton#btn_primary:hover {{ background-color: {TURQUESA_OSC}; }}
        QPushButton#btn_primary:disabled {{ background-color: {CELESTE}; }}
        QPushButton#btn_secondary {{ background-color: {CELESTE_CLARO}; color: {TEXTO}; }}
        QPushButton#btn_secondary:hover {{ background-color: {CELESTE}; }}
        QPushButton#btn_outline {{
            background-color: #FFFFFF;
            color: {TURQUESA_OSC};
            border: 2px solid {TURQUESA};
        }}
        QPushButton#btn_outline:hover {{ background-color: {CELESTE_CLARO}; }}
        QPushButton#btn_outline:disabled {{ color: {TEXTO_SUAVE}; border-color: {CELESTE}; }}
    """
