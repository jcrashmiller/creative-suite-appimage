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
Configuration and path management for Creative Suite Installer
"""

import os
import sys
from pathlib import Path

class Config:
    """Configuration class to manage paths and settings"""
    
    def __init__(self):
        # Determine if we're running from source or as an AppImage
        if getattr(sys, 'frozen', False):
            # Running as AppImage/executable
            self.app_dir = Path(sys.executable).parent
        else:
            # Running from source
            self.app_dir = Path(__file__).parent.parent.parent
        
        # Asset paths
        self.assets_dir = self.app_dir / "assets"
        self.app_definitions_file = self.assets_dir / "app_definitions.json"
        self.icons_dir = self.assets_dir / "icons"
        self.app_icons_dir = self.icons_dir / "app-icons" / "32x32"  # Point to 32x32 subdirectory
        self.suite_icons_dir = self.icons_dir / "suite-icons"
        self.desktop_files_dir = self.assets_dir / "desktop_files"
        self.images_dir = self.assets_dir / "images"
        
        # User data paths
        self.home_dir = Path.home()
        self.user_data_dir = self.home_dir / ".local" / "share" / "creative-suite"
        self.user_config_dir = self.home_dir / ".config" / "creative-suite"
        self.user_bin_dir = self.home_dir / ".local" / "bin"
        self.user_applications_dir = self.home_dir / ".local" / "share" / "applications"
        self.user_icons_dir = self.home_dir / ".local" / "share" / "icons"
        self.user_desktop_directories_dir = self.home_dir / ".local" / "share" / "desktop-directories"
        
        # State files
        self.install_state_file = self.user_data_dir / "install-state.json"
        self.user_app_definitions_file = self.user_data_dir / "app_definitions.json"
        
        # Application info
        self.app_name = "Linux Creative Suite"
        self.app_version = "1.0"
        self.app_description = "Open source alternatives to Adobe Creative Suite"
        
        # Create necessary directories
        self._create_user_directories()
    
    def _create_user_directories(self):
        """Create user directories if they don't exist"""
        directories = [
            self.user_data_dir,
            self.user_config_dir,
            self.user_bin_dir,
            self.user_applications_dir,
            self.user_icons_dir,
            self.user_desktop_directories_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_assets(self):
        """Validate that required assets exist"""
        required_files = [
            self.app_definitions_file,
        ]
        
        required_dirs = [
            self.assets_dir,
            self.icons_dir,
            self.desktop_files_dir
        ]
        
        missing_files = [f for f in required_files if not f.exists()]
        missing_dirs = [d for d in required_dirs if not d.exists()]
        
        if missing_files or missing_dirs:
            error_msg = "Missing required assets:\n"
            if missing_files:
                error_msg += "Files: " + ", ".join(str(f) for f in missing_files) + "\n"
            if missing_dirs:
                error_msg += "Directories: " + ", ".join(str(d) for d in missing_dirs)
            raise FileNotFoundError(error_msg)
        
        return True
    
    def get_relative_path(self, path):
        """Get a path relative to the app directory"""
        try:
            return Path(path).relative_to(self.app_dir)
        except ValueError:
            return Path(path)
    
    def __str__(self):
        """String representation for debugging"""
        return f"""Creative Suite Config:
App Dir: {self.app_dir}
Assets Dir: {self.assets_dir}
User Data Dir: {self.user_data_dir}
App Definitions: {self.app_definitions_file}
"""

# Global config instance
config_instance = None

def get_config():
    """Get the global config instance"""
    global config_instance
    if config_instance is None:
        config_instance = Config()
    return config_instance
