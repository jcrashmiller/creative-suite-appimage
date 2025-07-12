#!/usr/bin/env python3
"""
Linux Bundle Installer - Main Window (PySide6 Version)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Ported to PySide2: 2025-07-12
"""

import sys
import traceback
from pathlib import Path

from PySide2.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame,
    QMessageBox, QApplication
)
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QFont

# Import your existing pages (we'll port these next)
from gui.welcome_page import WelcomePage
from gui.selection_page import SelectionPage
from gui.installation_page import InstallationPage
from gui.manager_page import ManagerPage
from utils.json_parser import AppDefinitionParser

class ModernButton(QPushButton):
    """Custom button with modern styling"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

class StatusLabel(QLabel):
    """Custom status label with consistent styling"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 11px;
                padding: 5px;
            }
        """)

class SuccessBanner(QFrame):
    """Success banner widget"""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                padding: 8px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        label = QLabel(f"✓ {message}")
        label.setStyleSheet("""
            QLabel {
                color: #155724;
                font-weight: bold;
                background: transparent;
                border: none;
                margin: 0;
                padding: 0;
            }
        """)
        layout.addWidget(label)

class MainWindow(QMainWindow):
    """Main application window controller"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_page_type = None
        self.current_page = None
        self.success_banner = None
        
        # Try to load and validate app definitions
        try:
            self.config.validate_assets()
            self.app_parser = AppDefinitionParser(self.config.app_definitions_file)
            
            if not self.app_parser.validate_json_structure():
                raise ValueError("Invalid JSON structure in app definitions")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Failed to load application definitions:\n\n{str(e)}\n\n"
                "Please check that the installer package is complete."
            )
            sys.exit(1)
        
        # Set up the GUI
        self._setup_window()
        self._create_widgets()
        self._apply_styling()
        
        # Handle AppImage integration if needed
        self._handle_appimage_integration()
        
        # Start with welcome page
        self.show_welcome_page()
    
    def _setup_window(self):
        """Configure the main window with JSON-driven titles"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle Installer')
        suite_version = suite_info.get('version', '1.0')
        
        # Dynamic window title
        window_title = f"{suite_name} Installer v{suite_version} - Loading Screen Solutions"
        self.setWindowTitle(window_title)
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        # Center window on screen
        self._center_window()
    
    def _center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def _create_widgets(self):
        """Create the main container and navigation"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Success banner area (initially hidden)
        self.banner_container = QWidget()
        self.banner_layout = QVBoxLayout(self.banner_container)
        self.banner_layout.setContentsMargins(0, 0, 0, 0)
        self.banner_container.hide()
        main_layout.addWidget(self.banner_container)
        
        # Content stack (where pages will be displayed)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)  # Give it stretch priority
        
        # Navigation frame
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 10, 0, 0)
        
        # Navigation buttons
        self.back_button = ModernButton("← Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        nav_layout.addWidget(self.back_button)
        
        # Status label in center
        self.status_label = StatusLabel("Welcome")
        nav_layout.addWidget(self.status_label, 1)
        
        self.next_button = ModernButton("Next →")
        self.next_button.clicked.connect(self.go_next)
        nav_layout.addWidget(self.next_button)
        
        main_layout.addWidget(nav_frame)
    
    def _apply_styling(self):
        """Apply modern styling to the application"""
        # Set application-wide stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10px;
            }
            QFrame {
                background-color: white;
                border-radius: 4px;
            }
        """)
    
    def _clear_content_stack(self):
        """Clear the content stack"""
        while self.content_stack.count():
            widget = self.content_stack.widget(0)
            self.content_stack.removeWidget(widget)
            widget.deleteLater()
    
    def update_status_callback(self, status_text):
        """Callback function for child pages to update main window status"""
        try:
            self.status_label.setText(status_text)
            print(f"DEBUG: Main window status updated to: {status_text}")
            
            # Enable navigation buttons when complete
            if status_text in ["Complete", "Failed", "Bundle Removal Complete"]:
                self.next_button.setEnabled(True)
                self.back_button.setEnabled(True)
                print(f"DEBUG: Navigation buttons enabled")
            
        except Exception as e:
            print(f"ERROR: Failed to update status: {e}")
    
    def show_welcome_page(self):
        """Show the welcome/introduction page"""
        self._clear_content_stack()
        
        # Create a widget container for the page
        container = QWidget()
        suite_info = self.app_parser.get_suite_info()
        self.current_page = WelcomePage(
            container,  # parent widget 
            suite_info, 
            self.app_parser.get_all_apps(),
            self.config
        )
        self.current_page_type = "welcome"
        
        self.content_stack.addWidget(container)
        
        # Update navigation
        self.back_button.setEnabled(False)
        self.next_button.setText("Get Started →")
        self.next_button.setEnabled(True)
        self.status_label.setText("Welcome")
    
    def show_selection_page(self, success_message=None):
        """Show the application selection page"""
        print(f"DEBUG: MainWindow.show_selection_page called with message: {success_message}")
        self._clear_content_stack()
        
        # Create a temporary widget container for the tkinter-style page
        container = QWidget()
        self.current_page = SelectionPage(
            container,  # parent widget
            self.app_parser,
            self.config
        )
        self.current_page_type = "selection"
        
        self.content_stack.addWidget(container)
        
        # Show success banner if provided
        if success_message:
            print(f"DEBUG: Showing success banner: {success_message}")
            self.show_success_banner(success_message)
        
        # Update navigation
        self.back_button.setEnabled(True)
        # Dynamic button text based on bundle state
        if hasattr(self.current_page, 'bundle_info') and self.current_page.bundle_info["is_installed"]:
            self.next_button.setText("Apply Changes →")
        else:
            self.next_button.setText("Install Selected →")
        self.next_button.setEnabled(True)
        self.status_label.setText("Select Applications")
        
        print("DEBUG: Selection page shown successfully")
    
    def show_success_banner(self, message):
        """Show a temporary success banner at the top of the window"""
        print(f"DEBUG: Creating success banner with message: {message}")
        
        # Remove existing banner if any
        self._remove_banner()
        
        # Create new banner
        self.success_banner = SuccessBanner(message)
        self.banner_layout.addWidget(self.success_banner)
        self.banner_container.show()
        
        # Auto-remove banner after 4 seconds
        QTimer.singleShot(4000, self._remove_banner)
        
        print("DEBUG: Success banner created and scheduled for removal")

    def _remove_banner(self):
        """Remove the success banner"""
        try:
            if self.success_banner:
                print("DEBUG: Removing success banner")
                self.banner_layout.removeWidget(self.success_banner)
                self.success_banner.deleteLater()
                self.success_banner = None
                self.banner_container.hide()
                print("DEBUG: Success banner removed successfully")
        except Exception as e:
            print(f"DEBUG: Error removing banner: {e}")
    
    def show_installation_page(self, selected_apps):
        """Show the installation progress page"""
        print(f"DEBUG: MainWindow.show_installation_page called")
        self._clear_content_stack()
        
        # Create a temporary widget container for the tkinter-style page
        container = QWidget()
        # Pass the status callback to InstallationPage
        self.current_page = InstallationPage(
            container,  # parent widget
            selected_apps,
            self.app_parser,
            self.config,
            on_complete=self.show_manager_page,
            status_callback=self.update_status_callback
        )
        self.current_page_type = "installation"
        
        self.content_stack.addWidget(container)
        
        # Update navigation - initially disabled during installation
        self.back_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.status_label.setText("Installing...")
        
        print("DEBUG: Installation page created successfully")
    
    def show_manager_page(self):
        """Show the application manager page"""
        print("DEBUG: MainWindow.show_manager_page called")
        self._clear_content_stack()
        
        # Create a temporary widget container for the tkinter-style page
        container = QWidget()
        self.current_page = ManagerPage(
            container,  # parent widget
            self.app_parser,
            self.config
        )
        self.current_page_type = "manager"
        
        self.content_stack.addWidget(container)
        
        # Update navigation
        self.back_button.setEnabled(False)
        self.next_button.setText("Close")
        self.next_button.setEnabled(True)
        self.status_label.setText("Manage Applications")
        
        print("DEBUG: Manager page shown successfully")
    
    def go_back(self):
        """Handle back button click"""
        try:
            print(f"DEBUG: go_back called from page type: {self.current_page_type}")
            
            # Let the current page handle back if it has the method
            if hasattr(self.current_page, 'on_back'):
                result = self.current_page.on_back()
                # If page handled it and returned False, don't do default navigation
                if result is False:
                    return
            
            # Default back navigation based on current page type
            if self.current_page_type == "selection":
                self.show_welcome_page()
            elif self.current_page_type == "manager":
                # After installation completes, back should go to selection for re-modification
                self.show_selection_page()
            elif self.current_page_type == "installation":
                # Let installation page handle back navigation
                print("DEBUG: Back clicked on installation page")
                # Installation page will handle this directly
                pass
            # Welcome page doesn't have back navigation

        except Exception as e:
            self._handle_error("Navigation Error", e)
    
    def go_next(self):
        """Handle next button click"""
        try:
            print(f"DEBUG: go_next called from page type: {self.current_page_type}")
            
            # Get result from current page if it has on_next method
            result = None
            if hasattr(self.current_page, 'on_next'):
                result = self.current_page.on_next()
                print(f"DEBUG: on_next returned: {type(result)} - {result}")
            
            # Handle page transitions based on current page type and result
            if self.current_page_type == "welcome":
                self.show_selection_page()
                
            elif self.current_page_type == "selection":
                if result:  # result should be selected apps or removal data
                    # Check if this is a bundle removal operation
                    if isinstance(result, dict) and result.get('mode') == 'remove_bundle':
                        print("DEBUG: Starting bundle removal process")
                        # Start removal process
                        self.show_installation_page(result)
                    else:
                        print("DEBUG: Starting normal installation/modification")
                        # Normal installation/modification
                        self.show_installation_page(result)
                        
            elif self.current_page_type == "manager":
                print("DEBUG: Closing from manager page")
                self.close()
                
            elif self.current_page_type == "installation":
                print("DEBUG: Installation page handles its own completion")
                # Installation page handles its own completion via on_complete callback
                pass
                
        except Exception as e:
            self._handle_error("Navigation Error", e)
    
    def _handle_appimage_integration(self):
        """Handle AppImage integration setup"""
        import os
        
        # Only for AppImage
        if not os.environ.get('APPIMAGE'):
            print("DEBUG: Not running as AppImage - skipping integration dialog")
            return
        
        try:
            from gui.appimage_integration import check_appimage_integration
            suite_info = self.app_parser.get_suite_info()
            suite_name = suite_info.get('name', 'Linux Creative Suite')
            
            result = check_appimage_integration(suite_name)
            
            # Store the result for desktop integration
            self.appimage_integration_result = result
            
        except Exception as e:
            print(f"Warning: AppImage integration check failed: {e}")
            self.appimage_integration_result = None
    
    def _handle_error(self, title, error):
        """Handle and display errors"""
        error_msg = f"An error occurred:\n\n{str(error)}\n\nDetails:\n{traceback.format_exc()}"
        QMessageBox.critical(self, title, error_msg)
        print(f"ERROR: {title} - {error}")
        traceback.print_exc()
    
    def closeEvent(self, event):
        """Handle window closing"""
        print("DEBUG: MainWindow.closeEvent called")
        if hasattr(self.current_page, 'on_closing'):
            if not self.current_page.on_closing():
                print("DEBUG: Page prevented closing")
                event.ignore()
                return
        
        print("DEBUG: Accepting close event")
        event.accept()
