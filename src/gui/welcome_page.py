#!/usr/bin/env python3
"""
Linux Bundle Installer - Welcome Page (PySide2 Version)
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Ported to PySide2: 2025-07-12
"""

from pathlib import Path
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QPixmap
from gui.base_page import BasePage

# Loading Screen Solutions logo image
LSS_LOGO_PATH = Path(__file__).parent.parent.parent / "assets" / "icons" / "suite-icons" / "lss-logo-transparent-bg.png"

class WelcomePage(BasePage):
    def __init__(self, parent, suite_info, all_apps, config):
        self.suite_info = suite_info
        self.all_apps = all_apps
        super().__init__(parent, config)
    
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)
        
        # Welcome content
        title = QLabel("Linux Creative Suite")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        description = QLabel("Open source alternatives to Adobe Creative Suite")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc_font.setBold(True)
        description.setFont(desc_font)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666666; margin-bottom: 10px;")
        layout.addWidget(description)
        
        info_text = """Welcome to the Linux Creative Suite installer!

This installer will help you set up powerful open-source alternatives 
to Adobe Creative Suite applications, including:

• GIMP (Photoshop alternative)
• Inkscape (Illustrator alternative) 
• Kdenlive (Premiere Pro alternative)
• Blender (After Effects alternative)
• And many more...

Click 'Get Started' to begin selecting applications."""
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignLeft)
        info_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                line-height: 1.4;
                padding: 20px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
            }
        """)
        layout.addWidget(info_label, 1)  # Give it stretch priority
        
        # Add LSS credits section at the bottom
        self.create_credits_section(layout)
    
    def create_credits_section(self, layout):
        """Create the Loading Screen Solutions credits section"""
        try:
            if LSS_LOGO_PATH.exists():
                # Credits frame
                credits_frame = QWidget()
                credits_layout = QHBoxLayout(credits_frame)
                credits_layout.setContentsMargins(0, 30, 0, 20)
                
                # Logo label
                logo_label = QLabel()
                logo_pixmap = QPixmap(str(LSS_LOGO_PATH))
                # Scale the logo to a reasonable size
                scaled_pixmap = logo_pixmap.scaled(60, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                credits_layout.addWidget(logo_label)
                
                # Credits text
                credits_text = """Developed by
Loading Screen Solutions
Technology consulting & liberation"""
                
                credits_label = QLabel(credits_text)
                credits_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 9px;
                        margin-left: 10px;
                    }
                """)
                credits_layout.addWidget(credits_label)
                
                # Add stretch to center the credits
                credits_layout.addStretch()
                
                layout.addWidget(credits_frame)
                
        except Exception as e:
            print(f"Could not load LSS logo: {e}")
            # Fallback to text-only credits
            credits_text = """Developed by Loading Screen Solutions
Technology consulting & liberation"""
            
            credits_label = QLabel(credits_text)
            credits_label.setAlignment(Qt.AlignCenter)
            credits_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 9px;
                    font-style: italic;
                    margin-top: 30px;
                    margin-bottom: 20px;
                }
            """)
            layout.addWidget(credits_label)
