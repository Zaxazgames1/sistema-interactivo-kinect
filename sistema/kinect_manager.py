"""
Módulo para gestionar la conexión y operaciones con Kinect.
"""

import logging
import numpy as np
import cv2
from typing import Optional, Tuple

logger = logging.getLogger("SistemaKinect.KinectManager")

# Importación condicional para OpenNI2
try:
    from openni import openni2
    OPENNI_DISPONIBLE = True
except ImportError:
    logger.warning("OpenNI2 no está disponible. Funcionalidad Kinect desactivada.")
    OPENNI_DISPONIBLE = False

class KinectManager:
    """Gestiona la conexión y operaciones con Kinect."""
    
    def __init__(self, config_manager):
        self.config = config_manager.obtener_config("kinect")
        self.device = None
        self.color_stream = None
        self.resolution = tuple(self.config.get("resolution", [640, 480]))
        self.iniciado = False
        
        # Atributos para webcam como fallback
        self.usar_webcam = False
        self.webcam = None
    
    def iniciar(self, usar_webcam=False) -> bool:
        """Inicia la conexión con Kinect o webcam si se especifica."""
        self.usar_webcam = usar_webcam
        
        if self.usar_webcam:
            return self._iniciar_webcam()
        elif OPENNI_DISPONIBLE:
            return self._iniciar_kinect()
        else:
            logger.warning("OpenNI2 no disponible y no se solicitó webcam. Intentando iniciar webcam como fallback.")
            self.usar_webcam = True
            return self._iniciar_webcam()
    
    def _iniciar_kinect(self) -> bool:
        """Inicia la conexión con Kinect."""
        try:
            openni_path = self.config.get("openni_path", "C:/Program Files/OpenNI2/Redist")
            openni2.initialize(openni_path)
            self.device = openni2.Device.open_any()
            
            if self.device is None:
                logger.error("No se pudo conectar con ningún dispositivo Kinect.")
                return False
            
            self.color_stream = self.device.create_color_stream()
            self.color_stream.start()
            self.iniciado = True
            logger.info("Kinect iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar Kinect: {e}")
            return False
    
    def _iniciar_webcam(self) -> bool:
        """Inicia la conexión con webcam como alternativa a Kinect."""
        try:
            self.webcam = cv2.VideoCapture(0)
            if not self.webcam.isOpened():
                logger.error("No se pudo abrir la webcam.")
                return False
            
            # Establecer resolución de la webcam para que coincida con la configuración
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            self.iniciado = True
            logger.info("Webcam iniciada correctamente como reemplazo de Kinect.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar webcam: {e}")
            return False
    
    def obtener_imagen(self) -> Optional[np.ndarray]:
        """Obtiene una imagen desde Kinect o webcam."""
        if not self.iniciado:
            logger.warning("Dispositivo de captura no iniciado. No se puede obtener imagen.")
            return None
        
        try:
            if self.usar_webcam:
                return self._obtener_imagen_webcam()
            else:
                return self._obtener_imagen_kinect()
        except Exception as e:
            logger.error(f"Error al obtener imagen: {e}")
            return None
    
    def _obtener_imagen_kinect(self) -> Optional[np.ndarray]:
        """Obtiene una imagen desde Kinect."""
        try:
            frame = self.color_stream.read_frame()
            frame_data = np.frombuffer(frame.get_buffer_as_uint8(), dtype=np.uint8)
            frame_img = frame_data.reshape((self.resolution[1], self.resolution[0], 3))
            return cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Error al obtener imagen de Kinect: {e}")
            return None
    
    def _obtener_imagen_webcam(self) -> Optional[np.ndarray]:
        """Obtiene una imagen desde webcam."""
        try:
            ret, frame = self.webcam.read()
            if not ret:
                logger.warning("No se pudo leer frame de webcam.")
                return None
            return frame
        except Exception as e:
            logger.error(f"Error al obtener imagen de webcam: {e}")
            return None
    
    def cerrar(self) -> None:
        """Cierra la conexión con Kinect o webcam."""
        if not self.iniciado:
            return
            
        try:
            if self.usar_webcam and self.webcam is not None:
                self.webcam.release()
                logger.info("Webcam cerrada correctamente.")
            elif self.color_stream is not None:
                self.color_stream.stop()
                openni2.unload()
                logger.info("Kinect cerrado correctamente.")
            
            self.iniciado = False
        except Exception as e:
            logger.error(f"Error al cerrar dispositivo de captura: {e}")