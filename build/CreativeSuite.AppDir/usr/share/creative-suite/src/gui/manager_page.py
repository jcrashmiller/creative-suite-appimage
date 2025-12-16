#!/usr/bin/env python3
"""
Linux Bundle Installer - Manager Page (PySide2 Version)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Ported to PySide2: 2025-07-12
"""

from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from gui.base_page import BasePage

class ManagerPage(BasePage):
    def __init__(self, parent, app_parser, config):
        self.app_parser = app_parser
        super().__init__(parent, config)
    
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Manage Applications")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Company branding
        branding = QLabel("Loading Screen Solutions - Empowering you to use your tech, your way")
        branding.setAlignment(Qt.AlignCenter)
        branding.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 10px;
                font-style: italic;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(branding)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Future management features placeholder
        placeholder = QLabel("Application management features coming soon...")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #999999;
                background-color: #f8f9fa;
                border: 2px dashed #dddddd;
                border-radius: 8px;
                padding: 40px;
                margin: 20px;
            }
        """)
        content_layout.addWidget(placeholder)
        
        # Add some spacing
        content_layout.addStretch()
        
        layout.addWidget(content_widget, 1)  # Give it stretch priority
        
        # Success message area (if needed later)
        success_info = QLabel(
            "Installation completed successfully!\n\n"
            "Your selected applications have been installed and are now available "
            "in your application menu under the Creative Suite category.\n\n"
            "You can close this installer and start using your new applications."
        )
        success_info.setWordWrap(True)
        success_info.setAlignment(Qt.AlignCenter)
        success_info.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                border-radius: 6px;
                padding: 15px;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(success_info)
