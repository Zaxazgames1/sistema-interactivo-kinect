"""
Módulo principal del Sistema Interactivo con Kinect.
"""

# Importación de todos los módulos necesarios
from .config_manager import ConfigManager
from .kinect_manager import KinectManager
from .hand_tracker import HandTracker
from .mano_robotica import ManoRoboticaManager
from .text_recognizer import TextRecognizer
from .voice_engine import VoiceEngine
from .ui_manager import UIManager
from .dibujo_manager import DibujoManager
from .sistema_interactivo import SistemaInteractivo

# Exportar clases para que sean accesibles directamente desde el módulo
__all__ = [
    'SistemaInteractivo',
    'ConfigManager',
    'KinectManager',
    'HandTracker',
    'ManoRoboticaManager',
    'TextRecognizer',
    'VoiceEngine',
    'UIManager',
    'DibujoManager'
]

# Versión del módulo
__version__ = '2.0.0'