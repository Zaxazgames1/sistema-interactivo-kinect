"""
Módulo para gestionar la conexión y control de la mano robótica.
"""

import logging
import time
import threading
from typing import List, Optional

logger = logging.getLogger("SistemaKinect.ManoRobotica")

# Importación condicional para PySerial
try:
    import serial
    SERIAL_DISPONIBLE = True
except ImportError:
    logger.warning("PySerial no está disponible. Control de mano robótica desactivado.")
    SERIAL_DISPONIBLE = False

class ManoRoboticaManager:
    """Gestiona la conexión y control de la mano robótica."""
    
    def __init__(self, config_manager):
        self.config = config_manager.obtener_config("mano_robotica")
        self.puerto = self.config.get("puerto", "COM5")
        self.baudios = self.config.get("baudios", 9600)
        self.timeout = self.config.get("timeout", 2)
        self.conexion = None
        self.conectada = False
        self.mensaje_ultimo = ""
        self.hilo_envio = None
        self.cola_mensajes = []
    
    def conectar(self, puerto_override=None) -> bool:
        """Establece conexión con la mano robótica."""
        if not SERIAL_DISPONIBLE:
            logger.error("Serial no está disponible. No se puede conectar mano robótica.")
            return False
        
        # Usar puerto override si se proporciona
        puerto = puerto_override if puerto_override else self.puerto
        
        try:
            self.conexion = serial.Serial(
                puerto, 
                self.baudios,
                timeout=self.timeout
            )
            time.sleep(self.timeout)  # Esperar a que se establezca la conexión
            self.conectada = True
            logger.info(f"Conexión establecida con la mano robótica en {puerto}")
            
            # Iniciar hilo de procesamiento de mensajes
            self.hilo_envio = threading.Thread(target=self._procesar_cola_mensajes, daemon=True)
            self.hilo_envio.start()
            
            return True
        except Exception as e:
            logger.error(f"No se pudo conectar con la mano robótica: {e}")
            self.conectada = False
            return False
    
    def _procesar_cola_mensajes(self) -> None:
        """Procesa la cola de mensajes en segundo plano."""
        while self.conectada:
            if self.cola_mensajes:
                mensaje = self.cola_mensajes.pop(0)
                try:
                    self.conexion.write((mensaje + '\n').encode())
                    self.mensaje_ultimo = mensaje
                    logger.info(f"Mensaje enviado a mano robótica: {mensaje}")
                    time.sleep(0.5)  # Pequeña pausa entre mensajes
                except Exception as e:
                    logger.error(f"Error al enviar mensaje a mano robótica: {e}")
            time.sleep(0.1)
    
    def enviar_mensaje(self, mensaje: str) -> bool:
        """Añade un mensaje a la cola para enviar a la mano robótica."""
        if not self.conectada:
            logger.warning("Mano robótica no conectada. No se puede enviar mensaje.")
            return False
        
        self.cola_mensajes.append(mensaje)
        return True
    
    def enviar_mensaje_directo(self, mensaje: str) -> bool:
        """Envía un mensaje directamente a la mano robótica, sin usar la cola."""
        if not self.conectada or self.conexion is None:
            logger.warning("Mano robótica no conectada. No se puede enviar mensaje.")
            return False
        
        try:
            self.conexion.write((mensaje + '\n').encode())
            self.mensaje_ultimo = mensaje
            logger.info(f"Mensaje enviado directamente a mano robótica: {mensaje}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar mensaje directo a mano robótica: {e}")
            return False
    
    def limpiar_cola(self) -> None:
        """Limpia la cola de mensajes pendientes."""
        self.cola_mensajes.clear()
        logger.info("Cola de mensajes limpiada.")
    
    def cerrar(self) -> None:
        """Cierra la conexión con la mano robótica."""
        if self.conectada:
            try:
                self.conectada = False
                if self.hilo_envio and self.hilo_envio.is_alive():
                    self.hilo_envio.join(timeout=2)
                if self.conexion:
                    self.conexion.close()
                logger.info("Conexión con mano robótica cerrada correctamente.")
            except Exception as e:
                logger.error(f"Error al cerrar conexión con mano robótica: {e}")