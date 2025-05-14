"""
Clase principal que coordina todos los módulos del sistema interactivo.
"""

import logging
import time
import threading
import cv2
import os
import numpy as np
from typing import Dict, List, Tuple, Optional

from .config_manager import ConfigManager
from .kinect_manager import KinectManager
from .hand_tracker import HandTracker
from .mano_robotica import ManoRoboticaManager
from .text_recognizer import TextRecognizer
from .voice_engine import VoiceEngine
from .ui_manager import UIManager
from .dibujo_manager import DibujoManager
from .asistente_virtual import AsistenteVirtual

logger = logging.getLogger("SistemaKinect.SistemaInteractivo")

class SistemaInteractivo:
    """Clase principal que coordina todos los módulos del sistema."""
    
    def __init__(self, modo_debug=False, ruta_config=None, usar_webcam=False, puerto_mano=None):
        # Configurar el modo debug
        self.modo_debug = modo_debug
        
        # Inicializar gestor de configuración
        self.config_manager = ConfigManager(ruta_config)
        
        # Actualizar configuración con modo debug
        if modo_debug:
            self.config_manager.actualizar_config("", "modo_debug", True)
        
        # Inicializar todos los módulos
        self.kinect_manager = KinectManager(self.config_manager)
        self.hand_tracker = HandTracker()
        self.mano_robotica = ManoRoboticaManager(self.config_manager)
        self.text_recognizer = TextRecognizer(self.config_manager)
        # Crear directorios necesarios para el motor de voz
        os.makedirs("temp_audio", exist_ok=True)
        
        # Inicializar motor de voz y asegurar que use Google TTS
        self.voice_engine = VoiceEngine()
        # Configurar el motor de voz para usar Google TTS
        try:
            if hasattr(self.voice_engine, 'cambiar_motor'):
                self.voice_engine.cambiar_motor("google_tts")
            # Si no tiene el método, usar configuración directa
            elif hasattr(self.voice_engine, 'config'):
                self.voice_engine.config['motor'] = "google_tts"
                if hasattr(self.voice_engine, '_guardar_config'):
                    self.voice_engine._guardar_config()
        except Exception as e:
            logger.warning(f"No se pudo configurar Google TTS: {e}")
            # Si falla Google TTS, intentar con pyttsx3 como respaldo
            try:
                if hasattr(self.voice_engine, 'cambiar_motor'):
                    self.voice_engine.cambiar_motor("pyttsx3")
            except Exception as e2:
                logger.warning(f"También falló el motor de respaldo: {e2}")
        
        # Inicializar asistente virtual
        self.asistente = AsistenteVirtual(self.voice_engine)
        
        self.ui_manager = UIManager(self.config_manager)
        self.dibujo_manager = DibujoManager(self.config_manager)
        
        # Parámetros adicionales
        self.usar_webcam = usar_webcam
        self.puerto_mano = puerto_mano
        
        # Estado del sistema
        self.ejecutando = False
        self.modo_actual = None
        self.config = self.config_manager.obtener_config()
        self.botones = self.config.get("ui", {}).get("botones", {})
        self.ultima_posicion_mano = (0, 0)
        
        # Timer para estadísticas periódicas
        self.ultimo_reporte_estadisticas = time.time()
        
        # Inicializar semillas para números aleatorios
        np.random.seed(int(time.time()))
    
    def inicializar(self) -> bool:
        """Inicializa todos los módulos del sistema."""
        logger.info("Iniciando sistema interactivo...")
        
        # Crear ventana de UI
        self.ui_manager.crear_ventana()
        
        # Inicializar Kinect o webcam
        if not self.kinect_manager.iniciar(usar_webcam=self.usar_webcam):
            self.ui_manager.mostrar_mensaje("Error al iniciar dispositivo de captura.", 5)
            return False
        
        # Inicializar reconocimiento de manos
        self.hand_tracker.iniciar()
        
        # Intentar conectar con mano robótica
        if self.puerto_mano:
            if not self.mano_robotica.conectar(puerto_override=self.puerto_mano):
                self.ui_manager.mostrar_mensaje(f"Error al conectar mano robótica en {self.puerto_mano}", 3)
        else:
            # Usar detección automática
            resultado_conexion = self.mano_robotica.conectar()
            if resultado_conexion:
                puerto_detectado = getattr(self.mano_robotica, 'puerto_auto_detectado', None) or self.mano_robotica.puerto_configurado
                self.ui_manager.mostrar_mensaje(f"Mano robótica conectada en {puerto_detectado}", 3)
            else:
                self.ui_manager.mostrar_mensaje("No se pudo conectar la mano robótica. Verifica la conexión.", 3)
        
        # Iniciar reconocimiento de texto en segundo plano
        self.text_recognizer.iniciar()
        
        # Iniciar motor de síntesis de voz (asegurando Google TTS)
        if not self.voice_engine.iniciado:
            self.voice_engine.iniciar()
            # Verificar y cambiar al motor Google TTS si es necesario
            if hasattr(self.voice_engine, 'motor_actual') and self.voice_engine.motor_actual and self.voice_engine.motor_actual.value != "google_tts":
                logger.info("Cambiando motor de voz a Google TTS...")
                try:
                    self.voice_engine.cambiar_motor("google_tts")
                except Exception as e:
                    logger.warning(f"Error al cambiar a Google TTS: {e}")
                    logger.info("Usando motor de voz alternativo")
        
        # Crear directorio para sesiones si no existe
        sesiones_dir = self.config.get("dibujo", {}).get("sesiones_dir", "sesiones")
        if not os.path.exists(sesiones_dir):
            try:
                os.makedirs(sesiones_dir)
                logger.info(f"Directorio de sesiones creado: {sesiones_dir}")
            except Exception as e:
                logger.error(f"Error al crear directorio de sesiones: {e}")
        
        logger.info("Sistema interactivo iniciado correctamente.")
        
        # Saludar al usuario
        self.asistente.saludar()
        
        return True
    
    def _obtener_frame(self) -> Optional[cv2.Mat]:
        """Obtiene un frame de la cámara (Kinect o webcam)."""
        return self.kinect_manager.obtener_imagen()
    
    def _procesar_accion_boton(self, boton: str) -> None:
        """Procesa la acción correspondiente al botón seleccionado."""
        self.ui_manager.boton_seleccionado = boton
        
        # Narrar la selección del botón
        self.asistente.hablar(f"Has seleccionado {boton}", prioridad=2, categoria="navegacion")
        
        if boton == "Dibujar":
            # Activar modo dibujo
            self.modo_actual = "dibujar"
            self.ui_manager.estado_mano = "Modo: Dibujo"
            self.ui_manager.mostrar_mensaje("Modo dibujo activado. Use el dedo índice para dibujar.", 2)
            # Narrar el cambio de modo
            self.asistente.anunciar_modo("dibujar")
        
        elif boton == "Borrar":
            # Activar modo borrador
            self.modo_actual = "borrar"
            self.ui_manager.estado_mano = "Modo: Borrador"
            self.ui_manager.mostrar_mensaje("Modo borrador activado. Use la mano para borrar.", 2)
            # Narrar el cambio de modo
            self.asistente.anunciar_modo("borrar")
        
        elif boton == "Limpiar":
            # Limpiar el lienzo y desactivar cualquier modo
            self.dibujo_manager.limpiar_dibujo()
            self.modo_actual = None  # Desactivar modo actual
            self.ui_manager.estado_mano = "Lienzo limpiado"
            self.ui_manager.mostrar_mensaje("Lienzo limpiado. Seleccione 'Dibujar' o 'Borrar' para continuar.", 2)
            # Narrar la acción
            self.asistente.hablar("Lienzo limpiado completamente", prioridad=2, categoria="accion")
        
        elif boton == "Guardar":
            # Procesar guardado y desactivar cualquier modo
            self._procesar_guardado()
            self.modo_actual = None  # Desactivar modo actual
            self.ui_manager.estado_mano = "Guardando..."
            # Narrar el guardado
            self.asistente.anunciar_guardado()
        
        elif boton == "Salir":
            # Salir del programa
            self.ejecutando = False
            self.ui_manager.estado_mano = "Cerrando..."
            # Despedirse
            self.asistente.despedir()
        
        # Actualizar la interfaz
        if hasattr(self.ui_manager, 'mostrar_modo'):
            if self.modo_actual == "dibujar":
                self.ui_manager.mostrar_modo("Dibujo")
            elif self.modo_actual == "borrar":
                self.ui_manager.mostrar_modo("Borrador")
            elif self.modo_actual is None:
                self.ui_manager.mostrar_modo("Ninguno")
            else:
                self.ui_manager.mostrar_modo(self.modo_actual)
    
    def _procesar_guardado(self) -> None:
        """Procesa la acción de guardar y reconocer texto."""
        self.ui_manager.estado_mano = "Procesando..."
        self.ui_manager.mostrar_mensaje("Guardando y reconociendo texto...", 10)
        
        # Guardar sesión
        ruta_sesion = self.dibujo_manager.guardar_sesion()
        if ruta_sesion:
            logger.info(f"Sesión guardada como {ruta_sesion}")
        
        # Guardar dibujo como imagen
        nombre_archivo = self.dibujo_manager.guardar_dibujo()
        if not nombre_archivo:
            self.ui_manager.mostrar_mensaje("Error al guardar dibujo", 3)
            return
        
        # Ejecutar reconocimiento de texto en un hilo separado
        threading.Thread(target=self._reconocer_texto_hilo, args=(nombre_archivo,), daemon=True).start()
    
    def _reconocer_texto_hilo(self, nombre_archivo: str) -> None:
        """Procesa reconocimiento de texto en un hilo separado."""
        try:
            # Cargar imagen guardada
            img = cv2.imread(nombre_archivo)
            if img is None:
                logger.error(f"Error al cargar imagen {nombre_archivo}")
                self.ui_manager.mostrar_mensaje("Error al cargar imagen", 3)
                return
            
            # Reconocer texto
            resultados, img_con_texto = self.text_recognizer.reconocer_texto(img)
            
            # Mostrar imagen con texto reconocido
            self.ui_manager.mostrar_frame_secundario("Texto Reconocido", img_con_texto)
            
            if resultados:
                texto_reconocido = " ".join([texto for (_, texto, _) in resultados if _ and texto])
                logger.info(f"Texto reconocido: {texto_reconocido}")
                
                # Guardar en archivo
                with open("texto_reconocido.txt", "w", encoding="utf-8") as archivo:
                    archivo.write(f"Texto reconocido: {texto_reconocido}\n")
                
                # Mostrar mensaje en UI
                self.ui_manager.estado_mano = "Texto reconocido"
                self.ui_manager.mostrar_mensaje(f"Texto: {texto_reconocido}", 5)
                
                # Narrar el texto reconocido
                self.asistente.anunciar_texto_reconocido(texto_reconocido)
                
                # Sintetizar voz con Google TTS
                if self.voice_engine.iniciado:
                    # Verificar motor actual y cambiar a Google TTS si es necesario
                    if hasattr(self.voice_engine, 'motor_actual') and self.voice_engine.motor_actual and self.voice_engine.motor_actual.value != "google_tts":
                        try:
                            self.voice_engine.cambiar_motor("google_tts")
                        except Exception as e:
                            logger.warning(f"Error al cambiar a Google TTS: {e}")
                    
                    # Sintetizar voz
                    self.voice_engine.hablar(f"Texto reconocido: {texto_reconocido}")
                
                # Enviar a mano robótica
                if self.mano_robotica.conectada:
                    self.ui_manager.estado_mano = "Enviando a mano robótica..."
                    self.mano_robotica.enviar_mensaje(texto_reconocido)
            else:
                logger.warning("No se reconoció texto en la imagen")
                self.ui_manager.mostrar_mensaje("No se reconoció texto", 3)
                self.ui_manager.estado_mano = "Sin texto reconocido"
                self.asistente.anunciar_texto_reconocido(None)
        except Exception as e:
            logger.error(f"Error en proceso de reconocimiento: {e}")
            self.ui_manager.mostrar_mensaje("Error en reconocimiento de texto", 3)
    
    def _procesar_gestos(self, results, frame) -> None:
        """Procesa los gestos de la mano detectada."""
        if not results or not results.multi_hand_landmarks:
            return
        
        for hand_landmarks in results.multi_hand_landmarks:
            h, w, _ = frame.shape
            
            # Obtener posición de la punta del dedo índice
            x_index = int(hand_landmarks.landmark[self.hand_tracker.mp_hands.HandLandmark.INDEX_FINGER_TIP].x * w)
            y_index = int(hand_landmarks.landmark[self.hand_tracker.mp_hands.HandLandmark.INDEX_FINGER_TIP].y * h)
            
            # Actualizar posición para el indicador de mano
            self.ultima_posicion_mano = (x_index, y_index)
            self.ui_manager.dibujar_indicador_mano(x_index, y_index)
            
            # Verificar si estamos sobre algún botón para dar feedback
            boton_bajo_cursor = self.ui_manager.verificar_punto_en_boton(x_index, y_index)
            if boton_bajo_cursor:
                self.asistente.anunciar_boton_hover(boton_bajo_cursor)
            
            # Detectar dedos levantados
            dedos_levantados = self.hand_tracker.detectar_dedos_levantados(hand_landmarks)
            
            # Actualizar indicador de posición en el dibujo
            if self.modo_actual:
                self.dibujo_manager.dibujar_indicador_posicion(x_index, y_index)
            
            # Verificar gesto para dibujar (solo índice levantado)
            if self.modo_actual == "dibujar" and dedos_levantados[1] and not any(dedos_levantados[2:]):
                # Narrar inicio de trazo si es el primer punto
                if not self.dibujo_manager.dibujando:
                    self.asistente.anunciar_trazo("inicio")
                self.dibujo_manager.dibujar_punto(x_index, y_index)
            # Verificar gesto para borrar
            elif self.modo_actual == "borrar":
                self.dibujo_manager.borrar_punto(x_index, y_index)
            else:
                # Si no estamos en un modo de dibujo o borrado, simplemente terminamos cualquier trazo
                # Narrar fin de trazo si estaba dibujando
                if self.dibujo_manager.dibujando:
                    self.asistente.anunciar_trazo("fin")
                self.dibujo_manager.terminar_dibujo()
            
            # Verificar gesto para seleccionar botón (puño cerrado)
            if not any(dedos_levantados):
                # Usar el método mejorado para verificar si el punto está en algún botón
                boton_seleccionado = self.ui_manager.verificar_punto_en_boton(x_index, y_index)
                if boton_seleccionado:
                    self._procesar_accion_boton(boton_seleccionado)
                    # Pequeña pausa para evitar múltiples selecciones
                    time.sleep(0.5)
    
    def ejecutar(self) -> None:
        """Bucle principal del sistema."""
        if not self.inicializar():
            logger.error("Error al inicializar sistema. Abortando.")
            return
        
        self.ejecutando = True
        self.ui_manager.mostrar_mensaje("Sistema iniciado. Listo para interactuar.", 3)
        
        try:
            ultima_actualizacion_fps = time.time()
            frames_contados = 0
            
            while self.ejecutando:
                tiempo_inicio = time.time()
                
                # Obtener frame desde cámara
                frame = self._obtener_frame()
                if frame is None:
                    logger.warning("No se pudo obtener frame de la cámara.")
                    time.sleep(0.1)  # Pequeña pausa antes de reintentar
                    continue
                
                # Procesar frame para detección de manos
                results, frame_con_manos = self.hand_tracker.procesar_frame(frame)
                
                # Procesar gestos si hay manos detectadas
                self._procesar_gestos(results, frame)
                
                # Obtener dibujo actual con efectos temporales
                dibujo_actual = self.dibujo_manager.obtener_dibujo()
                
                # Dibujar interfaz
                frame_final = self.ui_manager.dibujar_ui(frame_con_manos, dibujo_actual)
                
                # Mostrar frame
                self.ui_manager.mostrar_frame(frame_final)
                
                # Calcular FPS para modo debug
                frames_contados += 1
                tiempo_actual = time.time()
                if tiempo_actual - ultima_actualizacion_fps >= 1.0:
                    self.ui_manager.fps = frames_contados
                    frames_contados = 0
                    ultima_actualizacion_fps = tiempo_actual
                
                # Dar estadísticas periódicas
                if tiempo_actual - self.ultimo_reporte_estadisticas > 300:  # Cada 5 minutos
                    self.asistente.dar_estadisticas_periodicas()
                    self.ultimo_reporte_estadisticas = tiempo_actual
                
                # Verificar salida
                tecla = cv2.waitKey(1) & 0xFF
                if tecla == ord('q') or tecla == 27:  # q o ESC
                    self.ejecutando = False
                elif tecla == ord('s'):  # s para guardar sesión
                    nombre_sesion = f"manual_{time.strftime('%Y%m%d_%H%M%S')}.session"
                    ruta = self.dibujo_manager.guardar_sesion(nombre_sesion)
                    if ruta:
                        self.ui_manager.mostrar_mensaje(f"Sesión guardada: {nombre_sesion}", 2)
                elif tecla == ord('v'):  # v para cambiar verbosidad
                    nivel_actual = self.asistente.nivel_verbosidad.value
                    nuevo_nivel = (nivel_actual + 1) % 5
                    self.asistente.cambiar_verbosidad(nuevo_nivel)
                elif tecla == ord('p'):  # p para cambiar personalidad
                    personalidades = ["profesional", "amigable", "infantil", "tutorial", "artista", "motivador"]
                    indice_actual = personalidades.index(self.asistente.personalidad.value)
                    nueva_personalidad = personalidades[(indice_actual + 1) % len(personalidades)]
                    self.asistente.cambiar_personalidad(nueva_personalidad)
                elif tecla == ord('t'):  # t para toggle modo tutorial
                    self.asistente.activar_modo_tutorial(not self.asistente.modo_tutorial)
                elif tecla == ord('a'):  # a para activar/desactivar asistente
                    self.asistente.activar_desactivar(not self.asistente.activo)
                elif tecla == ord('m'):  # m para toggle música
                    self.asistente.cambiar_configuracion_sonido(
                        usar_musica=not self.asistente.usar_musica_fondo)
                elif tecla == ord('e'):  # e para toggle efectos
                    self.asistente.cambiar_configuracion_sonido(
                        usar_efectos=not self.asistente.usar_efectos_sonido)
                elif tecla == ord('x'):  # x para toggle voz emotiva
                    self.asistente.cambiar_configuracion_sonido(
                        usar_voz_emotiva=not self.asistente.usar_voz_emotiva)
                elif tecla == ord('+'):  # + para subir volumen
                    volumen_actual = self.asistente.volumen_efectos
                    self.asistente.ajustar_volumenes(volumen_efectos=min(1.0, volumen_actual + 0.1))
                elif tecla == ord('-'):  # - para bajar volumen
                    volumen_actual = self.asistente.volumen_efectos
                    self.asistente.ajustar_volumenes(volumen_efectos=max(0.0, volumen_actual - 0.1))
                
                # Control de velocidad del bucle
                tiempo_procesamiento = time.time() - tiempo_inicio
                tiempo_espera = max(0.001, 1/30 - tiempo_procesamiento)  # Limitar a ~30 FPS
                time.sleep(tiempo_espera)
        
        except KeyboardInterrupt:
            logger.info("Interrupción de teclado. Cerrando sistema.")
        except Exception as e:
            logger.error(f"Error en bucle principal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cerrar()
    
    def cerrar(self) -> None:
        """Cierra todos los módulos del sistema."""
        logger.info("Cerrando sistema interactivo...")
        
        # Despedirse si el asistente está activo
        if hasattr(self, 'asistente') and self.asistente.activo:
            self.asistente.despedir()
            time.sleep(2)  # Dar tiempo para que termine de hablar
        
        # Guardar sesión antes de cerrar
        try:
            self.dibujo_manager.guardar_sesion("sesion_al_cerrar.session")
        except:
            pass
        
        # Cerrar conexión con mano robótica
        if hasattr(self, 'mano_robotica'):
            self.mano_robotica.cerrar()
        
        # Cerrar reconocimiento de manos
        if hasattr(self, 'hand_tracker'):
            self.hand_tracker.cerrar()
        
        # Cerrar síntesis de voz
        if hasattr(self, 'voice_engine'):
            self.voice_engine.cerrar()
        
        # Cerrar Kinect o webcam
        if hasattr(self, 'kinect_manager'):
            self.kinect_manager.cerrar()
        
        # Cerrar ventanas
        if hasattr(self, 'ui_manager'):
            self.ui_manager.cerrar_ventanas()
        
        logger.info("Sistema interactivo cerrado correctamente.")