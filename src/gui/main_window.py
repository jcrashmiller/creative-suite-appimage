#!/usr/bin/env python3
"""
Linux Bundle Installer - Main Window (FIXED Navigation)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
"""

"""
Main window and GUI controller for Creative Suite Installer
"""

import tkinter as tk
from tkinter import ttk, messagebox
import traceback

from gui.welcome_page import WelcomePage
from gui.selection_page import SelectionPage
from gui.installation_page import InstallationPage
from gui.manager_page import ManagerPage
from gui.styles import apply_modern_theme
from utils.json_parser import AppDefinitionParser

class MainWindow:
    """Main application window controller"""
    
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.current_page = None
        self.current_page_type = None  # Track page type for navigation
        self.pages = {}
        
        # Try to load and validate app definitions
        try:
            self.config.validate_assets()
            self.app_parser = AppDefinitionParser(self.config.app_definitions_file)
            
            if not self.app_parser.validate_json_structure():
                raise ValueError("Invalid JSON structure in app definitions")
                
        except Exception as e:
            messagebox.showerror(
                "Configuration Error",
                f"Failed to load application definitions:\n\n{str(e)}\n\n"
                "Please check that the installer package is complete."
            )
            self.root.quit()
            return
        
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
        
        self.root.title(window_title)
        self.root.minsize(700, 500)
        
        # Configure the main grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        """Create the main container and navigation"""
        # Main container frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Content frame where pages will be displayed
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Navigation frame at bottom
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        # Navigation buttons
        self.back_button = ttk.Button(
            self.nav_frame, 
            text="← Back", 
            command=self.go_back,
            state="disabled"
        )
        self.back_button.pack(side="left")
        
        self.next_button = ttk.Button(
            self.nav_frame, 
            text="Next →", 
            command=self.go_next
        )
        self.next_button.pack(side="right")
        
        # Status label in center
        self.status_label = ttk.Label(self.nav_frame, text="Welcome")
        self.status_label.pack(side="left", expand=True)
    
    def _apply_styling(self):
        """Apply modern styling to the GUI"""
        try:
            apply_modern_theme(self.root)
        except Exception as e:
            print(f"Warning: Could not apply custom styling: {e}")
    
    def _clear_content_frame(self):
        """Clear the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def update_status_callback(self, status_text):
        """Callback function for child pages to update main window status"""
        try:
            self.status_label.config(text=status_text)
            print(f"DEBUG: Main window status updated to: {status_text}")
            
            # Enable navigation buttons when complete
            if status_text in ["Complete", "Failed", "Bundle Removal Complete"]:
                self.next_button.config(state='normal')
                self.back_button.config(state='normal')  # ENABLE BACK BUTTON
                print(f"DEBUG: Navigation buttons enabled")
            
            # Force GUI update
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"ERROR: Failed to update status: {e}")
    
    def show_welcome_page(self):
        """Show the welcome/introduction page"""
        self._clear_content_frame()
        
        suite_info = self.app_parser.get_suite_info()
        self.current_page = WelcomePage(
            self.content_frame, 
            suite_info, 
            self.app_parser.get_all_apps(),
            self.config
        )
        self.current_page_type = "welcome"
        
        # Update navigation
        self.back_button.config(state="disabled")
        self.next_button.config(text="Get Started →", state="normal")
        self.status_label.config(text="Welcome")
    
    def show_selection_page(self, success_message=None):
        """Show the application selection page"""
        print(f"DEBUG: MainWindow.show_selection_page called with message: {success_message}")
        self._clear_content_frame()
        
        self.current_page = SelectionPage(
            self.content_frame,
            self.app_parser,
            self.config
        )
        self.current_page_type = "selection"
        
        # Show success banner if provided
        if success_message:
            print(f"DEBUG: Showing success banner: {success_message}")
            self.show_success_banner(success_message)
        
        # Update navigation
        self.back_button.config(state="normal")
        # Dynamic button text based on bundle state
        if hasattr(self.current_page, 'bundle_info') and self.current_page.bundle_info["is_installed"]:
            self.next_button.config(text="Apply Changes →", state="normal")
        else:
            self.next_button.config(text="Install Selected →", state="normal")
        self.status_label.config(text="Select Applications")
        
        print("DEBUG: Selection page shown successfully")
    
    def show_success_banner(self, message):
        """Show a temporary success banner at the top of the window"""
        print(f"DEBUG: Creating success banner with message: {message}")
        
        # Create banner frame
        banner = ttk.Frame(self.main_frame, style='Success.TFrame')
        banner.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Configure success style if not already done
        try:
            style = ttk.Style()
            style.configure('Success.TFrame', background='#d4edda', relief='solid', borderwidth=1)
            style.configure('Success.TLabel', background='#d4edda', foreground='#155724', font=('Arial', 10, 'bold'))
        except:
            pass
        
        # Success message
        success_label = ttk.Label(banner, text=f"✓ {message}", style='Success.TLabel')
        success_label.pack(pady=8)
        
        # Move content frame down
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        
        # Auto-remove banner after 4 seconds (longer to ensure user sees it)
        self.root.after(4000, lambda: self._remove_banner(banner))
        
        print("DEBUG: Success banner created and scheduled for removal")

    def _remove_banner(self, banner):
        """Remove the success banner"""
        try:
            print("DEBUG: Removing success banner")
            banner.destroy()
            # Move content frame back to row 0
            self.content_frame.grid(row=0, column=0, sticky="nsew")
            print("DEBUG: Success banner removed successfully")
        except Exception as e:
            print(f"DEBUG: Error removing banner: {e}")    
    
    def show_installation_page(self, selected_apps):
        """Show the installation progress page"""
        print(f"DEBUG: MainWindow.show_installation_page called")
        self._clear_content_frame()
        
        # FIXED: Pass the status callback to InstallationPage
        self.current_page = InstallationPage(
            self.content_frame,
            selected_apps,
            self.app_parser,
            self.config,
            on_complete=self.show_manager_page,
            status_callback=self.update_status_callback  # NEW: Add callback
        )
        self.current_page_type = "installation"
        
        # Update navigation - initially disabled during installation
        self.back_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.status_label.config(text="Installing...")
        
        print("DEBUG: Installation page created successfully")
    
    def show_manager_page(self):
        """Show the application manager page"""
        print("DEBUG: MainWindow.show_manager_page called")
        self._clear_content_frame()
        
        self.current_page = ManagerPage(
            self.content_frame,
            self.app_parser,
            self.config
        )
        self.current_page_type = "manager"
        
        # Update navigation
        self.back_button.config(state="disabled")
        self.next_button.config(text="Close", state="normal")
        self.status_label.config(text="Manage Applications")
        
        print("DEBUG: Manager page shown successfully")
    
    def go_back(self):
        """Handle back button click - fixed navigation logic"""
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
                self._on_closing()
                
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
        messagebox.showerror(title, error_msg)
        print(f"ERROR: {title} - {error}")
        traceback.print_exc()
    
    def _on_closing(self):
        """Handle window closing"""
        print("DEBUG: MainWindow._on_closing called")
        if hasattr(self.current_page, 'on_closing'):
            if not self.current_page.on_closing():
                print("DEBUG: Page prevented closing")
                return  # Page prevented closing
        
        print("DEBUG: Quitting application")
        self.root.quit()

# Page interface for consistency
class BasePage:
    """Base class for all pages"""
    
    def __init__(self, parent, config=None):
        self.parent = parent
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Override in subclasses to set up the UI"""
        pass
    
    def on_next(self):
        """Called when next button is clicked. Return data if needed."""
        pass
    
    def on_back(self):
        """Called when back button is clicked"""
        pass
    
    def on_closing(self):
        """Called when window is closing. Return False to prevent closing."""
        return True
