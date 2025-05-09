"""
Módulo para gestionar la interfaz de usuario del sistema.
"""

import logging
import time
import cv2
import numpy as np
from typing import Dict, Optional, Tuple, List, Any

logger = logging.getLogger("SistemaKinect.UIManager")

class UIManager:
    """Gestiona la interfaz de usuario del sistema."""
    
    def __init__(self, config_manager):
        self.config = config_manager.obtener_config("ui")
        self.botones = self.config.get("botones", {})
        self.dimensiones_boton = self.config.get("dimensiones_boton", {"ancho": 100, "alto": 40})
        self.colores = self.config.get("colores", {})
        self.ventana_nombre = "Sistema Interactivo - Kinect"
        self.ventana_creada = False
        self.boton_seleccionado = None
        self.estado_mano = "Esperando acción"
        self.mensaje_sistema = ""
        self.mensaje_timeout = 0
        self.fps = 0
        self.fps_contador = 0
        self.fps_tiempo = time.time()
        self.modo_debug = config_manager.obtener_config().get("modo_debug", False)
        
        # Ventanas secundarias
        self.ventanas_secundarias = {}
        
        # Obtener resolución para ajustar UI
        self.resolucion = tuple(config_manager.obtener_config("kinect").get("resolution", [640, 480]))
        
        # Verificar y ajustar posiciones de botones si es necesario
        self._verificar_ajustar_botones()
        
        # Inicializar capas de UI
        self._inicializar_capas_ui()
    
    def _inicializar_capas_ui(self) -> None:
        """Inicializa capas para la UI superpuesta."""
        self.capa_botones = np.zeros((self.resolucion[1], self.resolucion[0], 3), dtype=np.uint8)
        self.indicador_mano = np.zeros_like(self.capa_botones)
    
    def _verificar_ajustar_botones(self) -> None:
        """Verifica y ajusta las posiciones de los botones para que quepan en la pantalla."""
        ancho_boton = self.dimensiones_boton.get("ancho", 100)
        alto_boton = self.dimensiones_boton.get("alto", 40)
        
        # Verificar botones principales
        botones_ajustados = {}
        necesita_ajuste = False
        
        # Verificar si algún botón está fuera de los límites de la ventana
        for texto, (bx, by) in self.botones.items():
            if bx + ancho_boton > self.resolucion[0] or by + alto_boton > self.resolucion[1]:
                necesita_ajuste = True
                break
        
        if necesita_ajuste:
            logger.warning("Se detectaron botones principales fuera de los límites de la ventana. Ajustando posiciones.")
            # Distribuir botones uniformemente
            margen = 10
            botones_por_fila = max(1, int(self.resolucion[0] / (ancho_boton + margen)))
            
            for i, (texto, _) in enumerate(self.botones.items()):
                fila = i // botones_por_fila
                columna = i % botones_por_fila
                
                x = margen + columna * (ancho_boton + margen)
                y = margen + fila * (alto_boton + margen)
                
                botones_ajustados[texto] = [x, y]
            
            self.botones = botones_ajustados
            logger.info(f"Posiciones de botones principales ajustadas: {self.botones}")
    
    def crear_ventana(self) -> bool:
        """Crea la ventana principal de la interfaz."""
        try:
            cv2.namedWindow(self.ventana_nombre, cv2.WINDOW_AUTOSIZE)
            self.ventana_creada = True
            logger.info("Ventana de interfaz creada correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al crear ventana de interfaz: {e}")
            return False
    
    def crear_ventana_secundaria(self, nombre: str) -> bool:
        """Crea una ventana secundaria."""
        try:
            if nombre in self.ventanas_secundarias:
                logger.warning(f"Ventana {nombre} ya existe.")
                return True
                
            cv2.namedWindow(nombre, cv2.WINDOW_AUTOSIZE)
            self.ventanas_secundarias[nombre] = True
            logger.info(f"Ventana secundaria {nombre} creada correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al crear ventana secundaria {nombre}: {e}")
            return False
    
    def actualizar_fps(self) -> None:
        """Actualiza el contador de FPS."""
        self.fps_contador += 1
        if time.time() - self.fps_tiempo >= 1:
            self.fps = self.fps_contador
            self.fps_contador = 0
            self.fps_tiempo = time.time()
    
    def mostrar_mensaje(self, mensaje: str, duracion: int = 3) -> None:
        """Muestra un mensaje temporal en la interfaz."""
        self.mensaje_sistema = mensaje
        self.mensaje_timeout = time.time() + duracion
    
    def dibujar_ui(self, frame: np.ndarray, dibujo: np.ndarray) -> np.ndarray:
        """Dibuja la interfaz de usuario sobre el frame."""
        if not self.ventana_creada:
            logger.warning("Ventana no creada. No se puede dibujar UI.")
            return frame
        
        try:
            # Combinar frame con dibujo
            frame_combinado = cv2.addWeighted(frame, 1, dibujo, 1, 0)
            
            # Reiniciar capas de UI
            self.capa_botones = np.zeros_like(frame_combinado)
            
            # Dibujar botones principales
            self._dibujar_botones(self.botones, self.capa_botones)
            
            # Mostrar estado y mensajes
            y_texto = frame.shape[0] - 80
            cv2.putText(
                self.capa_botones, 
                f"Estado: {self.estado_mano}", 
                (20, y_texto), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                self.colores.get("texto", (255, 255, 255)), 
                2
            )
            
            # Mostrar mensaje del sistema si está activo
            if time.time() < self.mensaje_timeout:
                cv2.putText(
                    self.capa_botones, 
                    self.mensaje_sistema, 
                    (20, frame.shape[0] - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 0), 
                    2
                )
            
            # Mostrar FPS en modo debug
            if self.modo_debug:
                cv2.putText(
                    self.capa_botones, 
                    f"FPS: {self.fps}", 
                    (frame.shape[1] - 120, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 255), 
                    2
                )
            
            # Combinar todas las capas
            # Primero el frame con el dibujo
            resultado = frame_combinado.copy()
            
            # Añadir la capa de botones
            mascara_botones = cv2.cvtColor(self.capa_botones, cv2.COLOR_BGR2GRAY) > 0
            resultado[mascara_botones] = self.capa_botones[mascara_botones]
            
            # Añadir el indicador de mano
            mascara_indicador = cv2.cvtColor(self.indicador_mano, cv2.COLOR_BGR2GRAY) > 0
            resultado[mascara_indicador] = self.indicador_mano[mascara_indicador]
            
            return resultado
        except Exception as e:
            logger.error(f"Error al dibujar UI: {e}")
            return frame
    
    def _dibujar_botones(self, botones: Dict[str, List[int]], capa: np.ndarray) -> None:
        """Dibuja los botones en la capa especificada."""
        ancho_boton = self.dimensiones_boton.get("ancho", 100)
        alto_boton = self.dimensiones_boton.get("alto", 40)
        
        for texto, (bx, by) in botones.items():
            color = self.colores.get("boton_seleccionado", (0, 255, 255)) if self.boton_seleccionado == texto else self.colores.get("boton_normal", (200, 200, 200))
            
            # Asegurar que el botón esté dentro de los límites de la ventana
            if 0 <= bx < self.resolucion[0] and 0 <= by < self.resolucion[1]:
                # Ajustar el ancho para que no se salga de la pantalla
                ancho_ajustado = min(ancho_boton, self.resolucion[0] - bx)
                alto_ajustado = min(alto_boton, self.resolucion[1] - by)
                
                # Dibujar fondo del botón
                cv2.rectangle(
                    capa, 
                    (bx, by), 
                    (bx + ancho_ajustado, by + alto_ajustado), 
                    color, 
                    -1
                )
                
                # Dibujar borde del botón (para mejor visibilidad)
                cv2.rectangle(
                    capa, 
                    (bx, by), 
                    (bx + ancho_ajustado, by + alto_ajustado), 
                    (0, 0, 0), 
                    1
                )
                
                # Obtener tamaño de texto para centrarlo en el botón
                texto_size = cv2.getTextSize(
                    texto, 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    2
                )[0]
                
                # Calcular posición centrada del texto
                texto_x = bx + (ancho_ajustado - texto_size[0]) // 2
                texto_y = by + (alto_ajustado + texto_size[1]) // 2
                
                # Dibujar texto del botón
                cv2.putText(
                    capa, 
                    texto, 
                    (texto_x, texto_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 0, 0), 
                    2
                )
    
    def dibujar_indicador_mano(self, x: int, y: int, radio: int = 15) -> None:
        """Dibuja un indicador visual en la posición de la mano."""
        self.indicador_mano = np.zeros_like(self.capa_botones)
        if 0 <= x < self.resolucion[0] and 0 <= y < self.resolucion[1]:
            # Dibujar círculo para indicar posición
            cv2.circle(
                self.indicador_mano,
                (x, y),
                radio,
                (0, 255, 255),
                2
            )
            
            # Dibujar líneas cruzadas para mejor visibilidad
            cv2.line(
                self.indicador_mano,
                (x - radio, y),
                (x + radio, y),
                (0, 255, 255),
                1
            )
            cv2.line(
                self.indicador_mano,
                (x, y - radio),
                (x, y + radio),
                (0, 255, 255),
                1
            )
    
    def obtener_limites_boton(self, texto: str) -> Tuple[int, int, int, int]:
        """Obtiene los límites (x, y, ancho, alto) de un botón específico."""
        if texto not in self.botones:
            return (0, 0, 0, 0)
            
        bx, by = self.botones[texto]
        ancho = self.dimensiones_boton.get("ancho", 100)
        alto = self.dimensiones_boton.get("alto", 40)
        
        return (bx, by, ancho, alto)
    
    def verificar_punto_en_boton(self, punto_x: int, punto_y: int) -> Optional[str]:
        """Verifica si un punto está dentro de algún botón y devuelve el texto del botón."""
        ancho = self.dimensiones_boton.get("ancho", 100)
        alto = self.dimensiones_boton.get("alto", 40)
        
        for texto, (bx, by) in self.botones.items():
            if bx <= punto_x <= bx + ancho and by <= punto_y <= by + alto:
                return texto
                
        return None
    
    def mostrar_frame(self, frame: np.ndarray) -> None:
        """Muestra un frame en la ventana principal."""
        if not self.ventana_creada:
            logger.warning("Ventana no creada. No se puede mostrar frame.")
            return
        
        try:
            cv2.imshow(self.ventana_nombre, frame)
            self.actualizar_fps()
        except Exception as e:
            logger.error(f"Error al mostrar frame: {e}")
    
    def mostrar_frame_secundario(self, nombre: str, frame: np.ndarray) -> None:
        """Muestra un frame en una ventana secundaria."""
        if nombre not in self.ventanas_secundarias:
            if not self.crear_ventana_secundaria(nombre):
                return
        
        try:
            cv2.imshow(nombre, frame)
        except Exception as e:
            logger.error(f"Error al mostrar frame en ventana secundaria {nombre}: {e}")
    
    def cerrar_ventana_secundaria(self, nombre: str) -> None:
        """Cierra una ventana secundaria específica."""
        if nombre in self.ventanas_secundarias:
            try:
                cv2.destroyWindow(nombre)
                del self.ventanas_secundarias[nombre]
                logger.info(f"Ventana secundaria {nombre} cerrada.")
            except Exception as e:
                logger.error(f"Error al cerrar ventana secundaria {nombre}: {e}")
    
    def cerrar_ventanas(self) -> None:
        """Cierra todas las ventanas de la interfaz."""
        try:
            cv2.destroyAllWindows()
            self.ventana_creada = False
            self.ventanas_secundarias.clear()
            logger.info("Todas las ventanas cerradas correctamente.")
        except Exception as e:
            logger.error(f"Error al cerrar ventanas: {e}")