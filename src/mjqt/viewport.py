from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import mujoco as mj
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class MjQtViewport(QGLWidget):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """Initialize the MuJoCo Qt viewport.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        
        # Initialize with default simple box model
        self._model: Optional[mj.MjModel] = None
        self._data: Optional[mj.MjData] = None
        
        # Visualization state 
        self._cam: Optional[mj.MjvCamera] = None
        self._opt: Optional[mj.MjvOption] = None
        self._scene: Optional[mj.MjvScene] = None
        self._con: Optional[mj.MjrContext] = None
        self._viewport: Optional[mj.MjrRect] = None
        
        # Physics 
        self._paused: bool = False
        self._timer: QTimer = QTimer(self)
        self._timer.timeout.connect(self._on_physics_tick)
        
        # Default model will be loaded in initializeGL when GL context is ready
        self._default_model_loaded = False
        
    def _load_default_model(self) -> None:
        """Load the default simple box model."""
        default_xml = """
        <mujoco>
          <worldbody>
            <geom type="box" size="0.1 0.1 0.1" rgba="0.2 0.6 0.9 1"/>
            <light diffuse="1 1 1" pos="0 0 2"/>
            <camera name="free" mode="targetbody" target="world" pos="0 0 2"/>
          </worldbody>
        </mujoco>
        """
        try:
            # Create model and data
            self._model = mj.MjModel.from_xml_string(default_xml)
            self._data = mj.MjData(self._model)
            
            # Initialize visualization objects
            self._cam = mj.MjvCamera()
            self._opt = mj.MjvOption()
            self._scene = mj.MjvScene(self._model, maxgeom=1000)
            self._con = mj.MjrContext(self._model, mj.mjtFontScale.mjFONTSCALE_150)
            
            # Set defaults
            mj.mjv_defaultCamera(self._cam)
            mj.mjv_defaultOption(self._opt)
            
            logger.info("Default model loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to load default model: {e}")
            raise

    def load_model_from_path(self, path: str) -> None:
        """Load a MuJoCo model from file path.
        
        Args:
            path: Path to the XML model file.
            
        Raises:
            Exception: If the model file cannot be loaded.
        """
        model_path = Path(path)
        if not model_path.exists():
            raise Exception(f"Model file not found: {path}")
            
        try:
            with open(model_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
                
            # Create model and data
            self._model = mj.MjModel.from_xml_string(xml_content)
            self._data = mj.MjData(self._model)
            
            # Initialize visualization objects
            self._cam = mj.MjvCamera()
            self._opt = mj.MjvOption()
            self._scene = mj.MjvScene(self._model, maxgeom=1000)
            self._con = mj.MjrContext(self._model, mj.mjtFontScale.mjFONTSCALE_150)
            
            # Set defaults
            mj.mjv_defaultCamera(self._cam)
            mj.mjv_defaultOption(self._opt)
            
            logger.info(f"Model loaded successfully from {path}")
        except Exception as e:
            logger.error(f"Failed to load model from {path}: {e}")
            raise Exception(f"Failed to load model from {path}: {e}") from e

    def set_run(self, paused: bool) -> None:
        """Set the simulation run state.
        
        Args:
            paused: If True, pause the simulation. If False, resume.
        """
        self._paused = paused
        if paused:
            logger.info("Simulation paused")
        else:
            logger.info("Simulation resumed")

    # ---- Qt OpenGL lifecycle methods ----

    def initializeGL(self) -> None:
        """Initialize OpenGL context.
        
        Qt has made the context current for us. Now we can safely load the default model.
        """
        logger.debug("OpenGL context initialized")
        
        # Load default model now that OpenGL context is ready
        if not self._default_model_loaded:
            try:
                self._load_default_model()
                self._default_model_loaded = True
                # Start simulation timer
                if not self._timer.isActive():
                    self._timer.start(16)  # ~60 Hz
            except Exception as e:
                logger.error(f"Failed to load default model in initializeGL: {e}")

    def resizeGL(self, w: int, h: int) -> None:
        """Handle widget resize.
        
        Args:
            w: New widget width in pixels.
            h: New widget height in pixels.
        """
        if self._con is None:
            return
            
        # Handle high DPI displays
        pixel_ratio = self.devicePixelRatio()
        actual_w = int(w * pixel_ratio)
        actual_h = int(h * pixel_ratio)
        
        # Set MuJoCo viewport
        self._viewport = mj.MjrRect(0, 0, actual_w, actual_h)
        
        # Ensure we're using the window framebuffer
        mj.mjr_setBuffer(mj.mjtFramebuffer.mjFB_WINDOW, self._con)
        
        logger.debug(f"Viewport resized to {actual_w}x{actual_h} (device ratio: {pixel_ratio})")

    def paintGL(self) -> None:
        """Render the MuJoCo scene.
        
        This is called whenever the widget needs to be repainted. We update
        the scene from the current simulation state and render it.
        """
        if not all([self._model, self._data, self._scene, self._con, self._cam, self._opt, self._viewport]):
            return
            
        try:
            # Update scene from current simulation state
            mj.mjv_updateScene(
                self._model, self._data, self._opt, None, self._cam,
                mj.mjtCatBit.mjCAT_ALL, self._scene
            )
            
            # Render scene into Qt's current framebuffer
            mj.mjr_render(self._viewport, self._scene, self._con)
            
        except Exception as e:
            logger.error(f"Render error: {e}")

    # ---- Physics simulation ----

    def _on_physics_tick(self) -> None:
        """Handle physics simulation tick.
        
        Steps the physics forward and triggers a repaint.
        """
        if self._paused or self._model is None or self._data is None:
            return
            
        try:
            # Step physics (multiple sub-steps for stability)
            for _ in range(2):
                mj.mj_step(self._model, self._data)
            
            # Trigger repaint
            self.update()
            
        except Exception as e:
            logger.error(f"Physics step error: {e}")
