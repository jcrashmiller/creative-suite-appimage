#!/usr/bin/env python3
"""
Linux Bundle Installer - Bundle State Detection via Desktop Files
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
"""

from pathlib import Path
from typing import List, Dict, Optional

class BundleStateDetector:
    """
    Detect bundle installation state by checking for desktop files
    
    Philosophy: The filesystem IS the state. If our .desktop files exist,
    the bundle is installed. No separate state tracking needed.
    """
    
    def __init__(self, config):
        self.config = config
        self.desktop_dir = config.user_applications_dir
        self.icons_dir = config.user_icons_dir
        self.bundle_prefix = self._get_bundle_prefix()
        
        print(f"DEBUG: BundleStateDetector initialized with prefix: {self.bundle_prefix}")
        print(f"DEBUG: Looking in desktop dir: {self.desktop_dir}")
    
    def _get_bundle_prefix(self) -> str:
        """
        Get the bundle prefix - should always be 'creative-suite' based on desktop files
        """
        # The desktop files are created with 'creative-suite' prefix consistently
        # Don't try to derive from JSON, just use the fixed prefix
        return 'creative-suite'
    
    def get_installed_bundle_apps(self) -> List[str]:
        """
        Get list of app IDs that have bundle desktop files
        
        Returns:
            List of app IDs (e.g., ['gimp', 'inkscape', 'audacity'])
        """
        installed_apps = []
        
        if not self.desktop_dir.exists():
            print(f"DEBUG: Desktop directory doesn't exist: {self.desktop_dir}")
            return installed_apps
        
        # Look for our specific desktop files
        pattern = f"{self.bundle_prefix}-*.desktop"
        print(f"DEBUG: Looking for pattern: {pattern}")
        
        found_files = list(self.desktop_dir.glob(pattern))
        print(f"DEBUG: Found desktop files: {[f.name for f in found_files]}")
        
        for desktop_file in found_files:
            # Extract app ID from filename
            # creative-suite-gimp.desktop → gimp
            filename = desktop_file.stem  # Remove .desktop extension
            
            if filename.startswith(f"{self.bundle_prefix}-"):
                app_id = filename[len(f"{self.bundle_prefix}-"):]
                
                # Skip the manager desktop file
                if app_id not in ["manager", "main"]:
                    installed_apps.append(app_id)
                    print(f"DEBUG: Found installed app: {app_id}")
        
        print(f"DEBUG: Total installed apps found: {len(installed_apps)}")
        return sorted(installed_apps)
    
    def is_app_installed_by_bundle(self, app_id: str) -> bool:
        """Check if a specific app is installed by this bundle"""
        desktop_file = self.desktop_dir / f"{self.bundle_prefix}-{app_id}.desktop"
        exists = desktop_file.exists()
        print(f"DEBUG: Checking {app_id}: {desktop_file} exists = {exists}")
        return exists
    
    def is_bundle_installed(self) -> bool:
        """Check if bundle has any installed apps"""
        installed_count = len(self.get_installed_bundle_apps())
        print(f"DEBUG: Bundle installed check: {installed_count} apps found")
        return installed_count > 0
    
    def is_manager_installed(self) -> bool:
        """Check if the bundle manager is installed"""
        manager_desktop = self.desktop_dir / f"{self.bundle_prefix}-manager.desktop"
        return manager_desktop.exists()
    
    def is_category_installed(self) -> bool:
        """Check if the bundle category is installed"""
        category_file = self.config.user_desktop_directories_dir / "X-Creative-Suite.directory"
        return category_file.exists()
    
    def get_bundle_info(self) -> Dict:
        """Get complete bundle installation information"""
        installed_apps = self.get_installed_bundle_apps()
        
        # Get app names for the installed apps
        app_names = []
        if hasattr(self.config, 'app_parser'):
            for app_id in installed_apps:
                app_name = self.config.app_parser.get_app_field(app_id, 'name')
                if app_name:
                    app_names.append(app_name)
                else:
                    app_names.append(app_id.title())  # Fallback to capitalized ID
        
        bundle_info = {
            "is_installed": len(installed_apps) > 0,
            "installed_app_ids": installed_apps,
            "installed_app_names": app_names,
            "total_installed": len(installed_apps),
            "manager_installed": self.is_manager_installed(),
            "category_installed": self.is_category_installed(),
            "bundle_prefix": self.bundle_prefix
        }
        
        print(f"DEBUG: Bundle info result: {bundle_info}")
        return bundle_info
    
    def get_missing_apps(self, all_app_ids: List[str]) -> List[str]:
        """
        Get list of app IDs that are NOT installed by this bundle
        
        Args:
            all_app_ids: List of all possible app IDs from JSON
            
        Returns:
            List of app IDs not currently installed by bundle
        """
        installed = set(self.get_installed_bundle_apps())
        all_apps = set(all_app_ids)
        return sorted(list(all_apps - installed))
    
    def get_installation_changes(self, selected_app_ids: List[str]) -> Dict:
        """
        Calculate what changes would be made for a given selection
        
        Args:
            selected_app_ids: List of app IDs user wants installed
            
        Returns:
            Dict with 'to_add', 'to_remove', and 'no_change' lists
        """
        currently_installed = set(self.get_installed_bundle_apps())
        selected = set(selected_app_ids)
        
        return {
            "to_add": sorted(list(selected - currently_installed)),
            "to_remove": sorted(list(currently_installed - selected)),
            "no_change": sorted(list(selected & currently_installed)),
            "has_changes": len(selected.symmetric_difference(currently_installed)) > 0
        }
    
    def validate_bundle_integrity(self) -> Dict:
        """
        Check if bundle installation is complete and consistent
        
        Returns:
            Dict with integrity information and any issues found
        """
        issues = []
        installed_apps = self.get_installed_bundle_apps()
        
        # Check for orphaned desktop files
        for desktop_file in self.desktop_dir.glob(f"{self.bundle_prefix}-*.desktop"):
            filename = desktop_file.stem
            app_id = filename[len(f"{self.bundle_prefix}-"):]
            
            # Check if corresponding icon exists
            icon_file = self.icons_dir / f"{self.bundle_prefix}-{app_id}.png"
            if not icon_file.exists() and app_id not in ["manager", "main"]:
                issues.append(f"Missing icon for {app_id}")
        
        # Check for orphaned icons
        for icon_file in self.icons_dir.glob(f"{self.bundle_prefix}-*.png"):
            filename = icon_file.stem
            app_id = filename[len(f"{self.bundle_prefix}-"):]
            
            desktop_file = self.desktop_dir / f"{self.bundle_prefix}-{app_id}.desktop"
            if not desktop_file.exists() and app_id not in ["manager", "main"]:
                issues.append(f"Orphaned icon for {app_id}")
        
        return {
            "is_consistent": len(issues) == 0,
            "issues": issues,
            "installed_apps": installed_apps,
            "total_desktop_files": len(list(self.desktop_dir.glob(f"{self.bundle_prefix}-*.desktop"))),
            "total_icon_files": len(list(self.icons_dir.glob(f"{self.bundle_prefix}-*.png")))
        }
