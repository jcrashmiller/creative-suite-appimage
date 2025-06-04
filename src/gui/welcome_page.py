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

"""Welcome page placeholder"""
import tkinter as tk
from tkinter import ttk
from gui.base_page import BasePage
from pathlib import Path

# Loading Screen Solutions logo image
LSS_LOGO_PATH = Path(__file__).parent.parent.parent / "assets" / "icons" / "suite-icons" / "lss-logo-transparent-bg.png"

class WelcomePage(BasePage):
    def __init__(self, parent, suite_info, all_apps, config):
        self.suite_info = suite_info
        self.all_apps = all_apps
        super().__init__(parent, config)
    
    def setup_ui(self):
        # Welcome content
        title = ttk.Label(self.parent, text="Linux Creative Suite", style='Title.TLabel')
        title.pack(pady=20)
        
        description = ttk.Label(
            self.parent, 
            text="Open source alternatives to Adobe Creative Suite",
            style='Heading.TLabel'
        )
        description.pack(pady=10)
        
        info_text = """Welcome to the Linux Creative Suite installer!

    This installer will help you set up powerful open-source alternatives 
    to Adobe Creative Suite applications, including:

    - GIMP (Photoshop alternative)
    - Inkscape (Illustrator alternative) 
    - Kdenlive (Premiere Pro alternative)
    - Blender (After Effects alternative)
    - And many more...

    Click 'Get Started' to begin selecting applications."""
        
        info_label = ttk.Label(self.parent, text=info_text, justify='left')
        info_label.pack(pady=20, padx=40, expand=True)

        # Add LSS credits section at the bottom
        try:
            if LSS_LOGO_PATH.exists():
                # Credits frame
                credits_frame = ttk.Frame(self.parent)
                credits_frame.pack(pady=(30, 20))
                
                # Load and resize logo
                from PIL import Image, ImageTk
                logo_image = Image.open(LSS_LOGO_PATH)
                # Resize to reasonable size (adjust as needed)
                logo_image = logo_image.resize((60, 40), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                
                # Logo label
                logo_label = ttk.Label(credits_frame, image=self.logo_photo)
                logo_label.pack(side="left", padx=(0, 10))
                
                # Credits text
                credits_text = """Developed by
    Loading Screen Solutions
    Technology consulting & liberation"""
                
                credits_label = ttk.Label(
                    credits_frame, 
                    text=credits_text,
                    font=('Arial', 9),
                    foreground='gray',
                    justify='left'
                )
                credits_label.pack(side="left")
                
        except Exception as e:
            print(f"Could not load LSS logo: {e}")
            # Fallback to text-only credits
            credits_text = """Developed by Loading Screen Solutions
    Technology consulting & liberation"""
            
            credits_label = ttk.Label(
                self.parent,
                text=credits_text,
                font=('Arial', 9, 'italic'),
                foreground='gray',
                justify='center'
            )
            credits_label.pack(pady=(30, 20))