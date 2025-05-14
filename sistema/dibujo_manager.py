"""
Módulo para gestionar las funcionalidades de dibujo.
"""

import logging
import cv2
import numpy as np
import os
import time
import json
import pickle
from datetime import datetime
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger("SistemaKinect.DibujoManager")

class DibujoManager:
    """Gestiona las funcionalidades de dibujo avanzadas."""
    
    def __init__(self, config_manager):
        self.config = config_manager.obtener_config()
        self.dibujo_config = self.config.get("dibujo", {})
        self.colores = self.config.get("ui", {}).get("colores", {})
        self.paleta_colores = self.config.get("ui", {}).get("paleta_colores", {})
        
        self.resolution = tuple(self.config.get("kinect", {}).get("resolution", [640, 480]))
        self.dibujo = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        self.capa_temporal = np.zeros_like(self.dibujo)  # Capa para efectos temporales
        
        self.modo_dibujo = False
        self.puntos_dibujo = []
        self.historial_trazos = []  # Para deshacer/rehacer
        self.historial_index = -1
        self.grosor_linea = self.dibujo_config.get("grosor_linea", 3)
        self.radio_borrador = self.dibujo_config.get("radio_borrador", 30)
        self.color_dibujo = tuple(self.colores.get("dibujo", [0, 255, 0]))
        self.dibujando = False
        self.ultimo_autosave = time.time()
        self.autosave_interval = self.dibujo_config.get("autosave_interval", 60)  # en segundos
        self.sesiones_dir = self.dibujo_config.get("sesiones_dir", "sesiones")
        
        # Asegurar que exista el directorio para sesiones
        if not os.path.exists(self.sesiones_dir):
            try:
                os.makedirs(self.sesiones_dir)
            except Exception as e:
                logger.error(f"Error al crear directorio de sesiones: {e}")
        
        # Estado de sesión actual
        self.sesion_actual = None
    
    def limpiar_dibujo(self) -> None:
        """Limpia el lienzo de dibujo."""
        self.dibujo = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        self.capa_temporal = np.zeros_like(self.dibujo)
        self.historial_trazos = []
        self.historial_index = -1
        logger.info("Lienzo de dibujo limpiado.")
    
    def dibujar_punto(self, x: int, y: int) -> None:
        """Dibuja un punto en las coordenadas dadas."""
        if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
            if not self.dibujando:
                self.puntos_dibujo = [(x, y)]
                self.dibujando = True
                # Iniciar un nuevo trazo para el historial
                self.historial_trazos = self.historial_trazos[:self.historial_index + 1]
                self.historial_trazos.append({
                    'tipo': 'trazo',
                    'color': self.color_dibujo,
                    'grosor': self.grosor_linea,
                    'puntos': [(x, y)]
                })
                self.historial_index = len(self.historial_trazos) - 1
            else:
                self.puntos_dibujo.append((x, y))
                # Actualizar el trazo actual en el historial
                if self.historial_trazos and self.historial_index >= 0:
                    self.historial_trazos[self.historial_index]['puntos'].append((x, y))
                
                if len(self.puntos_dibujo) > 1:
                    cv2.line(
                        self.dibujo, 
                        self.puntos_dibujo[-2], 
                        self.puntos_dibujo[-1], 
                        self.color_dibujo, 
                        self.grosor_linea
                    )
            
            # Verificar si es momento de autosave
            if time.time() - self.ultimo_autosave > self.autosave_interval:
                self._auto_guardar_sesion()
                self.ultimo_autosave = time.time()
    
    def borrar_punto(self, x: int, y: int) -> None:
        """Borra en las coordenadas dadas utilizando un borrador circular."""
        if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
            if not self.dibujando:
                self.dibujando = True
                # Iniciar un nuevo trazo de borrado para el historial
                self.historial_trazos = self.historial_trazos[:self.historial_index + 1]
                self.historial_trazos.append({
                    'tipo': 'borrado',
                    'radio': self.radio_borrador,
                    'puntos': [(x, y)]
                })
                self.historial_index = len(self.historial_trazos) - 1
            else:
                # Actualizar el trazo de borrado en el historial
                if self.historial_trazos and self.historial_index >= 0:
                    self.historial_trazos[self.historial_index]['puntos'].append((x, y))
            
            cv2.circle(
                self.dibujo, 
                (x, y), 
                self.radio_borrador, 
                tuple(self.colores.get("borrador", [0, 0, 0])), 
                -1
            )
    
    def terminar_dibujo(self) -> None:
        """Termina el trazo actual de dibujo."""
        self.dibujando = False
        self.puntos_dibujo.clear()
    
    def cambiar_color(self, color: Tuple[int, int, int]) -> None:
        """Cambia el color de dibujo."""
        self.color_dibujo = color
        logger.info(f"Color de dibujo cambiado a {color}.")
    
    def cambiar_color_por_nombre(self, nombre_color: str) -> bool:
        """Cambia el color de dibujo según su nombre en la paleta."""
        if nombre_color in self.paleta_colores:
            self.color_dibujo = tuple(self.paleta_colores[nombre_color])
            logger.info(f"Color de dibujo cambiado a {nombre_color}: {self.color_dibujo}")
            
            # Narrar el cambio de color si el asistente está disponible
            try:
                from . import sistema_interactivo
                if hasattr(sistema_interactivo, 'asistente'):
                    sistema_interactivo.asistente.hablar(f"Color cambiado a {nombre_color}", 
                                                       prioridad=1, categoria="configuracion")
            except:
                pass
                
            return True
        logger.warning(f"Color {nombre_color} no encontrado en la paleta.")
        return False
    
    def cambiar_grosor(self, grosor: int) -> None:
        """Cambia el grosor de línea de dibujo."""
        if grosor > 0:
            self.grosor_linea = grosor
            logger.info(f"Grosor de línea cambiado a {grosor}.")
    
    def cambiar_radio_borrador(self, radio: int) -> None:
        """Cambia el radio del borrador."""
        if radio > 0:
            self.radio_borrador = radio
            logger.info(f"Radio de borrador cambiado a {radio}.")
    
    def deshacer(self) -> bool:
        """Deshace el último trazo."""
        if self.historial_index >= 0:
            self.historial_index -= 1
            self._reconstruir_dibujo()
            logger.info("Acción deshecha.")
            
            # Narrar la acción si el asistente está disponible
            try:
                from . import sistema_interactivo
                if hasattr(sistema_interactivo, 'asistente'):
                    sistema_interactivo.asistente.hablar("Acción deshecha", 
                                                       prioridad=1, categoria="edicion")
            except:
                pass
                
            return True
        logger.info("No hay más acciones para deshacer.")
        return False
    
    def rehacer(self) -> bool:
        """Rehace el último trazo deshecho."""
        if self.historial_index < len(self.historial_trazos) - 1:
            self.historial_index += 1
            self._reconstruir_dibujo()
            logger.info("Acción rehecha.")
            
            # Narrar la acción si el asistente está disponible
            try:
                from . import sistema_interactivo
                if hasattr(sistema_interactivo, 'asistente'):
                    sistema_interactivo.asistente.hablar("Acción rehecha", 
                                                       prioridad=1, categoria="edicion")
            except:
                pass
                
            return True
        logger.info("No hay más acciones para rehacer.")
        return False
    
    def _reconstruir_dibujo(self) -> None:
        """Reconstruye el dibujo a partir del historial de trazos hasta el índice actual."""
        self.dibujo = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        
        for i in range(self.historial_index + 1):
            trazo = self.historial_trazos[i]
            puntos = trazo['puntos']
            
            if trazo['tipo'] == 'trazo' and len(puntos) > 1:
                for j in range(1, len(puntos)):
                    cv2.line(
                        self.dibujo,
                        puntos[j-1],
                        puntos[j],
                        trazo['color'],
                        trazo['grosor']
                    )
            elif trazo['tipo'] == 'borrado':
                for punto in puntos:
                    cv2.circle(
                        self.dibujo,
                        punto,
                        trazo['radio'],
                        tuple(self.colores.get("borrador", [0, 0, 0])),
                        -1
                    )
    
    def guardar_dibujo(self, nombre_archivo: str = "dibujo.png") -> str:
        """Guarda el dibujo actual como imagen."""
        try:
            # Asegurar que la extensión sea .png
            if not nombre_archivo.lower().endswith('.png'):
                nombre_archivo += '.png'
                
            cv2.imwrite(nombre_archivo, self.dibujo)
            logger.info(f"Dibujo guardado como {nombre_archivo}")
            return nombre_archivo
        except Exception as e:
            logger.error(f"Error al guardar dibujo: {e}")
            return ""
    
    def guardar_sesion(self, nombre_sesion: Optional[str] = None) -> str:
        """Guarda la sesión de dibujo actual con historial para poder continuarla después."""
        try:
            if nombre_sesion is None:
                # Generar nombre basado en fecha y hora
                nombre_sesion = f"sesion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Asegurar que la extensión sea .session
            if not nombre_sesion.lower().endswith('.session'):
                nombre_sesion += '.session'
            
            ruta_sesion = os.path.join(self.sesiones_dir, nombre_sesion)
            
            # Crear diccionario con todos los datos de la sesión
            datos_sesion = {
                'dibujo': self.dibujo.tolist(),  # Convertir a lista para serialización
                'historial_trazos': self.historial_trazos,
                'historial_index': self.historial_index,
                'color_dibujo': self.color_dibujo,
                'grosor_linea': self.grosor_linea,
                'radio_borrador': self.radio_borrador,
                'timestamp': datetime.now().isoformat()
            }
            
            # Guardar datos usando pickle
            with open(ruta_sesion, 'wb') as archivo:
                pickle.dump(datos_sesion, archivo)
            
            self.sesion_actual = nombre_sesion
            logger.info(f"Sesión guardada como {ruta_sesion}")
            return ruta_sesion
        except Exception as e:
            logger.error(f"Error al guardar sesión: {e}")
            return ""
    
    def _auto_guardar_sesion(self) -> None:
        """Guarda automáticamente la sesión actual."""
        try:
            nombre_auto = f"autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}.session"
            ruta_sesion = os.path.join(self.sesiones_dir, nombre_auto)
            
            # Si hay demasiados autosaves, eliminar los más antiguos
            autosaves = [f for f in os.listdir(self.sesiones_dir) if f.startswith('autosave_')]
            if len(autosaves) > 5:  # mantener solo los 5 más recientes
                autosaves.sort()
                for autosave_viejo in autosaves[:-5]:
                    try:
                        os.remove(os.path.join(self.sesiones_dir, autosave_viejo))
                    except:
                        pass
            
            datos_sesion = {
                'dibujo': self.dibujo.tolist(),
                'historial_trazos': self.historial_trazos,
                'historial_index': self.historial_index,
                'color_dibujo': self.color_dibujo,
                'grosor_linea': self.grosor_linea,
                'radio_borrador': self.radio_borrador,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(ruta_sesion, 'wb') as archivo:
                pickle.dump(datos_sesion, archivo)
            
            logger.info(f"Sesión auto-guardada como {ruta_sesion}")
        except Exception as e:
            logger.error(f"Error al auto-guardar sesión: {e}")
    
    def cargar_sesion(self, ruta_sesion: str) -> bool:
        """Carga una sesión de dibujo guardada previamente."""
        try:
            if not os.path.exists(ruta_sesion):
                # Intentar buscar en el directorio de sesiones
                ruta_completa = os.path.join(self.sesiones_dir, ruta_sesion)
                if os.path.exists(ruta_completa):
                    ruta_sesion = ruta_completa
                else:
                    logger.error(f"Archivo de sesión no encontrado: {ruta_sesion}")
                    return False
            
            with open(ruta_sesion, 'rb') as archivo:
                datos_sesion = pickle.load(archivo)
            
            # Restaurar todos los datos
            self.dibujo = np.array(datos_sesion['dibujo'], dtype=np.uint8)
            self.historial_trazos = datos_sesion['historial_trazos']
            self.historial_index = datos_sesion['historial_index']
            self.color_dibujo = datos_sesion['color_dibujo']
            self.grosor_linea = datos_sesion['grosor_linea']
            self.radio_borrador = datos_sesion['radio_borrador']
            
            self.sesion_actual = os.path.basename(ruta_sesion)
            logger.info(f"Sesión cargada: {ruta_sesion}")
            return True
        except Exception as e:
            logger.error(f"Error al cargar sesión: {e}")
            return False
    
    def listar_sesiones(self) -> List[Dict[str, str]]:
        """Lista todas las sesiones guardadas con su información."""
        sesiones = []
        try:
            if os.path.exists(self.sesiones_dir):
                archivos = os.listdir(self.sesiones_dir)
                for archivo in archivos:
                    if archivo.endswith('.session'):
                        ruta_completa = os.path.join(self.sesiones_dir, archivo)
                        try:
                            # Obtener información básica sin cargar toda la sesión
                            with open(ruta_completa, 'rb') as f:
                                datos = pickle.load(f)
                            
                            # Extraer solo los metadatos necesarios
                            sesiones.append({
                                'nombre': archivo,
                                'ruta': ruta_completa,
                                'fecha': datos['timestamp'] if 'timestamp' in datos else 'Desconocido',
                                'es_autosave': archivo.startswith('autosave_')
                            })
                        except:
                            # Si hay error al leer, incluir con información mínima
                            sesiones.append({
                                'nombre': archivo,
                                'ruta': ruta_completa,
                                'fecha': 'Error al leer',
                                'es_autosave': archivo.startswith('autosave_')
                            })
            
            # Ordenar por fecha, más reciente primero
            sesiones.sort(key=lambda x: x['fecha'], reverse=True)
            return sesiones
        except Exception as e:
            logger.error(f"Error al listar sesiones: {e}")
            return []
    
    def cargar_dibujo(self, nombre_archivo: str) -> bool:
        """Carga un dibujo desde un archivo de imagen."""
        try:
            img = cv2.imread(nombre_archivo)
            if img is None:
                logger.error(f"No se pudo cargar la imagen {nombre_archivo}.")
                return False
                
            # Redimensionar si es necesario
            if img.shape[:2] != (self.resolution[1], self.resolution[0]):
                img = cv2.resize(img, (self.resolution[0], self.resolution[1]))
                
            self.dibujo = img
            # Al cargar una imagen, perdemos el historial
            self.historial_trazos = [{
                'tipo': 'imagen_cargada',
                'origen': nombre_archivo,
                'timestamp': datetime.now().isoformat()
            }]
            self.historial_index = 0
            
            logger.info(f"Dibujo cargado desde {nombre_archivo}")
            return True
        except Exception as e:
            logger.error(f"Error al cargar dibujo: {e}")
            return False
    
    def dibujar_indicador_posicion(self, x: int, y: int, radio: int = 10) -> None:
        """Dibuja un indicador temporal de posición del cursor."""
        self.capa_temporal = np.zeros_like(self.dibujo)
        if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
            # Dibujar círculo como indicador
            cv2.circle(
                self.capa_temporal,
                (x, y),
                radio,
                tuple(self.colores.get("indicador", (255, 0, 255))),
                2
            )
            
            # Dibujar líneas cruzadas para mejorar visibilidad
            cv2.line(
                self.capa_temporal,
                (x - radio, y),
                (x + radio, y),
                tuple(self.colores.get("indicador", (255, 0, 255))),
                1
            )
            cv2.line(
                self.capa_temporal,
                (x, y - radio),
                (x, y + radio),
                tuple(self.colores.get("indicador", (255, 0, 255))),
                1
            )
    
    def dibujar_paleta_colores(self, x_base: int, y_base: int, 
                             tamano_cuadro: int = 30, 
                             margen: int = 5) -> None:
        """Dibuja una paleta de colores en la capa temporal."""
        self.capa_temporal = np.zeros_like(self.dibujo)
        
        for i, (nombre, color) in enumerate(self.paleta_colores.items()):
           x = x_base + (i % 3) * (tamano_cuadro + margen)
           y = y_base + (i // 3) * (tamano_cuadro + margen)
           
           # Dibujar cuadro de color
           cv2.rectangle(
               self.capa_temporal,
               (x, y),
               (x + tamano_cuadro, y + tamano_cuadro),
               tuple(color),
               -1
           )
           
           # Marcar color seleccionado
           if tuple(color) == self.color_dibujo:
               cv2.rectangle(
                   self.capa_temporal,
                   (x - 2, y - 2),
                   (x + tamano_cuadro + 2, y + tamano_cuadro + 2),
                   (255, 255, 255),
                   2
               )
           
           # Texto con nombre del color
           cv2.putText(
               self.capa_temporal,
               nombre,
               (x, y + tamano_cuadro + 15),
               cv2.FONT_HERSHEY_SIMPLEX,
               0.4,
               (255, 255, 255),
               1
           )
   
    def obtener_dibujo(self) -> np.ndarray:
       """Obtiene la imagen actual del dibujo combinada con la capa temporal."""
       # Combinar dibujo con capa temporal
       resultado = cv2.addWeighted(self.dibujo, 1, self.capa_temporal, 1, 0)
       return resultado
   
    def obtener_dibujo_sin_capa_temporal(self) -> np.ndarray:
       """Obtiene la imagen actual del dibujo sin la capa temporal."""
       return self.dibujo.copy()