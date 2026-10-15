from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor
import config

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
            '.': QColor(0, 0, 0, 0),
            'K': QColor(26, 26, 26),
            'B': QColor(140, 80, 40),
            'L': QColor(200, 130, 70),
            'W': QColor(245, 245, 245),
            'R': QColor(220, 50, 50),
            'Y': QColor(255, 200, 0),
            'P': QColor(255, 150, 180)
        }

        self.matrix_sit_1 = [
            "................", ".....KKKK.......", "....KLLLLKK.....", "...KLLKBLLLK....",
            "...KLLLLLLLK....", "...KLLLLLRK.....", "....KLLLLK......", "....KBBBLLK.....",
            "...KBBBBBBBKK...", "..KBBBBBBBBBBK..", "..KBBBBBBBBBBK..", "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..", "..KWWK...KWWK...", ".KWWWK...KWWWK..", "................"
        ]

        self.matrix_sit_2 = [
            "................", ".....KKKK.......", "....KLLLLKK.....", "...KLLKKLLLK....",
            "...KLLLLLLLK....", "...KLLLLLRK.....", "....KLLLLK......", "....KBBBLLK.....",
            "...KBBBBBBBKK...", "..KBBBBBBBBBBK..", "..KBBBBBBBBBBK..", "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..", "..KWWK...KWWK...", ".KWWWK...KWWWK..", "................"
        ]

        self.matrix_bark_1 = [
            "....KK...KK.....", "...KLLK.KLLK....", "...KLLLKLLLK....", "...KLLKBLLLK....",
            "...KLLLLLLLK....", "...KLLLRRRK.....", "....KLLRPPK.....", "....KBBBLLK.....",
            "...KBBBBBBBKK...", "..KBBBBBBBBBBK..", "..KBBBBBBBBBBK..", "..KBBBBBBBBBBK..",
            "..KBBBBBBBBBBK..", "..KWWK...KWWK...", ".KWWWK...KWWWK..", "................"
        ]

        self.matrix_alarm_1 = [
            "YY...KK...KK....", ".YY.KLLK.KLLK...", "..Y.KLLLKLLLK...", "...KLLKBLLLK....",
            "...KLLLLLLLK....", "..KLLLRRRRRKYY..", "..KLLLRPRPRK.YY.", "...KBBBLLKK...Y.",
            "..KBBBBBBBKK....", ".KBBBBBBBBBBK...", ".KBBBBBBBBBBK...", ".KBBBBBBBBBBK...",
            ".KBBBBBBBBBBK...", ".KWWK...KWWK....", "KWWWK...KWWWK...", "................"
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

        # Fondo suave redondeado
        fondo = config.ESTILOS_ESTADO.get(self.state, config.ESTILOS_ESTADO["REPOSO"])[2]
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(fondo))
        painter.drawRoundedRect(offset_x, offset_y, pixel_size * 16, pixel_size * 16, 28, 28)
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