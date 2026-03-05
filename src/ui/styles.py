"""
WebCap Design System — Glassmorphism Dark Theme
"""

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
COLORS = {
    'bg_main':        '#0D0D0D',
    'bg_card':        '#1A1A2E',
    'bg_surface':     '#16213E',
    'bg_elevated':    '#1E2D4A',
    'primary':        '#007AFF',
    'primary_light':  '#00D4FF',
    'primary_hover':  '#339DFF',
    'primary_muted':  'rgba(0, 122, 255, 0.15)',
    'text_primary':   '#F0F0F0',
    'text_secondary': '#7B8794',
    'text_muted':     '#4A5568',
    'border':         '#1E2D3D',
    'border_light':   '#2A3F55',
    'danger':         '#FF4757',
    'danger_hover':   '#FF6B81',
    'success':        '#2ED573',
    'warning':        '#FFA502',
    'purple':         '#5352ED',
    'shadow':         'rgba(0, 0, 0, 0.5)',
    'glow_primary':   'rgba(0, 122, 255, 0.3)',
    'glass_bg':       'rgba(26, 26, 46, 0.85)',
}

# ---------------------------------------------------------------------------
# Spacing  (8-px grid)
# ---------------------------------------------------------------------------
SPACING = {
    'xs':  4,
    'sm':  8,
    'md':  16,
    'lg':  24,
    'xl':  32,
    'xxl': 48,
}

# ---------------------------------------------------------------------------
# Border Radius
# ---------------------------------------------------------------------------
RADIUS = {
    'sm': 6,
    'md': 10,
    'lg': 16,
    'xl': 24,
}

# ---------------------------------------------------------------------------
# Global Stylesheet
# ---------------------------------------------------------------------------
GLOBAL_STYLESHEET = f"""
/* ---- Base ---- */
QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 13px;
}}

/* ---- Buttons (default / secondary) ---- */
QPushButton {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['md']}px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_elevated']};
    border-color: {COLORS['primary']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_card']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}

/* ---- Primary button (object name "primary") ---- */
QPushButton#primary {{
    background-color: {COLORS['primary']};
    border: 1px solid {COLORS['primary']};
    color: white;
    font-weight: 600;
    border-radius: {RADIUS['md']}px;
}}

QPushButton#primary:hover {{
    background-color: {COLORS['primary_hover']};
    border-color: {COLORS['primary_hover']};
}}

QPushButton#primary:disabled {{
    background-color: {COLORS['text_muted']};
    border-color: {COLORS['text_muted']};
}}

/* ---- Danger button (object name "danger") ---- */
QPushButton#danger {{
    background-color: {COLORS['danger']};
    border: 1px solid {COLORS['danger']};
    color: white;
    font-weight: 600;
}}

QPushButton#danger:hover {{
    background-color: {COLORS['danger_hover']};
    border-color: {COLORS['danger_hover']};
}}

/* ---- Icon-only buttons (object name "icon_btn") ---- */
QPushButton#icon_btn {{
    background-color: transparent;
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['md']}px;
    padding: 6px;
}}

QPushButton#icon_btn:hover {{
    background-color: {COLORS['bg_elevated']};
    border-color: {COLORS['primary']};
}}

/* ---- Labels ---- */
QLabel {{
    background-color: transparent;
    color: {COLORS['text_primary']};
}}

QLabel#secondary {{
    color: {COLORS['text_secondary']};
}}

QLabel#muted {{
    color: {COLORS['text_muted']};
}}

QLabel#title {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

QLabel#section_title {{
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
}}

QLabel#timer {{
    font-size: 20px;
    font-family: 'SF Mono', 'JetBrains Mono', 'Fira Mono', 'Consolas', monospace;
    font-weight: 600;
    letter-spacing: 2px;
}}

QLabel#badge {{
    background-color: {COLORS['primary_muted']};
    color: {COLORS['primary_light']};
    border-radius: {RADIUS['sm']}px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}

/* ---- Line Edit ---- */
QLineEdit {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['sm']}px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    font-size: 13px;
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['bg_elevated']};
}}

QLineEdit:disabled {{
    color: {COLORS['text_muted']};
}}

/* ---- Spin Box ---- */
QSpinBox {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['sm']}px;
    padding: 6px 8px;
    color: {COLORS['text_primary']};
}}

QSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {COLORS['bg_elevated']};
    border: none;
    width: 16px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {COLORS['primary']};
}}

/* ---- Combo Box ---- */
QComboBox {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['sm']}px;
    padding: 6px 10px;
    color: {COLORS['text_primary']};
    min-height: 28px;
    min-width: 150px;
}}

QComboBox:focus {{
    border-color: {COLORS['primary']};
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
    background-color: {COLORS['bg_elevated']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    selection-background-color: {COLORS['primary']};
    selection-color: white;
    outline: none;
    padding: 4px;
}}

/* ---- Check Box ---- */
QCheckBox {{
    spacing: 8px;
    color: {COLORS['text_primary']};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: {RADIUS['sm']}px;
    border: 1px solid {COLORS['border_light']};
    background-color: {COLORS['bg_surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary']};
}}

/* ---- Slider ---- */
QSlider::groove:horizontal {{
    background: {COLORS['bg_surface']};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['primary']};
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
    border: 2px solid {COLORS['bg_main']};
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS['primary_hover']};
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['primary']};
    border-radius: 2px;
}}

/* ---- Scroll Bar ---- */
QScrollBar:vertical {{
    background: {COLORS['bg_main']};
    width: 6px;
    border: none;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['primary']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_main']};
    height: 6px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['border_light']};
    border-radius: 3px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['primary']};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ---- List Widget (fallback) ---- */
QListWidget {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS['md']}px;
    padding: 8px;
    outline: none;
}}

QListWidget::item {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    padding: 10px 12px;
    border-radius: {RADIUS['sm']}px;
    margin: 2px 0;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_surface']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

/* ---- Progress Bar ---- */
QProgressBar {{
    background-color: {COLORS['bg_surface']};
    border: none;
    border-radius: 2px;
    height: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 2px;
}}

/* ---- Group Box ---- */
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['md']}px;
    margin-top: 20px;
    padding: 16px 16px 12px 16px;
    font-weight: 600;
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    top: 0px;
    padding: 0 6px;
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    background-color: {COLORS['bg_main']};
}}

/* ---- Dialog ---- */
QDialog {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
}}

/* ---- Menu ---- */
QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['md']}px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: {RADIUS['sm']}px;
    color: {COLORS['text_primary']};
}}

QMenu::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

/* ---- Message Box ---- */
QMessageBox {{
    background-color: {COLORS['bg_card']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}

/* ---- Tooltip ---- */
QToolTip {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: {RADIUS['sm']}px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_stylesheet() -> str:
    """Return the global application stylesheet."""
    return GLOBAL_STYLESHEET


def get_card_style() -> str:
    """Return QSS for a card container widget."""
    return f"""
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']}px;
    """


def get_card_hover_style() -> str:
    """Return QSS for a card in hover state."""
    return f"""
        background-color: {COLORS['bg_elevated']};
        border: 1px solid {COLORS['primary']};
        border-radius: {RADIUS['md']}px;
    """


def get_gradient_button_style(color1: str = None, color2: str = None) -> str:
    """
    Return QSS for a gradient-style button.
    PyQt6 does not support CSS linear-gradient — this simulates it using
    the first color as background with a border matching the second.
    """
    c1 = color1 or COLORS['primary']
    c2 = color2 or COLORS['primary_light']
    return f"""
        QPushButton {{
            background-color: {c1};
            border: 1px solid {c2};
            border-radius: {RADIUS['md']}px;
            color: white;
            font-weight: 600;
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background-color: {c2};
            border-color: {c2};
        }}
        QPushButton:pressed {{
            background-color: {c1};
        }}
        QPushButton:disabled {{
            background-color: {COLORS['text_muted']};
            border-color: {COLORS['text_muted']};
        }}
    """


def get_glass_style() -> str:
    """Return QSS for a glassmorphism-style panel (semi-transparent dark)."""
    return f"""
        background-color: {COLORS['glass_bg']};
        border-top: 1px solid {COLORS['border_light']};
    """


def get_top_bar_style() -> str:
    """Return QSS for a top navigation bar, consistent across all views."""
    return f"""
        background-color: {COLORS['bg_card']};
        border-bottom: 1px solid {COLORS['border']};
    """


def get_danger_btn_style() -> str:
    """Return inline QSS for a danger button that shows on hover only."""
    return f"""
        QPushButton {{
            background-color: {COLORS['bg_surface']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_light']};
            border-radius: {RADIUS['md']}px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {COLORS['danger']};
            border-color: {COLORS['danger']};
            color: white;
        }}
    """


def get_record_btn_idle_style() -> str:
    """Return QSS for the record button in idle (not recording) state."""
    return f"""
        QPushButton {{
            background-color: {COLORS['bg_surface']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_light']};
            border-radius: {RADIUS['md']}px;
            padding: 10px 24px;
            font-weight: 600;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['bg_elevated']};
            border-color: {COLORS['primary']};
        }}
    """


def get_record_btn_active_style() -> str:
    """Return QSS for the record button in active (recording) state."""
    return f"""
        QPushButton {{
            background-color: {COLORS['bg_surface']};
            color: {COLORS['danger']};
            border: 2px solid {COLORS['danger']};
            border-radius: {RADIUS['md']}px;
            padding: 10px 24px;
            font-weight: 700;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 71, 87, 0.12);
            border-color: {COLORS['danger_hover']};
        }}
    """
