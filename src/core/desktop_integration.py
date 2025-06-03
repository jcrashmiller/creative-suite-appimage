#!/usr/bin/env python3
"""
Linux Bundle Installer - Desktop Integration
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Dict

class DesktopIntegrator:
    """Handle desktop file and icon installation"""
    
    def __init__(self, config):
        self.config = config
    
    def install_icons(self):
        """Install custom icons to user directory"""
        source_icons_dir = self.config.app_icons_dir
        target_icons_dir = self.config.user_icons_dir
        
        if not source_icons_dir.exists():
            print(f"Warning: Source icons directory not found: {source_icons_dir}")
            return False
        
        # Ensure target directory exists
        target_icons_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all icons
        icons_copied = 0
        for icon_file in source_icons_dir.glob("*.png"):
            target_file = target_icons_dir / icon_file.name
            try:
                shutil.copy2(icon_file, target_file)
                icons_copied += 1
            except Exception as e:
                print(f"Warning: Could not copy icon {icon_file.name}: {e}")
        
        print(f"Copied {icons_copied} custom icons")
        
        # Update icon cache if possible
        try:
            subprocess.run(['gtk-update-icon-cache', str(target_icons_dir)], 
                         capture_output=True, check=False, timeout=10)
        except:
            pass  # Icon cache update is optional
        
        return icons_copied > 0
    
    def install_desktop_files(self, selected_apps: List[Dict]):
        """Install desktop files for selected applications"""
        source_desktop_dir = self.config.desktop_files_dir
        target_desktop_dir = self.config.user_applications_dir
        target_directory_dir = self.config.user_desktop_directories_dir
        
        if not source_desktop_dir.exists():
            print(f"Warning: Source desktop files directory not found: {source_desktop_dir}")
            return False
        
        # Ensure target directories exist
        target_desktop_dir.mkdir(parents=True, exist_ok=True)
        target_directory_dir.mkdir(parents=True, exist_ok=True)
        
        # Get suite info for directory file
        suite_info = self.config.app_parser.get_suite_info() if hasattr(self.config, 'app_parser') else {}
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Install the Creative Suite category directory file
        self.create_category_directory_file(target_directory_dir, suite_name)
        
        # Install desktop files for selected apps
        desktop_files_installed = 0
        for app in selected_apps:
            app_id = app.get('id')
            if not app_id:
                continue
            
            # Look for desktop file
            desktop_file_name = f"creative-suite-{app_id}.desktop"
            source_desktop_file = source_desktop_dir / desktop_file_name
            
            if source_desktop_file.exists():
                target_desktop_file = target_desktop_dir / desktop_file_name
                try:
                    shutil.copy2(source_desktop_file, target_desktop_file)
                    desktop_files_installed += 1
                    print(f"Installed desktop file for {app.get('name', app_id)}")
                except Exception as e:
                    print(f"Warning: Could not install desktop file for {app_id}: {e}")
            else:
                print(f"Warning: Desktop file not found: {desktop_file_name}")
        
        # Hide original system desktop files to prevent duplicates
        self.hide_system_desktop_files(selected_apps, target_desktop_dir)
        
        # Update desktop database
        try:
            subprocess.run(['update-desktop-database', str(target_desktop_dir)], 
                         capture_output=True, check=False, timeout=10)
        except:
            pass  # Desktop database update is optional
        
        print(f"Installed {desktop_files_installed} desktop files")
        return desktop_files_installed > 0
    
    def create_category_directory_file(self, target_dir: Path, suite_name: str):
        """Create the Creative Suite category directory file"""
        directory_file = target_dir / "X-Creative-Suite.directory"
        
        directory_content = f"""[Desktop Entry]
Version=1.0
Type=Directory
Name={suite_name}
Comment=Open source alternatives to proprietary creative software
Icon=creative-suite-main
Name[en_US]={suite_name}
"""
        
        try:
            with open(directory_file, 'w', encoding='utf-8') as f:
                f.write(directory_content)
            print(f"Created category directory file for {suite_name}")
        except Exception as e:
            print(f"Warning: Could not create category directory file: {e}")
    
    def hide_system_desktop_files(self, selected_apps: List[Dict], target_dir: Path):
        """Hide original system desktop files to prevent duplicates"""
        for app in selected_apps:
            app_id = app.get('id')
            if not app_id:
                continue
            
            # Create hidden desktop file that overrides system one
            system_desktop_paths = [
                Path(f"/usr/share/applications/{app_id}.desktop"),
                Path(f"/usr/local/share/applications/{app_id}.desktop")
            ]
            
            # Check if system desktop file exists
            system_file_exists = any(path.exists() for path in system_desktop_paths)
            
            if system_file_exists:
                hidden_desktop_file = target_dir / f"{app_id}.desktop"
                hidden_content = f"""[Desktop Entry]
Type=Application
Name={app_id}
NoDisplay=true
Hidden=true
"""
                try:
                    with open(hidden_desktop_file, 'w', encoding='utf-8') as f:
                        f.write(hidden_content)
                    print(f"Hidden system desktop file for {app_id}")
                except Exception as e:
                    print(f"Warning: Could not hide system desktop file for {app_id}: {e}")
    
    def create_manager_script(self):
        """Create the Creative Suite manager script - DISABLED: Not needed for Python version"""
        print("Manager script creation skipped - handled by Python application")
        return True
    
    def create_manager_desktop_entry(self):
        """Create desktop entry for the Creative Suite manager - DISABLED: Not needed for Python version"""
        print("Manager desktop entry creation skipped - handled by Python application")
        return True
    
    def remove_apps_from_bundle(self, app_ids: List[str]) -> int:
        """
        Remove specific apps from bundle (for modification, not complete removal)
        
        Args:
            app_ids: List of app IDs to remove from bundle
            
        Returns:
            Number of apps successfully removed
        """
        target_desktop_dir = self.config.user_applications_dir
        target_icons_dir = self.config.user_icons_dir
        
        removed_count = 0
        
        print(f"Removing {len(app_ids)} applications from bundle...")
        
        # Remove bundle desktop files for specified apps
        for app_id in app_ids:
            # Remove bundle desktop file
            bundle_desktop_file = target_desktop_dir / f"creative-suite-{app_id}.desktop"
            if bundle_desktop_file.exists():
                try:
                    bundle_desktop_file.unlink()
                    removed_count += 1
                    print(f"✓ Removed bundle menu entry for {app_id}")
                except Exception as e:
                    print(f"Warning: Could not remove bundle menu entry for {app_id}: {e}")
            
            # Remove hidden system desktop file (restore original)
            hidden_desktop_file = target_desktop_dir / f"{app_id}.desktop"
            if hidden_desktop_file.exists():
                try:
                    # Check if this is our hidden file
                    with open(hidden_desktop_file, 'r') as f:
                        content = f.read()
                    if "NoDisplay=true" in content and "Hidden=true" in content:
                        hidden_desktop_file.unlink()
                        print(f"✓ Restored original menu entry for {app_id}")
                except Exception as e:
                    print(f"Warning: Could not restore original menu entry for {app_id}: {e}")
            
            # Remove bundle icons
            for icon_ext in ['.png', '.svg']:
                icon_file = target_icons_dir / f"creative-suite-{app_id}{icon_ext}"
                if icon_file.exists():
                    try:
                        icon_file.unlink()
                        print(f"✓ Removed custom icon for {app_id}")
                    except Exception as e:
                        print(f"Warning: Could not remove icon for {app_id}: {e}")
        
        # Update desktop database
        try:
            subprocess.run(['update-desktop-database', str(target_desktop_dir)], 
                         capture_output=True, check=False, timeout=10)
            print("✓ Updated desktop database")
        except:
            pass
        
        print(f"Successfully removed {removed_count} applications from bundle")
        return removed_count
    
    def show_bundle_removal_explanation(self, suite_name: str, app_names: List[str]) -> bool:
        """
        Show user explanation of what bundle removal does
        Returns: True if user confirms, False if cancelled
        """
        import tkinter as tk
        from tkinter import messagebox
        
        explanation = f"""Bundle Removal - What This Does:

✓ Removes {suite_name} menu entries and custom icons
✓ Removes {suite_name} category from your application menu

✗ DOES NOT uninstall the applications themselves:
"""
        
        for app_name in app_names[:8]:  # Show first 8 apps
            explanation += f"\n  • {app_name}"
        
        if len(app_names) > 8:
            explanation += f"\n  • ... and {len(app_names) - 8} more"
        
        explanation += f"""

These applications remain installed and usable:
• They keep their original menu entries
• You can still launch them normally
• Other bundles using them are unaffected

To remove applications from your system:
sudo apt autoremove
(or use your system's package manager)

Continue with {suite_name} removal?"""
        
        return messagebox.askyesno(
            f"Remove {suite_name}",
            explanation
        )
    
    def remove_entire_bundle(self, suite_name: str) -> bool:
        """
        Remove entire bundle integration
        
        Args:
            suite_name: Name of the suite for user confirmation
            
        Returns:
            True if removal completed, False if cancelled
        """
        from core.bundle_state_detector import BundleStateDetector
        
        # Get current bundle state
        state_detector = BundleStateDetector(self.config)
        bundle_info = state_detector.get_bundle_info()
        
        if not bundle_info["is_installed"]:
            print("No bundle installation found")
            return True
        
        app_ids = bundle_info["installed_app_ids"]
        app_names = bundle_info["installed_app_names"]
        
        # Show explanation and get confirmation
        if not self.show_bundle_removal_explanation(suite_name, app_names):
            return False  # User cancelled
        
        return self.uninstall_bundle_integration(app_ids, suite_name, app_names)
    
    def uninstall_bundle_integration(self, app_ids: List[str], suite_name: str = None, app_names: List[str] = None):
        """
        Remove desktop integration for a bundle (bundle-scoped uninstall)
        
        Args:
            app_ids: List of app IDs to remove integration for
            suite_name: Name of the suite being removed (for user dialog)
            app_names: Human-readable app names (for user dialog)
        """
        target_desktop_dir = self.config.user_applications_dir
        target_icons_dir = self.config.user_icons_dir
        
        removed_count = 0
        
        print(f"Removing {suite_name or 'bundle'} integration...")
        
        # Remove bundle desktop files
        for app_id in app_ids:
            # Remove bundle desktop file
            bundle_desktop_file = target_desktop_dir / f"creative-suite-{app_id}.desktop"
            if bundle_desktop_file.exists():
                try:
                    bundle_desktop_file.unlink()
                    removed_count += 1
                    print(f"✓ Removed menu entry for {app_id}")
                except Exception as e:
                    print(f"Warning: Could not remove menu entry for {app_id}: {e}")
            
            # Remove hidden system desktop file (restore original)
            hidden_desktop_file = target_desktop_dir / f"{app_id}.desktop"
            if hidden_desktop_file.exists():
                try:
                    # Check if this is our hidden file
                    with open(hidden_desktop_file, 'r') as f:
                        content = f.read()
                    if "NoDisplay=true" in content and "Hidden=true" in content:
                        hidden_desktop_file.unlink()
                        print(f"✓ Restored original menu entry for {app_id}")
                except Exception as e:
                    print(f"Warning: Could not restore original menu entry for {app_id}: {e}")
            
            # Remove bundle icons
            for icon_ext in ['.png', '.svg']:
                icon_file = target_icons_dir / f"creative-suite-{app_id}{icon_ext}"
                if icon_file.exists():
                    try:
                        icon_file.unlink()
                        print(f"✓ Removed custom icon for {app_id}")
                    except Exception as e:
                        print(f"Warning: Could not remove icon for {app_id}: {e}")
        
        # Remove the manager desktop entry if this is a complete uninstall
        manager_desktop_file = target_desktop_dir / "creative-suite-manager.desktop"
        if manager_desktop_file.exists():
            try:
                manager_desktop_file.unlink()
                print("✓ Removed bundle manager menu entry")
            except Exception as e:
                print(f"Warning: Could not remove manager menu entry: {e}")
        
        # Remove the category directory file
        target_directory_dir = self.config.user_desktop_directories_dir
        category_file = target_directory_dir / "X-Creative-Suite.directory"
        if category_file.exists():
            try:
                category_file.unlink()
                print("✓ Removed bundle category")
            except Exception as e:
                print(f"Warning: Could not remove category file: {e}")
        
        # Update desktop database
        try:
            subprocess.run(['update-desktop-database', str(target_desktop_dir)], 
                         capture_output=True, check=False, timeout=10)
            print("✓ Updated desktop database")
        except:
            pass
        
        # Update icon cache
        try:
            subprocess.run(['gtk-update-icon-cache', str(target_icons_dir)], 
                         capture_output=True, check=False, timeout=10)
            print("✓ Updated icon cache")
        except:
            pass
        
        print(f"\n✓ Bundle removal complete!")
        print(f"✓ Removed menu integration for {removed_count} applications")
        print(f"✓ Applications remain installed and available")
        
        return True
