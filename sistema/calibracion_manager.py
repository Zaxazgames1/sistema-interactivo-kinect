"""
Módulo para gestionar la calibración de gestos y sensibilidad.
"""

import logging
import cv2
import numpy as np
import json
import os
import time
from typing import Dict, Tuple, Optional, List, Any

logger = logging.getLogger("SistemaKinect.CalibracionManager")

class CalibracionManager:
    """Gestiona la calibración de gestos y sensibilidad del sistema."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.obtener_config()
        self.calibracion_config = self.config.get("calibracion", {})
        
        # Parámetros de calibración
        self.sensibilidad_gestos = self.calibracion_config.get("sensibilidad_gestos", 0.7)
        self.distancia_minima_dedos = self.calibracion_config.get("distancia_minima_dedos", 0.1)
        self.tiempo_gesto = self.calibracion_config.get("tiempo_gesto", 0.5)
        
        # Estado de calibración
        self.calibrando = False
        self.paso_calibracion = 0
        self.total_pasos = 4
        self.datos_calibracion = {}
        self.instrucciones = [
            "Extienda todos los dedos y muestre la palma de la mano",
            "Cierre el puño completamente",
            "Extienda solo el dedo índice",
            "Forme un gesto de pinza (pulgar e índice)"
        ]
        self.inicio_paso = 0
        self.duracion_paso = 3  # segundos para mantener cada gesto
        
        # Imagen para mostrar durante calibración
        self.resolution = tuple(self.config.get("kinect", {}).get("resolution", [640, 480]))
        self.imagen_calibracion = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        
        # Referencia a las funciones de umbral para cada gesto
        self.umbrales_gestos = {
            "mano_abierta": 0.7,
            "puno_cerrado": 0.7,
            "indice_extendido": 0.7,
            "pinza": 0.7
        }
        
        # Cargar calibración guardada si existe
        self._cargar_calibracion()
    
    def iniciar_calibracion(self) -> bool:
        """Inicia el proceso de calibración."""
        try:
            self.calibrando = True
            self.paso_calibracion = 0
            self.datos_calibracion = {}
            self.inicio_paso = time.time()
            logger.info("Iniciando proceso de calibración")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar calibración: {e}")
            return False
    
    def siguiente_paso_calibracion(self) -> Tuple[bool, str]:
        """Avanza al siguiente paso de calibración."""
        if not self.calibrando:
            return False, "No hay calibración en curso"
        
        self.paso_calibracion += 1
        self.inicio_paso = time.time()
        
        if self.paso_calibracion >= self.total_pasos:
            # Finalizar calibración
            self._finalizar_calibracion()
            return True, "Calibración completada"
        
        logger.info(f"Avanzando a paso de calibración {self.paso_calibracion+1}/{self.total_pasos}")
        return True, self._obtener_instruccion_actual()
    
    def _finalizar_calibracion(self) -> None:
        """Finaliza el proceso de calibración y guarda los resultados."""
        try:
            # Procesar datos recopilados y establecer umbrales
            if "mano_abierta" in self.datos_calibracion:
                self.umbrales_gestos["mano_abierta"] = self._calcular_umbral(self.datos_calibracion["mano_abierta"])
            
            if "puno_cerrado" in self.datos_calibracion:
                self.umbrales_gestos["puno_cerrado"] = self._calcular_umbral(self.datos_calibracion["puno_cerrado"])
            
            if "indice_extendido" in self.datos_calibracion:
                self.umbrales_gestos["indice_extendido"] = self._calcular_umbral(self.datos_calibracion["indice_extendido"])
            
            if "pinza" in self.datos_calibracion:
                self.umbrales_gestos["pinza"] = self._calcular_umbral(self.datos_calibracion["pinza"])
            
            # Actualizar configuración
            nueva_config = self.config.copy()
            nueva_config["calibracion"] = {
                "sensibilidad_gestos": self.sensibilidad_gestos,
                "distancia_minima_dedos": self.distancia_minima_dedos,
                "tiempo_gesto": self.tiempo_gesto,
                "umbrales_gestos": self.umbrales_gestos
            }
            
            # Guardar en archivo
            self._guardar_calibracion()
            
            # Actualizar configuración en gestor
            self.config_manager.config = nueva_config
            self.config_manager.guardar_config()
            
            self.calibrando = False
            logger.info("Calibración finalizada y guardada")
        except Exception as e:
            logger.error(f"Error al finalizar calibración: {e}")
            self.calibrando = False
    
    def _calcular_umbral(self, datos: List[float]) -> float:
        """Calcula umbral óptimo a partir de datos recopilados."""
        if not datos:
            return 0.7  # valor por defecto
        
        # Usar promedio con ajuste de sensibilidad
        promedio = sum(datos) / len(datos)
        return promedio * self.sensibilidad_gestos
    
    def _obtener_instruccion_actual(self) -> str:
        """Obtiene la instrucción para el paso actual de calibración."""
        if 0 <= self.paso_calibracion < len(self.instrucciones):
            return self.instrucciones[self.paso_calibracion]
        return "Mantenga la posición"
    
    def registrar_datos_gesto(self, landmarks, dedos_levantados: List[bool]) -> None:
        """Registra datos de un gesto para la calibración actual."""
        if not self.calibrando:
            return
        
        # Solo registrar si ha pasado el tiempo mínimo de inicio del paso
        tiempo_actual = time.time()
        if tiempo_actual - self.inicio_paso < 1.0:
            return  # Esperar al menos 1 segundo para estabilizar el gesto
        
        # Registrar datos según el paso actual
        try:
            if self.paso_calibracion == 0:  # Mano abierta
                # Calcular apertura de la mano (distancia entre dedos)
                if sum(dedos_levantados) >= 4:  # Al menos 4 dedos levantados
                    if "mano_abierta" not in self.datos_calibracion:
                        self.datos_calibracion["mano_abierta"] = []
                    
                    # Calcular apertura promedio entre dedos
                    apertura = self._calcular_apertura_mano(landmarks)
                    self.datos_calibracion["mano_abierta"].append(apertura)
            
            elif self.paso_calibracion == 1:  # Puño cerrado
                if sum(dedos_levantados) <= 1:  # Máximo 1 dedo levantado (para contemplar variaciones)
                    if "puno_cerrado" not in self.datos_calibracion:
                        self.datos_calibracion["puno_cerrado"] = []
                    
                    # Calcular cierre del puño
                    cierre = self._calcular_cierre_puno(landmarks)
                    self.datos_calibracion["puno_cerrado"].append(cierre)
            
            elif self.paso_calibracion == 2:  # Índice extendido
                if dedos_levantados[1] and not any(dedos_levantados[2:]):
                    if "indice_extendido" not in self.datos_calibracion:
                        self.datos_calibracion["indice_extendido"] = []
                    
                    # Calcular extensión del índice
                    extension = self._calcular_extension_indice(landmarks)
                    self.datos_calibracion["indice_extendido"].append(extension)
            
            elif self.paso_calibracion == 3:  # Pinza
                if "pinza" not in self.datos_calibracion:
                    self.datos_calibracion["pinza"] = []
                
                # Calcular distancia pinza
                distancia_pinza = self._calcular_distancia_pinza(landmarks)
                self.datos_calibracion["pinza"].append(distancia_pinza)
        
        except Exception as e:
            logger.error(f"Error al registrar datos de gesto: {e}")
    
    def _calcular_apertura_mano(self, landmarks) -> float:
        """Calcula la apertura de la mano basada en la distancia entre dedos."""
        try:
            # Calcular distancia entre puntas de dedos
            mp_hands = self._get_mp_hands()
            
            # Puntos de punta de dedos
            puntas = [
                landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP],
                landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
                landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
            ]
            
            # Calcular distancias entre dedos adyacentes
            distancias = []
            for i in range(len(puntas) - 1):
                dx = puntas[i].x - puntas[i+1].x
                dy = puntas[i].y - puntas[i+1].y
                distancia = (dx**2 + dy**2)**0.5
                distancias.append(distancia)
            
            # Promedio de distancias
            return sum(distancias) / len(distancias)
        except Exception as e:
            logger.error(f"Error al calcular apertura de mano: {e}")
            return 0.1  # valor por defecto
    
    def _calcular_cierre_puno(self, landmarks) -> float:
        """Calcula qué tan cerrado está el puño."""
        try:
            mp_hands = self._get_mp_hands()
            
            # Obtener punto central de la palma
            wrist = landmarks.landmark[mp_hands.HandLandmark.WRIST]
            middle_base = landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
            
            # Centro aproximado de la palma
            center_x = (wrist.x + middle_base.x) / 2
            center_y = (wrist.y + middle_base.y) / 2
            
            # Puntas de los dedos
            finger_tips = [
                landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP],
                landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
                landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
            ]
            
            # Calcular distancia promedio desde el centro a las puntas
            distances = []
            for tip in finger_tips:
                dx = tip.x - center_x
                dy = tip.y - center_y
                distance = (dx**2 + dy**2)**0.5
                distances.append(distance)
            
            # Un puño cerrado tendrá distancias más pequeñas
            return sum(distances) / len(distances)
        except Exception as e:
            logger.error(f"Error al calcular cierre de puño: {e}")
            return 0.2  # valor por defecto
    
    def _calcular_extension_indice(self, landmarks) -> float:
        """Calcula la extensión del dedo índice."""
        try:
            mp_hands = self._get_mp_hands()
            
            # Puntos clave del dedo índice
            index_tip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            index_dip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP]
            index_pip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
            index_mcp = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
            
            # Calcular longitud total del dedo
            d1 = self._distancia_entre_puntos(index_tip, index_dip)
            d2 = self._distancia_entre_puntos(index_dip, index_pip)
            d3 = self._distancia_entre_puntos(index_pip, index_mcp)
            
            # Distancia directa entre punta y base
            d_directa = self._distancia_entre_puntos(index_tip, index_mcp)
            
            # Relación entre distancia directa y suma de segmentos
            # Un dedo extendido tendrá una relación más cercana a 1
            extension = d_directa / (d1 + d2 + d3) if (d1 + d2 + d3) > 0 else 0
            
            return extension
        except Exception as e:
            logger.error(f"Error al calcular extensión del índice: {e}")
            return 0.8  # valor por defecto
    
    def _calcular_distancia_pinza(self, landmarks) -> float:
        """Calcula la distancia entre el pulgar y el índice para el gesto de pinza."""
        try:
            mp_hands = self._get_mp_hands()
            
            # Obtener puntas de pulgar e índice
            thumb_tip = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            # Calcular distancia
            return self._distancia_entre_puntos(thumb_tip, index_tip)
        except Exception as e:
            logger.error(f"Error al calcular distancia de pinza: {e}")
            return 0.1  # valor por defecto
    
    def _distancia_entre_puntos(self, p1, p2) -> float:
        """Calcula la distancia euclidiana entre dos puntos."""
        return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)**0.5
    
    def _get_mp_hands(self):
        """Obtiene la referencia a mp_hands (MediaPipe Hands)."""
        import mediapipe as mp
        return mp.solutions.hands
    
    def verificar_tiempo_paso(self) -> bool:
        """Verifica si ha pasado suficiente tiempo en el paso actual para avanzar automáticamente."""
        tiempo_actual = time.time()
        return tiempo_actual - self.inicio_paso >= self.duracion_paso
    
    def obtener_progreso_paso(self) -> float:
        """Obtiene el progreso del paso actual de calibración (0.0 a 1.0)."""
        if not self.calibrando:
            return 0.0
            
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - self.inicio_paso
        return min(1.0, tiempo_transcurrido / self.duracion_paso)
    
    def generar_imagen_instruccion(self) -> np.ndarray:
        """Genera una imagen con instrucciones de calibración."""
        img = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        
        if not self.calibrando:
            texto = "Presione el botón 'Calibrar' para iniciar calibración"
            cv2.putText(img, texto, (50, self.resolution[1]//2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            return img
        
        # Título
        cv2.putText(
            img, 
            f"Calibración - Paso {self.paso_calibracion + 1} de {self.total_pasos}", 
            (50, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (0, 255, 255), 
            2
        )
        
        # Instrucción actual
        instruccion = self._obtener_instruccion_actual()
        y = 100
        # Dividir instrucción si es muy larga
        palabras = instruccion.split()
        linea = ""
        for palabra in palabras:
            prueba = linea + " " + palabra if linea else palabra
            if len(prueba) > 40:  # máximo ~40 caracteres por línea
                cv2.putText(img, linea, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y += 40
                linea = palabra
            else:
                linea = prueba
        
        if linea:
            cv2.putText(img, linea, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Barra de progreso
        progreso = self.obtener_progreso_paso()
        ancho_barra = int(self.resolution[0] * 0.7)
        alto_barra = 30
        x_barra = (self.resolution[0] - ancho_barra) // 2
        y_barra = self.resolution[1] - 100
        
        # Fondo de la barra
        cv2.rectangle(
            img, 
            (x_barra, y_barra), 
            (x_barra + ancho_barra, y_barra + alto_barra), 
            (100, 100, 100), 
            -1
        )
        
        # Barra de progreso
        ancho_progreso = int(ancho_barra * progreso)
        cv2.rectangle(
            img, 
            (x_barra, y_barra), 
            (x_barra + ancho_progreso, y_barra + alto_barra), 
            (0, 255, 0), 
            -1
        )
        
        # Borde de la barra
        cv2.rectangle(
            img, 
            (x_barra, y_barra), 
            (x_barra + ancho_barra, y_barra + alto_barra), 
            (255, 255, 255), 
            2
        )
        
        # Ilustración o imagen de referencia para el gesto
        self._dibujar_ilustracion_gesto(img)
        
        return img
    
    def _dibujar_ilustracion_gesto(self, img: np.ndarray) -> None:
        """Dibuja una ilustración del gesto que se debe realizar."""
        centro_x = self.resolution[0] // 2
        centro_y = self.resolution[1] // 2
        
        if self.paso_calibracion == 0:  # Mano abierta
            # Dibujar palma
            cv2.circle(img, (centro_x, centro_y), 50, (100, 100, 255), -1)
            
            # Dibujar dedos
            for i in range(5):
                angulo = np.pi / 6 + i * np.pi / 6
                x_fin = int(centro_x + 120 * np.cos(angulo))
                y_fin = int(centro_y - 120 * np.sin(angulo))
                cv2.line(img, (centro_x, centro_y), (x_fin, y_fin), (100, 100, 255), 15)
                cv2.circle(img, (x_fin, y_fin), 10, (255, 200, 200), -1)
        
        elif self.paso_calibracion == 1:  # Puño cerrado
            # Dibujar puño
            cv2.circle(img, (centro_x, centro_y), 60, (100, 100, 200), -1)
            cv2.circle(img, (centro_x, centro_y), 40, (150, 150, 220), -1)
        
        elif self.paso_calibracion == 2:  # Índice extendido
            # Dibujar palma
            cv2.circle(img, (centro_x, centro_y), 50, (100, 100, 255), -1)
            
            # Dibujar índice extendido
            x_fin = centro_x
            y_fin = centro_y - 120
            cv2.line(img, (centro_x, centro_y), (x_fin, y_fin), (100, 100, 255), 15)
            cv2.circle(img, (x_fin, y_fin), 10, (255, 200, 200), -1)
        
        elif self.paso_calibracion == 3:  # Pinza
            # Dibujar palma
            cv2.circle(img, (centro_x, centro_y), 50, (100, 100, 255), -1)
            
            # Dibujar pulgar e índice formando pinza
            x_pulgar = centro_x - 30
            y_pulgar = centro_y - 40
            cv2.line(img, (centro_x, centro_y), (x_pulgar, y_pulgar), (100, 100, 255), 15)
            
            x_indice = centro_x + 10
            y_indice = centro_y - 50
            cv2.line(img, (centro_x, centro_y), (x_indice, y_indice), (100, 100, 255), 15)
            
            # Dibujar círculo donde se juntan
            cv2.circle(img, ((x_pulgar + x_indice) // 2, (y_pulgar + y_indice) // 2), 
                      15, (255, 200, 200), -1)
    
    def _guardar_calibracion(self) -> bool:
        """Guarda la calibración actual en un archivo."""
        try:
            datos = {
                "sensibilidad_gestos": self.sensibilidad_gestos,
                "distancia_minima_dedos": self.distancia_minima_dedos,
                "tiempo_gesto": self.tiempo_gesto,
                "umbrales_gestos": self.umbrales_gestos,
                "fecha_calibracion": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open("calibracion.json", "w") as archivo:
                json.dump(datos, archivo, indent=4)
            
            logger.info("Calibración guardada en archivo")
            return True
        except Exception as e:
            logger.error(f"Error al guardar calibración: {e}")
            return False
    
    def _cargar_calibracion(self) -> bool:
        """Carga la calibración desde un archivo si existe."""
        try:
            if os.path.exists("calibracion.json"):
                with open("calibracion.json", "r") as archivo:
                    datos = json.load(archivo)
                
                self.sensibilidad_gestos = datos.get("sensibilidad_gestos", self.sensibilidad_gestos)
                self.distancia_minima_dedos = datos.get("distancia_minima_dedos", self.distancia_minima_dedos)
                self.tiempo_gesto = datos.get("tiempo_gesto", self.tiempo_gesto)
                self.umbrales_gestos = datos.get("umbrales_gestos", self.umbrales_gestos)
                
                logger.info("Calibración cargada desde archivo")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al cargar calibración: {e}")
            return False
    
    def cancelar_calibracion(self) -> None:
        """Cancela el proceso de calibración actual."""
        self.calibrando = False
        logger.info("Calibración cancelada")
    
    def ajustar_sensibilidad(self, valor: float) -> None:
        """Ajusta la sensibilidad global de los gestos."""
        if 0.1 <= valor <= 1.0:
            self.sensibilidad_gestos = valor
            logger.info(f"Sensibilidad ajustada a {valor}")
    
    def verificar_gesto(self, landmarks, dedos_levantados: List[bool], tipo_gesto: str) -> float:
        """Verifica qué tan cerca está un gesto del umbral de reconocimiento."""
        try:
            if tipo_gesto == "mano_abierta":
                apertura = self._calcular_apertura_mano(landmarks)
                umbral = self.umbrales_gestos.get("mano_abierta", 0.7)
                return apertura / umbral if umbral > 0 else 0
            
            elif tipo_gesto == "puno_cerrado":
                cierre = self._calcular_cierre_puno(landmarks)
                umbral = self.umbrales_gestos.get("puno_cerrado", 0.7)
                return cierre / umbral if umbral > 0 else 0
            
            elif tipo_gesto == "indice_extendido":
                extension = self._calcular_extension_indice(landmarks)
                umbral = self.umbrales_gestos.get("indice_extendido", 0.7)
                return extension / umbral if umbral > 0 else 0
            
            elif tipo_gesto == "pinza":
                distancia = self._calcular_distancia_pinza(landmarks)
                umbral = self.umbrales_gestos.get("pinza", 0.7)
                return distancia / umbral if umbral > 0 else 0
            
            return 0.0
        except Exception as e:
            logger.error(f"Error al verificar gesto: {e}")
            return 0.0