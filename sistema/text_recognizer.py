"""
Módulo para el reconocimiento de texto en imágenes.
"""

import logging
import threading
import cv2
import numpy as np
from typing import List, Tuple, Optional

logger = logging.getLogger("SistemaKinect.TextRecognizer")

# Importación condicional para EasyOCR
try:
    import easyocr
    EASYOCR_DISPONIBLE = True
except ImportError:
    logger.warning("EasyOCR no está disponible. Reconocimiento de texto desactivado.")
    EASYOCR_DISPONIBLE = False

class TextRecognizer:
    """Gestiona el reconocimiento de texto en imágenes."""
    
    def __init__(self, config_manager):
        self.config = config_manager.obtener_config()
        self.idiomas = self.config.get("idiomas_ocr", ["es", "en"])
        self.reader = None
        self.iniciado = False
        self.ultimo_texto = ""
        self.inicializando = False
    
    def iniciar(self) -> bool:
        """Inicia el módulo de reconocimiento de texto."""
        if not EASYOCR_DISPONIBLE:
            logger.error("EasyOCR no está disponible. No se puede iniciar reconocimiento de texto.")
            return False
        
        if self.inicializando:
            logger.info("Inicialización de EasyOCR ya en progreso.")
            return True
            
        try:
            # Iniciar EasyOCR en un hilo separado para no bloquear la UI
            self.inicializando = True
            threading.Thread(target=self._iniciar_easyocr, daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"Error al iniciar reconocimiento de texto: {e}")
            self.inicializando = False
            return False
    
    def _iniciar_easyocr(self) -> None:
        """Inicializa EasyOCR en segundo plano."""
        try:
            logger.info(f"Iniciando EasyOCR con idiomas: {self.idiomas}...")
            self.reader = easyocr.Reader(self.idiomas)
            self.iniciado = True
            logger.info("EasyOCR iniciado correctamente.")
        except Exception as e:
            logger.error(f"Error al iniciar EasyOCR: {e}")
            self.iniciado = False
        finally:
            self.inicializando = False
    
    def reconocer_texto(self, imagen: np.ndarray) -> Tuple[List, np.ndarray]:
        """Realiza reconocimiento de texto en una imagen."""
        if not self.iniciado or self.reader is None:
            logger.warning("EasyOCR no iniciado. No se puede reconocer texto.")
            return [], imagen
        
        try:
            imagen_procesada = self._preprocesar_imagen(imagen)
            resultado = self.reader.readtext(imagen_procesada)
            
            # Visualizar resultados en la imagen
            imagen_con_texto = imagen.copy()
            for (bbox, texto, prob) in resultado:
                if prob > 0.5:  # Solo mostrar resultados con confianza mayor a 50%
                    top_left = tuple(map(int, bbox[0]))
                    bottom_right = tuple(map(int, bbox[2]))
                    cv2.rectangle(imagen_con_texto, top_left, bottom_right, (0, 255, 0), 2)
                    cv2.putText(
                        imagen_con_texto, 
                        texto, 
                        (top_left[0], top_left[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.8, 
                        (0, 255, 0), 
                        2
                    )
            
            # Obtener texto completo
            textos = [texto for (_, texto, prob) in resultado if prob > 0.5]
            self.ultimo_texto = " ".join(textos)
            
            return resultado, imagen_con_texto
        except Exception as e:
            logger.error(f"Error al reconocer texto: {e}")
            return [], imagen
    
    def reconocer_texto_async(self, imagen: np.ndarray, callback=None) -> None:
        """Inicia reconocimiento de texto en segundo plano."""
        if not self.iniciado and not self.inicializando:
            logger.warning("EasyOCR no iniciado. Intentando iniciar...")
            self.iniciar()
            return
            
        # Lanzar reconocimiento en un hilo separado
        threading.Thread(
            target=self._reconocer_texto_hilo, 
            args=(imagen, callback),
            daemon=True
        ).start()
    
    def _reconocer_texto_hilo(self, imagen: np.ndarray, callback=None) -> None:
        """Procesa reconocimiento de texto en un hilo."""
        try:
            # Esperar a que EasyOCR esté inicializado
            timeout = 30  # Esperar máximo 30 segundos
            start_time = time.time()
            while self.inicializando and time.time() - start_time < timeout:
                time.sleep(0.5)
                
            if not self.iniciado:
                logger.error("OCR no inicializado después de esperar.")
                if callback:
                    callback([], imagen)
                return
                
            resultado, imagen_con_texto = self.reconocer_texto(imagen)
            
            if callback:
                callback(resultado, imagen_con_texto)
        except Exception as e:
            logger.error(f"Error en hilo de reconocimiento: {e}")
            if callback:
                callback([], imagen)
    
    def _preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """Preprocesa la imagen para mejorar reconocimiento de texto."""
        try:
            # Convertir a escala de grises
            gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
            
            # Aplicar filtro gaussiano para reducir ruido
            gris = cv2.GaussianBlur(gris, (5, 5), 0)
            
            # Binarización adaptativa
            _, thresh = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Operaciones morfológicas para limpiar la imagen
            kernel = np.ones((2, 2), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return thresh
        except Exception as e:
            logger.error(f"Error al preprocesar imagen: {e}")
            return imagen
            
# Importación de tiempo para uso en métodos asíncronos
import time