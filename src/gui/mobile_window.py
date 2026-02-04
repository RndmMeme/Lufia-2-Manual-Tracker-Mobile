from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QScrollArea, 
    QToolBar, QMessageBox, QFrame, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QAction, QIcon, QFont

import logging
from core.layout_manager import LayoutManager
from .map_widget import MapWidget
from .inventory_widgets import ToolsWidget, ScenarioWidget
from .widgets.items_widget import ItemsWidget
from .widgets.characters_widget import CharactersWidget
from .widgets.maiden_widget import MaidenWidget
from .widgets.hint_widget import HintWidget
from .widgets.hint_widget import HintWidget
from .widgets.item_search_widget import ItemSearchWidget
from .dialogs.item_search_dialog import ItemSearchDialog
from utils.constants import STATE_ORDER

class MobileMainWindow(QMainWindow):
    def __init__(self, state_manager, data_loader, logic_engine):
        super().__init__()
        self.state_manager = state_manager
        self.data_loader = data_loader
        self.logic_engine = logic_engine
        self.layout_manager = LayoutManager()
        
        self.setWindowTitle("Lufia 2 Tracker (Mobile)")
        self.resize(400, 800) # Phone-like aspect ratio
        
        self._setup_ui()
        self._connect_signals()
        
        # Initial Refresh
        self._load_settings()
        self._refresh_all()
        
    def _setup_ui(self):
        # 1. Main Container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setLayout(self.main_layout)
        
        # 2. Toolbar (Top) - Replaces Menu Bar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(32, 32)) # Larger icons for touch
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Toolbar Actions (Text for clear touch targets if icons missing)
        self.act_edit = QAction("Edit", self)
        self.act_edit.setCheckable(True)
        self.act_edit.toggled.connect(self._set_edit_mode)
        self.toolbar.addAction(self.act_edit)

        self.act_reset = QAction("Reset", self)
        self.act_reset.triggered.connect(self._handle_reset)
        self.toolbar.addAction(self.act_reset)
        
        self.act_save = QAction("Save", self)
        self.act_save.triggered.connect(self._handle_save)
        self.toolbar.addAction(self.act_save)
        
        self.act_load = QAction("Load", self)
        self.act_load.triggered.connect(self._handle_load)
        self.toolbar.addAction(self.act_load)
        
        # 3. Tab Widget (The Core Navigation)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                height: 50px; 
                font-size: 16px; 
                width: 90px;
            }
            QTabWidget::pane {
                border: none;
            }
        """)
        self.main_layout.addWidget(self.tabs)
        
        # --- Tab 1: Map ---
        self.map_container = QWidget()
        mc_layout = QVBoxLayout()
        mc_layout.setContentsMargins(0,0,0,0)
        self.map_container.setLayout(mc_layout)
        
        self.map_widget = MapWidget(self.data_loader)
        mc_layout.addWidget(self.map_widget)
        
        # Info Label (Replacement for Tooltip)
        self.lbl_info = QLabel("Tap a location for info")
        self.lbl_info.setStyleSheet("background-color: #222; color: #eee; padding: 10px; font-size: 14px;")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setFixedHeight(50)
        mc_layout.addWidget(self.lbl_info)
        
        self.tabs.addTab(self.map_container, "Map")
        
        # --- Tab 2: Inventory ---
        self.inv_container = QWidget()
        inv_layout = QVBoxLayout()
        # inv_layout.setContentsMargins(10, 10, 10, 10) # Mobile Padding
        self.inv_container.setLayout(inv_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.inv_container)
        
        # -- Inventory Sections --
        self._add_section_header(inv_layout, "Tools")
        self.tools_widget = ToolsWidget(self.data_loader, self.layout_manager)
        inv_layout.addWidget(self.tools_widget)

        self._add_section_header(inv_layout, "Keys / Scenario")
        self.scenario_widget = ScenarioWidget(self.data_loader, self.layout_manager)
        inv_layout.addWidget(self.scenario_widget)
        
        self._add_section_header(inv_layout, "Items / Spells")
        self.items_widget = ItemsWidget(self.state_manager)
        self.items_widget.setMinimumHeight(200) 
        inv_layout.addWidget(self.items_widget)
        
        inv_layout.addStretch() 
        
        self.tabs.addTab(scroll, "Items")
        
        # --- Tab 3: Characters ---
        self.chars_container = QWidget()
        chars_layout = QVBoxLayout()
        # chars_layout.setContentsMargins(10, 10, 10, 10)
        self.chars_container.setLayout(chars_layout)

        # Characters Widget (Scrollable Canvas)
        # Note: characters_widget already has a scroll area. 
        # Inside a VBoxLayout it might shrink awkwardly. 
        # We want it to take most space.
        self.characters_widget = CharactersWidget(self.data_loader, self.state_manager, self.layout_manager)
        chars_layout.addWidget(self.characters_widget)
        
        # Maidens (Moved here)
        # Maidens take little space (horizontal row). Put them at top? Or bottom?
        # User said "put the Maidens into the Chars tab". 
        # Usually they are less important? Let's put at Bottom for now or Top?
        # Tools/Keys were moved to top of Items. Maybe Maidens at Top of Chars?
        # Let's put at Top for visibility.
        self.maiden_widget = MaidenWidget(self.data_loader, self.state_manager, self.layout_manager)
        chars_layout.insertWidget(0, self.maiden_widget) # Insert at Top
        
        self.tabs.addTab(self.chars_container, "Chars")
        
        # --- Tab 4: Hints ---
        self.hint_widget = HintWidget()
        self.tabs.addTab(self.hint_widget, "Hints")

        # --- Tab 5: Add Item (Search) ---
        self.search_widget = ItemSearchWidget(self.data_loader, show_close_button=False)
        self.tabs.addTab(self.search_widget, "Add")

    def _add_section_header(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #81d4fa; margin-top: 10px; border-bottom: 1px solid #555;")
        layout.addWidget(lbl)

    def _connect_signals(self):
        # --- Reusing connections from Desktop MainWindow ---
        
        # State -> UI
        self.state_manager.location_changed.connect(self.map_widget.update_dot_color)
        self.state_manager.player_position_changed.connect(self.map_widget.update_player_position)
        
        self.tools_widget.connect_signals(self.state_manager)
        self.scenario_widget.connect_signals(self.state_manager)
        
        self.state_manager.inventory_changed.connect(lambda _: self._refresh_all())
        
        # UI -> State
        self.map_widget.location_clicked.connect(self._handle_location_click)
        self.map_widget.location_right_clicked.connect(self._handle_location_right_click)
        
        # Character Signals
        self.state_manager.character_assigned.connect(self._on_character_assigned)
        self.state_manager.character_unassigned.connect(self.map_widget.remove_character_sprite)
        self.state_manager.character_changed.connect(lambda n, o: self.characters_widget.refresh_state())
        
        self.map_widget.sprite_removed.connect(self.state_manager.remove_character_assignment)
        
        self.state_manager.reset_occurred.connect(self._on_reset_occurred)
        self.state_manager.shop_items_changed.connect(lambda _: self.items_widget.refresh_from_state())
        
        # Items Widget -> Switch to Search Tab
        self.items_widget.request_add_item.connect(lambda: self.tabs.setCurrentWidget(self.search_widget))
        
        # Search Widget -> Add Item
        self.search_widget.item_added.connect(lambda l, i: self.items_widget.add_item(l, i))
        
        # Hints
        self.hint_widget.hints_changed.connect(self.state_manager.update_hints)
        self.state_manager.hints_changed.connect(self.hint_widget.set_hints)
        
    # --- Handlers (Mostly reused) ---

    def _set_edit_mode(self, enabled: bool):
        """Toggles 'Edit Layout' mode for draggable widgets."""
        # Get the actual button widget required for styling
        btn = self.toolbar.widgetForAction(self.act_edit)
        
        if enabled:
            self.act_edit.setText("Done")
            if btn:
                btn.setStyleSheet("background-color: #4CAF50;") # Visual cue
        else:
            self.act_edit.setText("Edit")
            if btn:
                btn.setStyleSheet("")
            
        self.tools_widget.set_edit_mode(enabled)
        self.scenario_widget.set_edit_mode(enabled)
        self.characters_widget.set_edit_mode(enabled)
        self.maiden_widget.set_edit_mode(enabled)
    
    def _refresh_all(self):
        # Copied logic to update map colors
        accessibility = self.logic_engine.calculate_accessibility(self.state_manager.inventory)
        current_loc_states = self.state_manager.locations
        locations_data = self.data_loader.get_locations()
        
        for name in locations_data.keys():
            is_accessible = accessibility.get(name, False)
            is_cleared = (current_loc_states.get(name) == "cleared")
            
            final_color = self.logic_engine.determine_color(name, is_accessible, is_cleared)
            
            effective_state = current_loc_states.get(name)
            if effective_state:
                final_color = effective_state
            
            # TODO: Improve Tooltip handling for Mobile (Tap to show info?)
            # self.map_widget.update_dot_tooltip(name, ...)
            
            self.map_widget.update_dot_color(name, final_color)

    def _handle_location_click(self, name):
        # Update Info Label Logic
        accessibility = self.logic_engine.calculate_accessibility(self.state_manager.inventory)
        is_accessible = accessibility.get(name, False)
        
        info_text = name
        if not is_accessible:
             reqs = self.logic_engine.get_missing_requirements(name, self.state_manager.inventory)
             if reqs:
                 info_text += f"\nNeed: {' OR '.join(reqs)}"
        
        self.lbl_info.setText(info_text)
        
        # Cycle Logic
        current_state = self.state_manager.locations.get(name)
        cycle_order = list(STATE_ORDER)
        if name in self.data_loader.get_cities():
             cycle_order = ["city"]
        else:
             cycle_order = ["not_accessible", "fully_accessible", "cleared"]

        if not current_state or current_state not in cycle_order:
             new_state = cycle_order[0]
        else:
             idx = cycle_order.index(current_state)
             new_state = cycle_order[(idx + 1) % len(cycle_order)]
                
        self.state_manager.set_manual_location_state(name, new_state)

    def _handle_location_right_click(self, name):
         # On Mobile, this comes from Long Press or Right Click emulation
         # We reuse the logic, but maybe we need a bigger Context Menu?
         # QMenu works fine on Android usually.
         
        cities = self.data_loader.get_cities()
        if name in cities:
            self._open_item_search(name)
        else:
            self._open_character_assignment(name)

    def _open_character_assignment(self, location_name):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        # Larger font for menu
        menu.setStyleSheet("font-size: 16px; padding: 10px;")
        menu.setTitle(f"Assign: {location_name}")
        
        chars_data = self.data_loader.load_json("characters.json")
        sorted_names = sorted(chars_data.keys())
        assigned_chars = set(self.state_manager._character_locations.values())

        for char in sorted_names:
            if char in ["Claire", "Lisa", "Marie"]: continue
            if char in assigned_chars: continue
                
            action = menu.addAction(char)
            action.triggered.connect(lambda c, ch=char: self.state_manager.assign_character_to_location(location_name, ch))
        
        existing = self.state_manager.get_character_at_location(location_name)
        if existing:
            menu.addSeparator()
            rem_action = menu.addAction(f"Remove {existing}")
            rem_action.triggered.connect(lambda: self.state_manager.remove_character_assignment(location_name))
            
        menu.exec(self.map_widget.cursor().pos())

    def _on_character_assigned(self, location, name):
        # Reused
        chars_data = self.data_loader.load_json("characters.json")
        if name not in chars_data: return
        rel_path = chars_data[name]["image_path"]
        full_path = self.data_loader.resolve_image_path(rel_path)
        self.map_widget.add_character_sprite(location, name, full_path)

    def _open_item_search(self, location_name):
        dlg = ItemSearchDialog(location_name, self.data_loader, parent=self)
        dlg.item_added.connect(lambda l, i: self.items_widget.add_item(l, i))
        # Maximize dialog for mobile
        dlg.showMaximized()
        dlg.exec()

    def _handle_reset(self):
        self.state_manager.reset_state()
    
    def _on_reset_occurred(self):
        if self.hint_widget: self.hint_widget.set_hints("")
        if self.map_widget: self.map_widget.reset()
        if self.items_widget: self.items_widget.clear_all()
        self._refresh_all()

    def _handle_save(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "JSON (*.json)")
        if path: self.state_manager.save_state(path)

    def _handle_load(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Load", "", "JSON (*.json)")
        if path:
            self.state_manager.load_state(path)
            self._refresh_all()
            
    def _load_settings(self):
        # Persistence less critical for prototype, but basic load OK
        pass

