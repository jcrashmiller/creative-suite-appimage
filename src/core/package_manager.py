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

import subprocess
import shutil
import os
from typing import List, Optional, Tuple
from pathlib import Path

class PackageManager:
    """
    Handle package installation across different Linux distributions
    
    Philosophy: Install missing apps, leave existing ones alone.
    Never uninstall packages - only manage menu entries.
    """
    
    def __init__(self):
        self.detected_manager = self._detect_package_manager()
        self.flatpak_available = self._check_flatpak_status()
        self.snap_available = self._check_snap_status()
    
    def _detect_package_manager(self) -> str:
        """Detect the system's package manager"""
        # Check for apt (Debian/Ubuntu/Mint)
        if shutil.which('apt') and shutil.which('dpkg'):
            return 'apt'
        
        # Check for dnf (Fedora)
        elif shutil.which('dnf'):
            return 'dnf'
        
        # Check for yum (older RHEL/CentOS)
        elif shutil.which('yum'):
            return 'yum'
        
        # Check for pacman (Arch/Manjaro)
        elif shutil.which('pacman'):
            return 'pacman'
        
        # Check for zypper (openSUSE)
        elif shutil.which('zypper'):
            return 'zypper'
        
        else:
            return 'unknown'
    
    def _check_flatpak_status(self) -> bool:
        """Check if Flatpak is available and functional"""
        if not shutil.which('flatpak'):
            return False
        
        try:
            # Check if flatpak is working
            result = subprocess.run(['flatpak', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
            
            # Check if flathub repo exists
            result = subprocess.run(['flatpak', 'remotes'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
            
            return 'flathub' in result.stdout.lower()
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def _check_snap_status(self) -> bool:
        """Check if Snap is available and functional"""
        if not shutil.which('snap'):
            return False
        
        try:
            result = subprocess.run(['snap', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def is_package_installed(self, package_name: str) -> bool:
        """Check if a package is already installed via the native package manager"""
        try:
            if self.detected_manager == 'apt':
                # Use dpkg to check if package is installed
                result = subprocess.run(['dpkg', '-l', package_name], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0 and 'ii' in result.stdout
            
            elif self.detected_manager == 'dnf':
                result = subprocess.run(['rpm', '-q', package_name], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            
            elif self.detected_manager == 'yum':
                result = subprocess.run(['rpm', '-q', package_name], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            
            elif self.detected_manager == 'pacman':
                result = subprocess.run(['pacman', '-Q', package_name], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            
            elif self.detected_manager == 'zypper':
                result = subprocess.run(['zypper', 'search', '-i', package_name], 
                                      capture_output=True, text=True, timeout=10)
                return result.returncode == 0 and package_name in result.stdout
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        return False
    
    def is_flatpak_installed(self, flatpak_id: str) -> bool:
        """Check if a Flatpak is already installed"""
        if not self.flatpak_available or not flatpak_id:
            return False
        
        try:
            result = subprocess.run(['flatpak', 'list', '--app'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and flatpak_id in result.stdout
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def is_snap_installed(self, snap_name: str) -> bool:
        """Check if a Snap is already installed"""
        if not self.snap_available or not snap_name:
            return False
        
        try:
            result = subprocess.run(['snap', 'list', snap_name], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def install_packages(self, packages: List[str], use_sudo: bool = True) -> Tuple[bool, str]:
        """
        Install packages using the detected package manager
        Returns: (success, message)
        """
        if not packages:
            return True, "No packages to install"
        
        if self.detected_manager == 'unknown':
            return False, f"No supported package manager detected. Supported: apt, dnf, yum, pacman, zypper"
        
        # Filter out already installed packages
        packages_to_install = []
        already_installed = []
        
        for package in packages:
            if self.is_package_installed(package):
                already_installed.append(package)
            else:
                packages_to_install.append(package)
        
        # If all packages are already installed
        if not packages_to_install:
            if already_installed:
                return True, f"Already installed: {', '.join(already_installed)}"
            else:
                return True, "No packages needed"
        
        try:
            # Build command based on package manager
            if self.detected_manager == 'apt':
                # Update package list first (quietly)
                if use_sudo:
                    update_cmd = ['sudo', 'apt', 'update', '-qq']
                else:
                    update_cmd = ['apt', 'update', '-qq']
                subprocess.run(update_cmd, capture_output=True, timeout=60)
                
                # Install packages
                cmd = ['apt', 'install', '-y'] + packages_to_install
                if use_sudo:
                    cmd = ['sudo'] + cmd
            
            elif self.detected_manager == 'dnf':
                cmd = ['dnf', 'install', '-y'] + packages_to_install
                if use_sudo:
                    cmd = ['sudo'] + cmd
            
            elif self.detected_manager == 'yum':
                cmd = ['yum', 'install', '-y'] + packages_to_install
                if use_sudo:
                    cmd = ['sudo'] + cmd
            
            elif self.detected_manager == 'pacman':
                # Update package database first
                if use_sudo:
                    update_cmd = ['sudo', 'pacman', '-Sy']
                else:
                    update_cmd = ['pacman', '-Sy']
                subprocess.run(update_cmd, capture_output=True, timeout=60)
                
                cmd = ['pacman', '-S', '--noconfirm'] + packages_to_install
                if use_sudo:
                    cmd = ['sudo'] + cmd
            
            elif self.detected_manager == 'zypper':
                cmd = ['zypper', 'install', '-y'] + packages_to_install
                if use_sudo:
                    cmd = ['sudo'] + cmd
            
            else:
                return False, f"Unsupported package manager: {self.detected_manager}"
            
            # Execute installation
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                success_msg = f"Successfully installed: {', '.join(packages_to_install)}"
                if already_installed:
                    success_msg += f" (already had: {', '.join(already_installed)})"
                return True, success_msg
            else:
                error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                return False, f"Installation failed: {error_output}"
        
        except subprocess.TimeoutExpired:
            return False, f"Installation timed out after 10 minutes"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def install_flatpak_app(self, app_id: str) -> Tuple[bool, str]:
        """Install an application via Flatpak"""
        if not self.flatpak_available:
            return False, "Flatpak not available or not configured"
        
        if not app_id:
            return False, "No Flatpak ID provided"
        
        # Check if already installed
        if self.is_flatpak_installed(app_id):
            return True, f"Flatpak {app_id} already installed"
        
        try:
            cmd = ['flatpak', 'install', '-y', 'flathub', app_id]
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return True, f"Successfully installed {app_id} via Flatpak"
            else:
                error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                return False, f"Flatpak installation failed: {error_output}"
        
        except subprocess.TimeoutExpired:
            return False, f"Flatpak installation timed out"
        except Exception as e:
            return False, f"Flatpak error: {str(e)}"
    
    def install_snap_app(self, snap_name: str) -> Tuple[bool, str]:
        """Install an application via Snap"""
        if not self.snap_available:
            return False, "Snap not available"
        
        if not snap_name:
            return False, "No Snap name provided"
        
        # Check if already installed
        if self.is_snap_installed(snap_name):
            return True, f"Snap {snap_name} already installed"
        
        try:
            cmd = ['sudo', 'snap', 'install', snap_name]
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return True, f"Successfully installed {snap_name} via Snap"
            else:
                error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                return False, f"Snap installation failed: {error_output}"
        
        except subprocess.TimeoutExpired:
            return False, f"Snap installation timed out"
        except Exception as e:
            return False, f"Snap error: {str(e)}"
    
    def install_app(self, app_data: dict, json_parser) -> Tuple[bool, str, str]:
        """
        Install a single app using the best available method
        Returns: (success, message, method_used)
        
        Philosophy: Try native package manager first, then Flatpak, then Snap.
        If app is already installed via any method, consider it successful.
        """
        app_id = app_data.get('id', 'unknown')
        app_name = app_data.get('name', app_id)
        
        # Method 1: Try native package manager first
        packages = json_parser.get_packages_for_manager(app_id, self.detected_manager)
        if packages:
            print(f"Attempting to install {app_name} via {self.detected_manager}: {packages}")
            success, message = self.install_packages(packages)
            if success:
                return True, message, self.detected_manager
            else:
                print(f"Native package installation failed for {app_name}: {message}")
        
        # Method 2: Try Flatpak as fallback
        if self.flatpak_available:
            flatpak_id = json_parser.get_flatpak_id(app_id)
            if flatpak_id:
                print(f"Attempting to install {app_name} via Flatpak: {flatpak_id}")
                success, message = self.install_flatpak_app(flatpak_id)
                if success:
                    return True, message, 'flatpak'
                else:
                    print(f"Flatpak installation failed for {app_name}: {message}")
        
        # Method 3: Try Snap as last resort
        if self.snap_available:
            snap_name = json_parser.get_snap_id(app_id)
            if snap_name:
                print(f"Attempting to install {app_name} via Snap: {snap_name}")
                success, message = self.install_snap_app(snap_name)
                if success:
                    return True, message, 'snap'
                else:
                    print(f"Snap installation failed for {app_name}: {message}")
        
        # All methods failed
        return False, f"All installation methods failed for {app_name}", 'none'
    
    def check_sudo_access(self) -> bool:
        """Check if we have sudo access without prompting"""
        try:
            result = subprocess.run(['sudo', '-n', 'true'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def request_sudo_access(self) -> bool:
        """Request sudo access (will prompt for password in terminal)"""
        try:
            print("\nAdministrative access required for package installation.")
            print("Please enter your password when prompted:")
            result = subprocess.run(['sudo', '-v'], timeout=60)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout waiting for password")
            return False
        except:
            return False
    
    def get_manager_info(self) -> dict:
        """Get information about detected package manager and alternatives"""
        return {
            'primary_manager': self.detected_manager,
            'flatpak_available': self.flatpak_available,
            'snap_available': self.snap_available,
            'managers_detected': [
                manager for manager in ['apt', 'dnf', 'yum', 'pacman', 'zypper']
                if shutil.which(manager)
            ]
        }
    
    def get_installation_summary(self) -> str:
        """Get a summary of available installation methods"""
        info = self.get_manager_info()
        
        summary = f"Primary package manager: {info['primary_manager']}"
        
        alternatives = []
        if info['flatpak_available']:
            alternatives.append("Flatpak")
        if info['snap_available']:
            alternatives.append("Snap")
        
        if alternatives:
            summary += f"\nAlternative methods: {', '.join(alternatives)}"
        
        return summary


# Keep your existing DesktopIntegrator class here as well
from typing import List, Dict

class DesktopIntegrator:
    """Handle desktop file and icon installation"""
    
    def __init__(self, config):
        self.config = config

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
        """Create the Creative Suite manager script"""
        manager_dir = self.config.user_bin_dir
        manager_script_path = manager_dir / "creative-suite-manager"
        
        # Ensure bin directory exists
        manager_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the manager script from assets if it exists
        source_manager = self.config.assets_dir / "creative-suite-manager.sh"
        
        if source_manager.exists():
            try:
                shutil.copy2(source_manager, manager_script_path)
                manager_script_path.chmod(0o755)  # Make executable
                print(f"Installed Creative Suite manager script")
                
                # Create desktop entry for the manager
                self.create_manager_desktop_entry()
                return True
                
            except Exception as e:
                print(f"Warning: Could not install manager script: {e}")
                return False
        else:
            print("Warning: Manager script not found in assets")
            return False
    
    def create_manager_desktop_entry(self):
        """Create desktop entry for the Creative Suite manager"""
        target_dir = self.config.user_applications_dir
        manager_desktop_file = target_dir / "creative-suite-manager.desktop"
        
        # Get suite info
        suite_info = self.config.app_parser.get_suite_info() if hasattr(self.config, 'app_parser') else {}
        suite_name = suite_info.get('name', 'Application Bundle')
        
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Manage {suite_name}
Comment=Add, remove, or modify {suite_name.lower()} applications
Icon=creative-suite-main
Exec=gnome-terminal -- {self.config.user_bin_dir}/creative-suite-manager
Terminal=false
Categories=System;Settings;X-Creative-Suite;
Keywords=creative;suite;manager;uninstall;modify;
StartupNotify=true
"""
        
        try:
            with open(manager_desktop_file, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            print(f"Created 'Manage {suite_name}' menu entry")
        except Exception as e:
            print(f"Warning: Could not create manager desktop entry: {e}")
    
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
    
    def uninstall_bundle_integration(self, app_ids: List[str], suite_name: str = None, app_names: List[str] = None):
        """
        Remove desktop integration for a bundle (bundle-scoped uninstall)
        
        Args:
            app_ids: List of app IDs to remove integration for
            suite_name: Name of the suite being removed (for user dialog)
            app_names: Human-readable app names (for user dialog)
        """
        # Show explanation to user if this is an interactive removal
        if suite_name and app_names:
            if not self.show_bundle_removal_explanation(suite_name, app_names):
                return False  # User cancelled
        
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

