import os
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPalette, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QStackedWidget, QButtonGroup, QFrame, QSizePolicy, QDialog, QPlainTextEdit,
    QProgressBar
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui import theme
from utils import ConfigManager
from models import list_installed_models, list_selectable_models
import autostart


class StatusDot(QWidget):
    """A small colored circle indicating app status."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = QColor(theme.OK)

    def set_color(self, hex_color):
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, 10, 10)


_QT_NAMED = {
    Qt.Key_Space: 'space', Qt.Key_Return: 'enter', Qt.Key_Enter: 'enter',
    Qt.Key_Tab: 'tab', Qt.Key_Backspace: 'backspace', Qt.Key_Escape: 'esc',
    Qt.Key_Up: 'up', Qt.Key_Down: 'down', Qt.Key_Left: 'left', Qt.Key_Right: 'right',
    Qt.Key_Insert: 'insert', Qt.Key_Delete: 'delete', Qt.Key_Home: 'home', Qt.Key_End: 'end',
    Qt.Key_PageUp: 'page_up', Qt.Key_PageDown: 'page_down',
}
_DIGIT_WORDS = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
                '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
_MOD_ORDER = ['ctrl', 'shift', 'alt', 'meta']


def _qt_key_to_token(k):
    """Map a Qt key code to the app's activation-key token (or None)."""
    if Qt.Key_A <= k <= Qt.Key_Z:
        return chr(k).lower()
    if Qt.Key_0 <= k <= Qt.Key_9:
        return _DIGIT_WORDS[chr(k)]
    if Qt.Key_F1 <= k <= Qt.Key_F35:
        return 'f' + str(k - Qt.Key_F1 + 1)
    return _QT_NAMED.get(k)


def _format_combo(tokens):
    mods = [t for t in _MOD_ORDER if t in tokens]
    rest = [t for t in tokens if t not in _MOD_ORDER]
    return '+'.join(mods + rest)


class HotkeyCaptureDialog(QDialog):
    """Modal dialog that records the largest key combination the user holds down,
    including modifier-only combos like Ctrl+Win."""

    _MODS = {
        Qt.Key_Control: 'ctrl', Qt.Key_Shift: 'shift', Qt.Key_Alt: 'alt',
        Qt.Key_Meta: 'meta', Qt.Key_Super_L: 'meta', Qt.Key_Super_R: 'meta',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.result_combo = ''
        self._pressed = []
        self._best = []

        root = QWidget(self)
        root.setObjectName('RootCard')
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)

        title = QLabel('Назначение горячей клавиши')
        title.setObjectName('PageTitle')
        lay.addWidget(title)

        self.combo_label = QLabel('Зажмите сочетание…')
        self.combo_label.setObjectName('HotkeyDisplay')
        self.combo_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.combo_label)

        hint = QLabel('Например: Ctrl + Win, либо Ctrl + Shift + Space.\nОтпустите клавиши и нажмите «Сохранить».')
        hint.setObjectName('Hint')
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        lay.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel = QPushButton('Отмена')
        cancel.setObjectName('Ghost')
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        ok = QPushButton('Сохранить')
        ok.setObjectName('Primary')
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self._accept)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        lay.addLayout(btn_row)

        self.resize(440, 240)
        self.setStyleSheet(theme.QSS)
        if parent:
            c = parent.frameGeometry().center()
            self.move(c.x() - self.width() // 2, c.y() - self.height() // 2)

    def showEvent(self, event):
        super().showEvent(event)
        self.grabKeyboard()
        self.setFocus()

    def _token(self, e):
        return self._MODS.get(e.key()) or _qt_key_to_token(e.key())

    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            return
        token = self._token(e)
        if token and token not in self._pressed:
            self._pressed.append(token)
            if len(self._pressed) > len(self._best):
                self._best = list(self._pressed)
                self.combo_label.setText(_format_combo(self._best) or '…')

    def keyReleaseEvent(self, e):
        if e.isAutoRepeat():
            return
        token = self._token(e)
        if token in self._pressed:
            self._pressed.remove(token)

    def _accept(self):
        self.result_combo = _format_combo(self._best)
        self.accept()

    def closeEvent(self, event):
        self.releaseKeyboard()
        super().closeEvent(event)

    def done(self, r):
        self.releaseKeyboard()
        super().done(r)


class DashboardWindow(QMainWindow):
    recordToggle = pyqtSignal()
    modelChanged = pyqtSignal(str, str)   # name, path
    settingsSaved = pyqtSignal()
    requestExit = pyqtSignal()
    reinsertRequested = pyqtSignal(str)   # type this text into the active window

    STATUS_LABELS = {
        'idle': 'Готов',
        'recording': 'Слушаю…',
        'transcribing': 'Распознаю…',
        'loading': 'Загрузка модели…',
        'error': 'Ошибка',
    }

    def __init__(self, history_store):
        super().__init__()
        self.history = history_store
        self._drag_pos = None
        self._is_recording = False
        self._installed_models = list_installed_models()

        self.setWindowTitle('WhisperWriter by CatBoneheaD')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(940, 660)
        self.setMinimumSize(840, 580)

        root = QWidget()
        root.setObjectName('RootCard')
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(8)

        outer.addWidget(self._build_title_bar())

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_content(), 1)
        outer.addLayout(body, 1)

        self.setStyleSheet(theme.QSS)
        self._center()
        self.refresh_history()
        self._sync_model_combo()
        self._nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    # ---------- Title bar ----------
    def _build_title_bar(self):
        bar = QWidget()
        bar.setObjectName('TitleBar')
        bar.setFixedHeight(36)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(6, 0, 0, 0)
        lay.setSpacing(8)

        logo = QLabel()
        logo_path = os.path.join('assets', 'ww-logo.png')
        if os.path.exists(logo_path):
            logo.setPixmap(QPixmap(logo_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel('WhisperWriter')
        title.setObjectName('TitleLabel')
        byline = QLabel('by CatBoneheaD')
        byline.setObjectName('Byline')

        lay.addWidget(logo)
        lay.addWidget(title)
        lay.addWidget(byline)
        lay.addStretch(1)

        min_btn = QPushButton('—')
        min_btn.setObjectName('WinBtn')
        min_btn.setFixedSize(28, 26)
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton('×')
        close_btn.setObjectName('WinBtn')
        close_btn.setProperty('class', 'close')
        close_btn.setObjectName('CloseBtn')
        close_btn.setFixedSize(28, 26)
        close_btn.clicked.connect(self.hide)  # hide to tray

        lay.addWidget(min_btn)
        lay.addWidget(close_btn)
        self._title_bar = bar
        return bar

    # ---------- Sidebar ----------
    def _build_sidebar(self):
        side = QWidget()
        side.setObjectName('Sidebar')
        side.setFixedWidth(190)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(12, 14, 12, 12)
        lay.setSpacing(6)

        self._nav_buttons = []
        self._nav_group = QButtonGroup(self)
        for i, (label, _) in enumerate([('  История', 0), ('  Настройки', 1)]):
            btn = QPushButton(label)
            btn.setObjectName('NavBtn')
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._switch_page(idx))
            self._nav_group.addButton(btn)
            self._nav_buttons.append(btn)
            lay.addWidget(btn)

        lay.addStretch(1)

        # Status box
        status_box = QWidget()
        status_box.setObjectName('StatusBox')
        sb = QVBoxLayout(status_box)
        sb.setContentsMargins(12, 10, 12, 12)
        sb.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.status_dot = StatusDot()
        self.status_text = QLabel('Готов')
        self.status_text.setObjectName('StatusText')
        row.addWidget(self.status_dot)
        row.addWidget(self.status_text)
        row.addStretch(1)
        sb.addLayout(row)

        model_lbl = QLabel('Модель')
        model_lbl.setObjectName('StatusSub')
        sb.addWidget(model_lbl)

        self.model_combo = QComboBox()
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.currentIndexChanged.connect(self._on_model_combo_changed)
        sb.addWidget(self.model_combo)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)   # indeterminate (busy)
        self.progress.setFixedHeight(6)
        self.progress.hide()
        sb.addWidget(self.progress)

        lay.addWidget(status_box)

        credit = QLabel('made by CatBoneheaD')
        credit.setObjectName('Credit')
        credit.setAlignment(Qt.AlignCenter)
        lay.addWidget(credit)
        return side

    # ---------- Content ----------
    def _build_content(self):
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_history_page())
        self.stack.addWidget(self._build_settings_page())
        return self.stack

    def _build_history_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel('История')
        title.setObjectName('PageTitle')
        header.addWidget(title)
        header.addStretch(1)
        clear_btn = QPushButton('Очистить всё')
        clear_btn.setObjectName('Ghost')
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn)
        lay.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText('🔍  Поиск по транскрипциям…')
        self.search.textChanged.connect(self.refresh_history)
        lay.addWidget(self.search)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 6, 0)
        self.history_layout.setSpacing(10)
        self.history_layout.addStretch(1)
        scroll.setWidget(self.history_container)
        lay.addWidget(scroll, 1)

        self.record_btn = QPushButton('🎙  Записать  (или горячая клавиша)')
        self.record_btn.setObjectName('RecordBtn')
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.clicked.connect(self.recordToggle.emit)
        lay.addWidget(self.record_btn)

        return page

    def _build_settings_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(2, 2, 2, 2)
        outer.setSpacing(12)

        title = QLabel('Настройки')
        title.setObjectName('PageTitle')
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        # Opaque background so widgets without their own fill (checkboxes) render
        # crisp text — on the translucent window, text over transparency looks faint.
        form_host.setAutoFillBackground(True)
        _pal = form_host.palette()
        _pal.setColor(QPalette.Window, QColor(theme.BG))
        form_host.setPalette(_pal)
        grid = QGridLayout(form_host)
        grid.setContentsMargins(0, 0, 6, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        r = 0
        # Hotkey: manual field + "press keys" capture button
        self.f_hotkey = QLineEdit(ConfigManager.get_config_value('recording_options', 'activation_key') or '')
        capture_btn = QPushButton('⌨  Нажать клавиши')
        capture_btn.setObjectName('Ghost')
        capture_btn.setCursor(Qt.PointingHandCursor)
        capture_btn.clicked.connect(self._capture_hotkey)
        hk_row = QHBoxLayout()
        hk_row.setSpacing(8)
        hk_row.addWidget(self.f_hotkey, 1)
        hk_row.addWidget(capture_btn)
        hk_box = QVBoxLayout()
        hk_box.setSpacing(3)
        hk_box.addLayout(hk_row)
        hk_hint = QLabel('Нажмите кнопку и зажмите нужное сочетание (например Ctrl+Win) — или впишите вручную.')
        hk_hint.setObjectName('Hint')
        hk_hint.setWordWrap(True)
        hk_box.addWidget(hk_hint)
        hk_host = QWidget()
        hk_host.setLayout(hk_box)
        hk_lbl = QLabel('Горячая клавиша')
        hk_lbl.setObjectName('FieldLabel')
        grid.addWidget(hk_lbl, r, 0, Qt.AlignTop | Qt.AlignRight)
        grid.addWidget(hk_host, r, 1)
        r += 1

        # Recording mode
        self.f_mode = QComboBox()
        self._modes = ['continuous', 'voice_activity_detection', 'press_to_toggle', 'hold_to_record']
        mode_labels = ['Непрерывный', 'По тишине (VAD)', 'Переключатель', 'Удержание']
        self.f_mode.addItems(mode_labels)
        cur_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
        if cur_mode in self._modes:
            self.f_mode.setCurrentIndex(self._modes.index(cur_mode))
        r = self._add_field(grid, r, 'Режим записи', self.f_mode)

        # Language (dropdown)
        self.f_lang = QComboBox()
        self._langs = [
            ('Авто (определять)', ''),
            ('Русский', 'ru'), ('Английский', 'en'), ('Испанский', 'es'),
            ('Итальянский', 'it'), ('Французский', 'fr'), ('Немецкий', 'de'),
            ('Португальский', 'pt'), ('Польский', 'pl'), ('Украинский', 'uk'),
            ('Китайский', 'zh'), ('Японский', 'ja'), ('Турецкий', 'tr'),
        ]
        for label, code in self._langs:
            self.f_lang.addItem(label, code)
        cur_lang = ConfigManager.get_config_value('model_options', 'common', 'language') or ''
        self.f_lang.setCurrentIndex(
            next((i for i, (l, c) in enumerate(self._langs) if c == cur_lang), 0))
        r = self._add_field(grid, r, 'Язык', self.f_lang, 'Язык речи (или «Авто» — определить автоматически).')

        # Task: transcribe vs translate-to-English
        self.f_task = QComboBox()
        self._tasks = [('Транскрибация (как сказано)', 'transcribe'),
                       ('Перевод на английский', 'translate')]
        for label, code in self._tasks:
            self.f_task.addItem(label, code)
        cur_task = ConfigManager.get_config_value('model_options', 'common', 'task') or 'transcribe'
        self.f_task.setCurrentIndex(
            next((i for i, (l, c) in enumerate(self._tasks) if c == cur_task), 0))
        r = self._add_field(grid, r, 'Режим распознавания', self.f_task,
                            'Перевод возможен только на английский (ограничение Whisper).')

        # Device
        self.f_device = QComboBox()
        self._devices = ['auto', 'cuda', 'cpu']
        self.f_device.addItems(self._devices)
        cur_dev = ConfigManager.get_config_value('model_options', 'local', 'device')
        if cur_dev in self._devices:
            self.f_device.setCurrentIndex(self._devices.index(cur_dev))
        r = self._add_field(grid, r, 'Устройство', self.f_device)

        # Compute type
        self.f_compute = QComboBox()
        self._computes = ['default', 'float32', 'float16', 'int8']
        self.f_compute.addItems(self._computes)
        cur_ct = ConfigManager.get_config_value('model_options', 'local', 'compute_type')
        if cur_ct in self._computes:
            self.f_compute.setCurrentIndex(self._computes.index(cur_ct))
        r = self._add_field(grid, r, 'Тип вычислений', self.f_compute)

        # Theme
        self.f_theme = QComboBox()
        self._themes = [('Тёмная', 'dark'), ('Светлая', 'light')]
        for label, code in self._themes:
            self.f_theme.addItem(label, code)
        cur_theme = ConfigManager.get_config_value('misc', 'theme') or 'dark'
        self.f_theme.setCurrentIndex(
            next((i for i, (l, c) in enumerate(self._themes) if c == cur_theme), 0))
        r = self._add_field(grid, r, 'Тема оформления', self.f_theme)

        # Replacements editor
        self.f_replacements = QPlainTextEdit()
        self.f_replacements.setPlaceholderText('новая строка => \\n\nточка => .\nзапятая => ,')
        self.f_replacements.setFixedHeight(110)
        rules = ConfigManager.get_config_value('post_processing', 'replacements') or []
        self.f_replacements.setPlainText('\n'.join(rules))
        r = self._add_field(grid, r, 'Замены текста', self.f_replacements,
                            'По строке: «фраза => замена». Голосовые команды, пунктуация, переносы (\\n).')

        # Checkboxes
        self.f_trailing_space = self._make_check(
            'Добавлять пробел в конце',
            bool(ConfigManager.get_config_value('post_processing', 'add_trailing_space')))
        grid.addWidget(self.f_trailing_space, r, 1); r += 1

        self.f_capitalize = self._make_check(
            'Заглавная буква в начале предложений',
            bool(ConfigManager.get_config_value('post_processing', 'capitalize_sentences')))
        grid.addWidget(self.f_capitalize, r, 1); r += 1

        self.f_noise = self._make_check(
            'Звук по завершении',
            bool(ConfigManager.get_config_value('misc', 'noise_on_completion')))
        grid.addWidget(self.f_noise, r, 1); r += 1

        self.f_hide_status = self._make_check(
            'Скрывать всплывающий индикатор записи',
            bool(ConfigManager.get_config_value('misc', 'hide_status_window')))
        grid.addWidget(self.f_hide_status, r, 1); r += 1

        self.f_autostart = self._make_check('Запускать при старте Windows', autostart.is_enabled())
        grid.addWidget(self.f_autostart, r, 1); r += 1

        scroll.setWidget(form_host)
        outer.addWidget(scroll, 1)

        note = QLabel('Настройки применяются сразу после сохранения.')
        note.setObjectName('Hint')
        note.setWordWrap(True)
        outer.addWidget(note)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QPushButton('Сохранить')
        save_btn.setObjectName('Primary')
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

        return page

    def _make_check(self, text, checked):
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.setCursor(Qt.PointingHandCursor)
        # Force a readable text color via palette (QSS color on QCheckBox text is
        # unreliable once ::indicator is styled), and a clear font.
        pal = cb.palette()
        pal.setColor(QPalette.WindowText, QColor(theme.TEXT))
        pal.setColor(QPalette.Text, QColor(theme.TEXT))
        cb.setPalette(pal)
        cb.setFont(QFont('Segoe UI', 11))
        return cb

    def _capture_hotkey(self):
        dlg = HotkeyCaptureDialog(self)
        if dlg.exec_() == QDialog.Accepted and dlg.result_combo:
            self.f_hotkey.setText(dlg.result_combo)

    def _add_field(self, grid, row, label, widget, hint=None):
        lbl = QLabel(label)
        lbl.setObjectName('FieldLabel')
        grid.addWidget(lbl, row, 0, Qt.AlignTop | Qt.AlignRight)
        if hint:
            box = QVBoxLayout()
            box.setSpacing(3)
            box.addWidget(widget)
            h = QLabel(hint)
            h.setObjectName('Hint')
            h.setWordWrap(True)
            box.addWidget(h)
            host = QWidget()
            host.setLayout(box)
            grid.addWidget(host, row, 1)
        else:
            grid.addWidget(widget, row, 1)
        return row + 1

    # ---------- History rendering ----------
    def refresh_history(self):
        # Clear existing cards (keep trailing stretch)
        while self.history_layout.count() > 1:
            item = self.history_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        query = self.search.text().strip() if hasattr(self, 'search') else ''
        rows = self.history.list(query)

        if not rows:
            empty = QLabel('Здесь появятся ваши транскрипции.\nНажмите горячую клавишу и начните говорить.')
            empty.setObjectName('EmptyHint')
            empty.setAlignment(Qt.AlignCenter)
            self.history_layout.insertWidget(0, empty)
            return

        for row in rows:
            self.history_layout.insertWidget(self.history_layout.count() - 1, self._make_card(row))

    def _make_card(self, row):
        card = QFrame()
        card.setObjectName('HistoryCard')
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 12, 12)
        lay.setSpacing(6)

        top = QHBoxLayout()
        time_lbl = QLabel(self._fmt_time(row['created_at'], row.get('duration'), row.get('model')))
        time_lbl.setObjectName('CardTime')
        top.addWidget(time_lbl)
        top.addStretch(1)

        insert_btn = QPushButton('▸')
        insert_btn.setObjectName('IconBtn')
        insert_btn.setFixedSize(28, 26)
        insert_btn.setToolTip('Вставить в активное окно')
        insert_btn.setCursor(Qt.PointingHandCursor)
        insert_btn.clicked.connect(lambda _, t=row['text']: self._reinsert(t))

        copy_btn = QPushButton('⧉')
        copy_btn.setObjectName('IconBtn')
        copy_btn.setFixedSize(28, 26)
        copy_btn.setToolTip('Копировать')
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(lambda _, t=row['text']: self._copy(t))

        del_btn = QPushButton('🗑')
        del_btn.setObjectName('IconBtn')
        del_btn.setFixedSize(28, 26)
        del_btn.setToolTip('Удалить')
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda _, i=row['id']: self._delete(i))

        top.addWidget(insert_btn)
        top.addWidget(copy_btn)
        top.addWidget(del_btn)
        lay.addLayout(top)

        text = QLabel(row['text'])
        text.setObjectName('CardText')
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(text)
        return card

    def _fmt_time(self, created_at, duration=None, model=None):
        try:
            dt = datetime.fromisoformat(created_at)
            stamp = dt.strftime('%d.%m %H:%M')
        except (ValueError, TypeError):
            stamp = created_at
        parts = [stamp]
        if duration:
            parts.append(f'{duration:.0f} c')
        if model:
            parts.append(str(model))
        return '   •   '.join(parts)

    def _copy(self, text):
        QApplication.clipboard().setText(text)
        self.status_text.setText('Скопировано ✓')

    def _reinsert(self, text):
        # Hide the window so focus returns to the previous app, then type there.
        self.hide()
        self.reinsertRequested.emit(text)

    def _delete(self, item_id):
        self.history.delete(item_id)
        self.refresh_history()

    def _clear_history(self):
        self.history.clear()
        self.refresh_history()

    # ---------- Model combo ----------
    def _sync_model_combo(self):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self._selectable_models = list_selectable_models()
        cur_name = ConfigManager.get_config_value('model_options', 'local', 'model')
        selected = 0
        for i, m in enumerate(self._selectable_models):
            mark = '✓' if m['installed'] else '⬇'
            self.model_combo.addItem(f"{m['name']}  {mark}", (m['name'], m['path'] or ''))
            if m['name'] == cur_name:
                selected = i
        self.model_combo.setItemData(
            0, 'Модели: ✓ — установлена, ⬇ — скачается при выборе', Qt.ToolTipRole)
        self.model_combo.setCurrentIndex(selected)
        self.model_combo.blockSignals(False)

    def _on_model_combo_changed(self, index):
        data = self.model_combo.currentData()
        if not data:
            return
        name, path = data
        if name:
            self.modelChanged.emit(name, path or '')

    # ---------- Settings save ----------
    def _save_settings(self):
        ConfigManager.set_config_value(self.f_hotkey.text().strip(),
                                       'recording_options', 'activation_key')
        ConfigManager.set_config_value(self._modes[self.f_mode.currentIndex()],
                                       'recording_options', 'recording_mode')
        ConfigManager.set_config_value(self.f_lang.currentData() or None,
                                       'model_options', 'common', 'language')
        ConfigManager.set_config_value(self.f_task.currentData() or 'transcribe',
                                       'model_options', 'common', 'task')
        ConfigManager.set_config_value(self._devices[self.f_device.currentIndex()],
                                       'model_options', 'local', 'device')
        ConfigManager.set_config_value(self._computes[self.f_compute.currentIndex()],
                                       'model_options', 'local', 'compute_type')
        ConfigManager.set_config_value(self.f_trailing_space.isChecked(),
                                       'post_processing', 'add_trailing_space')
        ConfigManager.set_config_value(self.f_capitalize.isChecked(),
                                       'post_processing', 'capitalize_sentences')
        rules = [ln.strip() for ln in self.f_replacements.toPlainText().splitlines() if ln.strip()]
        ConfigManager.set_config_value(rules, 'post_processing', 'replacements')
        ConfigManager.set_config_value(self.f_theme.currentData() or 'dark',
                                       'misc', 'theme')
        ConfigManager.set_config_value(self.f_noise.isChecked(),
                                       'misc', 'noise_on_completion')
        ConfigManager.set_config_value(self.f_hide_status.isChecked(),
                                       'misc', 'hide_status_window')
        # Autostart is applied immediately (registry), and mirrored in config.
        autostart.set_enabled(self.f_autostart.isChecked())
        ConfigManager.set_config_value(self.f_autostart.isChecked(), 'misc', 'autostart')
        ConfigManager.save_config()
        self.settingsSaved.emit()

    # ---------- Public API for main ----------
    def set_status(self, status):
        self.status_text.setText(self.STATUS_LABELS.get(status, status))
        self.status_dot.set_color(theme.STATUS_COLORS.get(status, theme.TEXT_DIM))
        self.progress.setVisible(status == 'loading')
        if status == 'recording':
            self.set_recording(True)
        elif status in ('idle', 'error'):
            self.set_recording(False)

    def set_recording(self, is_recording):
        self._is_recording = is_recording
        self.record_btn.setText('■  Остановить запись' if is_recording
                                else '🎙  Записать  (или горячая клавиша)')
        self.record_btn.setProperty('recording', 'true' if is_recording else 'false')
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)

    # ---------- Window helpers ----------
    def _switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self._nav_buttons[index].setChecked(True)

    def open_settings(self):
        self._switch_page(1)
        self.show()
        self.raise_()
        self.activateWindow()

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2,
                  screen.center().y() - self.height() // 2)

    def closeEvent(self, event):
        # Hide to tray instead of quitting
        event.ignore()
        self.hide()

    # Drag window by the title bar
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() <= 46:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


if __name__ == '__main__':
    from history import HistoryStore
    ConfigManager.initialize()
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.QSS)
    w = DashboardWindow(HistoryStore())
    w.show()
    sys.exit(app.exec_())
