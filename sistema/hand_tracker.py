"""
Módulo para el seguimiento y reconocimiento de gestos de manos.
"""

import logging
import numpy as np
import cv2
from typing import Tuple, Optional

logger = logging.getLogger("SistemaKinect.HandTracker")

# Importación condicional para MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_DISPONIBLE = True
except ImportError:
    logger.warning("MediaPipe no está disponible. Reconocimiento de gestos desactivado.")
    MEDIAPIPE_DISPONIBLE = False

class HandTracker:
    """Gestiona el seguimiento de manos con MediaPipe."""
    
    def __init__(self):
        self.iniciado = False
        self.hands = None
        self.mp_hands = None
        self.mp_drawing = None
        
        # Intentar iniciar si MediaPipe está disponible
        if MEDIAPIPE_DISPONIBLE:
            self.iniciar()
    
    def iniciar(self) -> bool:
        """Inicia el módulo de seguimiento de manos."""
        if not MEDIAPIPE_DISPONIBLE:
            logger.error("MediaPipe no está disponible. No se puede iniciar seguimiento de manos.")
            return False
        
        try:
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            self.hands = self.mp_hands.Hands(
                min_detection_confidence=0.7,  # Aumentado para mejor precisión
                min_tracking_confidence=0.7,
                max_num_hands=1  # Limitado a una mano para mejor rendimiento
            )
            self.iniciado = True
            logger.info("Seguimiento de manos iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar seguimiento de manos: {e}")
            return False
    
    def procesar_frame(self, frame: np.ndarray) -> Tuple[Optional[any], np.ndarray]:
        """Procesa un frame para detectar y seguir manos."""
        if not self.iniciado or not MEDIAPIPE_DISPONIBLE:
            logger.warning("Seguimiento de manos no iniciado. No se puede procesar frame.")
            return None, frame
        
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)
            
            frame_con_manos = frame.copy()
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame_con_manos, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                        self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )
            
            return results, frame_con_manos
        except Exception as e:
            logger.error(f"Error al procesar frame para seguimiento de manos: {e}")
            return None, frame
    
    def detectar_dedos_levantados(self, landmarks) -> list:
        """Detecta qué dedos están levantados a partir de los landmarks de una mano."""
        if not self.iniciado or not MEDIAPIPE_DISPONIBLE:
            return [False, False, False, False, False]  # Ningún dedo detectado
            
        try:
            dedos_levantados = []
            
            # Pulgar (comprobación especial)
            if landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP].x > landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP].x:
                dedos_levantados.append(True)
            else:
                dedos_levantados.append(False)
            
            # Índice, medio, anular y meñique
            for dedo in [
                self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                self.mp_hands.HandLandmark.RING_FINGER_TIP,
                self.mp_hands.HandLandmark.PINKY_TIP
            ]:
                # Comprobar si la punta del dedo está por encima de la segunda falange
                if landmarks.landmark[dedo].y < landmarks.landmark[dedo - 2].y:
                    dedos_levantados.append(True)
                else:
                    dedos_levantados.append(False)
                    
            return dedos_levantados
        except Exception as e:
            logger.error(f"Error al detectar dedos levantados: {e}")
            return [False, False, False, False, False]
    
    def cerrar(self) -> None:
        """Cierra el módulo de seguimiento de manos."""
        if self.iniciado and hasattr(self.hands, 'close'):
            try:
                self.hands.close()
                self.iniciado = False
                logger.info("Seguimiento de manos cerrado correctamente.")
            except Exception as e:
                logger.error(f"Error al cerrar seguimiento de manos: {e}")