"""
stylesheet.py

Defines the application's global Qt stylesheet.
"""
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon
from utils.theme import get_theme


def build_global_stylesheet():
    """
    Construct the application's style sheet allowing
    for light and dark themes.
    """
    t = get_theme()

    return f"""
    QWidget#mainWindow {{
        background-color: {t.BG_MAIN};
    }}

    QFrame {{
        background: transparent;
    }}
    
    QLabel.loginError {{
        color: #e04f4f;
        font-size: 12pt;
        font-weight: 600;
    }}

    QFrame#topBar {{
        background-color: {t.BG_CARD};
        border-radius: 20px;
    }}
    
    QLabel#topBarTitle {{
        color: {t.PRIMARY_BTN};
        font-size: 32pt;
        font-weight: 600;
        letter-spacing: 0.8px;
        font-family: "Franklin Gothic Medium";
    }}
        
    QMessageBox {{
        background-color: {t.BG_CARD};
    }}

    QMessageBox QLabel {{
        color: {t.TEXT_PRIMARY};
    }}

    QFrame#card {{
        background-color: {t.BG_CARD};
        border-radius: 28px;
    }}
    
    QFrame#dbcard {{
        background-color: {t.BG_CARD};
        border-radius: 24px;
    }}
    
    QFrame#filterBar {{
        background-color: {t.BG_CARD};
        border-radius: 16px;
    }} 
    
    QFrame#filterBar QLineEdit,
    QFrame#filterBar QComboBox {{
        background-color: {t.BG_MAIN};
        color: {t.TEXT_PRIMARY};
        border-radius: 14px;
        padding: 6px 10px;
        border: 1px solid rgba(255,255,255,0.06);
    }}

    QFrame#filterBar QComboBox {{
        padding-right: 20px;
    }}

    QFrame#filterBar QComboBox QAbstractItemView {{
        background-color: {t.BG_CARD};
        color: {t.TEXT_PRIMARY};
        selection-background-color: {t.PRIMARY_BTN};
    }}
    
    QFrame#filterBar QCheckBox {{
        color: {t.TEXT_PRIMARY};
        spacing: 6px;
    }}

    QFrame#filterBar QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.15);
        background-color: {t.BG_MAIN};
    }}

    QFrame#filterBar QCheckBox::indicator:checked {{
        background-color: {t.PRIMARY_BTN};
    }}
 
    QFrame#eventPanel {{
        background-color: {t.BG_CARD};
        border-radius: 28px;
    }}

    QFrame#eventPanel QScrollArea,
    QFrame#eventPanel QScrollArea > QWidget,
    QFrame#eventPanel QScrollArea > QWidget > QWidget {{
        background-color: {t.BG_CARD};
    }}

    QFrame#eventCard {{
        border-radius: 14px;
    }}

    QFrame#eventCard[severity="info"] {{
        background-color: #4f7fd9;
    }}
    QFrame#eventCard[severity="success"] {{
        background-color: #2Fa36b;
    }}
    QFrame#eventCard[severity="warning"] {{
        background-color: #d49a2a;
    }}
    QFrame#eventCard[severity="error"] {{
        background-color: #d25555;
    }}
    
    QLabel#eventTimestamp {{
        font-size: 9pt;
        font-weight: 600;
    }}

    QLabel#eventMessage {{
        font-size: 9pt;
    }}
    
    QFrame#logCardStrip {{
        border-radius: 24px;
    }}
    
    QLabel.logHeading {{
    font-weight: 600;
    }}

    QLabel#logAction {{
        font-size: 11pt;
    }}

    QLabel#logCategory,
    QLabel#logInfoTitle {{
        font-size: 9pt;
    }}
    
    QFrame#logCard {{
        background-color: {t.BG_CARD};
        border-radius: 22px;
    }}
    
    QFrame#logCardStrip[category="authentication"] {{
        background-color: #e86615;
    }}

    QFrame#logCardStrip[category="search"] {{
        background-color: #2fa36b;
    }}

    QFrame#logCardStrip[category="database"] {{
        background-color: #0f9e05;
    }}

    QFrame#logCardStrip[category="security"] {{
        background-color: #d25555;
    }}

    QFrame#logCardStrip[category="system"] {{
        background-color: #4f7fd9;
    }}
    
    QFrame#logCardStrip[category="analytics"] {{
        background-color: #cf13ac;
    }}
    
    QFrame#noteCard {{
        background-color: {t.BG_MAIN};
        border-radius: 14px;
    }}
    
    QTextEdit#noteEditor,
    QLineEdit#noteEditor {{
        background-color: {t.BG_MAIN};
        color: {t.TEXT_PRIMARY};
        border-radius: 14px;
        padding: 8px;
        border: 1px solid rgba(255,255,255,0.06);
    }}


    QWidget#profilePage {{
        background-color: {t.BG_MAIN};
    }}
    
    QFrame#profileHeader,
    QFrame#profileImagePanel,
    QFrame#profileNotesPanel {{
        background-color: {t.BG_CARD};
        border-radius: 24px;
    }}
    
    QScrollArea#profileLeftScroll {{
        background: transparent;
        border: none;
    }}

    QWidget#profileLeftViewport {{
        background: transparent;
    }}

    QFrame#settingsCard {{
        background-color: {t.BG_MAIN};
        border-radius: 20px;
    }}

    QLabel#settingsTitle {{
        color: {t.TEXT_PRIMARY};
        font-size: 14pt;
        font-weight: 600;
    }}

    QLabel#settingsSectionLabel {{
        color: {t.TEXT_PRIMARY};
    }}
    
    QFrame.settingsRow {{
        background-color: {t.BG_CARD};
        border-radius: 12px;
    }}
    
    QDialog#helpBackground {{
    background-color: {t.BG_CARD};
    }}
    
    QLabel.section {{
        font-size: 11pt;
        font-weight: 600;
        color: {t.TEXT_PRIMARY};
    }}
        
    QPushButton {{
        color: {t.TEXT_PRIMARY};
    }}

    QPushButton#primaryButton {{
        background-color: {t.PRIMARY_BTN};
        color: white;
        border-radius: 22px;
        font-size: 11pt;
        font-weight: bold;
        padding: 6px 12px;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {t.PRIMARY_HOVER};
    }}

    QPushButton#iconButton {{
        border-radius: 18px;
        background: transparent;
    }}

    QLabel {{
        color: {t.TEXT_PRIMARY};
    }}

    QLabel.secondary {{
        color: {t.TEXT_SECONDARY};
        font-size: 9pt; 
    }}
    
    QLabel.title {{
        font-size: 14pt;
        font-weight: 600;
    }}
    
    QLabel.score {{  
        font-size: 12pt;
        font-weight: 600;
    }}

    QComboBox {{
        background-color: {t.BG_CARD};
        color: {t.TEXT_PRIMARY};
        border-radius: 10px;
        padding: 6px;
    }}

    QCheckBox {{
        color: {t.TEXT_PRIMARY};
        spacing: 8px;
    }}

    QScrollArea {{
        background-color: {t.BG_MAIN};
        border: none;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: {t.BG_MAIN};
    }}
    """


def make_icon_button(icon_path, size=48):
    """
    Creates a standardised icon button widget.
    Used for top bar buttons.
    """
    btn = QPushButton()
    btn.setFixedSize(size, size)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setIcon(QIcon(icon_path))
    btn.setIconSize(QSize(size, size))
    btn.setObjectName("iconButton")
    return btn