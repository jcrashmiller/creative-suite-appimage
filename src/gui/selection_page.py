#!/usr/bin/env python3
"""
Linux Bundle Installer - Application Selection Page with Desktop File Detection
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.

Author: James T. Miller
Created: 2025-06-01
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from pathlib import Path
from gui.base_page import BasePage
from core.bundle_state_detector import BundleStateDetector

class SelectionPage(BasePage):
    """Application selection page with desktop file detection and icons"""
    
    def __init__(self, parent, app_parser, config):
        self.app_parser = app_parser
        self.config = config
        
        # Add app_parser reference to config for bundle prefix detection
        self.config.app_parser = app_parser
        
        # Initialize state detector
        self.state_detector = BundleStateDetector(config)
        
        # Get current bundle state
        self.bundle_info = self.state_detector.get_bundle_info_with_availability(app_parser)
        self.currently_installed = self.bundle_info["installed_app_ids"]
        
        print(f"DEBUG: Bundle info: {self.bundle_info}")  # Debug output
        
        self.app_checkboxes = {}  # Store checkbox variables
        self.app_widgets = {}     # Store widget references
        self.icons_cache = {}     # Cache loaded icons
        
        super().__init__(parent, config)
    
    def setup_ui(self):
        """Set up the application selection interface"""
        # Get suite info for dynamic titles
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Main container with scrolling
        self.setup_scrollable_frame()
        
        # Dynamic title based on bundle state
        if self.bundle_info["is_installed"]:
            title_text = f"Modify {suite_name}"
            desc_text = f"Add or remove applications from your {suite_name.lower()} installation. Currently installed applications are pre-selected."
        else:
            title_text = f"Select {suite_name} Applications"
            desc_text = f"Choose which {suite_name.lower()} applications to install. Recommended applications are pre-selected."
        
        title = ttk.Label(self.content_frame, text=title_text, style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        desc_label = ttk.Label(self.content_frame, text=desc_text, style='Heading.TLabel')
        desc_label.pack(pady=(0, 20))
        
        # Show current state if bundle is installed
        if self.bundle_info["is_installed"]:
            self.show_current_state_info()
        
        # Selection controls
        self.create_selection_controls()
        
        # Apps organized by category
        self.create_app_selection_area()
        
        # Summary area
        self.create_summary_area()
    
    def show_current_state_info(self):
        """Show information about current bundle installation"""
        info_frame = ttk.LabelFrame(self.content_frame, text="Current Installation", padding=10)
        info_frame.pack(fill="x", pady=(0, 15), padx=10)
        
        total = self.bundle_info["total_installed"]
        app_names = self.bundle_info["installed_app_names"]
        
        info_text = f"Currently installed: {total} applications\n"
        if app_names:
            info_text += "• " + "\n• ".join(app_names[:5])
            if len(app_names) > 5:
                info_text += f"\n• ... and {len(app_names) - 5} more"
        
        info_label = ttk.Label(info_frame, text=info_text, justify='left')
        info_label.pack(anchor="w")

    def show_availability_warnings(self):
        """Show warnings for orphaned menu entries"""
        orphaned_entries = self.state_detector.get_orphaned_entries(self.app_parser)
        
        if orphaned_entries:
            warning_frame = ttk.LabelFrame(self.content_frame, text="⚠ Attention Required", padding=10)
            warning_frame.pack(fill="x", pady=(0, 15), padx=10)
            
            warning_text = f"Found {len(orphaned_entries)} menu entries for applications that are no longer installed:\n"
            for entry in orphaned_entries[:3]:  # Show first 3
                app_name = entry['app_data'].get('name', entry['app_id'])
                warning_text += f"• {app_name}\n"
            
            if len(orphaned_entries) > 3:
                warning_text += f"• ... and {len(orphaned_entries) - 3} more\n"
            
            warning_text += "\nThese applications were likely removed outside the bundle manager."
            
            warning_label = ttk.Label(warning_frame, text=warning_text, justify='left', foreground='orange')
            warning_label.pack(anchor="w", pady=(0, 5))
            
            # Cleanup button
            cleanup_button = ttk.Button(
                warning_frame,
                text="Clean Up Orphaned Entries",
                command=self.cleanup_orphaned_entries
            )
            cleanup_button.pack(anchor="w")

    def cleanup_orphaned_entries(self):
        """Remove orphaned menu entries"""
        orphaned_entries = self.state_detector.get_orphaned_entries(self.app_parser)
        
        if not orphaned_entries:
            messagebox.showinfo("No Orphaned Entries", "No orphaned menu entries found.")
            return
        
        app_names = [entry['app_data'].get('name', entry['app_id']) for entry in orphaned_entries]
        
        if messagebox.askyesno(
            "Clean Up Orphaned Entries",
            f"Remove menu entries for {len(orphaned_entries)} applications that are no longer installed?\n\n" +
            "\n".join(f"• {name}" for name in app_names[:5]) +
            (f"\n• ... and {len(app_names) - 5} more" if len(app_names) > 5 else "")
        ):
            try:
                from core.desktop_integration import DesktopIntegrator
                integrator = DesktopIntegrator(self.config)
                
                orphaned_ids = [entry['app_id'] for entry in orphaned_entries]
                removed_count = integrator.remove_apps_from_bundle(orphaned_ids)
                
                # Invalidate cache and refresh
                self.state_detector.invalidate_availability_cache()
                
                messagebox.showinfo(
                    "Cleanup Complete", 
                    f"Removed {removed_count} orphaned menu entries.\n\nRefresh the page to see updated status."
                )
                
                # Refresh the current page
                # Find main window and refresh selection page
                current = self.parent
                while current and not hasattr(current, 'show_selection_page'):
                    current = getattr(current, 'master', None) or getattr(current, 'parent', None)
                
                if current and hasattr(current, 'show_selection_page'):
                    current.show_selection_page(success_message="Orphaned entries cleaned up successfully")
                
            except Exception as e:
                messagebox.showerror("Cleanup Failed", f"Could not clean up orphaned entries:\n{str(e)}")
    
    def setup_scrollable_frame(self):
        """Create a scrollable frame for the content"""
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.parent, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Handle canvas resizing
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self.on_mousewheel)
        
        # Content frame is now the scrollable frame
        self.content_frame = self.scrollable_frame
    
    def on_canvas_configure(self, event):
        """Handle canvas resize"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def load_app_icon(self, app_id):
        """Load and cache an app icon"""
        if app_id in self.icons_cache:
            return self.icons_cache[app_id]
        
        # Try to find icon file - check multiple possible names/locations
        icon_paths_to_try = [
            # Custom Creative Suite icons (preferred)
            self.config.app_icons_dir / f"creative-suite-{app_id}.png",
            self.config.app_icons_dir / f"{app_id}.png",
            # Fallback to system icons if available
            Path(f"/usr/share/pixmaps/{app_id}.png"),
            Path(f"/usr/share/icons/hicolor/32x32/apps/{app_id}.png"),
        ]
        
        icon_photo = None
        
        for icon_path in icon_paths_to_try:
            if icon_path.exists():
                try:
                    # Load and resize icon
                    pil_image = Image.open(icon_path)
                    # Resize to 32x32 for consistent appearance
                    pil_image = pil_image.resize((32, 32), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(pil_image)
                    break
                except Exception as e:
                    print(f"Warning: Could not load icon {icon_path}: {e}")
                    continue
        
        # Create default icon if none found
        if icon_photo is None:
            icon_photo = self.create_default_icon(app_id)
        
        # Cache the icon
        self.icons_cache[app_id] = icon_photo
        return icon_photo
    
    def create_default_icon(self, app_id):
        """Create a default icon if no icon file is found"""
        # Create a simple colored square with initials
        pil_image = Image.new('RGBA', (32, 32), (100, 150, 200, 255))
        return ImageTk.PhotoImage(pil_image)
    
    def create_selection_controls(self):
        """Create Select All/None buttons"""
        controls_frame = ttk.Frame(self.content_frame)
        controls_frame.pack(fill="x", pady=(0, 15))
        
        # Left side - selection buttons
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side="left")
        
        ttk.Button(
            left_controls, 
            text="Select All", 
            command=self.select_all
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            left_controls, 
            text="Select None", 
            command=self.select_none
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            left_controls, 
            text="Select Recommended", 
            command=self.select_recommended
        ).pack(side="left")
        
        # Right side - bundle management and selection count
        right_controls = ttk.Frame(controls_frame)
        right_controls.pack(side="right")
        
        # Add "Remove Bundle" button if bundle is installed - FIXED CONDITION
        print(f"DEBUG: Checking bundle installation - is_installed: {self.bundle_info['is_installed']}")
        print(f"DEBUG: Total installed: {self.bundle_info['total_installed']}")
        
        if self.bundle_info["is_installed"] and self.bundle_info["total_installed"] > 0:
            print("DEBUG: Creating Remove Bundle button")
            self.remove_bundle_button = ttk.Button(
                right_controls,
                text="🗑 Remove Bundle",
                command=self.confirm_remove_bundle
            )
            self.remove_bundle_button.pack(side="left", padx=(0, 15))
        else:
            print("DEBUG: Not creating Remove Bundle button - bundle not installed")
        
        # Selection count label
        self.selection_count_label = ttk.Label(right_controls, text="")
        self.selection_count_label.pack(side="left")
    
    def confirm_remove_bundle(self):
        """Confirm and initiate complete bundle removal"""
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Get list of currently installed apps for confirmation
        app_names = self.bundle_info["installed_app_names"]
        
        # Show detailed confirmation
        confirm_msg = f"""Remove {suite_name} Completely?

This will remove:
✓ All {suite_name} menu entries and icons
✓ {suite_name} category from application menu

✗ Applications remain installed:"""
        
        for app_name in app_names[:6]:
            confirm_msg += f"\n  • {app_name}"
        
        if len(app_names) > 6:
            confirm_msg += f"\n  • ... and {len(app_names) - 6} more"
        
        confirm_msg += f"""

The applications will be available in their original menu locations.

Continue with {suite_name} removal?"""
        
        if messagebox.askyesno(f"Remove {suite_name}", confirm_msg):
            # Store removal result and trigger navigation
            self._removal_result = {
                'mode': 'remove_bundle',
                'suite_name': suite_name,
                'installed_apps': self.bundle_info["installed_app_ids"],
                'app_names': self.bundle_info["installed_app_names"]
            }
            
            # We'll return this in on_next() - the main window will handle the navigation
            print("DEBUG: Bundle removal confirmed, will be processed in on_next()")
    
    def create_app_selection_area(self):
        """Create the main app selection area organized by categories"""
        # Get apps organized by category
        apps_by_category = self.app_parser.get_apps_by_category()
        
        for category, apps in apps_by_category.items():
            self.create_category_section(category, apps)
        
        # Update selection count initially
        self.update_selection_count()
    
    def create_category_section(self, category_name, apps):
        """Create a section for a specific category"""
        # Category frame with border
        category_frame = ttk.LabelFrame(self.content_frame, text=category_name, padding=10)
        category_frame.pack(fill="x", pady=(0, 15), padx=10)
        
        # Create app entries for this category
        for app in apps:
            self.create_app_entry(category_frame, app)
    
    def create_app_entry(self, parent, app):
        """Create a single app entry with icon, checkbox and info"""
        app_id = app.get('id')
        
        # Main app frame
        app_frame = ttk.Frame(parent)
        app_frame.pack(fill="x", pady=8, padx=5)
        
        # Checkbox variable
        var = tk.BooleanVar()
        
        # Determine checkbox state based on current installation
        is_currently_installed = app_id in self.currently_installed
        
        if is_currently_installed:
            # If currently installed by bundle, always check
            var.set(True)
        else:
            # If not installed, use default selection
            var.set(app.get('default_selected', False))
        
        # Store the variable
        self.app_checkboxes[app_id] = var
        
        # Left side: checkbox
        checkbox = ttk.Checkbutton(
            app_frame, 
            variable=var,
            command=self.on_selection_changed
        )
        checkbox.pack(side="left", padx=(0, 10))
        
        # Icon (next to checkbox)
        icon_label = ttk.Label(app_frame)
        icon_label.pack(side="left", padx=(0, 10))
        
        # Load and set icon
        try:
            icon_photo = self.load_app_icon(app_id)
            icon_label.configure(image=icon_photo)
            icon_label.image = icon_photo  # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Warning: Could not set icon for {app_id}: {e}")
        
        # App info frame (takes remaining space)
        info_frame = ttk.Frame(app_frame)
        info_frame.pack(side="left", fill="x", expand=True)
        
        # App name (bold)
        name_label = ttk.Label(
            info_frame, 
            text=app.get('name', 'Unknown'), 
            font=('Arial', 11, 'bold')
        )
        name_label.pack(anchor="w")
        
        # App description
        description = app.get('description', '')
        if description:
            desc_label = ttk.Label(
                info_frame, 
                text=description, 
                foreground='gray',
                font=('Arial', 9)
            )
            desc_label.pack(anchor="w")
        
        # Adobe equivalent (if available)
        adobe_equiv = app.get('adobe_equivalent', '')
        if adobe_equiv:
            equiv_text = f"Alternative to: {adobe_equiv}"
            equiv_label = ttk.Label(
                info_frame, 
                text=equiv_text, 
                foreground='#0066cc', 
                font=('Arial', 9, 'italic')
            )
            equiv_label.pack(anchor="w")
        
        # Status indicators
        if is_currently_installed:
            status_label = ttk.Label(
                info_frame, 
                text="[CURRENTLY IN BUNDLE]", 
                foreground='green', 
                font=('Arial', 8, 'bold')
            )
            status_label.pack(anchor="w")

        # Show availability status
        if app_id in self.bundle_info.get("availability_info", {}):
            availability = self.bundle_info["availability_info"][app_id]
            if availability and not availability.is_available:
                status_label = ttk.Label(
                    info_frame, 
                    text="[ORPHANED - APP REMOVED]", 
                    foreground='red', 
                    font=('Arial', 8, 'bold')
                )
                status_label.pack(anchor="w")
        
        # Required indicator (if any apps are still marked required)
        if app.get('required', False):
            req_label = ttk.Label(
                info_frame, 
                text="[RECOMMENDED]", 
                foreground='blue', 
                font=('Arial', 8, 'bold')
            )
            req_label.pack(anchor="w")
        
        # Store widget references
        self.app_widgets[app_id] = {
            'frame': app_frame,
            'checkbox': checkbox,
            'variable': var,
            'app_data': app,
            'icon_label': icon_label,
            'currently_installed': is_currently_installed
        }
    
    def create_summary_area(self):
        """Create summary area showing what will be installed/changed"""
        # Get suite name for dynamic text
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        if self.bundle_info["is_installed"]:
            summary_title = f"{suite_name} Changes Summary"
        else:
            summary_title = f"{suite_name} Installation Summary"
        
        summary_frame = ttk.LabelFrame(
            self.content_frame, 
            text=summary_title, 
            padding=10
        )
        summary_frame.pack(fill="x", pady=15, padx=10)
        
        self.summary_text = tk.Text(summary_frame, height=4, wrap=tk.WORD, state='disabled')
        self.summary_text.pack(fill="x")
        
        # Update summary initially
        self.update_summary()
    
    def select_all(self):
        """Select all applications"""
        for app_id, var in self.app_checkboxes.items():
            var.set(True)
        self.on_selection_changed()
    
    def select_none(self):
        """Deselect all applications"""
        for app_id, var in self.app_checkboxes.items():
            var.set(False)
        self.on_selection_changed()
    
    def select_recommended(self):
        """Select recommended applications and currently installed"""
        for app_id, var in self.app_checkboxes.items():
            widget_info = self.app_widgets[app_id]
            app_data = widget_info['app_data']
            is_currently_installed = widget_info['currently_installed']
            
            # Select if recommended OR currently installed
            if app_data.get('default_selected', False) or is_currently_installed:
                var.set(True)
            else:
                var.set(False)
        self.on_selection_changed()
    
    def on_selection_changed(self):
        """Called when selection changes"""
        self.update_selection_count()
        self.update_summary()
    
    def update_selection_count(self):
        """Update the selection count label"""
        selected_count = sum(1 for var in self.app_checkboxes.values() if var.get())
        total_count = len(self.app_checkboxes)
        
        self.selection_count_label.config(text=f"Selected: {selected_count}/{total_count}")
    
    def update_summary(self):
        """Update the installation/changes summary"""
        selected_apps = self.get_selected_apps()
        selected_ids = [app.get('id') for app in selected_apps]
        
        # Calculate changes if bundle is installed
        if self.bundle_info["is_installed"]:
            changes = self.state_detector.get_installation_changes(selected_ids)
            
            if not changes["has_changes"]:
                summary_text = "No changes - selection matches current installation."
            else:
                summary_lines = []
                
                if changes["to_add"]:
                    summary_lines.append(f"Install {len(changes['to_add'])} new applications:")
                    for app_id in changes["to_add"]:
                        app_name = self.app_parser.get_app_field(app_id, 'name') or app_id
                        summary_lines.append(f"  + {app_name}")
                
                if changes["to_remove"]:
                    summary_lines.append(f"Remove {len(changes['to_remove'])} from bundle:")
                    for app_id in changes["to_remove"]:
                        app_name = self.app_parser.get_app_field(app_id, 'name') or app_id
                        summary_lines.append(f"  - {app_name}")
                
                if changes["no_change"]:
                    summary_lines.append(f"Keep {len(changes['no_change'])} current applications")
                
                summary_text = "\n".join(summary_lines)
        else:
            # Fresh installation
            if not selected_apps:
                summary_text = "No applications selected."
            else:
                summary_lines = ["Applications to be installed:"]
                for app in selected_apps:
                    app_name = app.get('name', 'Unknown')
                    adobe_equiv = app.get('adobe_equivalent', '')
                    if adobe_equiv:
                        summary_lines.append(f"• {app_name} (replaces {adobe_equiv})")
                    else:
                        summary_lines.append(f"• {app_name}")
                
                summary_text = "\n".join(summary_lines)
        
        # Update text widget
        self.summary_text.configure(state='normal')
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)
        self.summary_text.configure(state='disabled')
    
    def get_selected_apps(self):
        """Get list of selected applications"""
        selected_apps = []
        
        for app_id, var in self.app_checkboxes.items():
            if var.get():
                app_data = self.app_widgets[app_id]['app_data']
                selected_apps.append(app_data)
        
        return selected_apps
    
    def validate_selection(self):
        """Validate that selection is acceptable"""
        selected_apps = self.get_selected_apps()
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        if not selected_apps:
            # Check if this is removing everything from an existing bundle
            if self.bundle_info["is_installed"]:
                # Instead of asking here, suggest using the Remove Bundle button
                messagebox.showinfo(
                    "Remove All Applications",
                    f"To completely remove {suite_name}, use the '🗑 Remove Bundle' button.\n\n"
                    "This will remove all menu entries while keeping the applications installed."
                )
                return False
            else:
                messagebox.showwarning(
                    "No Selection", 
                    f"Please select at least one {suite_name.lower()} application to install."
                )
                return False
        
        return True
    
    def on_next(self):
        """Called when Install/Apply button is clicked"""
        # Check if we're in bundle removal mode (button was clicked)
        if hasattr(self, '_removal_result'):
            result = self._removal_result
            delattr(self, '_removal_result')  # Clean up
            print("DEBUG: Returning removal result from on_next()")
            return result
        
        if not self.validate_selection():
            return None
        
        selected_apps = self.get_selected_apps()
        selected_ids = [app.get('id') for app in selected_apps]
        
        # Calculate what needs to be done
        if self.bundle_info["is_installed"]:
            changes = self.state_detector.get_installation_changes(selected_ids)
            
            if not changes["has_changes"] and selected_apps:
                messagebox.showinfo("No Changes", "Selection matches current installation - no changes needed.")
                return None
            
            # Return modification data
            return {
                'mode': 'modify',
                'changes': changes,
                'selected_apps': selected_apps
            }
        else:
            # Fresh installation
            suite_info = self.app_parser.get_suite_info()
            suite_name = suite_info.get('name', 'Application Bundle')
            
            # Confirm installation
            app_names = [app.get('name', 'Unknown') for app in selected_apps]
            confirm_msg = f"Ready to install {len(selected_apps)} {suite_name.lower()} applications:\n\n"
            confirm_msg += "\n".join(f"• {name}" for name in app_names[:10])
            
            if len(app_names) > 10:
                confirm_msg += f"\n... and {len(app_names) - 10} more"
            
            confirm_msg += "\n\nProceed with installation?"
            
            if messagebox.askyesno("Confirm Installation", confirm_msg):
                return {
                    'mode': 'install',
                    'selected_apps': selected_apps
                }
            else:
                return None
