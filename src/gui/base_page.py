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

#!/usr/bin/env python3
"""
Linux Bundle Installer - Base Page Class
Copyright (c) 2025 Loading Screen Solutions

Licensed under the MIT License. See LICENSE file for details.
"""

class BasePage:
    """Base class for all pages"""
    
    def __init__(self, parent, config=None):
        self.parent = parent
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Override in subclasses to set up the UI"""
        pass
    
    def on_next(self):
        """Called when next button is clicked. Return data if needed."""
        pass
    
    def on_back(self):
        """Called when back button is clicked"""
        pass
    
    def on_closing(self):
        """Called when window is closing. Return False to prevent closing."""
        return True
