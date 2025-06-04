#!/usr/bin/env python3
"""
AppImage Integration Dialog
Offers to install AppImage to standard location for better menu integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
from pathlib import Path

class AppImageIntegrationDialog:
    """Dialog to offer AppImage integration options"""
    
    def __init__(self, current_appimage_path, suite_name="Linux Creative Suite"):
        self.current_appimage_path = current_appimage_path
        self.suite_name = suite_name
        self.result = None
        
    def show_integration_options(self):
        """Show dialog asking user about AppImage integration"""
        
        # Check if we're in a temporary location (Downloads, /tmp, etc.)
        if not self._is_temporary_location():
            # Already in a good location, just create menu entry
            return {'action': 'create_menu', 'path': self.current_appimage_path}
        
        # Create dialog
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        dialog = tk.Toplevel(root)
        dialog.title(f"{self.suite_name} - Integration Options")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Make it modal
        dialog.transient(root)
        dialog.grab_set()
        
        # Content
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text=f"Install {self.suite_name}?",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Explanation
        explanation = f"""You're running {self.suite_name} from a temporary location:
{self.current_appimage_path}

For the best experience, we recommend installing it to a permanent location.
This will allow you to easily manage your Creative Suite applications later."""
        
        explanation_label = ttk.Label(
            main_frame,
            text=explanation,
            wraplength=450,
            justify='left'
        )
        explanation_label.pack(pady=(0, 20))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Installation Options", padding=15)
        options_frame.pack(fill="x", pady=(0, 20))
        
        # Option 1: Install permanently
        install_frame = ttk.Frame(options_frame)
        install_frame.pack(fill="x", pady=(0, 15))
        
        install_text = f"""✓ Copy to ~/Applications/{self.suite_name}.AppImage
✓ Create permanent menu entry "Manage {self.suite_name}"
✓ Easy access for future modifications"""
        
        ttk.Label(install_frame, text="📦 Install Permanently", font=('Arial', 11, 'bold')).pack(anchor="w")
        ttk.Label(install_frame, text=install_text, foreground='green').pack(anchor="w", padx=(20, 0))
        
        install_button = ttk.Button(
            install_frame,
            text="Install to Applications Folder",
            command=lambda: self._set_result('install')
        )
        install_button.pack(anchor="w", padx=(20, 0), pady=(5, 0))
        
        # Option 2: Run once
        once_frame = ttk.Frame(options_frame)
        once_frame.pack(fill="x")
        
        once_text = f"""✓ Install your selected applications
✗ No permanent menu entry for management
⚠ Re-run AppImage from current location to modify later"""
        
        ttk.Label(once_frame, text="⚡ Run Once Only", font=('Arial', 11, 'bold')).pack(anchor="w")
        ttk.Label(once_frame, text=once_text, foreground='orange').pack(anchor="w", padx=(20, 0))
        
        once_button = ttk.Button(
            once_frame,
            text="Continue Without Installing",
            command=lambda: self._set_result('once')
        )
        once_button.pack(anchor="w", padx=(20, 0), pady=(5, 0))
        
        # Note
        note_label = ttk.Label(
            main_frame,
            text="Note: You can always move the AppImage to ~/Applications/ manually later.",
            font=('Arial', 9),
            foreground='gray'
        )
        note_label.pack()
        
        # Wait for user choice
        dialog.wait_window()
        root.destroy()
        
        return self.result
    
    def _is_temporary_location(self):
        """Check if AppImage is in a temporary location"""
        path_str = str(self.current_appimage_path).lower()
        temp_locations = [
            '/tmp/',
            'downloads',
            'download',
            'desktop',
            'temp'
        ]
        
        return any(loc in path_str for loc in temp_locations)
    
    def _set_result(self, action):
        """Set the result and close dialog"""
        if action == 'install':
            # Install to Applications folder
            applications_dir = Path.home() / "Applications"
            applications_dir.mkdir(exist_ok=True)
            
            appimage_name = f"{self.suite_name}.AppImage"
            target_path = applications_dir / appimage_name
            
            try:
                # Copy AppImage to Applications
                shutil.copy2(self.current_appimage_path, target_path)
                # Make it executable
                target_path.chmod(0o755)
                
                self.result = {'action': 'installed', 'path': str(target_path)}
                messagebox.showinfo(
                    "Installation Complete",
                    f"{self.suite_name} has been installed to:\n{target_path}\n\n"
                    "A menu entry will be created for easy access."
                )
            except Exception as e:
                messagebox.showerror(
                    "Installation Failed",
                    f"Could not install to Applications folder:\n{str(e)}\n\n"
                    "Continuing with run-once mode."
                )
                self.result = {'action': 'once', 'path': self.current_appimage_path}
        else:
            self.result = {'action': 'once', 'path': self.current_appimage_path}
        
        # Close dialog
        dialog = self.result  # Store result
        for widget in tk._default_root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        self.result = dialog  # Restore result

def check_appimage_integration(suite_name="Linux Creative Suite"):
    """Check if AppImage needs integration setup"""
    
    appimage_path = os.environ.get('APPIMAGE')
    if not appimage_path:
        # Not running as AppImage
        return {'action': 'not_appimage', 'path': None}
    
    # Check if already integrated
    applications_dir = Path.home() / "Applications"
    expected_name = f"{suite_name}.AppImage"
    expected_path = applications_dir / expected_name
    
    if str(expected_path) == appimage_path:
        # Already running from Applications folder
        return {'action': 'already_integrated', 'path': appimage_path}
    
    if expected_path.exists():
        # AppImage exists in Applications but we're running from elsewhere
        return {'action': 'duplicate_detected', 'path': appimage_path}
    
    # Show integration dialog
    dialog = AppImageIntegrationDialog(appimage_path, suite_name)
    return dialog.show_integration_options()

if __name__ == "__main__":
    # Test the dialog
    result = check_appimage_integration()
    print(f"Result: {result}")
