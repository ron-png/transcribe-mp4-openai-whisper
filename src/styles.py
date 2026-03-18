"""
Premium dark theme stylesheet for the application.

Provides a modern, visually appealing dark UI with accent colors,
smooth hover states, and consistent styling across all platforms.
"""

# Color palette
COLORS = {
    "bg_primary": "#0f0f14",
    "bg_secondary": "#1a1a24",
    "bg_tertiary": "#24243a",
    "bg_hover": "#2e2e48",
    "bg_input": "#16162a",
    "border": "#2a2a44",
    "border_focus": "#6c5ce7",
    "text_primary": "#e8e8f0",
    "text_secondary": "#8888aa",
    "text_muted": "#555577",
    "accent": "#6c5ce7",
    "accent_hover": "#7f70f0",
    "accent_pressed": "#5a4bd4",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#e74c3c",
    "progress_bg": "#1a1a2e",
    "progress_chunk": "#6c5ce7",
    "scrollbar_bg": "#16162a",
    "scrollbar_handle": "#3a3a5a",
}


def get_stylesheet() -> str:
    """Return the complete QSS stylesheet for the application."""
    c = COLORS
    return f"""
    /* ═══════════════════════════════════════════════════════════
       GLOBAL
       ═══════════════════════════════════════════════════════════ */
    QWidget {{
        background-color: {c['bg_primary']};
        color: {c['text_primary']};
        font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }}

    /* ═══════════════════════════════════════════════════════════
       MAIN WINDOW
       ═══════════════════════════════════════════════════════════ */
    QMainWindow {{
        background-color: {c['bg_primary']};
    }}

    /* ═══════════════════════════════════════════════════════════
       LABELS
       ═══════════════════════════════════════════════════════════ */
    QLabel {{
        background-color: transparent;
        color: {c['text_primary']};
    }}

    QLabel#titleLabel {{
        font-size: 22px;
        font-weight: bold;
        color: {c['text_primary']};
    }}

    QLabel#subtitleLabel {{
        font-size: 12px;
        color: {c['text_secondary']};
    }}

    QLabel#statusLabel {{
        font-size: 12px;
        color: {c['text_secondary']};
        padding: 4px 0px;
    }}

    QLabel#modelStatusLabel {{
        font-size: 11px;
        color: {c['accent']};
        padding: 2px 8px;
        border: 1px solid {c['border']};
        border-radius: 10px;
        background-color: {c['bg_tertiary']};
    }}

    QLabel#deviceLabel {{
        font-size: 11px;
        color: {c['success']};
        padding: 2px 8px;
        border: 1px solid {c['border']};
        border-radius: 10px;
        background-color: {c['bg_tertiary']};
    }}

    QLabel#fileCountLabel {{
        font-size: 11px;
        color: {c['text_secondary']};
        padding: 2px 8px;
        border: 1px solid {c['border']};
        border-radius: 10px;
        background-color: {c['bg_tertiary']};
    }}

    QLabel#sectionLabel {{
        font-size: 14px;
        font-weight: 600;
        color: {c['text_primary']};
        padding: 4px 0px;
    }}

    QLabel#dropHintLabel {{
        font-size: 15px;
        color: {c['text_muted']};
        padding: 40px;
    }}

    /* ═══════════════════════════════════════════════════════════
       BUTTONS
       ═══════════════════════════════════════════════════════════ */
    QPushButton {{
        background-color: {c['bg_tertiary']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        min-height: 18px;
    }}

    QPushButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['accent']};
    }}

    QPushButton:pressed {{
        background-color: {c['accent_pressed']};
    }}

    QPushButton:disabled {{
        background-color: {c['bg_secondary']};
        color: {c['text_muted']};
        border-color: {c['bg_secondary']};
    }}

    QPushButton#primaryButton {{
        background-color: {c['accent']};
        color: white;
        border: none;
        font-weight: 600;
        padding: 10px 24px;
        font-size: 14px;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {c['accent_hover']};
    }}

    QPushButton#primaryButton:pressed {{
        background-color: {c['accent_pressed']};
    }}

    QPushButton#primaryButton:disabled {{
        background-color: {c['bg_tertiary']};
        color: {c['text_muted']};
    }}

    QPushButton#dangerButton {{
        background-color: transparent;
        color: {c['error']};
        border: 1px solid {c['error']};
    }}

    QPushButton#dangerButton:hover {{
        background-color: {c['error']};
        color: white;
    }}

    /* ═══════════════════════════════════════════════════════════
       TABLE / QUEUE VIEW
       ═══════════════════════════════════════════════════════════ */
    QTableWidget {{
        background-color: {c['bg_secondary']};
        alternate-background-color: {c['bg_primary']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        gridline-color: {c['border']};
        selection-background-color: {c['bg_tertiary']};
        selection-color: {c['text_primary']};
        font-size: 12px;
    }}

    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid {c['border']};
    }}

    QTableWidget::item:selected {{
        background-color: {c['bg_tertiary']};
    }}

    QHeaderView::section {{
        background-color: {c['bg_tertiary']};
        color: {c['text_secondary']};
        padding: 8px 10px;
        border: none;
        border-bottom: 2px solid {c['accent']};
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
    }}

    /* ═══════════════════════════════════════════════════════════
       PROGRESS BAR
       ═══════════════════════════════════════════════════════════ */
    QProgressBar {{
        background-color: {c['progress_bg']};
        border: 1px solid {c['border']};
        border-radius: 5px;
        text-align: center;
        color: {c['text_secondary']};
        font-size: 11px;
        min-height: 12px;
        max-height: 12px;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent']}, stop:1 {c['accent_hover']}
        );
        border-radius: 4px;
    }}

    /* ═══════════════════════════════════════════════════════════
       TEXT EDIT / LOG PANEL
       ═══════════════════════════════════════════════════════════ */
    QTextEdit {{
        background-color: {c['bg_input']};
        color: {c['text_secondary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px;
        font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", monospace;
        font-size: 11px;
        selection-background-color: {c['accent']};
    }}

    /* ═══════════════════════════════════════════════════════════
       COMBO BOX
       ═══════════════════════════════════════════════════════════ */
    QComboBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 20px;
    }}

    QComboBox:hover {{
        border-color: {c['accent']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['bg_secondary']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent']};
        padding: 4px;
    }}

    /* ═══════════════════════════════════════════════════════════
       SPIN BOX
       ═══════════════════════════════════════════════════════════ */
    QSpinBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 12px;
    }}

    QSpinBox:hover {{
        border-color: {c['accent']};
    }}

    QDoubleSpinBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 12px;
    }}

    QDoubleSpinBox:hover {{
        border-color: {c['accent']};
    }}

    /* ═══════════════════════════════════════════════════════════
       CHECK BOX
       ═══════════════════════════════════════════════════════════ */
    QCheckBox {{
        color: {c['text_primary']};
        spacing: 8px;
        background-color: transparent;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {c['border']};
        border-radius: 4px;
        background-color: {c['bg_input']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {c['accent']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}

    /* ═══════════════════════════════════════════════════════════
       DIALOG
       ═══════════════════════════════════════════════════════════ */
    QDialog {{
        background-color: {c['bg_primary']};
    }}

    QGroupBox {{
        background-color: {c['bg_secondary']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        margin-top: 16px;
        padding: 16px;
        padding-top: 24px;
        font-weight: 600;
        color: {c['text_primary']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {c['accent']};
    }}

    /* ═══════════════════════════════════════════════════════════
       SCROLLBAR
       ═══════════════════════════════════════════════════════════ */
    QScrollBar:vertical {{
        background-color: {c['scrollbar_bg']};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c['scrollbar_handle']};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c['accent']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background-color: {c['scrollbar_bg']};
        height: 10px;
        border-radius: 5px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c['scrollbar_handle']};
        border-radius: 5px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {c['accent']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ═══════════════════════════════════════════════════════════
       SPLITTER
       ═══════════════════════════════════════════════════════════ */
    QSplitter::handle {{
        background-color: {c['border']};
    }}

    QSplitter::handle:horizontal {{
        width: 1px;
    }}

    QSplitter::handle:vertical {{
        height: 1px;
    }}

    /* ═══════════════════════════════════════════════════════════
       TOOLTIP
       ═══════════════════════════════════════════════════════════ */
    QToolTip {{
        background-color: {c['bg_tertiary']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* ═══════════════════════════════════════════════════════════
       LINE EDIT / FILE PATH INPUT
       ═══════════════════════════════════════════════════════════ */
    QLineEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 12px;
    }}

    QLineEdit:focus {{
        border-color: {c['border_focus']};
    }}

    /* ═══════════════════════════════════════════════════════════
       TAB WIDGET
       ═══════════════════════════════════════════════════════════ */
    QTabWidget {{
        background-color: {c['bg_primary']};
        border: none;
    }}

    QTabWidget::pane {{
        background-color: {c['bg_primary']};
        border: 1px solid {c['border']};
        border-top: none;
        border-radius: 0 0 6px 6px;
    }}

    QTabBar::tab {{
        background-color: {c['bg_secondary']};
        color: {c['text_secondary']};
        border: 1px solid {c['border']};
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 8px 18px;
        margin-right: 2px;
        font-size: 12px;
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        background-color: {c['bg_primary']};
        color: {c['accent']};
        border-bottom: 2px solid {c['accent']};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {c['bg_hover']};
        color: {c['text_primary']};
    }}
    """
