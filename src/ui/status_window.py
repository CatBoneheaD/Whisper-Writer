import os
from collections import deque
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPainterPath, QPen
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QMainWindow

SIZE = 84


def _tint(pixmap, color):
    """Return a copy of pixmap recolored to the given QColor (keeps alpha)."""
    if pixmap.isNull():
        return pixmap
    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return tinted


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = 12
        self.levels = deque([0.0] * self.bars, maxlen=self.bars)
        self.setFixedSize(56, 20)

    def update_level(self, level):
        self.levels.append(max(0.04, level))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        total = len(self.levels)
        bar_w = w / total * 0.55
        step = w / total
        for i, lvl in enumerate(self.levels):
            bar_h = max(3, lvl * h * 0.88)
            x = i * step + (step - bar_w) / 2
            y = (h - bar_h) / 2
            alpha = 160 + int(95 * lvl)
            painter.setBrush(QBrush(QColor(124, 92, 255, min(255, alpha))))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), max(2, int(bar_w)), int(bar_h), 2, 2)


class StatusWindow(QMainWindow):
    statusSignal = pyqtSignal(str)
    closeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(SIZE, SIZE)

        central = QWidget(self)
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 14, 0, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignHCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        microphone_path = os.path.join('assets', 'microphone.png')
        pencil_path = os.path.join('assets', 'pencil.png')
        self.microphone_pixmap = _tint(QPixmap(microphone_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation), QColor('#e7e9f0'))
        self.pencil_pixmap = _tint(QPixmap(pencil_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation), QColor('#ffb454'))
        self.icon_label.setPixmap(self.microphone_pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.waveform = WaveformWidget()

        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.waveform, alignment=Qt.AlignCenter)

        self.statusSignal.connect(self.updateStatus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1.5, 1.5, SIZE - 3, SIZE - 3)
        painter.setBrush(QBrush(QColor(30, 32, 42, 235)))
        painter.setPen(QPen(QColor(124, 92, 255, 220), 1.5))
        painter.drawEllipse(rect)

    def show(self):
        screen = QApplication.primaryScreen()
        sg = screen.geometry()
        x = (sg.width() - self.width()) // 2
        y = sg.height() - self.height() - 100
        self.move(x, y)
        super().show()

    def closeEvent(self, event):
        self.closeSignal.emit()
        super().closeEvent(event)

    @pyqtSlot(float)
    def updateAudioLevel(self, level):
        self.waveform.update_level(level)

    @pyqtSlot(str)
    def updateStatus(self, status):
        if status == 'recording':
            self.icon_label.setPixmap(self.microphone_pixmap)
            self.waveform.update_level(0.0)
            self.show()
        elif status == 'transcribing':
            self.icon_label.setPixmap(self.pencil_pixmap)
            self.waveform.update_level(0.0)

        if status in ('idle', 'error', 'cancel'):
            self.close()
