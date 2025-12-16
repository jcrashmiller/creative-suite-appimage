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

"""Modern styling for tkinter GUI"""
import tkinter as tk
from tkinter import ttk

def apply_modern_theme(root):
    """Apply modern theme to the application"""
    style = ttk.Style()
    
    # Use a more modern theme if available
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')
    
    # Configure some basic styling
    style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
    style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
    style.configure('Big.TButton', font=('Arial', 12))
