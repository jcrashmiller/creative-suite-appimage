#!/usr/bin/env python3
"""
Linux Bundle Installer - Enhanced Bundle State Detection with Availability
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
Enhanced: 2025-06-05
"""

from pathlib import Path
from typing import List, Dict, Optional

# Import our new availability detector
from core.app_availability_detector import AppAvailabilityDetector, AppAvailability

class BundleStateDetector:
    """
    Detect bundle installation state by checking for desktop files
    Enhanced with application availability detection
    
    Philosophy: The filesystem IS the state. If our .desktop files exist,
    the bundle is installed. Additionally, verify that target apps are actually available.
    """
    
    def __init__(self, config):
        self.config = config
        self.desktop_dir = config.user_applications_dir
        self.icons_dir = config.user_icons_dir
        self.bundle_prefix = self._get_bundle_prefix()
        
        # Initialize availability detector
        self.availability_detector = AppAvailabilityDetector()
        
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
    
    def get_bundle_info_with_availability(self, app_parser=None) -> Dict:
        """
        Get complete bundle installation information with availability status
        
        This is the enhanced version that checks actual app availability
        """
        installed_apps = self.get_installed_bundle_apps()
        
        # Get app names for the installed apps
        app_names = []
        availability_info = {}
        
        if app_parser:
            # Get all apps from JSON to check availability
            all_apps = app_parser.get_all_apps()
            
            # Detect availability for all apps
            availability_results = self.availability_detector.detect_multiple_apps(all_apps, app_parser)
            
            # Process installed bundle apps
            for app_id in installed_apps:
                app_name = app_parser.get_app_field(app_id, 'name')
                if app_name:
                    app_names.append(app_name)
                else:
                    app_names.append(app_id.title())  # Fallback to capitalized ID
                
                # Store availability info
                availability_info[app_id] = availability_results.get(app_id)
        
        bundle_info = {
            "is_installed": len(installed_apps) > 0,
            "installed_app_ids": installed_apps,
            "installed_app_names": app_names,
            "total_installed": len(installed_apps),
            "manager_installed": self.is_manager_installed(),
            "category_installed": self.is_category_installed(),
            "bundle_prefix": self.bundle_prefix,
            "availability_info": availability_info  # NEW: Detailed availability data
        }
        
        # Add summary of app states
        if availability_info:
            available_count = sum(1 for avail in availability_info.values() 
                                if avail and avail.is_available)
            orphaned_count = len(installed_apps) - available_count
            
            bundle_info.update({
                "apps_available": available_count,
                "apps_orphaned": orphaned_count,
                "has_orphaned_entries": orphaned_count > 0
            })
        
        print(f"DEBUG: Enhanced bundle info result: {bundle_info}")
        return bundle_info
    
    def get_bundle_info(self) -> Dict:
        """Get basic bundle installation information (backward compatibility)"""
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
    
    def get_orphaned_entries(self, app_parser) -> List[Dict]:
        """
        Get list of bundle menu entries that point to uninstalled applications
        
        Returns list of dicts with app info and availability status
        """
        installed_bundle_apps = self.get_installed_bundle_apps()
        orphaned_entries = []
        
        if not installed_bundle_apps:
            return orphaned_entries
        
        # Get app data for installed bundle apps
        bundle_app_data = []
        for app_id in installed_bundle_apps:
            app_data = app_parser.get_app_by_id(app_id)
            if app_data:
                bundle_app_data.append(app_data)
        
        # Check availability
        availability_results = self.availability_detector.detect_multiple_apps(bundle_app_data, app_parser)
        
        # Find orphaned entries
        for app_id in installed_bundle_apps:
            availability = availability_results.get(app_id)
            if availability and not availability.is_available:
                app_data = app_parser.get_app_by_id(app_id)
                orphaned_entries.append({
                    'app_id': app_id,
                    'app_data': app_data,
                    'availability': availability
                })
        
        print(f"DEBUG: Found {len(orphaned_entries)} orphaned entries")
        return orphaned_entries
    
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
    
    def invalidate_availability_cache(self):
        """Invalidate availability cache (call after installing/removing apps)"""
        self.availability_detector.invalidate_cache()
