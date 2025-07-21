#!/usr/bin/env python3
"""
Linux Bundle Installer - Installation Progress Page (PySide2 Version)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Ported to PySide2: 2025-07-12
"""

import threading
import time
from pathlib import Path
import subprocess
import os

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QFrame, QMessageBox
)
from PySide2.QtCore import Qt, QThread, QObject, Signal, QTimer
from PySide2.QtGui import QFont, QTextCursor

from gui.base_page import BasePage
from core.package_manager import PackageManager
from core.desktop_integration import DesktopIntegrator

class InstallationWorker(QObject):
    """Worker object for installation operations in separate thread"""
    
    # Signals for communication with main thread
    progress_updated = Signal(int, int, str)  # step, total, message
    app_progress_updated = Signal(str, str, bool)  # app_name, status, is_working
    log_message = Signal(str, str)  # message, level
    installation_complete = Signal(bool, dict)  # success, results
    status_update = Signal(str)  # status text for main window
    
    def __init__(self, selection_result, app_parser, config, parent=None):
        super().__init__(parent)
        self.selection_result = selection_result
        self.app_parser = app_parser
        self.config = config
        
        # Installation components
        self.package_manager = PackageManager()
        self.desktop_integrator = DesktopIntegrator(config)
        
        # Progress tracking
        self.current_step = 0
        self.total_steps = 0
        self.installation_results = {}
        self.installation_errors = []
        
        # Determine operation mode
        if isinstance(selection_result, dict):
            self.mode = selection_result.get('mode', 'install')
            if self.mode == 'modify':
                self.changes = selection_result['changes']
                self.selected_apps = selection_result['selected_apps']
            elif self.mode == 'remove_bundle':
                self.suite_name = selection_result['suite_name']
                self.installed_apps = selection_result['installed_apps']
                self.app_names = selection_result['app_names']
                self.selected_apps = []
            else:
                self.selected_apps = selection_result.get('selected_apps', [])
        else:
            self.mode = 'install'
            self.selected_apps = selection_result if isinstance(selection_result, list) else []
    
    def start_installation(self):
        """Start the installation process"""
        try:
            if self.mode == 'modify':
                self.handle_modification_process()
            elif self.mode == 'remove_bundle':
                self.handle_bundle_removal_process()
            else:
                self.handle_installation_process()
        except Exception as e:
            self.log_message.emit(f"Critical error: {str(e)}", "error")
            self.installation_complete.emit(False, {"error": str(e)})
    
    def check_sudo_access(self):
        """Check and request sudo access if needed"""
        self.log_message.emit("Checking administrative privileges...", "info")
        
        if not self.package_manager.check_sudo_access():
            self.log_message.emit("Administrative access required for package installation", "info")
            return self.package_manager.request_sudo_access()
        else:
            self.log_message.emit("Administrative access already available", "success")
            return True
    
    def handle_installation_process(self):
        """Handle fresh installation process"""
        self.total_steps = len(self.selected_apps) + 2  # +2 for sudo check and desktop integration
        
        # Step 1: Check sudo access
        self.progress_updated.emit(0, self.total_steps, "Checking permissions...")
        if not self.check_sudo_access():
            self.installation_complete.emit(False, {"error": "Administrative access required"})
            return
        
        # Step 2: Install packages
        successful_installs, failed_installs = self.install_packages_step()
        
        # Step 3: Desktop integration
        desktop_success = self.install_desktop_integration_step()
        
        # Final step
        self.current_step += 1
        self.progress_updated.emit(self.current_step, self.total_steps, "Installation complete!")
        
        # Complete
        results = {
            "successful_installs": successful_installs,
            "failed_installs": failed_installs,
            "desktop_success": desktop_success
        }
        self.installation_complete.emit(len(failed_installs) == 0, results)
        self.status_update.emit("Complete")
    
    def handle_modification_process(self):
        """Handle bundle modification process"""
        changes = self.changes
        apps_to_add = changes.get('to_add', [])
        apps_to_remove = changes.get('to_remove', [])
        
        # Calculate total steps
        add_steps = len(apps_to_add) + (1 if apps_to_add else 0)
        remove_steps = 1 if apps_to_remove else 0
        sudo_steps = 1 if apps_to_add else 0
        
        self.total_steps = sudo_steps + add_steps + remove_steps
        
        successful_adds = []
        failed_adds = []
        
        # Check sudo access if installing new apps
        if apps_to_add:
            self.progress_updated.emit(0, self.total_steps, "Checking permissions...")
            if not self.check_sudo_access():
                self.installation_complete.emit(False, {"error": "Administrative access required"})
                return
        
        # Remove apps from bundle if any
        if apps_to_remove:
            self.current_step += 1
            self.progress_updated.emit(self.current_step, self.total_steps, f"Removing {len(apps_to_remove)} apps from bundle...")
            self.app_progress_updated.emit("Bundle Removal", "Removing menu entries...", True)
            self.log_message.emit(f"Removing {len(apps_to_remove)} applications from bundle...", "info")
            
            try:
                removed_count = self.desktop_integrator.remove_apps_from_bundle(apps_to_remove)
                self.log_message.emit(f"✓ Removed {removed_count} applications from bundle", "success")
                self.app_progress_updated.emit("Bundle Removal", "Complete", False)
            except Exception as e:
                self.log_message.emit(f"✗ Error removing apps from bundle: {str(e)}", "error")
                self.app_progress_updated.emit("Bundle Removal", "Error", False)
        
        # Install new apps if any
        if apps_to_add:
            # Get full app data for apps to add
            apps_to_install = []
            for app_id in apps_to_add:
                app_data = self.app_parser.get_app_by_id(app_id)
                if app_data:
                    apps_to_install.append(app_data)
            
            # Install new packages
            for i, app in enumerate(apps_to_install):
                self.current_step += 1
                app_name = app.get('name', app.get('id', 'Unknown'))
                
                self.progress_updated.emit(self.current_step, self.total_steps, f"Installing new applications ({i+1}/{len(apps_to_install)})...")
                self.app_progress_updated.emit(app_name, "Installing...", True)
                self.log_message.emit(f"Installing {app_name}...", "info")
                
                try:
                    success, message, method = self.package_manager.install_app(app, self.app_parser)
                    
                    if success:
                        self.log_message.emit(f"✓ {app_name} installed successfully via {method}", "success")
                        successful_adds.append(app_name)
                    else:
                        self.log_message.emit(f"✗ {app_name} installation failed: {message}", "error")
                        failed_adds.append(app_name)
                        self.installation_errors.append(f"{app_name}: {message}")
                    
                    self.app_progress_updated.emit(app_name, "Complete", False)
                    
                except Exception as e:
                    error_msg = f"Unexpected error installing {app_name}: {str(e)}"
                    self.log_message.emit(f"✗ {error_msg}", "error")
                    failed_adds.append(app_name)
                    self.installation_errors.append(error_msg)
                    self.app_progress_updated.emit(app_name, "Error", False)
            
            # Install desktop integration for new apps
            if successful_adds:
                self.current_step += 1
                self.progress_updated.emit(self.current_step, self.total_steps, "Installing menu integration...")
                self.app_progress_updated.emit("Menu Integration", "Installing desktop files...", True)
                self.log_message.emit("Installing desktop integration for new apps...", "info")
                
                try:
                    self.desktop_integrator.install_icons()
                    self.desktop_integrator.install_desktop_files(apps_to_install)
                    self.log_message.emit("✓ Desktop integration installed for new apps", "success")
                    self.app_progress_updated.emit("Menu Integration", "Complete", False)
                except Exception as e:
                    error_msg = f"Desktop integration failed: {str(e)}"
                    self.log_message.emit(f"✗ {error_msg}", "error")
                    self.installation_errors.append(error_msg)
                    self.app_progress_updated.emit("Menu Integration", "Error", False)
        
        # Final step
        self.current_step = self.total_steps
        self.progress_updated.emit(self.current_step, self.total_steps, "Modification complete!")
        
        # Complete
        results = {
            "requested_adds": apps_to_add,
            "successful_adds": successful_adds,
            "failed_adds": failed_adds,
            "removed_apps": apps_to_remove
        }
        self.installation_complete.emit(len(failed_adds) == 0, results)
        self.status_update.emit("Complete")
    
    def handle_bundle_removal_process(self):
        """Handle complete bundle removal process"""
        self.total_steps = 2
        
        # Step 1: Prepare removal
        self.current_step = 1
        self.progress_updated.emit(self.current_step, self.total_steps, "Preparing bundle removal...")
        self.app_progress_updated.emit("Bundle Removal", "Preparing...", True)
        self.log_message.emit(f"Preparing to remove {self.suite_name}...", "info")
        
        # Step 2: Remove bundle
        self.current_step = 2
        self.progress_updated.emit(self.current_step, self.total_steps, f"Removing {self.suite_name}...")
        self.app_progress_updated.emit("Bundle Removal", "Removing menu entries...", True)
        self.log_message.emit(f"Removing {len(self.installed_apps)} applications from bundle...", "info")
        
        try:
            removal_success = self.desktop_integrator.uninstall_bundle_integration(
                self.installed_apps,
                suite_name=None,
                app_names=None
            )
            
            if removal_success:
                self.log_message.emit(f"✓ {self.suite_name} removed successfully", "success")
                self.app_progress_updated.emit("Bundle Removal", "Complete", False)
                results = {"suite_name": self.suite_name}
                self.installation_complete.emit(True, results)
                self.status_update.emit("Bundle Removal Complete")
            else:
                self.log_message.emit(f"✗ Bundle removal failed", "error")
                self.app_progress_updated.emit("Bundle Removal", "Failed", False)
                self.installation_complete.emit(False, {"error": "Bundle removal failed"})
                self.status_update.emit("Failed")
                
        except Exception as e:
            error_msg = f"Bundle removal failed: {str(e)}"
            self.log_message.emit(f"✗ {error_msg}", "error")
            self.installation_errors.append(error_msg)
            self.app_progress_updated.emit("Bundle Removal", "Error", False)
            self.installation_complete.emit(False, {"error": error_msg})
            self.status_update.emit("Failed")
    
    def install_packages_step(self):
        """Install the selected applications"""
        successful_installs = []
        failed_installs = []
        
        for i, app in enumerate(self.selected_apps):
            app_id = app.get('id', 'unknown')
            app_name = app.get('name', app_id)
            
            self.current_step = i + 1
            self.progress_updated.emit(self.current_step, self.total_steps, f"Installing applications ({self.current_step}/{len(self.selected_apps)})...")
            self.app_progress_updated.emit(app_name, "Installing...", True)
            self.log_message.emit(f"Installing {app_name}...", "info")
            
            try:
                success, message, method = self.package_manager.install_app(app, self.app_parser)
                
                if success:
                    self.log_message.emit(f"✓ {app_name} installed successfully via {method}", "success")
                    successful_installs.append(app_name)
                    self.installation_results[app_id] = {'success': True, 'method': method, 'message': message}
                else:
                    self.log_message.emit(f"✗ {app_name} installation failed: {message}", "error")
                    failed_installs.append(app_name)
                    self.installation_results[app_id] = {'success': False, 'method': 'none', 'message': message}
                    self.installation_errors.append(f"{app_name}: {message}")
                
                self.app_progress_updated.emit(app_name, "Complete", False)
                
            except Exception as e:
                error_msg = f"Unexpected error installing {app_name}: {str(e)}"
                self.log_message.emit(f"✗ {error_msg}", "error")
                failed_installs.append(app_name)
                self.installation_errors.append(error_msg)
                self.app_progress_updated.emit(app_name, "Error", False)
            
            # Small delay to make progress visible
            time.sleep(0.1)
        
        return successful_installs, failed_installs
    
    def install_desktop_integration_step(self):
        """Install desktop files and icons"""
        self.current_step += 1
        self.progress_updated.emit(self.current_step, self.total_steps, "Installing menu integration...")
        self.app_progress_updated.emit("Menu Integration", "Installing desktop files...", True)
        self.log_message.emit("Installing desktop integration...", "info")
        
        try:
            successful_apps = [
                app for app in self.selected_apps 
                if self.installation_results.get(app.get('id', ''), {}).get('success', False)
            ]
            
            if successful_apps:
                self.desktop_integrator.install_icons()
                self.desktop_integrator.install_desktop_files(successful_apps)
                self.desktop_integrator.create_manager_script()
                
                self.log_message.emit("✓ Desktop integration installed successfully", "success")
                self.app_progress_updated.emit("Menu Integration", "Complete", False)
                return True
            else:
                self.log_message.emit("⚠ No applications installed successfully - skipping desktop integration", "warning")
                return False
                
        except Exception as e:
            error_msg = f"Desktop integration failed: {str(e)}"
            self.log_message.emit(f"✗ {error_msg}", "error")
            self.installation_errors.append(error_msg)
            self.app_progress_updated.emit("Menu Integration", "Error", False)
            return False

class InstallationPage(BasePage):
    """Installation progress page with PySide2"""
    
    def __init__(self, parent, selection_result, app_parser, config, on_complete=None, status_callback=None):
        self.selection_result = selection_result
        self.app_parser = app_parser
        self.on_complete = on_complete
        self.status_callback = status_callback
        self.config = config
        
        # Store reference to main window for navigation
        self.main_window = None
        current = parent
        search_depth = 0
        while current and search_depth < 5:
            if hasattr(current, 'show_selection_page'):
                self.main_window = current
                break
            current = getattr(current, 'parent', lambda: None)()
            search_depth += 1
        
        # Determine operation mode for UI
        if isinstance(selection_result, dict):
            self.mode = selection_result.get('mode', 'install')
        else:
            self.mode = 'install'
        
        self.is_installing = False
        self.worker = None
        self.worker_thread = None
        
        super().__init__(parent, config)
        
        # Start installation automatically
        self.start_installation()
    
    def setup_ui(self):
        """Set up the installation progress interface"""
        # Main layout
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Dynamic title based on mode
        if self.mode == 'modify':
            title_text = "Modifying Linux Creative Suite"
        elif self.mode == 'remove_bundle':
            title_text = "Removing Linux Creative Suite"
        else:
            title_text = "Installing Linux Creative Suite"
        
        title = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Overall progress section
        progress_box = QGroupBox("Installation Progress")
        progress_layout = QVBoxLayout(progress_box)
        
        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.overall_progress)
        
        # Overall status label
        self.overall_status = QLabel("Preparing installation...")
        self.overall_status.setAlignment(Qt.AlignCenter)
        overall_font = QFont()
        overall_font.setBold(True)
        self.overall_status.setFont(overall_font)
        progress_layout.addWidget(self.overall_status)
        
        layout.addWidget(progress_box)
        
        # Current app progress section
        app_box = QGroupBox("Current Application")
        app_layout = QVBoxLayout(app_box)
        
        # Current app info
        self.current_app_label = QLabel("Initializing...")
        app_font = QFont()
        app_font.setBold(True)
        self.current_app_label.setFont(app_font)
        app_layout.addWidget(self.current_app_label)
        
        # Current app progress bar
        self.app_progress = QProgressBar()
        self.app_progress.setMinimum(0)
        self.app_progress.setMaximum(0)  # Indeterminate mode
        self.app_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        app_layout.addWidget(self.app_progress)
        
        # Current app status
        self.app_status = QLabel("")
        self.app_status.setStyleSheet("color: #666666;")
        app_layout.addWidget(self.app_status)
        
        layout.addWidget(app_box)
        
        # Log section
        log_box = QGroupBox("Installation Log")
        log_layout = QVBoxLayout(log_box)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 9px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_box, 1)
        
        # Control buttons
        self.buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(self.buttons_frame)
        buttons_layout.addStretch()
        
        if self.mode == 'remove_bundle':
            button_text = "Close"
        else:
            button_text = "Continue to Manager →"
        
        self.complete_button = QPushButton(button_text)
        self.complete_button.setEnabled(False)
        self.complete_button.clicked.connect(self.on_installation_complete)
        self.complete_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        buttons_layout.addWidget(self.complete_button)
        
        layout.addWidget(self.buttons_frame)
    
    def log_message(self, message, level="info"):
        """Add a message to the installation log"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Color coding based on level
        if level == "error":
            color = "red"
        elif level == "success":
            color = "green"
        elif level == "warning":
            color = "orange"
        else:
            color = "black"
        
        # Format message with HTML for colors
        formatted_message = f'<span style="color: {color}">[{timestamp}] {message}</span><br>'
        
        # Insert message
        self.log_text.insertHtml(formatted_message)
        
        # Scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
    
    def update_overall_progress(self, step, total, message):
        """Update the overall progress bar and status"""
        if total > 0:
            progress_percent = int((step / total) * 100)
            self.overall_progress.setValue(progress_percent)
        
        self.overall_status.setText(message)
    
    def update_app_progress(self, app_name, status, is_working=True):
        """Update the current app progress section"""
        self.current_app_label.setText(app_name)
        self.app_status.setText(status)
        
        if is_working:
            self.app_progress.setMaximum(0)  # Indeterminate
        else:
            self.app_progress.setMaximum(100)
            self.app_progress.setValue(100)
    
    def start_installation(self):
        """Start the installation process in a background thread"""
        if self.mode != 'remove_bundle' and not self.selection_result:
            self.show_installation_failed("No applications selected")
            return
        
        self.is_installing = True
        
        # Create worker and thread
        self.worker = InstallationWorker(self.selection_result, self.app_parser, self.config)
        self.worker_thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.progress_updated.connect(self.update_overall_progress)
        self.worker.app_progress_updated.connect(self.update_app_progress)
        self.worker.log_message.connect(self.log_message)
        self.worker.installation_complete.connect(self.on_worker_complete)
        self.worker.status_update.connect(self._update_main_window_status)
        
        # Connect thread signals
        self.worker_thread.started.connect(self.worker.start_installation)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        # Start the thread
        self.worker_thread.start()
    
    def on_worker_complete(self, success, results):
        """Handle worker completion"""
        self.is_installing = False
        
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        if self.mode == 'remove_bundle':
            self.show_bundle_removal_complete(success, results)
        elif self.mode == 'modify':
            self.show_modification_complete(success, results)
        else:
            self.show_installation_complete(success, results)
    
    def show_installation_complete(self, success, results):
        """Show installation completion status"""
        successful = results.get("successful_installs", [])
        failed = results.get("failed_installs", [])
        
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        if success and successful and not failed:
            self.overall_status.setText(f"🎉 {suite_name} installed successfully!")
            self.log_message("Installation complete! Applications installed successfully.", "success")
            self.log_message(f"You can now find them in your application menu under '{suite_name}'", "info")
        elif successful and failed:
            self.overall_status.setText(f"⚠ {suite_name} partially installed")
            self.log_message(f"Partial installation: {len(successful)} successful, {len(failed)} failed.", "warning")
        else:
            self.overall_status.setText("❌ Installation failed")
            self.log_message("Installation failed - no applications were installed.", "error")
        
        # Fix: Always show correct button text for modification mode
        if self.mode == 'remove_bundle':
            self.complete_button.setText("Exit")
        else:
            self.complete_button.setText("Continue Modifying →")
        
        self.complete_button.setEnabled(True)
        self.update_app_progress("Installation Complete", "Ready to continue", False)
        
        # Update main window status properly
        self._update_main_window_status("Complete")
        
    def show_modification_complete(self, success, results):
        """Show modification completion status"""
        successful_adds = results.get("successful_adds", [])
        failed_adds = results.get("failed_adds", [])
        removed_apps = results.get("removed_apps", [])
        
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Build status message
        status_parts = []
        if removed_apps:
            status_parts.append(f"Removed {len(removed_apps)} apps")
        if successful_adds:
            status_parts.append(f"Added {len(successful_adds)} apps")
        if failed_adds:
            status_parts.append(f"Failed to add {len(failed_adds)} apps")
        
        if status_parts:
            status_message = f"✓ {suite_name} modified: " + ", ".join(status_parts)
        else:
            status_message = f"✓ {suite_name} modification complete"
        
        self.overall_status.setText(status_message)
        
        # Log details
        if removed_apps:
            self.log_message(f"Removed from bundle: {', '.join(removed_apps)}", "info")
        if successful_adds:
            self.log_message(f"Added to bundle: {', '.join(successful_adds)}", "success")
        if failed_adds:
            self.log_message(f"Failed to add: {', '.join(failed_adds)}", "error")
        
        # Set correct button
        self.complete_button.setText("Continue Modifying →")
        self.complete_button.setEnabled(True)
        self.update_app_progress("Modification Complete", "Ready to continue", False)
        
        # Update main window status
        self._update_main_window_status("Complete")
    
    def show_bundle_removal_complete(self, success, results):
        """Show bundle removal completion status"""
        if success:
            suite_name = results.get("suite_name", "Linux Creative Suite")
            self.overall_status.setText(f"✓ {suite_name} removed successfully!")
            self.log_message("Bundle removal complete!", "success")
            self.log_message("Applications remain installed and available in original locations", "info")
        else:
            self.overall_status.setText("❌ Bundle removal failed")
            error = results.get("error", "Unknown error")
            self.log_message(f"Bundle removal failed: {error}", "error")
        
        self.complete_button.setText("Exit")
        self.complete_button.setEnabled(True)
        self.update_app_progress("Removal Complete", "Ready to close", False)
        
        # Update main window status
        self._update_main_window_status("Complete")
    
    def show_installation_failed(self, error_message):
        """Show installation failure"""
        self.overall_status.setText("❌ Installation failed")
        self.log_message(f"Installation failed: {error_message}", "error")
        self.update_app_progress("Installation Failed", error_message, False)
        
        self.complete_button.setText("Back to Selection →")
        self.complete_button.setEnabled(True)
        self._update_main_window_status("Failed")
    
    def _update_main_window_status(self, status_text):
        """Update the main window navigation status using callback"""
        try:
            if self.status_callback:
                self.status_callback(status_text)
        except Exception as e:
            print(f"Warning: Could not update main window status via callback: {e}")
    
    def on_installation_complete(self):
        """Handle completion button click"""
        print("DEBUG: Installation completion button clicked")
        
        if self.mode == 'remove_bundle':
            # Close the application after bundle removal
            print("DEBUG: Closing application after bundle removal")
            import sys
            sys.exit(0)
        else:
            # Return to selection page for further modifications
            print("DEBUG: Returning to selection page for modifications")
            
            # Find the main window more reliably
            # In PySide2, we need to traverse the widget hierarchy differently
            main_window = None
            
            # Try to find MainWindow through parent chain
            current_widget = self.parent
            search_depth = 0
            while current_widget and search_depth < 10:
                if hasattr(current_widget, 'show_selection_page'):
                    main_window = current_widget
                    break
                # Try different parent attributes for PySide2
                current_widget = getattr(current_widget, 'parent', None)
                if callable(current_widget):
                    current_widget = current_widget()
                search_depth += 1
            
            if main_window:
                print("DEBUG: Found main window, calling show_selection_page")
                success_message = "Linux Creative Suite modified successfully" if self.mode == 'modify' else "Linux Creative Suite installed successfully"
                main_window.show_selection_page(success_message=success_message)
            else:
                print("DEBUG: Could not find main window - trying QApplication approach")
                # Fallback: Find MainWindow through QApplication
                from PySide2.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    for widget in app.allWidgets():
                        if hasattr(widget, 'show_selection_page') and hasattr(widget, 'setWindowTitle'):
                            print("DEBUG: Found MainWindow via QApplication")
                            success_message = "Linux Creative Suite modified successfully" if self.mode == 'modify' else "Linux Creative Suite installed successfully"
                            widget.show_selection_page(success_message=success_message)
                            return
                
                print("ERROR: Could not find main window to navigate back")
    
    def on_next(self):
        """Called when next/continue button is clicked"""
        if not self.is_installing:
            if self.mode == 'remove_bundle':
                return None  # This will trigger close
            else:
                # Return to selection page for modifications or go to manager
                if self.main_window and hasattr(self.main_window, 'show_selection_page'):
                    message = "Linux Creative Suite modified successfully" if self.mode == 'modify' else "Linux Creative Suite installed successfully"
                    self.main_window.show_selection_page(success_message=message)
                return None
        return None
    
    def on_back(self):
        """Called when back button is clicked"""
        if not self.is_installing:
            if self.main_window and hasattr(self.main_window, 'show_selection_page'):
                self.main_window.show_selection_page()
            return False
        return True
    
    def on_closing(self):
        """Handle window closing during installation"""
        if self.is_installing:
            reply = QMessageBox.question(
                self.parent,
                "Installation in Progress",
                "Installation is currently running.\n\n"
                "Closing now may leave your system in an incomplete state.\n\n"
                "Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes
        return True
