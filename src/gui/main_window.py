#!/usr/bin/env python3
"""
Linux Bundle Installer - Application Selection GUI
Copyright (c) 2025 Loading Screen Solutions
https://github.com/LoadingScreenSolutions/linux-bundle-installer

This file is part of Linux Bundle Installer.

Linux Bundle Installer is free software: you can redistribute it and/or modify
it under the terms of the MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

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
        
        # Start with welcome page
        self.show_welcome_page()
    
    def _setup_window(self):
        """Configure the main window with JSON-driven titles"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle Installer')
        suite_version = suite_info.get('version', '1.0')
        
        # Dynamic window title
        window_title = f"{suite_name} Installer v{suite_version}"
        
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
        
        # Update navigation
        self.back_button.config(state="disabled")
        self.next_button.config(text="Get Started →", state="normal")
        self.status_label.config(text="Welcome")
    
    def show_selection_page(self):
        """Show the application selection page"""
        self._clear_content_frame()
        
        self.current_page = SelectionPage(
            self.content_frame,
            self.app_parser,
            self.config
        )
        
        # Update navigation
        self.back_button.config(state="normal")
        self.next_button.config(text="Install Selected →", state="normal")
        self.status_label.config(text="Select Applications")
    
    def show_installation_page(self, selected_apps):
        """Show the installation progress page"""
        self._clear_content_frame()
        
        self.current_page = InstallationPage(
            self.content_frame,
            selected_apps,
            self.app_parser,
            self.config,
            on_complete=self.show_manager_page
        )
        
        # Update navigation
        self.back_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.status_label.config(text="Installing...")
    
    def show_manager_page(self):
        """Show the application manager page"""
        self._clear_content_frame()
        
        self.current_page = ManagerPage(
            self.content_frame,
            self.app_parser,
            self.config
        )
        
        # Update navigation
        self.back_button.config(state="disabled")
        self.next_button.config(text="Close", state="normal")
        self.status_label.config(text="Manage Applications")
    
    def go_back(self):
        """Handle back button click"""
        try:
            if hasattr(self.current_page, 'on_back'):
                self.current_page.on_back()
            else:
                # Default back behavior
                if isinstance(self.current_page, SelectionPage):
                    self.show_welcome_page()
                elif isinstance(self.current_page, ManagerPage):
                    self.show_selection_page()
        except Exception as e:
            self._handle_error("Navigation Error", e)
    
    def go_next(self):
        """Handle next button click"""
        try:
            if hasattr(self.current_page, 'on_next'):
                result = self.current_page.on_next()
                
                # Handle page transitions based on current page
                if isinstance(self.current_page, WelcomePage):
                    self.show_selection_page()
                elif isinstance(self.current_page, SelectionPage):
                    if result:  # result should be selected apps
                        self.show_installation_page(result)
                elif isinstance(self.current_page, ManagerPage):
                    self._on_closing()
            else:
                # Default next behavior
                if isinstance(self.current_page, WelcomePage):
                    self.show_selection_page()
                elif isinstance(self.current_page, ManagerPage):
                    self._on_closing()
        except Exception as e:
            self._handle_error("Navigation Error", e)
    
    def _handle_error(self, title, error):
        """Handle and display errors"""
        error_msg = f"An error occurred:\n\n{str(error)}\n\nDetails:\n{traceback.format_exc()}"
        messagebox.showerror(title, error_msg)
    
    def _on_closing(self):
        """Handle window closing"""
        if hasattr(self.current_page, 'on_closing'):
            if not self.current_page.on_closing():
                return  # Page prevented closing
        
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
