import os
import struct
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import Qt, QBuffer, QByteArray, QRectF
from PyQt5.QtSvg import QSvgRenderer

HERE = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(HERE, 'bear.svg')
SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_png(renderer, size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(p, QRectF(0, 0, size, size))
    p.end()
    buf = QBuffer()
    buf.open(QBuffer.WriteOnly)
    img.save(buf, 'PNG')
    return bytes(buf.data())


def build_ico(entries):
    header = struct.pack('<HHH', 0, 1, len(entries))
    dir_entries = b''
    offset = 6 + 16 * len(entries)
    blob = b''
    for size, data in entries:
        b = size % 256  # 256 -> 0
        dir_entries += struct.pack('<BBBBHHII', b, b, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
        blob += data
    return header + dir_entries + blob


def main():
    app = QApplication([])
    renderer = QSvgRenderer(SVG)
    assert renderer.isValid(), 'SVG failed to parse'

    pngs = [(s, render_png(renderer, s)) for s in SIZES]

    # Main PNG logo (256) used by the app/tray
    with open(os.path.join(HERE, 'ww-logo.png'), 'wb') as f:
        f.write(dict(pngs)[256])

    # Multi-resolution ICO (PNG-compressed entries)
    with open(os.path.join(HERE, 'ww-logo.ico'), 'wb') as f:
        f.write(build_ico(pngs))

    print('OK sizes:', [s for s, _ in pngs])


if __name__ == '__main__':
    main()
