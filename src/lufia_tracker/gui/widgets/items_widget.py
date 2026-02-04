from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class AddedItemEntry(QWidget):
    """
    Represents a single row in the Added Items list: "Location: Itemname [x]"
    """
    remove_requested = pyqtSignal(str, str) # location, item_name

    def __init__(self, location, item_name, parent=None, font_size=11):
        super().__init__(parent)
        self.location = location
        self.item_name = item_name
        self.font_size = font_size
        
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # Text
        self.label = QLabel(f"{location}: {item_name}")
        self.label.setStyleSheet(f"color: white; font-family: Arial; font-size: {font_size}px;")
        layout.addWidget(self.label)
        
        layout.addStretch()
        
        # Remove Button (x)
        self.btn_remove = QPushButton("x")
        self.btn_remove.setFixedSize(20, 20)
        self.btn_remove.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: red;
            }
        """)
        self.btn_remove.clicked.connect(self._on_remove)
        layout.addWidget(self.btn_remove)

    def update_font_size(self, size):
        self.font_size = size
        self.label.setStyleSheet(f"color: white; font-family: Arial; font-size: {size}px;")
        
    def _on_remove(self):
        self.remove_requested.emit(self.location, self.item_name)

from .item_search_widget import ItemSearchWidget

class ItemsWidget(QWidget):
    """
    Refactor of the v1.3 Item Canvas list.
    Displays added items/spells.
    Includes Sort and Clear buttons.
    """
    def __init__(self, state_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        
        # Data storage
        # entry = {'location': str, 'name': str, 'category': str}
        self.entries = [] 
        
        self.init_ui()
        self.connect_signals()
        
    request_add_item = pyqtSignal()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # -- Search Panel (Collapsible) --
        # We need DataLoader... but ItemsWidget doesn't have it passed in init usually?
        # Check usages. MobileWindow passes only state_manager.
        # MainWindow passes only state_manager.
        # BUT state_manager has logic_engine has data_loader? No, logic_engine has it.
        # We might need to pass data_loader to ItemsWidget now.
        # For now, let's assume we can get it or fail gracefully.
        
        # WAIT: The tool calls below will fix the init to accept DataLoader.
        
        # -- Header / Buttons --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        
        self.btn_add = QPushButton("+") 
        self.btn_sort_loc = QPushButton("Sort Loc")
        self.btn_sort_item = QPushButton("Sort Item")
        self.btn_clear = QPushButton("Clear")
        
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px;
                font-size: 14px;
                padding: 2px 10px;
            }
        """)

        for btn in [self.btn_sort_loc, self.btn_sort_item, self.btn_clear]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: black;
                    color: white;
                    border: 1px solid #555;
                    font-size: 10px;
                    padding: 2px;
                }
                QPushButton:hover {
                    border: 1px solid #888;
                }
            """)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_sort_loc)
        btn_layout.addWidget(self.btn_sort_item)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        
        # Placeholder for Search Widget (inserted dynamically or initialized if data_loader present)
        self.search_container = QWidget()
        self.search_layout = QVBoxLayout()
        self.search_layout.setContentsMargins(0,0,0,0)
        self.search_container.setLayout(self.search_layout)
        self.search_container.hide()
        layout.addWidget(self.search_container)

        # -- List Area --
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #2b2b2b; border: none;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.setSpacing(2)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.list_container.setLayout(self.list_layout)
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)
        
        # Button Logic
        # self.btn_add.clicked.connect(...) -> Handle internally now
        self.btn_add.clicked.connect(self.toggle_search_panel)
        self.btn_sort_loc.clicked.connect(self.sort_by_location)
        self.btn_sort_item.clicked.connect(self.sort_by_item)
        self.btn_clear.clicked.connect(self.clear_all)

    def set_data_loader(self, data_loader):
        """Late initialization of search widget if data_loader wasn't available at init."""
        self.data_loader = data_loader
        # Init search widget
        self.search_widget = ItemSearchWidget(data_loader)
        self.search_widget.item_added.connect(self.add_item)
        self.search_widget.close_requested.connect(self.hide_search_panel)
        self.search_layout.addWidget(self.search_widget)
        
    def toggle_search_panel(self):
        if self.search_container.isVisible():
            self.hide_search_panel()
        else:
            self.show_search_panel()
            
    def show_search_panel(self):
        if hasattr(self, 'search_widget'):
            self.search_container.show()
            self.btn_add.setStyleSheet("background-color: #666; color: #aaa; border: 1px solid #444;") # Disabled look
            self.btn_add.setEnabled(False) # Disable + when open, use - to close
        else:
            # Fallback for old signal usage if data loader not set
            self.request_add_item.emit()

    def hide_search_panel(self):
        self.search_container.hide()
        self.btn_add.setEnabled(True)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px;
                font-size: 14px;
                padding: 2px 10px;
            }
        """)

    def connect_signals(self):
        # We need a signal from StateManager when an item is added via search
        # Currently StateManager treats inventory as a dict {name: bool}.
        # But this "Shop Items" list works differently?
        # In v1.3 "Item/Spells" are added to a text list.
        # This list IS the "inventory" for shop items.
        pass

    def add_item(self, location, item_name):
        """Adds a new item entry."""
        # Use StateManager as source of truth
        self.state_manager.register_shop_item(location, item_name)
        # self.refresh_list() # Signal will trigger refresh
        
    def refresh_from_state(self):
        self.entries = self.state_manager.shop_items
        self.refresh_list()
        
    def refresh_list(self):
        # Clear layout
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Rebuild
        font_size = getattr(self, 'current_font_size', 11)
        for entry in self.entries:
            row = AddedItemEntry(entry['location'], entry['name'], font_size=font_size)
            row.remove_requested.connect(self.remove_item)
            self.list_layout.addWidget(row)
            
    def remove_item(self, location, item_name):
        self.entries = [e for e in self.entries if not (e['name'] == item_name and e['location'] == location)]
        self.refresh_list()
        
    def sort_by_location(self):
        self.entries.sort(key=lambda x: x['location'])
        self.refresh_list()
        
    def sort_by_item(self):
        self.entries.sort(key=lambda x: x['name'])
        self.refresh_list()
        
    def clear_all(self):
        self.entries.clear()
        self.refresh_list()

    def set_content_font_size(self, size):
        self.current_font_size = size
        # Update existing
        for i in range(self.list_layout.count()):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, AddedItemEntry):
                widget.update_font_size(size)
                
    def refresh_list(self):
        # Clear layout
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Rebuild
        font_size = getattr(self, 'current_font_size', 11)
        for entry in self.entries:
            row = AddedItemEntry(entry['location'], entry['name'], font_size=font_size)
            row.remove_requested.connect(self.remove_item)
            self.list_layout.addWidget(row)
