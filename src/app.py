"""Minimal MuJoCo × PyQt5 Viewport application.

Simple Qt application that displays a MuJoCo viewport widget.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from .mjqt.viewport import MjQtViewport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MjQtApp(QMainWindow):
    """Simple application window with MuJoCo viewport."""

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()
        
        # Set up main window
        self.setWindowTitle("MuJoCo × PyQt5 Viewport")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create and add the MuJoCo viewport
        self.viewport = MjQtViewport()
        layout.addWidget(self.viewport)
        
        logger.info("MjQtApp initialized successfully")


def main() -> int:
    """Main entry point for the application.
    
    Returns:
        Exit code.
    """
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("MuJoCo Qt Viewport")
    app.setApplicationVersion("1.0")
    
    # Enable high DPI support
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and show main window
    window = MjQtApp()
    window.show()
    
    logger.info("Application started successfully")
    
    # Run event loop
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
