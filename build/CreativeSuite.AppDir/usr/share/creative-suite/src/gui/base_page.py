#!/usr/bin/env python3
"""
Linux Bundle Installer - Base Page Class (PySide2 Version)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Ported to PySide2: 2025-07-12
"""

from PySide2.QtWidgets import QWidget

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
