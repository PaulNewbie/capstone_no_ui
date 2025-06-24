# ui/__init__.py - UI Module Initialization

"""
MotorPass UI Module

This module contains all GUI interfaces for the MotorPass system:
- main_window.py: Main menu interface
- student_gui.py: Student/Staff verification GUI
- guest_gui.py: Guest verification GUI
"""

# Import main components for easier access
from .main_window import MotorPassGUI
from .student_gui import StudentVerificationGUI
from .guest_gui import GuestVerificationGUI

__all__ = [
    'MotorPassGUI',
    'StudentVerificationGUI', 
    'GuestVerificationGUI'
]

# Module version
__version__ = '1.0.0'
