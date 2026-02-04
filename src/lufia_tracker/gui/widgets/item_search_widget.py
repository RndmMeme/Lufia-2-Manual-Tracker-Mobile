from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QListWidget, QListWidgetItem, QLabel, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

class ItemSearchWidget(QWidget):
    """
    Reusable widget for searching and adding items/spells.
    Can be embedded in a Dialog or a collapsible panel.
    """
    item_added = pyqtSignal(str, str) # location, item_name
    close_requested = pyqtSignal() # Request parent to hide this widget

    def __init__(self, data_loader, initial_location="Artea", show_close_button=True, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.location = initial_location
        self.show_close_button = show_close_button
        self.item_spells = data_loader.get_items_spells()
        self.all_categories = list(self.item_spells.keys())
        self.current_category = self.all_categories[0] if self.all_categories else ""
        
        self.init_ui()
        self.load_list()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # --- Top Row: Label, City Picker, Close Button ---
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 5, 0, 5)
        
        if self.show_close_button:
            # Red Minus Button (Close)
            self.btn_close = QPushButton("-")
            self.btn_close.setFixedSize(30, 30)
            self.btn_close.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F; 
                    color: white; 
                    font-weight: bold; 
                    border-radius: 4px;
                    font-size: 18px;
                }
                QPushButton:hover {
                    background-color: #F44336;
                }
            """)
            self.btn_close.clicked.connect(self.close_requested.emit)
            top_layout.addWidget(self.btn_close)

        top_layout.addWidget(QLabel("Add to:"))
        
        # Location Selector (City Picker)
        self.loc_combo = QComboBox()
        self.loc_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cities = sorted(self.data_loader.get_cities())
        self.loc_combo.addItems(cities)
        
        # Set initial selection
        index = self.loc_combo.findText(self.location)
        if index >= 0:
            self.loc_combo.setCurrentIndex(index)
            
        self.loc_combo.currentTextChanged.connect(self._on_location_changed)
        top_layout.addWidget(self.loc_combo)
        
        layout.addLayout(top_layout)
        
        # --- Categories ---
        cat_layout = QHBoxLayout()
        self.cat_buttons = []
        for cat in self.all_categories:
            label = cat
            if cat == "is Treasure":
                label = "Iris Items"
            
            btn = QPushButton(label)
            btn.setCheckable(True)
            # Mobile friendly styling
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px;
                    background-color: #444;
                    color: white;
                    border: 1px solid #222;
                }
                QPushButton:checked {
                    background-color: #666;
                    border: 1px solid #888;
                }
            """)
            btn.clicked.connect(lambda checked, c=cat: self.change_category(c))
            cat_layout.addWidget(btn)
            self.cat_buttons.append(btn)
        layout.addLayout(cat_layout)
        
        self.update_cat_buttons()
        
        # --- Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search item name...")
        self.search_bar.setStyleSheet("padding: 5px; font-size: 14px;")
        self.search_bar.textChanged.connect(self.filter_list)
        self.search_bar.returnPressed.connect(self.add_selected)
        layout.addWidget(self.search_bar)
        
        # --- List ---
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("font-size: 14px;")
        self.list_widget.itemDoubleClicked.connect(self.add_selected)
        # Single click to add? For mobile double click is hard sometimes.
        # But single click might cause accidental adds while scrolling.
        # Stick to double click or explicit "Add" button if needed. 
        # Or maybe add a "Tap to Add" mode.
        layout.addWidget(self.list_widget)

    def update_cat_buttons(self):
        for btn in self.cat_buttons:
            # We map back label to category to check? Or store ref.
            # We stored ref in list.
            # Oh wait, we need to match text/label.
            # Simplified:
            is_match = False
            if btn.text() == "Iris Items" and self.current_category == "is Treasure":
                is_match = True
            elif btn.text() == self.current_category:
                is_match = True
            
            btn.setChecked(is_match)
            if is_match:
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px;
                        background-color: #007ACC; 
                        color: white;
                        border: 1px solid #888;
                    }
                """)
            else:
                 btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px;
                        background-color: #444;
                        color: white;
                        border: 1px solid #222;
                    }
                """)

    def change_category(self, category):
        self.current_category = category
        self.update_cat_buttons()
        self.load_list()

    def load_list(self):
        self.list_widget.clear()
        query = self.search_bar.text().lower()
        items = self.item_spells.get(self.current_category, {})
        
        source_list = []
        if isinstance(items, dict):
            source_list = list(items.values())
        elif isinstance(items, list):
            source_list = items
        
        filtered_items = []
        for item_name in source_list:
            if isinstance(item_name, dict):
                item_name = item_name.get('name', '')
            if query in str(item_name).lower():
                filtered_items.append(str(item_name))
        
        filtered_items.sort()
        for name in filtered_items:
            self.list_widget.addItem(name)
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_list(self):
        self.load_list()

    def add_selected(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            self.item_added.emit(self.location, item.text())
        
        # Advance selection
        nrow = self.list_widget.currentRow()
        if nrow < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(nrow + 1)

    def _on_location_changed(self, new_location):
        self.location = new_location

    def set_location(self, location):
        """Programmatic update"""
        index = self.loc_combo.findText(location)
        if index >= 0:
            self.loc_combo.setCurrentIndex(index)
