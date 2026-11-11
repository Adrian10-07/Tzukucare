from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen
from views import alert_styles, dog_sprites
import config

# Colores de todo el pixel art: cachorro + iconos de las alertas
COLORES = {k: QColor(*rgb) for k, rgb in {**dog_sprites.COLORES, **alert_styles.COLORES_EXTRA}.items()}

# Poses de cada estado, una por fotograma (la animación tiene 4 fotogramas)
POSES_ESTADO = {
    "REPOSO":                ("sentado", "sentado", "sentado", "parpadeo"),
    "ESCUCHA ACTIVA":        ("ladrando", "atento", "ladrando", "atento"),
    "¡¡ ALARMA ACTIVADA !!": ("alarma", "ladrando", "alarma", "ladrando"),
}


class PixelDogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.state = "REPOSO"
        self.alerta = None  # clave de config.ALERTAS_EXTRA mientras se muestra una alerta extra
        self.frame = 0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._next_frame)
        self.anim_timer.start(200)

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self._update_interval()
            self.update()

    def set_alert(self, clave):
        """Muestra el cachorro de una alerta extra (None vuelve al estado normal)."""
        if clave not in alert_styles.ESTILOS_ALERTA:
            clave = None
        if self.alerta != clave:
            self.alerta = clave
            self._update_interval()
            self.update()

    def _update_interval(self):
        if self.alerta:
            self.anim_timer.setInterval(150)
        elif self.state == "¡¡ ALARMA ACTIVADA !!":
            self.anim_timer.setInterval(100)
        else:
            self.anim_timer.setInterval(200)

    def _next_frame(self):
        self.frame = (self.frame + 1) % 4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        estilo = alert_styles.ESTILOS_ALERTA.get(self.alerta)
        if estilo:
            grid = dog_sprites.sprite(estilo["poses"][self.frame % 2])
            fondo = estilo["colores"][2]
        else:
            poses = POSES_ESTADO.get(self.state, POSES_ESTADO["¡¡ ALARMA ACTIVADA !!"])
            grid = dog_sprites.sprite(poses[self.frame])
            fondo = config.ESTILOS_ESTADO.get(self.state, config.ESTILOS_ESTADO["REPOSO"])[2]

        # En una alerta el cachorro se dibuja algo más pequeño para dejar sitio a la burbuja
        n = len(grid)
        celdas = n + 7 if estilo else n + 2
        pixel_size = max(1, min(self.width(), self.height()) // celdas)
        offset_x = (self.width() - (pixel_size * celdas)) // 2
        offset_y = (self.height() - (pixel_size * celdas)) // 2

        # Fondo suave redondeado
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(fondo))
        painter.drawRoundedRect(offset_x, offset_y, pixel_size * celdas, pixel_size * celdas, 28, 28)
        painter.setRenderHint(QPainter.Antialiasing, False)

        if not estilo:
            self._draw_grid(painter, grid, offset_x + pixel_size, offset_y + pixel_size, pixel_size)
            return

        # El cachorro tiembla en las alertas de sustos fuertes
        dx = 0
        if estilo["temblor"]:
            dx = (-1, 1, 0, 1)[self.frame] * max(1, pixel_size // 2)
        self._draw_grid(painter, grid, offset_x + pixel_size + dx, offset_y + pixel_size * 6, pixel_size)
        self._draw_badge(painter, offset_x, offset_y, pixel_size * celdas, pixel_size, estilo)

    @staticmethod
    def _draw_grid(painter, grid, x0, y0, pixel_size):
        for r, fila in enumerate(grid):
            for c, char in enumerate(fila):
                color = COLORES.get(char)
                if color is not None:
                    painter.fillRect(x0 + c * pixel_size, y0 + r * pixel_size,
                                     pixel_size, pixel_size, color)

    def _draw_badge(self, painter, offset_x, offset_y, ancho, pixel_size, estilo):
        """Burbuja con el icono de la alerta en la esquina superior derecha."""
        icono = alert_styles.ICONOS[self.alerta][self.frame % 2]
        lado = pixel_size * 10
        x = offset_x + ancho - lado - pixel_size // 2
        y = offset_y + pixel_size // 2

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(estilo["colores"][0]), max(2, pixel_size // 2)))
        painter.drawRoundedRect(x, y, lado, lado, lado // 4, lado // 4)
        painter.setRenderHint(QPainter.Antialiasing, False)
        self._draw_grid(painter, icono, x + pixel_size, y + pixel_size, pixel_size)

    @staticmethod
    def badge_pixmap(clave: str, size: int = 24, frame: int = 0) -> QPixmap:
        """Icono pixel art de una alerta (para listas y botones del panel de configuración)."""
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        icono = alert_styles.ICONOS.get(clave)
        if not icono:
            return pix
        celda = size // 8
        margen = (size - celda * 8) // 2
        p = QPainter(pix)
        PixelDogWidget._draw_grid(p, icono[frame % 2], margen, margen, celda)
        p.end()
        return pix
