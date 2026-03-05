"""
WebCap Design System - Dark Mode with Neomorphic Elements
"""

COLORS = {
    'bg_main': '#1a1a1a',
    'bg_card': '#242424',
    'bg_surface': '#2a2a2a',
    'primary': '#007AFF',
    'primary_hover': '#0066DD',
    'text_primary': '#FFFFFF',
    'text_secondary': '#A0A0A0',
    'border': '#333333',
    'shadow': 'rgba(0, 0, 0, 0.5)',
    'highlight': 'rgba(255, 255, 255, 0.05)',
    'danger': '#FF3B30',
    'success': '#34C759',
}

GLOBAL_STYLESHEET = f"""
QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
}}

QPushButton {{
    background-color: {COLORS['bg_surface']};
    color: {COLORS['text_primary']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_card']};
    border-color: {COLORS['primary']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_main']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_secondary']};
    border-color: {COLORS['bg_surface']};
}}

QPushButton#primary {{
    background-color: {COLORS['primary']};
    border: 2px solid {COLORS['primary']};
    color: white;
    font-weight: 600;
}}

QPushButton#primary:hover {{
    background-color: {COLORS['primary_hover']};
    border-color: {COLORS['primary_hover']};
}}

QPushButton#danger {{
    background-color: {COLORS['danger']};
    border: 2px solid {COLORS['danger']};
    color: white;
    font-weight: 600;
}}

QPushButton#danger:hover {{
    background-color: #E6342A;
    border-color: #E6342A;
}}

QLabel {{
    background-color: transparent;
    color: {COLORS['text_primary']};
}}

QLabel#secondary {{
    color: {COLORS['text_secondary']};
}}

QLabel#title {{
    font-size: 24px;
    font-weight: bold;
}}

QLabel#timer {{
    font-size: 18px;
    font-family: 'SF Mono', 'Monaco', monospace;
    font-weight: 600;
}}

QListWidget {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px;
    outline: none;
}}

QListWidget::item {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    padding: 12px;
    border-radius: 6px;
    margin: 2px 0;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_surface']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QSlider::groove:horizontal {{
    background: {COLORS['bg_surface']};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['primary']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['primary']};
    border-radius: 3px;
}}

QLineEdit {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QSpinBox {{
    background-color: {COLORS['bg_surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
    color: {COLORS['text_primary']};
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color: {COLORS['bg_surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['primary']};
}}

QMessageBox {{
    background-color: {COLORS['bg_card']};
}}

QDialog {{
    background-color: {COLORS['bg_card']};
}}
"""

def get_stylesheet():
    return GLOBAL_STYLESHEET
