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
Linux Creative Suite Installer
Entry point for the GUI application
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback

# Add src directory to Python path for imports
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Now we can use absolute imports
from gui.main_window import MainWindow
from core.config import Config

def check_requirements():
    """Check if we're running with appropriate permissions and dependencies"""
    # Check if we're running as root (we shouldn't be)
    if os.geteuid() == 0:
        messagebox.showerror(
            "Error", 
            "Please do not run this installer as root.\n"
            "The installer will request sudo permissions when needed."
        )
        return False
    
    # Check if we have a desktop environment
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        print("Error: No display environment detected.")
        print("This installer requires a graphical desktop environment.")
        return False
    
    return True

def main():
    """Main application entry point"""
    try:
        # Check system requirements
        if not check_requirements():
            sys.exit(1)
        
        # Initialize configuration
        config = Config()
        
        # Create the main tkinter window
        root = tk.Tk()
        
        # Set some basic window properties
        root.title("Linux Creative Suite Installer")
        root.geometry("800x600")
        root.resizable(True, True)
        
        # Center the window on screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (800 // 2)
        y = (root.winfo_screenheight() // 2) - (600 // 2)
        root.geometry(f"800x600+{x}+{y}")
        
        # Create and start the main application
        app = MainWindow(root, config)
        
        # Start the GUI event loop
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nInstaller interrupted by user")
        sys.exit(0)
    except Exception as e:
        # Show error dialog for unexpected errors
        error_msg = f"An unexpected error occurred:\n\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        
        try:
            messagebox.showerror("Fatal Error", error_msg)
        except:
            # If GUI fails, print to console
            print("FATAL ERROR:")
            print(error_msg)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
