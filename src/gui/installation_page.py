#!/usr/bin/env python3
"""
Linux Bundle Installer - Installation Progress Page
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from pathlib import Path
import subprocess
import os

from gui.base_page import BasePage
from core.package_manager import PackageManager
from core.desktop_integration import DesktopIntegrator

class InstallationPage(BasePage):
    """Real installation page with progress tracking"""
    
    def __init__(self, parent, selection_result, app_parser, config, on_complete=None):
        self.selection_result = selection_result  # Can be apps list, modify dict, or removal dict
        self.app_parser = app_parser
        self.on_complete = on_complete
        
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
            self.changes = None
        
        # Installation components
        self.package_manager = PackageManager()
        self.desktop_integrator = DesktopIntegrator(config)
        
        # Progress tracking
        self.current_step = 0
        self.total_steps = 0
        self.installation_results = {}
        self.installation_errors = []
        self.is_installing = False
        
        super().__init__(parent, config)
        
        # Start installation automatically
        self.start_installation()
    
    def setup_ui(self):
        """Set up the installation progress interface"""
        # Get suite info for dynamic titles
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Dynamic title based on mode
        if self.mode == 'modify':
            title_text = f"Modifying {suite_name}"
        elif self.mode == 'remove_bundle':
            title_text = f"Removing {suite_name}"
        else:
            title_text = f"Installing {suite_name}"
        
        title = ttk.Label(self.parent, text=title_text, style='Title.TLabel')
        title.pack(pady=(20, 10))
        
        # Overall progress section
        progress_frame = ttk.LabelFrame(self.parent, text="Installation Progress", padding=15)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        # Overall progress bar
        self.overall_progress = ttk.Progressbar(
            progress_frame, 
            mode='determinate',
            length=400
        )
        self.overall_progress.pack(fill="x", pady=(0, 10))
        
        # Overall status label
        self.overall_status = ttk.Label(
            progress_frame, 
            text="Preparing installation...",
            font=('Arial', 10, 'bold')
        )
        self.overall_status.pack()
        
        # Current app progress section
        app_frame = ttk.LabelFrame(self.parent, text="Current Application", padding=15)
        app_frame.pack(fill="x", padx=20, pady=10)
        
        # Current app info
        self.current_app_label = ttk.Label(
            app_frame, 
            text="Initializing...",
            font=('Arial', 11, 'bold')
        )
        self.current_app_label.pack(pady=(0, 5))
        
        # Current app progress bar
        self.app_progress = ttk.Progressbar(
            app_frame, 
            mode='indeterminate',
            length=400
        )
        self.app_progress.pack(fill="x", pady=(0, 5))
        
        # Current app status
        self.app_status = ttk.Label(
            app_frame, 
            text="",
            foreground='gray'
        )
        self.app_status.pack()
        
        # Log/details section
        log_frame = ttk.LabelFrame(self.parent, text="Installation Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollable log text
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(
            log_container, 
            height=8, 
            wrap=tk.WORD,
            font=('Courier', 9),
            state='disabled'
        )
        log_scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # Control buttons frame
        self.buttons_frame = ttk.Frame(self.parent)
        self.buttons_frame.pack(fill="x", padx=20, pady=10)
        
        # Initially hidden, shown when installation completes
        if self.mode == 'remove_bundle':
            button_text = "Close"
        else:
            button_text = "Continue to Manager →"
            
        self.complete_button = ttk.Button(
            self.buttons_frame,
            text=button_text,
            command=self.on_installation_complete,
            state='disabled'
        )
        self.complete_button.pack(side="right")
    
    def log_message(self, message, level="info"):
        """Add a message to the installation log"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Color coding based on level
        if level == "error":
            color_tag = "error"
        elif level == "success":
            color_tag = "success"
        elif level == "warning":
            color_tag = "warning"
        else:
            color_tag = "info"
        
        # Insert message
        self.log_text.configure(state='normal')
        
        # Configure tags if not already done
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("info", foreground="black")
        
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", color_tag)
        self.log_text.configure(state='disabled')
        self.log_text.see(tk.END)
        
        # Force GUI update
        self.parent.update_idletasks()
    
    def update_overall_progress(self, step, total, message):
        """Update the overall progress bar and status"""
        if total > 0:
            progress_percent = (step / total) * 100
            self.overall_progress.configure(value=progress_percent)
        
        self.overall_status.configure(text=message)
        self.parent.update_idletasks()
    
    def update_app_progress(self, app_name, status, is_working=True):
        """Update the current app progress section"""
        self.current_app_label.configure(text=app_name)
        self.app_status.configure(text=status)
        
        if is_working:
            self.app_progress.configure(mode='indeterminate')
            self.app_progress.start()
        else:
            self.app_progress.stop()
            self.app_progress.configure(mode='determinate', value=100)
        
        self.parent.update_idletasks()
    
    def check_sudo_access(self):
        """Check and request sudo access if needed"""
        self.log_message("Checking administrative privileges...", "info")
        
        if not self.package_manager.check_sudo_access():
            self.log_message("Administrative access required for package installation", "info")
            
            # Show sudo prompt
            if messagebox.askyesno(
                "Administrative Access Required",
                "This installer needs administrative privileges to install packages.\n\n"
                "A password prompt will appear in your terminal.\n\n"
                "Continue?"
            ):
                if not self.package_manager.request_sudo_access():
                    self.log_message("Failed to obtain administrative access", "error")
                    return False
                else:
                    self.log_message("Administrative access granted", "success")
                    return True
            else:
                self.log_message("Installation cancelled - administrative access required", "error")
                return False
        else:
            self.log_message("Administrative access already available", "success")
            return True
    
    def install_packages_step(self):
        """Install the selected applications"""
        successful_installs = []
        failed_installs = []
        
        for i, app in enumerate(self.selected_apps):
            app_id = app.get('id', 'unknown')
            app_name = app.get('name', app_id)
            
            self.current_step = i + 1
            self.update_overall_progress(
                self.current_step, 
                self.total_steps, 
                f"Installing applications ({self.current_step}/{len(self.selected_apps)})..."
            )
            
            self.update_app_progress(app_name, "Installing...", True)
            self.log_message(f"Installing {app_name}...", "info")
            
            try:
                # Install the application
                success, message, method = self.package_manager.install_app(app, self.app_parser)
                
                if success:
                    self.log_message(f"✓ {app_name} installed successfully via {method}", "success")
                    successful_installs.append(app_name)
                    self.installation_results[app_id] = {
                        'success': True,
                        'method': method,
                        'message': message
                    }
                else:
                    self.log_message(f"✗ {app_name} installation failed: {message}", "error")
                    failed_installs.append(app_name)
                    self.installation_results[app_id] = {
                        'success': False,
                        'method': 'none',
                        'message': message
                    }
                    self.installation_errors.append(f"{app_name}: {message}")
                
                self.update_app_progress(app_name, "Complete", False)
                
            except Exception as e:
                error_msg = f"Unexpected error installing {app_name}: {str(e)}"
                self.log_message(f"✗ {error_msg}", "error")
                failed_installs.append(app_name)
                self.installation_errors.append(error_msg)
                self.update_app_progress(app_name, "Error", False)
            
            # Small delay to make progress visible
            time.sleep(0.5)
        
        return successful_installs, failed_installs
    
    def install_desktop_integration_step(self):
        """Install desktop files and icons"""
        self.current_step += 1
        self.update_overall_progress(
            self.current_step, 
            self.total_steps, 
            "Installing menu integration..."
        )
        
        self.update_app_progress("Menu Integration", "Installing desktop files...", True)
        self.log_message("Installing desktop integration...", "info")
        
        try:
            # Install icons and desktop files for successful installations
            successful_apps = [
                app for app in self.selected_apps 
                if self.installation_results.get(app.get('id', ''), {}).get('success', False)
            ]
            
            if successful_apps:
                self.desktop_integrator.install_icons()
                self.desktop_integrator.install_desktop_files(successful_apps)
                self.desktop_integrator.create_manager_script()
                
                self.log_message("✓ Desktop integration installed successfully", "success")
                self.update_app_progress("Menu Integration", "Complete", False)
                return True
            else:
                self.log_message("⚠ No applications installed successfully - skipping desktop integration", "warning")
                return False
                
        except Exception as e:
            error_msg = f"Desktop integration failed: {str(e)}"
            self.log_message(f"✗ {error_msg}", "error")
            self.installation_errors.append(error_msg)
            self.update_app_progress("Menu Integration", "Error", False)
            return False
    
    def installation_worker(self):
        """Worker thread for installation/modification/removal process"""
        try:
            self.is_installing = True
            
            if self.mode == 'modify':
                self.handle_modification_process()
            elif self.mode == 'remove_bundle':
                self.handle_bundle_removal_process()
            else:
                self.handle_installation_process()
                
        except Exception as e:
            self.log_message(f"Critical error: {str(e)}", "error")
            self.show_installation_failed(str(e))
        finally:
            self.is_installing = False
    
    def handle_bundle_removal_process(self):
        """Handle complete bundle removal process"""
        self.total_steps = 2  # Check + Remove
        
        # Step 1: Prepare removal
        self.current_step = 1
        self.update_overall_progress(
            self.current_step, 
            self.total_steps, 
            "Preparing bundle removal..."
        )
        
        self.update_app_progress("Bundle Removal", "Preparing...", True)
        self.log_message(f"Preparing to remove {self.suite_name}...", "info")
        
        # Step 2: Remove bundle
        self.current_step = 2
        self.update_overall_progress(
            self.current_step, 
            self.total_steps, 
            f"Removing {self.suite_name}..."
        )
        
        self.update_app_progress("Bundle Removal", "Removing menu entries...", True)
        self.log_message(f"Removing {len(self.installed_apps)} applications from bundle...", "info")
        
        try:
            # Use the desktop integrator removal method
            removal_success = self.desktop_integrator.uninstall_bundle_integration(
                self.installed_apps,
                suite_name=None,  # Don't show dialog again - already confirmed
                app_names=None
            )
            
            if removal_success:
                self.log_message(f"✓ {self.suite_name} removed successfully", "success")
                self.update_app_progress("Bundle Removal", "Complete", False)
                self.show_bundle_removal_complete()
            else:
                self.log_message(f"✗ Bundle removal failed", "error")
                self.update_app_progress("Bundle Removal", "Failed", False)
                self.show_installation_failed("Bundle removal failed")
                
        except Exception as e:
            error_msg = f"Bundle removal failed: {str(e)}"
            self.log_message(f"✗ {error_msg}", "error")
            self.installation_errors.append(error_msg)
            self.update_app_progress("Bundle Removal", "Error", False)
            self.show_installation_failed(error_msg)
    
    def show_bundle_removal_complete(self):
        """Show bundle removal completion status"""
        self.overall_status.configure(text=f"✓ {self.suite_name} removed successfully!")
        
        self.log_message("Bundle removal complete!", "success")
        self.log_message("Applications remain installed and available in original locations", "info")
        
        # Enable close button
        self.complete_button.configure(state='normal')
        self.complete_button.configure(text="Close")
        
        # Update current app status
        self.update_app_progress("Removal Complete", "", False)
    
    def handle_installation_process(self):
        """Handle fresh installation process"""
        # Calculate total steps
        self.total_steps = len(self.selected_apps) + 2  # +2 for sudo check and desktop integration
        
        # Step 1: Check sudo access
        self.update_overall_progress(0, self.total_steps, "Checking permissions...")
        if not self.check_sudo_access():
            self.show_installation_failed("Administrative access required")
            return
        
        # Step 2: Install packages
        successful_installs, failed_installs = self.install_packages_step()
        
        # Step 3: Desktop integration
        desktop_success = self.install_desktop_integration_step()
        
        # Final step
        self.current_step += 1
        self.update_overall_progress(self.current_step, self.total_steps, "Installation complete!")
        
        # Show completion
        self.show_installation_complete(successful_installs, failed_installs, desktop_success)
    
    def handle_modification_process(self):
        """Handle bundle modification process"""
        changes = self.changes
        apps_to_add = changes.get('to_add', [])
        apps_to_remove = changes.get('to_remove', [])
        
        # Calculate total steps
        add_steps = len(apps_to_add) + (1 if apps_to_add else 0)  # +1 for desktop integration
        remove_steps = 1 if apps_to_remove else 0  # Bundle removal step
        sudo_steps = 1 if apps_to_add else 0  # Only need sudo if installing
        
        self.total_steps = sudo_steps + add_steps + remove_steps
        
        successful_adds = []
        failed_adds = []
        
        # Step 1: Check sudo access (only if we're installing new apps)
        if apps_to_add:
            self.update_overall_progress(0, self.total_steps, "Checking permissions...")
            if not self.check_sudo_access():
                self.show_installation_failed("Administrative access required")
                return
        
        # Step 2: Remove apps from bundle (if any)
        if apps_to_remove:
            self.current_step += 1
            self.update_overall_progress(
                self.current_step, 
                self.total_steps, 
                f"Removing {len(apps_to_remove)} apps from bundle..."
            )
            
            self.update_app_progress("Bundle Removal", "Removing menu entries...", True)
            self.log_message(f"Removing {len(apps_to_remove)} applications from bundle...", "info")
            
            try:
                removed_count = self.desktop_integrator.remove_apps_from_bundle(apps_to_remove)
                self.log_message(f"✓ Removed {removed_count} applications from bundle", "success")
                self.update_app_progress("Bundle Removal", "Complete", False)
            except Exception as e:
                self.log_message(f"✗ Error removing apps from bundle: {str(e)}", "error")
                self.update_app_progress("Bundle Removal", "Error", False)
        
        # Step 3: Install new apps (if any)
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
                
                self.update_overall_progress(
                    self.current_step, 
                    self.total_steps, 
                    f"Installing new applications ({i+1}/{len(apps_to_install)})..."
                )
                
                self.update_app_progress(app_name, "Installing...", True)
                self.log_message(f"Installing {app_name}...", "info")
                
                try:
                    success, message, method = self.package_manager.install_app(app, self.app_parser)
                    
                    if success:
                        self.log_message(f"✓ {app_name} installed successfully via {method}", "success")
                        successful_adds.append(app_name)
                    else:
                        self.log_message(f"✗ {app_name} installation failed: {message}", "error")
                        failed_adds.append(app_name)
                        self.installation_errors.append(f"{app_name}: {message}")
                    
                    self.update_app_progress(app_name, "Complete", False)
                    
                except Exception as e:
                    error_msg = f"Unexpected error installing {app_name}: {str(e)}"
                    self.log_message(f"✗ {error_msg}", "error")
                    failed_adds.append(app_name)
                    self.installation_errors.append(error_msg)
                    self.update_app_progress(app_name, "Error", False)
            
            # Install desktop integration for new apps
            if successful_adds:
                self.current_step += 1
                self.update_overall_progress(
                    self.current_step, 
                    self.total_steps, 
                    "Installing menu integration..."
                )
                
                self.update_app_progress("Menu Integration", "Installing desktop files...", True)
                self.log_message("Installing desktop integration for new apps...", "info")
                
                try:
                    self.desktop_integrator.install_icons()
                    self.desktop_integrator.install_desktop_files(apps_to_install)
                    self.log_message("✓ Desktop integration installed for new apps", "success")
                    self.update_app_progress("Menu Integration", "Complete", False)
                except Exception as e:
                    error_msg = f"Desktop integration failed: {str(e)}"
                    self.log_message(f"✗ {error_msg}", "error")
                    self.installation_errors.append(error_msg)
                    self.update_app_progress("Menu Integration", "Error", False)
        
        # Final step
        self.current_step = self.total_steps
        self.update_overall_progress(self.current_step, self.total_steps, "Modification complete!")
        
        # Show completion
        self.show_modification_complete(apps_to_add, successful_adds, failed_adds, apps_to_remove)
    
    def show_modification_complete(self, requested_adds, successful_adds, failed_adds, removed_apps):
        """Show modification completion status"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Build status message
        status_parts = []
        
        if removed_apps:
            status_parts.append(f"Removed {len(removed_apps)} apps from bundle")
        
        if successful_adds:
            status_parts.append(f"Added {len(successful_adds)} new apps")
        
        if failed_adds:
            status_parts.append(f"Failed to add {len(failed_adds)} apps")
        
        if status_parts:
            status_message = f"✓ {suite_name} modified: " + ", ".join(status_parts)
        else:
            status_message = f"✓ {suite_name} modification complete"
        
        self.overall_status.configure(text=status_message)
        
        # Log summary
        if removed_apps:
            self.log_message(f"Removed from bundle: {', '.join(removed_apps)}", "info")
        if successful_adds:
            self.log_message(f"Added to bundle: {', '.join(successful_adds)}", "success")
        if failed_adds:
            self.log_message(f"Failed to add: {', '.join(failed_adds)}", "error")
        
        # Enable continue button
        self.complete_button.configure(state='normal')
        self.update_app_progress("Modification Complete", "", False)
    
    def start_installation(self):
        """Start the installation process in a background thread"""
        if self.mode != 'remove_bundle' and not self.selected_apps:
            self.show_installation_failed("No applications selected")
            return
        
        # Start installation in background thread
        install_thread = threading.Thread(target=self.installation_worker, daemon=True)
        install_thread.start()
    
    def show_installation_complete(self, successful, failed, desktop_success):
        """Show installation completion status"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        if successful and not failed:
            # Perfect success
            self.overall_status.configure(text=f"🎉 {suite_name} installed successfully!")
            self.log_message(f"Installation complete! {len(successful)} applications installed.", "success")
            self.log_message(f"You can now find them in your application menu under '{suite_name}'", "info")
        elif successful and failed:
            # Partial success
            self.overall_status.configure(text=f"⚠ {suite_name} partially installed")
            self.log_message(f"Partial installation: {len(successful)} successful, {len(failed)} failed.", "warning")
        else:
            # Complete failure
            self.overall_status.configure(text="❌ Installation failed")
            self.log_message("Installation failed - no applications were installed.", "error")
        
        # Enable continue button
        self.complete_button.configure(state='normal')
        self.complete_button.configure(text="Manage Bundle →")
        
        # Update current app status
        self.update_app_progress("Installation Complete", "", False)
    
    def show_installation_failed(self, error_message):
        """Show installation failure"""
        self.overall_status.configure(text="❌ Installation failed")
        self.log_message(f"Installation failed: {error_message}", "error")
        self.update_app_progress("Installation Failed", error_message, False)
        
        # Enable continue button (will go to manager to show what's available)
        self.complete_button.configure(state='normal')
    
    def on_installation_complete(self):
        """Handle completion button click"""
        if self.mode == 'remove_bundle':
            # Close the application after bundle removal
            print("DEBUG: Bundle removal complete, closing application")
            # Find the root window and quit
            current = self.parent
            while current and not hasattr(current, 'quit'):
                current = getattr(current, 'master', None) or getattr(current, 'parent', None)
            
            if current and hasattr(current, 'quit'):
                current.quit()
            else:
                # Fallback - try to close via the main window
                import sys
                sys.exit(0)
        else:
            # Normal completion - go to manager
            if self.on_complete:
                self.on_complete()
    
    def on_closing(self):
        """Handle window closing during installation"""
        if self.is_installing:
            if messagebox.askyesno(
                "Installation in Progress",
                "Installation is currently running.\n\n"
                "Closing now may leave your system in an incomplete state.\n\n"
                "Are you sure you want to close?"
            ):
                return True
            else:
                return False
        return True
