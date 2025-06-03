#!/usr/bin/env python3
"""
Linux Bundle Installer - Application Selection Page with Icons
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

class SelectionPage(BasePage):
    """Application selection page with icons, checkboxes and categories"""
    
    def __init__(self, parent, app_parser, config):
        self.app_parser = app_parser
        self.config = config
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
        
        # Dynamic title based on JSON
        title = ttk.Label(
            self.content_frame, 
            text=f"Select {suite_name} Applications", 
            style='Title.TLabel'
        )
        title.pack(pady=(0, 20))
        
        # Dynamic description
        desc_text = f"Choose which {suite_name.lower()} applications to install. Recommended applications are pre-selected."
        desc_label = ttk.Label(self.content_frame, text=desc_text, style='Heading.TLabel')
        desc_label.pack(pady=(0, 20))
        
        # Selection controls
        self.create_selection_controls()
        
        # Apps organized by category
        self.create_app_selection_area()
        
        # Summary area
        self.create_summary_area()
    
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
        
        # TODO: Could add text/initials here using PIL.ImageDraw
        # For now, just return a simple colored square
        
        return ImageTk.PhotoImage(pil_image)
    
    def create_selection_controls(self):
        """Create Select All/None buttons"""
        controls_frame = ttk.Frame(self.content_frame)
        controls_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Button(
            controls_frame, 
            text="Select All", 
            command=self.select_all
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            controls_frame, 
            text="Select None", 
            command=self.select_none
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            controls_frame, 
            text="Select Recommended", 
            command=self.select_recommended
        ).pack(side="left")
        
        # Selection count label
        self.selection_count_label = ttk.Label(controls_frame, text="")
        self.selection_count_label.pack(side="right")
    
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
        
        # Set default selection
        if app.get('default_selected', False):
            var.set(True)
        
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
        
        # Required indicator
        if app.get('required', False):
            req_label = ttk.Label(
                info_frame, 
                text="[REQUIRED]", 
                foreground='red', 
                font=('Arial', 8, 'bold')
            )
            req_label.pack(anchor="w")
            # Required apps can't be unchecked
            checkbox.configure(state='disabled')
            var.set(True)
        
        # Store widget references
        self.app_widgets[app_id] = {
            'frame': app_frame,
            'checkbox': checkbox,
            'variable': var,
            'app_data': app,
            'icon_label': icon_label
        }
    
    def create_summary_area(self):
        """Create summary area showing what will be installed"""
        # Get suite name for dynamic text
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        summary_frame = ttk.LabelFrame(
            self.content_frame, 
            text=f"{suite_name} Installation Summary", 
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
            widget_info = self.app_widgets[app_id]
            if widget_info['checkbox']['state'] != 'disabled':
                var.set(True)
        self.on_selection_changed()
    
    def select_none(self):
        """Deselect all non-required applications"""
        for app_id, var in self.app_checkboxes.items():
            widget_info = self.app_widgets[app_id]
            app_data = widget_info['app_data']
            if not app_data.get('required', False):
                var.set(False)
        self.on_selection_changed()
    
    def select_recommended(self):
        """Select only recommended applications"""
        for app_id, var in self.app_checkboxes.items():
            widget_info = self.app_widgets[app_id]
            app_data = widget_info['app_data']
            
            if app_data.get('required', False) or app_data.get('default_selected', False):
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
        """Update the installation summary"""
        selected_apps = self.get_selected_apps()
        
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
            messagebox.showwarning(
                "No Selection", 
                f"Please select at least one {suite_name.lower()} application to install."
            )
            return False
        
        # Check that all required apps are selected
        all_apps = self.app_parser.get_all_apps()
        required_apps = [app for app in all_apps if app.get('required', False)]
        selected_ids = [app.get('id') for app in selected_apps]
        
        missing_required = []
        for req_app in required_apps:
            if req_app.get('id') not in selected_ids:
                missing_required.append(req_app.get('name', req_app.get('id')))
        
        if missing_required:
            messagebox.showerror(
                "Missing Required Applications",
                f"The following required applications must be selected:\n\n" +
                "\n".join(f"• {name}" for name in missing_required)
            )
            return False
        
        return True
    
    def on_next(self):
        """Called when Install Selected button is clicked"""
        if not self.validate_selection():
            return None
        
        selected_apps = self.get_selected_apps()
        suite_info = self.app_parser.get_suite_info()
        suite_name = suite_info.get('name', 'Application Bundle')
        
        # Confirm installation with dynamic text
        app_names = [app.get('name', 'Unknown') for app in selected_apps]
        confirm_msg = f"Ready to install {len(selected_apps)} {suite_name.lower()} applications:\n\n"
        confirm_msg += "\n".join(f"• {name}" for name in app_names[:10])  # Show first 10
        
        if len(app_names) > 10:
            confirm_msg += f"\n... and {len(app_names) - 10} more"
        
        confirm_msg += "\n\nProceed with installation?"
        
        if messagebox.askyesno("Confirm Installation", confirm_msg):
            return selected_apps
        else:
            return None
