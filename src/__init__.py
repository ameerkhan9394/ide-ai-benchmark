"""
IDE AI Benchmark - Multi-IDE AI model benchmarking framework
"""

from .ide_automation import (CursorAutomation, IDEAutomation, VSCodeAutomation,
                             WindsurfAutomation, create_ide_automation)

__all__ = [
    "IDEAutomation",
    "CursorAutomation",
    "WindsurfAutomation",
    "VSCodeAutomation",
    "create_ide_automation",
]
