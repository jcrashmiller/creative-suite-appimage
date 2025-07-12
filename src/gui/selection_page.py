#!/usr/bin/env python3
"""
Linux Bundle Installer - Application Selection Page (PySide2 Version)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Ported to PySide2: 2025-07-12
"""

from pathlib import Path
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QCheckBox, QGroupBox, QTextEdit,
    QMessageBox, QSizePolicy
)
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QFont, QPixmap

from gui.base_page import BasePage
from core.bundle_state_detector import BundleStateDetector

class ModernButton(QPushButton):
    """Modern styled button"""
    def __init__(self, text, button_type="normal", parent=None):
        super().__init__(text, parent)
        
        if button_type == "danger":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)

class AppEntryWidget(QFrame):
    """Custom widget for each application entry"""
    
    def __init__(self, app_data, is_currently_installed, config, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.is_currently_installed = is_currently_installed
        self.config = config
        
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                margin: 4px;
            }
            QFrame:hover {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Checkbox
        self.checkbox = QCheckBox()
        # Set initial state
        if self.is_currently_installed:
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(self.app_data.get('default_selected', False))
        layout.addWidget(self.checkbox)
        
        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(60, 60)  # Larger container for breathing room
        
        # Load icon
        icon_pixmap = self.load_app_icon()
        if icon_pixmap:
            scaled_pixmap = icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)  # Center the 32px icon in the 60px container
        else:
            icon_label.setStyleSheet("background-color: #e0e0e0; border-radius: 6px; font-size: 18px;")
            icon_label.setText("📱")
            icon_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(icon_label)
        
        # App info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # App name
        name_label = QLabel(self.app_data.get('name', 'Unknown'))
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)
        
        # Description
        description = self.app_data.get('description', '')
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #666666; font-size: 9px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        # Adobe equivalent
        adobe_equiv = self.app_data.get('adobe_equivalent', '')
        if adobe_equiv:
            equiv_label = QLabel(f"Alternative to: {adobe_equiv}")
            equiv_label.setStyleSheet("color: #0066cc; font-size: 9px; font-style: italic;")
            info_layout.addWidget(equiv_label)
        
        # Status indicators
        if self.is_currently_installed:
            status_label = QLabel("[CURRENTLY IN BUNDLE]")
            status_label.setStyleSheet("color: #28a745; font-size: 8px; font-weight: bold;")
            info_layout.addWidget(status_label)
        
        if self.app_data.get('required', False):
            req_label = QLabel("[RECOMMENDED]")
            req_label.setStyleSheet("color: #007bff; font-size: 8px; font-weight: bold;")
            info_layout.addWidget(req_label)
        
        layout.addWidget(info_widget, 1)  # Give it stretch priority
    
    def load_app_icon(self):
        """Load app icon with fallback options"""
        app_id = self.app_data.get('id', '')
        
        # Try to find icon file
        icon_paths_to_try = [
            self.config.app_icons_dir / f"creative-suite-{app_id}.png",
            self.config.app_icons_dir / f"{app_id}.png",
            # Try your available icon sizes in order of preference
            Path(f"/usr/share/icons/hicolor/32x32/apps/{app_id}.png"),
            Path(f"/usr/share/icons/hicolor/48x48/apps/{app_id}.png"),
            Path(f"/usr/share/icons/hicolor/24x24/apps/{app_id}.png"),
            Path(f"/usr/share/pixmaps/{app_id}.png"),
        ]
        
        for icon_path in icon_paths_to_try:
            if icon_path.exists():
                try:
                    return QPixmap(str(icon_path))
                except Exception as e:
                    print(f"Warning: Could not load icon {icon_path}: {e}")
                    continue
        
        return None
    
    def is_checked(self):
        """Return checkbox state"""
        return self.checkbox.isChecked()
    
    def set_checked(self, checked):
        """Set checkbox state"""
        self.checkbox.setChecked(checked)

class SelectionPage(BasePage):
    """Application selection page with PySide2"""
    
    def __init__(self, parent, app_parser, config):
        self.app_parser = app_parser
        self.config = config
        
        # Add app_parser reference to config for bundle prefix detection
        self.config.app_parser = app_parser
        
        # Initialize state detector
        self.state_detector = BundleStateDetector(config)
        
        # Get current bundle state
        self.bundle_info = self.state_detector.get_bundle_info_with_availability(app_parser)
        self.currently_installed = self.bundle_info["installed_app_ids"]
        
        print(f"DEBUG: Bundle info: {self.bundle_info}")
        
        self.app_widgets = {}  # Store widget references
        self._removal_result = None  # For bundle removal
        
        super().__init__(parent, config)
    
    def setup_ui(self):
        """Set up the application selection interface"""
        # Main layout
        main_layout = QVBoxLayout(self.parent)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Get suite info for dynamic titles
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Dynamic title based on bundle state
        if self.bundle_info["is_installed"]:
            title_text = f"Modify {suite_name}"
            desc_text = f"Add or remove applications from your {suite_name.lower()} installation. Currently installed applications are pre-selected."
        else:
            title_text = f"Select {suite_name} Applications"
            desc_text = f"Choose which {suite_name.lower()} applications to install. Recommended applications are pre-selected."
        
        # Title
        title = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Description
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666666; font-size: 11px; margin-bottom: 10px;")
        main_layout.addWidget(desc_label)
        
        # Show current state if bundle is installed
        if self.bundle_info["is_installed"]:
            self.show_current_state_info(main_layout)
        
        # Selection controls
        self.create_selection_controls(main_layout)
        
        # Scrollable app selection area
        self.create_app_selection_area(main_layout)
        
        # Summary area
        self.create_summary_area(main_layout)
        
        # Update selection count initially
        self.update_selection_count()
        self.update_summary()
    
    def show_current_state_info(self, layout):
        """Show information about current bundle installation"""
        info_frame = QGroupBox("Current Installation")
        info_layout = QVBoxLayout(info_frame)
        
        total = self.bundle_info["total_installed"]
        app_names = self.bundle_info["installed_app_names"]
        
        info_text = f"Currently installed: {total} applications\n"
        if app_names:
            info_text += "• " + "\n• ".join(app_names[:5])
            if len(app_names) > 5:
                info_text += f"\n• ... and {len(app_names) - 5} more"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 10px;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_frame)
    
    def create_selection_controls(self, layout):
        """Create Select All/None buttons"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side - selection buttons
        select_all_btn = ModernButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        controls_layout.addWidget(select_all_btn)
        
        select_none_btn = ModernButton("Select None")
        select_none_btn.clicked.connect(self.select_none)
        controls_layout.addWidget(select_none_btn)
        
        select_recommended_btn = ModernButton("Select Recommended")
        select_recommended_btn.clicked.connect(self.select_recommended)
        controls_layout.addWidget(select_recommended_btn)
        
        # Add stretch
        controls_layout.addStretch()
        
        # Right side - bundle management and selection count
        # Add "Remove Bundle" button if bundle is installed
        if self.bundle_info["is_installed"] and self.bundle_info["total_installed"] > 0:
            self.remove_bundle_button = ModernButton("🗑 Remove Bundle", "danger")
            self.remove_bundle_button.clicked.connect(self.confirm_remove_bundle)
            controls_layout.addWidget(self.remove_bundle_button)
        
        # Selection count label
        self.selection_count_label = QLabel("")
        self.selection_count_label.setStyleSheet("font-weight: bold; margin-left: 15px;")
        controls_layout.addWidget(self.selection_count_label)
        
        layout.addWidget(controls_frame)
    
    def create_app_selection_area(self, layout):
        """Create the main app selection area organized by categories"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)
        
        # Get apps organized by category
        apps_by_category = self.app_parser.get_apps_by_category()
        
        for category, apps in apps_by_category.items():
            self.create_category_section(content_layout, category, apps)
        
        # Add stretch at the end
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area, 1)  # Give it stretch priority
    
    def create_category_section(self, layout, category_name, apps):
        """Create a section for a specific category"""
        # Category group box
        category_box = QGroupBox(category_name)
        category_layout = QVBoxLayout(category_box)
        category_layout.setSpacing(8)
        
        # Create app entries for this category
        for app in apps:
            self.create_app_entry(category_layout, app)
        
        layout.addWidget(category_box)
    
    def create_app_entry(self, layout, app):
        """Create a single app entry widget"""
        app_id = app.get('id')
        is_currently_installed = app_id in self.currently_installed
        
        # Create app entry widget
        app_widget = AppEntryWidget(app, is_currently_installed, self.config)
        
        # Connect checkbox change
        app_widget.checkbox.stateChanged.connect(self.on_selection_changed)
        
        # Store the widget
        self.app_widgets[app_id] = app_widget
        
        layout.addWidget(app_widget)
    
    def create_summary_area(self, layout):
        """Create summary area showing what will be installed/changed"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        if self.bundle_info["is_installed"]:
            summary_title = f"{suite_name} Changes Summary"
        else:
            summary_title = f"{suite_name} Installation Summary"
        
        summary_box = QGroupBox(summary_title)
        summary_layout = QVBoxLayout(summary_box)
        
        self.summary_text = QTextEdit()
        self.summary_text.setFixedHeight(100)
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-size: 10px;
            }
        """)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_box)
    
    def select_all(self):
        """Select all applications"""
        for app_widget in self.app_widgets.values():
            app_widget.set_checked(True)
        self.on_selection_changed()
    
    def select_none(self):
        """Deselect all applications"""
        for app_widget in self.app_widgets.values():
            app_widget.set_checked(False)
        self.on_selection_changed()
    
    def select_recommended(self):
        """Select recommended applications and currently installed"""
        for app_id, app_widget in self.app_widgets.items():
            app_data = app_widget.app_data
            is_currently_installed = app_widget.is_currently_installed
            
            # Select if recommended OR currently installed
            if app_data.get('default_selected', False) or is_currently_installed:
                app_widget.set_checked(True)
            else:
                app_widget.set_checked(False)
        self.on_selection_changed()
    
    def on_selection_changed(self):
        """Called when selection changes"""
        self.update_selection_count()
        self.update_summary()
    
    def update_selection_count(self):
        """Update the selection count label"""
        selected_count = sum(1 for widget in self.app_widgets.values() if widget.is_checked())
        total_count = len(self.app_widgets)
        
        self.selection_count_label.setText(f"Selected: {selected_count}/{total_count}")
    
    def update_summary(self):
        """Update the installation/changes summary"""
        selected_apps = self.get_selected_apps()
        selected_ids = [app.get('id') for app in selected_apps]
        
        # Calculate changes if bundle is installed
        if self.bundle_info["is_installed"]:
            changes = self.state_detector.get_installation_changes(selected_ids)
            
            if not changes["has_changes"]:
                summary_text = "No changes - selection matches current installation."
            else:
                summary_lines = []
                
                if changes["to_add"]:
                    summary_lines.append(f"Install {len(changes['to_add'])} new applications:")
                    for app_id in changes["to_add"]:
                        app_name = self.app_parser.get_app_field(app_id, 'name') or app_id
                        summary_lines.append(f"  + {app_name}")
                
                if changes["to_remove"]:
                    summary_lines.append(f"Remove {len(changes['to_remove'])} from bundle:")
                    for app_id in changes["to_remove"]:
                        app_name = self.app_parser.get_app_field(app_id, 'name') or app_id
                        summary_lines.append(f"  - {app_name}")
                
                if changes["no_change"]:
                    summary_lines.append(f"Keep {len(changes['no_change'])} current applications")
                
                summary_text = "\n".join(summary_lines)
        else:
            # Fresh installation
            if not selected_apps:
                summary_text = "No applications selected."
            else:
                summary_lines = ["Applications to be installed:"]
                for app in selected_apps:
                    app_name = app.get('name', 'Unknown')
                    adobe_equiv = app.get('adobe_equivalent', '')
                    if adobe_equiv:
                        summary_lines.append(f"• {app_name} (replaces {adobe_equiv})")
                    else:
                        summary_lines.append(f"• {app_name}")
                
                summary_text = "\n".join(summary_lines)
        
        # Update text widget
        self.summary_text.setPlainText(summary_text)
    
    def get_selected_apps(self):
        """Get list of selected applications"""
        selected_apps = []
        
        for app_id, app_widget in self.app_widgets.items():
            if app_widget.is_checked():
                selected_apps.append(app_widget.app_data)
        
        return selected_apps
    
    def confirm_remove_bundle(self):
        """Confirm and initiate complete bundle removal"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Get list of currently installed apps for confirmation
        app_names = self.bundle_info["installed_app_names"]
        
        # Show detailed confirmation
        confirm_msg = f"""Remove {suite_name} Completely?

This will remove:
✓ All {suite_name} menu entries and icons
✓ {suite_name} category from application menu

✗ Applications remain installed:"""
        
        for app_name in app_names[:6]:
            confirm_msg += f"\n  • {app_name}"
        
        if len(app_names) > 6:
            confirm_msg += f"\n  • ... and {len(app_names) - 6} more"
        
        confirm_msg += f"""

The applications will be available in their original menu locations.

Continue with {suite_name} removal?"""
        
        reply = QMessageBox.question(
            self.parent, 
            f"Remove {suite_name}", 
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Store removal result and trigger navigation
            self._removal_result = {
                'mode': 'remove_bundle',
                'suite_name': suite_name,
                'installed_apps': self.bundle_info["installed_app_ids"],
                'app_names': self.bundle_info["installed_app_names"]
            }
            
            print("DEBUG: Bundle removal confirmed, will be processed in on_next()")
    
    def validate_selection(self):
        """Validate that selection is acceptable"""
        selected_apps = self.get_selected_apps()
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        if not selected_apps:
            # Check if this is removing everything from an existing bundle
            if self.bundle_info["is_installed"]:
                # Instead of asking here, suggest using the Remove Bundle button
                QMessageBox.information(
                    self.parent,
                    "Remove All Applications",
                    f"To completely remove {suite_name}, use the '🗑 Remove Bundle' button.\n\n"
                    "This will remove all menu entries while keeping the applications installed."
                )
                return False
            else:
                QMessageBox.warning(
                    self.parent,
                    "No Selection", 
                    f"Please select at least one {suite_name.lower()} application to install."
                )
                return False
        
        return True
    
    def on_next(self):
        """Called when Install/Apply button is clicked"""
        # Check if we're in bundle removal mode (button was clicked)
        if self._removal_result:
            result = self._removal_result
            self._removal_result = None  # Clean up
            print("DEBUG: Returning removal result from on_next()")
            return result
        
        if not self.validate_selection():
            return None
        
        selected_apps = self.get_selected_apps()
        selected_ids = [app.get('id') for app in selected_apps]
        
        # Calculate what needs to be done
        if self.bundle_info["is_installed"]:
            changes = self.state_detector.get_installation_changes(selected_ids)
            
            if not changes["has_changes"] and selected_apps:
                QMessageBox.information(
                    self.parent, 
                    "No Changes", 
                    "Selection matches current installation - no changes needed."
                )
                return None
            
            # Return modification data
            return {
                'mode': 'modify',
                'changes': changes,
                'selected_apps': selected_apps
            }
        else:
            # Fresh installation
            suite_info = self.app_parser.get_suite_info()
            suite_name = suite_info.get('name', 'Application Bundle')
            
            # Confirm installation
            app_names = [app.get('name', 'Unknown') for app in selected_apps]
            confirm_msg = f"Ready to install {len(selected_apps)} {suite_name.lower()} applications:\n\n"
            confirm_msg += "\n".join(f"• {name}" for name in app_names[:10])
            
            if len(app_names) > 10:
                confirm_msg += f"\n... and {len(app_names) - 10} more"
            
            confirm_msg += "\n\nProceed with installation?"
            
            reply = QMessageBox.question(
                self.parent,
                "Confirm Installation", 
                confirm_msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                return {
                    'mode': 'install',
                    'selected_apps': selected_apps
                }
            else:
                return None
