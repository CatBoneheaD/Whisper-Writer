"""Dark theme (Voice Ink-inspired) for WhisperWriter."""

# Palette
BG = "#15161c"          # window background
SURFACE = "#1e202a"     # cards / panels
SURFACE_2 = "#272a36"   # inputs / hover
BORDER = "#323645"
TEXT = "#e7e9f0"
TEXT_DIM = "#9aa0b4"
ACCENT = "#7c5cff"       # primary accent (violet)
ACCENT_HOVER = "#8f72ff"
ACCENT_SOFT = "#2a2546"
DANGER = "#ff5c72"
OK = "#46d18b"

# Status colors
STATUS_COLORS = {
    'idle': OK,
    'recording': "#ff5c72",
    'transcribing': "#ffb454",
    'loading': "#ffb454",
    'error': DANGER,
}

QSS = f"""
QWidget {{
    color: {TEXT};
    font-family: 'Segoe UI';
    font-size: 13px;
}}

#RootCard {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}

/* Title bar */
#TitleBar {{ background: transparent; }}
#TitleLabel {{ font-size: 14px; font-weight: 600; color: {TEXT}; }}
#Byline {{ font-size: 12px; color: {ACCENT}; font-weight: 600; }}
#Credit {{ font-size: 11px; color: {TEXT_DIM}; padding-top: 4px; }}
#WinBtn {{
    background: transparent; border: none; color: {TEXT_DIM};
    font-size: 16px; border-radius: 6px;
}}
#WinBtn:hover {{ background: {SURFACE_2}; color: {TEXT}; }}
#CloseBtn:hover {{ background: {DANGER}; color: white; }}

/* Sidebar */
#Sidebar {{ background-color: {SURFACE}; border-radius: 12px; }}
#NavBtn {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 9px;
    background: transparent; color: {TEXT_DIM}; font-size: 13px;
}}
#NavBtn:hover {{ background: {SURFACE_2}; color: {TEXT}; }}
#NavBtn:checked {{ background: {ACCENT_SOFT}; color: {TEXT}; font-weight: 600; }}

#StatusBox {{ background-color: {SURFACE_2}; border-radius: 10px; }}
#StatusText {{ color: {TEXT}; font-size: 12px; font-weight: 600; }}
#StatusSub {{ color: {TEXT_DIM}; font-size: 11px; }}

/* Content */
#PageTitle {{ font-size: 18px; font-weight: 700; color: {TEXT}; }}
#Hint {{ color: {TEXT_DIM}; font-size: 12px; }}

QLineEdit, QComboBox {{
    background-color: {SURFACE_2}; border: 1px solid {BORDER};
    border-radius: 9px; padding: 8px 10px; color: {TEXT}; selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_2}; border: 1px solid {BORDER};
    selection-background-color: {ACCENT}; outline: none; border-radius: 8px;
}}

QCheckBox {{ color: {TEXT}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid {BORDER}; background: {SURFACE_2};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 1px solid {ACCENT}; }}

QLabel#FieldLabel {{ color: {TEXT_DIM}; font-size: 12px; }}

/* Buttons */
QPushButton#Primary {{
    background-color: {ACCENT}; color: white; border: none;
    border-radius: 10px; padding: 10px 18px; font-weight: 600;
}}
QPushButton#Primary:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton#Ghost {{
    background-color: {SURFACE_2}; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 10px; padding: 10px 18px;
}}
QPushButton#Ghost:hover {{ border: 1px solid {ACCENT}; }}

/* History card */
#HistoryCard {{
    background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;
}}
#CardTime {{ color: {TEXT_DIM}; font-size: 11px; }}
#CardText {{ color: {TEXT}; font-size: 13px; }}
#IconBtn {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 8px;
    color: {TEXT_DIM}; font-size: 13px; padding: 4px;
}}
#IconBtn:hover {{ color: {TEXT}; border: 1px solid {ACCENT}; }}
#EmptyHint {{ color: {TEXT_DIM}; font-size: 13px; }}

/* Big record button */
#RecordBtn {{
    background-color: {ACCENT}; color: white; border: none;
    border-radius: 12px; padding: 14px; font-size: 14px; font-weight: 700;
}}
#RecordBtn:hover {{ background-color: {ACCENT_HOVER}; }}
#RecordBtn[recording="true"] {{ background-color: {DANGER}; }}

/* Scrollbar */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
"""
