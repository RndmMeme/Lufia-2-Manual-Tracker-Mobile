import sys
import logging
from PyQt6.QtWidgets import QApplication
from gui.mobile_window import MobileMainWindow
from core.data_loader import DataLoader
from core.logic_engine import LogicEngine
from core.state_manager import StateManager

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lufia 2 Mobile Tracker")
    app.setStyle("Fusion")
    
    # Global Dark Theme (Mobile Optimized)
    # Larger scrollbars, larger text base
    app.setStyleSheet("""
        QMainWindow, QWidget, QTabWidget {
            background-color: #2b2b2b;
            color: #eeeeee;
            font-size: 14px;
        }
        QLineEdit, QTextEdit, QListWidget, QScrollArea {
            background-color: #2b2b2b;
            color: #eeeeee;
            border: 1px solid #444;
        }
        QTabBar::tab {
            background: #444;
            color: #ccc;
            padding: 10px;
            margin: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #2b2b2b;
            color: #81d4fa;
            border-bottom: 2px solid #81d4fa;
        }
        QToolBar {
            background: #333;
            border-bottom: 2px solid #555;
            padding: 5px;
        }
        QToolBar QToolButton {
            background: #444;
            color: white;
            border-radius: 4px;
            padding: 5px;
            margin: 2px;
            width: 60px; /* Wide buttons for touch */
        }
        QToolBar QToolButton:pressed {
            background: #666;
        }
        /* Mobile Scrollbars */
        QScrollBar:vertical {
            border: none;
            background: #2b2b2b;
            width: 25px; /* Wider for touch */
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            min-height: 40px;
            border-radius: 10px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    """)
    
    # Core Components
    data_loader = DataLoader()
    logic_engine = LogicEngine(data_loader)
    state_manager = StateManager(logic_engine)
    
    # GUI
    window = MobileMainWindow(state_manager, data_loader, logic_engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
