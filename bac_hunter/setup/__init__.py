"""
Setup and configuration modules for BAC Hunter
"""

from .wizard import SetupWizard, run_wizard
from .profiles import ProfileManager, get_profile_recommendations

__all__ = [
    "SetupWizard",
    "run_wizard", 
    "ProfileManager",
    "get_profile_recommendations"
]