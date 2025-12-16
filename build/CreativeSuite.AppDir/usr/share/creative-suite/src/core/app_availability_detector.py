#!/usr/bin/env python3
"""
Linux Bundle Installer - Application Availability Detector
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-05
"""

import subprocess
import shutil
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AppAvailability:
    """Represents the availability status of an application"""
    app_id: str
    app_name: str
    is_available: bool
    installation_method: Optional[str] = None  # 'apt', 'flatpak', 'snap', 'executable'
    package_name: Optional[str] = None
    executable_path: Optional[str] = None
    version_info: Optional[str] = None
    error_message: Optional[str] = None
    
    @property
    def status_description(self) -> str:
        """Human-readable status description"""
        if self.is_available:
            return f"Installed via {self.installation_method}"
        else:
            return "Not installed"

class AppAvailabilityDetector:
    """
    Detect application availability across different installation methods
    
    Philosophy: Query the system directly, no state files.
    Focus on apt/dpkg first, expand to other managers later.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamp = 0
        self.cache_duration = 300  # 5 minutes
        
        # Check what package managers are available
        self.has_apt = shutil.which('apt') is not None and shutil.which('dpkg') is not None
        self.has_flatpak = shutil.which('flatpak') is not None
        self.has_snap = shutil.which('snap') is not None
        
        print(f"DEBUG: Available package managers - apt: {self.has_apt}, flatpak: {self.has_flatpak}, snap: {self.has_snap}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return (time.time() - self.cache_timestamp) < self.cache_duration
    
    def _run_command(self, cmd: List[str], timeout: int = 5) -> Tuple[bool, str, str]:
        """
        Run a command safely with timeout
        Returns: (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _check_apt_package(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a package is installed via apt/dpkg
        Returns: (is_installed, version_info)
        """
        if not self.has_apt:
            return False, None
        
        # Use dpkg-query for precise package status
        success, stdout, stderr = self._run_command([
            'dpkg-query', '-W', '-f=${Status} ${Version}', package_name
        ])
        
        if success and 'install ok installed' in stdout:
            # Extract version from output
            parts = stdout.strip().split()
            version = parts[-1] if len(parts) > 3 else "unknown"
            return True, version
        
        return False, None
    
    def _check_flatpak_app(self, flatpak_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a Flatpak application is installed
        Returns: (is_installed, version_info)
        """
        if not self.has_flatpak or not flatpak_id:
            return False, None
        
        success, stdout, stderr = self._run_command([
            'flatpak', 'list', '--app', '--columns=application,version'
        ])
        
        if success:
            for line in stdout.split('\n'):
                if flatpak_id in line:
                    parts = line.strip().split('\t')
                    version = parts[1] if len(parts) > 1 else "unknown"
                    return True, version
        
        return False, None
    
    def _check_snap_app(self, snap_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a Snap application is installed
        Returns: (is_installed, version_info)
        """
        if not self.has_snap or not snap_name:
            return False, None
        
        success, stdout, stderr = self._run_command([
            'snap', 'list', snap_name
        ])
        
        if success:
            lines = stdout.strip().split('\n')
            if len(lines) > 1:  # Header + data
                parts = lines[1].split()
                version = parts[1] if len(parts) > 1 else "unknown"
                return True, version
        
        return False, None
    
    def _check_executable(self, app_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if executable is available in PATH
        Returns: (is_available, executable_path)
        """
        executable_path = shutil.which(app_id)
        if executable_path:
            return True, executable_path
        
        # Try some common variations
        common_variations = [
            app_id.lower(),
            app_id.replace('-', ''),
            app_id.replace('_', ''),
        ]
        
        for variation in common_variations:
            path = shutil.which(variation)
            if path:
                return True, path
        
        return False, None
    
    def detect_app_availability(self, app_data: Dict, json_parser) -> AppAvailability:
        """
        Detect availability of a single application using multiple methods
        """
        app_id = app_data.get('id', 'unknown')
        app_name = app_data.get('name', app_id)
        
        print(f"DEBUG: Detecting availability for {app_name} ({app_id})")
        
        # Method 1: Check apt packages (primary method for Mint)
        apt_packages = json_parser.get_packages_for_manager(app_id, 'apt')
        for package_name in apt_packages:
            is_installed, version = self._check_apt_package(package_name)
            if is_installed:
                print(f"DEBUG: {app_name} found via apt package: {package_name}")
                return AppAvailability(
                    app_id=app_id,
                    app_name=app_name,
                    is_available=True,
                    installation_method='apt',
                    package_name=package_name,
                    version_info=version
                )
        
        # Method 2: Check Flatpak (if available)
        if self.has_flatpak:
            flatpak_id = json_parser.get_flatpak_id(app_id)
            if flatpak_id:
                is_installed, version = self._check_flatpak_app(flatpak_id)
                if is_installed:
                    print(f"DEBUG: {app_name} found via Flatpak: {flatpak_id}")
                    return AppAvailability(
                        app_id=app_id,
                        app_name=app_name,
                        is_available=True,
                        installation_method='flatpak',
                        package_name=flatpak_id,
                        version_info=version
                    )
        
        # Method 3: Check Snap (if available)
        if self.has_snap:
            snap_name = json_parser.get_snap_id(app_id)
            if snap_name:
                is_installed, version = self._check_snap_app(snap_name)
                if is_installed:
                    print(f"DEBUG: {app_name} found via Snap: {snap_name}")
                    return AppAvailability(
                        app_id=app_id,
                        app_name=app_name,
                        is_available=True,
                        installation_method='snap',
                        package_name=snap_name,
                        version_info=version
                    )
        
        # Method 4: Check executable in PATH (fallback)
        is_available, executable_path = self._check_executable(app_id)
        if is_available:
            print(f"DEBUG: {app_name} found as executable: {executable_path}")
            return AppAvailability(
                app_id=app_id,
                app_name=app_name,
                is_available=True,
                installation_method='executable',
                executable_path=executable_path
            )
        
        # Not found anywhere
        print(f"DEBUG: {app_name} not found via any method")
        return AppAvailability(
            app_id=app_id,
            app_name=app_name,
            is_available=False,
            error_message="Application not installed"
        )
    
    def detect_multiple_apps(self, app_list: List[Dict], json_parser) -> Dict[str, AppAvailability]:
        """
        Detect availability for multiple applications
        Uses caching to avoid repeated scans
        """
        # Check cache first
        if self._is_cache_valid() and self.cache:
            print("DEBUG: Using cached availability results")
            # Filter cache for requested apps
            requested_ids = {app.get('id') for app in app_list}
            cached_results = {
                app_id: availability 
                for app_id, availability in self.cache.items() 
                if app_id in requested_ids
            }
            
            # If we have all requested apps in cache, return cached results
            if len(cached_results) == len(app_list):
                return cached_results
        
        print(f"DEBUG: Scanning availability for {len(app_list)} applications...")
        start_time = time.time()
        
        results = {}
        for app_data in app_list:
            app_id = app_data.get('id')
            if app_id:
                availability = self.detect_app_availability(app_data, json_parser)
                results[app_id] = availability
        
        # Update cache
        self.cache.update(results)
        self.cache_timestamp = time.time()
        
        scan_time = time.time() - start_time
        print(f"DEBUG: Availability scan completed in {scan_time:.2f} seconds")
        
        return results
    
    def invalidate_cache(self):
        """Invalidate the availability cache (call after installing/removing apps)"""
        print("DEBUG: Invalidating availability cache")
        self.cache.clear()
        self.cache_timestamp = 0
    
    def get_system_summary(self) -> Dict[str, any]:
        """Get summary of system package manager availability"""
        return {
            'package_managers': {
                'apt': self.has_apt,
                'flatpak': self.has_flatpak,
                'snap': self.has_snap
            },
            'cache_valid': self._is_cache_valid(),
            'cache_size': len(self.cache)
        }

# Convenience functions for easy integration
def detect_app_availability(app_data: Dict, json_parser) -> AppAvailability:
    """Standalone function to detect single app availability"""
    detector = AppAvailabilityDetector()
    return detector.detect_app_availability(app_data, json_parser)

def detect_multiple_apps_availability(app_list: List[Dict], json_parser) -> Dict[str, AppAvailability]:
    """Standalone function to detect multiple apps availability"""
    detector = AppAvailabilityDetector()
    return detector.detect_multiple_apps(app_list, json_parser)
