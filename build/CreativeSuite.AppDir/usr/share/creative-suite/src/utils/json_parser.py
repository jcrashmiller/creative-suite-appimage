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
JSON parsing utilities for app definitions
Adapted from the bash script logic
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

class AppDefinitionParser:
    """Parser for app_definitions.json file"""
    
    def __init__(self, json_file_path: Path):
        self.json_file_path = json_file_path
        self.data = None
        self._load_json()
    
    def _load_json(self):
        """Load and parse the JSON file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"App definitions file not found: {self.json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in app definitions file: {e}")
    
    def get_suite_info(self) -> Dict[str, str]:
        """Get general suite information"""
        return self.data.get('suite', {})
    
    def get_all_apps(self) -> List[Dict[str, Any]]:
        """Get list of all applications"""
        return self.data.get('apps', [])
    
    def get_app_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific app by its ID"""
        for app in self.get_all_apps():
            if app.get('id') == app_id:
                return app
        return None
    
    def get_app_field(self, app_id: str, field: str) -> Optional[Any]:
        """Get a specific field from an app (equivalent to bash get_app_field function)"""
        app = self.get_app_by_id(app_id)
        if app:
            return app.get(field)
        return None
    
    def get_all_app_ids(self) -> List[str]:
        """Get list of all app IDs"""
        return [app.get('id') for app in self.get_all_apps() if app.get('id')]
    
    def get_apps_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group apps by category"""
        categories = {}
        for app in self.get_all_apps():
            category = app.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(app)
        return categories
    
    def get_required_apps(self) -> List[Dict[str, Any]]:
        """Get list of required applications"""
        return [app for app in self.get_all_apps() if app.get('required', False)]
    
    def get_default_selected_apps(self) -> List[Dict[str, Any]]:
        """Get list of apps that should be selected by default"""
        return [app for app in self.get_all_apps() if app.get('default_selected', False)]
    
    def get_packages_for_manager(self, app_id: str, package_manager: str) -> List[str]:
        """Get package list for a specific package manager"""
        app = self.get_app_by_id(app_id)
        if not app:
            return []
        
        packages = app.get(package_manager, [])
        if isinstance(packages, str):
            # Handle single package as string
            return [packages] if packages else []
        elif isinstance(packages, list):
            # Handle list of packages
            return [pkg for pkg in packages if pkg]
        else:
            return []
    
    def get_flatpak_id(self, app_id: str) -> Optional[str]:
        """Get Flatpak ID for an app"""
        return self.get_app_field(app_id, 'flatpak')
    
    def get_snap_id(self, app_id: str) -> Optional[str]:
        """Get Snap ID for an app"""
        return self.get_app_field(app_id, 'snap')
    
    def validate_json_structure(self) -> bool:
        """Validate that the JSON has the expected structure"""
        if not isinstance(self.data, dict):
            return False
        
        # Check for required top-level keys
        if 'suite' not in self.data or 'apps' not in self.data:
            return False
        
        # Check suite structure
        suite = self.data['suite']
        required_suite_fields = ['name', 'version', 'description']
        if not all(field in suite for field in required_suite_fields):
            return False
        
        # Check apps structure
        apps = self.data['apps']
        if not isinstance(apps, list):
            return False
        
        # Check each app has required fields
        required_app_fields = ['id', 'name', 'description', 'category']
        for app in apps:
            if not isinstance(app, dict):
                return False
            if not all(field in app for field in required_app_fields):
                return False
        
        return True
    
    def copy_to_user_location(self, destination_path: Path):
        """Copy the JSON file to user's data directory"""
        try:
            shutil.copy2(self.json_file_path, destination_path)
            return True
        except Exception as e:
            print(f"Error copying JSON file: {e}")
            return False

# Convenience functions for backwards compatibility with bash script logic
def get_app_field(json_file_path: Path, app_id: str, field: str) -> Optional[Any]:
    """Standalone function equivalent to bash get_app_field"""
    parser = AppDefinitionParser(json_file_path)
    return parser.get_app_field(app_id, field)

def get_all_app_ids(json_file_path: Path) -> List[str]:
    """Standalone function equivalent to bash get_all_app_ids"""
    parser = AppDefinitionParser(json_file_path)
    return parser.get_all_app_ids()

# Utility function to check if jq equivalent functionality is available
def has_json_support() -> bool:
    """Check if we can parse JSON (always True in Python)"""
    return True
