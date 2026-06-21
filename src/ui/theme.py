"""Theming for WhisperWriter — dark (Voice Ink-inspired) and light palettes.

Call set_theme('dark'|'light') before building windows. Module-level names
(BG, TEXT, ACCENT, QSS, STATUS_COLORS, ...) reflect the active theme so existing
code that reads e.g. theme.TEXT keeps working.
"""

DARK = {
    'BG': '#15161c', 'SURFACE': '#1e202a', 'SURFACE_2': '#272a36', 'BORDER': '#323645',
    'TEXT': '#e7e9f0', 'TEXT_DIM': '#9aa0b4',
    'ACCENT': '#7c5cff', 'ACCENT_HOVER': '#8f72ff', 'ACCENT_SOFT': '#2a2546',
    'DANGER': '#ff5c72', 'OK': '#46d18b', 'WARN': '#ffb454',
}

LIGHT = {
    'BG': '#f3f4f8', 'SURFACE': '#ffffff', 'SURFACE_2': '#eaecf2', 'BORDER': '#d4d8e2',
    'TEXT': '#1c2030', 'TEXT_DIM': '#697086',
    'ACCENT': '#6b4dff', 'ACCENT_HOVER': '#5a3df0', 'ACCENT_SOFT': '#e6e0ff',
    'DANGER': '#e0455a', 'OK': '#1faf6b', 'WARN': '#bf8420',
}

PALETTES = {'dark': DARK, 'light': LIGHT}


def build_qss(c):
    return f"""
QWidget {{
    color: {c['TEXT']};
    font-family: 'Segoe UI';
    font-size: 13px;
}}

#RootCard {{
    background-color: {c['BG']};
    border: 1px solid {c['BORDER']};
    border-radius: 16px;
}}

/* Title bar */
#TitleBar {{ background: transparent; }}
#TitleLabel {{ font-size: 14px; font-weight: 600; color: {c['TEXT']}; }}
#Byline {{ font-size: 12px; color: {c['ACCENT']}; font-weight: 600; }}
#Credit {{ font-size: 11px; color: {c['TEXT_DIM']}; padding-top: 4px; }}
#WinBtn {{
    background: transparent; border: none; color: {c['TEXT_DIM']};
    font-size: 16px; border-radius: 6px;
}}
#WinBtn:hover {{ background: {c['SURFACE_2']}; color: {c['TEXT']}; }}
#CloseBtn:hover {{ background: {c['DANGER']}; color: white; }}

/* Sidebar */
#Sidebar {{ background-color: {c['SURFACE']}; border-radius: 12px; }}
#NavBtn {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 9px;
    background: transparent; color: {c['TEXT_DIM']}; font-size: 13px;
}}
#NavBtn:hover {{ background: {c['SURFACE_2']}; color: {c['TEXT']}; }}
#NavBtn:checked {{ background: {c['ACCENT_SOFT']}; color: {c['TEXT']}; font-weight: 600; }}

#StatusBox {{ background-color: {c['SURFACE_2']}; border-radius: 10px; }}
#StatusText {{ color: {c['TEXT']}; font-size: 12px; font-weight: 600; }}
#StatusSub {{ color: {c['TEXT_DIM']}; font-size: 11px; }}

/* Content */
#PageTitle {{ font-size: 18px; font-weight: 700; color: {c['TEXT']}; }}
#Hint {{ color: {c['TEXT_DIM']}; font-size: 12px; }}

QLineEdit, QComboBox, QPlainTextEdit {{
    background-color: {c['SURFACE_2']}; border: 1px solid {c['BORDER']};
    border-radius: 9px; padding: 9px 12px; min-height: 20px; font-size: 13px;
    color: {c['TEXT']}; selection-background-color: {c['ACCENT']};
}}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {c['ACCENT']}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {c['SURFACE_2']}; border: 1px solid {c['BORDER']};
    selection-background-color: {c['ACCENT']}; outline: none; border-radius: 8px;
}}

QCheckBox {{ color: {c['TEXT']}; font-size: 13px; spacing: 10px; padding: 4px 0; }}
QCheckBox::indicator {{
    width: 20px; height: 20px; border-radius: 5px;
    border: 1px solid {c['BORDER']}; background: {c['SURFACE_2']};
}}
QCheckBox::indicator:hover {{ border: 1px solid {c['ACCENT']}; }}
QCheckBox::indicator:checked {{ background: {c['ACCENT']}; border: 1px solid {c['ACCENT']}; }}

#HotkeyDisplay {{
    font-size: 22px; font-weight: 700; color: {c['ACCENT']};
    background: {c['SURFACE_2']}; border: 1px solid {c['BORDER']}; border-radius: 10px;
    padding: 14px;
}}

QLabel#FieldLabel {{ color: {c['TEXT_DIM']}; font-size: 12px; }}

/* Buttons */
QPushButton#Primary {{
    background-color: {c['ACCENT']}; color: white; border: none;
    border-radius: 10px; padding: 10px 18px; font-weight: 600;
}}
QPushButton#Primary:hover {{ background-color: {c['ACCENT_HOVER']}; }}
QPushButton#Ghost {{
    background-color: {c['SURFACE_2']}; color: {c['TEXT']}; border: 1px solid {c['BORDER']};
    border-radius: 10px; padding: 10px 18px;
}}
QPushButton#Ghost:hover {{ border: 1px solid {c['ACCENT']}; }}

/* History card */
#HistoryCard {{
    background-color: {c['SURFACE']}; border: 1px solid {c['BORDER']}; border-radius: 12px;
}}
#CardTime {{ color: {c['TEXT_DIM']}; font-size: 11px; }}
#CardText {{ color: {c['TEXT']}; font-size: 13px; }}
#IconBtn {{
    background: {c['SURFACE_2']}; border: 1px solid {c['BORDER']}; border-radius: 8px;
    color: {c['TEXT_DIM']}; font-size: 13px; padding: 4px;
}}
#IconBtn:hover {{ color: {c['TEXT']}; border: 1px solid {c['ACCENT']}; }}
#EmptyHint {{ color: {c['TEXT_DIM']}; font-size: 13px; }}

/* Big record button */
#RecordBtn {{
    background-color: {c['ACCENT']}; color: white; border: none;
    border-radius: 12px; padding: 14px; font-size: 14px; font-weight: 700;
}}
#RecordBtn:hover {{ background-color: {c['ACCENT_HOVER']}; }}
#RecordBtn[recording="true"] {{ background-color: {c['DANGER']}; }}

/* Progress bar (model download/load) */
QProgressBar {{
    background: {c['SURFACE_2']}; border: none; border-radius: 4px;
    height: 6px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background: {c['ACCENT']}; border-radius: 4px; }}

/* Scrollbar */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['BORDER']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {c['TEXT_DIM']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
"""


def set_theme(name):
    """Activate a theme by name and refresh module-level color/QSS globals."""
    c = PALETTES.get(name, DARK)
    g = globals()
    g['ACTIVE'] = name if name in PALETTES else 'dark'
    g['_C'] = c
    for k, v in c.items():
        g[k] = v
    g['STATUS_COLORS'] = {
        'idle': c['OK'], 'recording': c['DANGER'], 'transcribing': c['WARN'],
        'loading': c['WARN'], 'error': c['DANGER'],
    }
    g['QSS'] = build_qss(c)


# Initialize to dark by default.
set_theme('dark')
