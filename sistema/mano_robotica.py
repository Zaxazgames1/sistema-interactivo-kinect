"""
Módulo para gestionar la conexión y control de la mano robótica.
"""

import logging
import time
import threading
import re
from typing import List, Optional, Tuple

logger = logging.getLogger("SistemaKinect.ManoRobotica")

# Importación condicional para PySerial
try:
    import serial
    import serial.tools.list_ports
    SERIAL_DISPONIBLE = True
except ImportError:
    logger.warning("PySerial no está disponible. Control de mano robótica desactivado.")
    SERIAL_DISPONIBLE = False

class ManoRoboticaManager:
    """Gestiona la conexión y control de la mano robótica."""
    
    def __init__(self, config_manager):
        self.config = config_manager.obtener_config("mano_robotica")
        self.puerto_configurado = self.config.get("puerto", "COM5")  # Puerto configurado manualmente
        self.baudios = self.config.get("baudios", 9600)
        self.timeout = self.config.get("timeout", 2)
        self.identificadores_mano = self.config.get("identificadores", ["Arduino", "CH340", "USB Serial", "FTDI"])
        self.conexion = None
        self.conectada = False
        self.mensaje_ultimo = ""
        self.hilo_envio = None
        self.cola_mensajes = []
        self.puerto_auto_detectado = None  # Almacena el puerto detectado automáticamente
    
    def detectar_puertos_disponibles(self) -> List[Tuple[str, str]]:
        """Detecta los puertos seriales disponibles en el sistema.
        
        Returns:
            Lista de tuplas (puerto, descripción)
        """
        if not SERIAL_DISPONIBLE:
            logger.error("Serial no está disponible. No se pueden detectar puertos.")
            return []
        
        try:
            puertos = list(serial.tools.list_ports.comports())
            puertos_info = [(p.device, p.description) for p in puertos]
            logger.info(f"Puertos seriales detectados: {puertos_info}")
            return puertos_info
        except Exception as e:
            logger.error(f"Error al detectar puertos seriales: {e}")
            return []
    
    def identificar_puerto_mano_robotica(self) -> Optional[str]:
        """Intenta identificar automáticamente el puerto de la mano robótica.
        
        Returns:
            Nombre del puerto detectado o None si no se encuentra
        """
        puertos = self.detectar_puertos_disponibles()
        
        if not puertos:
            logger.warning("No se detectaron puertos seriales disponibles.")
            return None
        
        logger.info("Analizando puertos para identificar la mano robótica...")
        
        # Primero intentar con identificadores específicos en la descripción
        for puerto, descripcion in puertos:
            for identificador in self.identificadores_mano:
                if identificador.lower() in descripcion.lower():
                    logger.info(f"Mano robótica probablemente en {puerto} (descripción: {descripcion})")
                    return puerto
        
        # Si no se encontró, intentar verificando respuesta del dispositivo
        logger.info("Intentando conectar a cada puerto para verificar si es la mano robótica...")
        for puerto, _ in puertos:
            try:
                # Intento de conexión con timeout bajo para ser rápido
                conexion_prueba = serial.Serial(puerto, self.baudios, timeout=0.5)
                time.sleep(0.5)  # Breve pausa para estabilizar conexión
                
                # Enviar comando de prueba y verificar respuesta
                conexion_prueba.write(b"IDENTIFY\n")
                time.sleep(0.5)
                respuesta = conexion_prueba.read(64)  # Leer posible respuesta
                conexion_prueba.close()
                
                # Verificar si es una respuesta esperada de la mano robótica
                # Esto depende de la programación específica de tu mano robótica
                if respuesta and (b"ROBOT" in respuesta or b"HAND" in respuesta or b"MANO" in respuesta):
                    logger.info(f"Mano robótica verificada en {puerto}")
                    return puerto
                
            except Exception as e:
                logger.debug(f"Error al probar puerto {puerto}: {e}")
                continue
        
        # Si no se pudo identificar con certeza, usar el primer puerto como alternativa
        if puertos:
            puerto_alternativo = puertos[0][0]
            logger.info(f"No se identificó con certeza la mano robótica. Usando primer puerto disponible: {puerto_alternativo}")
            return puerto_alternativo
        
        logger.warning("No se pudo identificar un puerto para la mano robótica.")
        return None
    
    def guardar_configuracion_puerto(self, puerto: str) -> None:
        """Guarda el puerto detectado en la configuración."""
        try:
            # Actualizar el objeto de configuración
            self.config["puerto"] = puerto
            self.puerto_configurado = puerto
            
            # Actualizar en el archivo de configuración principal
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.obtener_config()
            if "mano_robotica" in config:
                config["mano_robotica"]["puerto"] = puerto
            else:
                config["mano_robotica"] = {"puerto": puerto, "baudios": self.baudios, "timeout": self.timeout}
            config_manager.config = config
            config_manager.guardar_config()
            logger.info(f"Puerto {puerto} guardado en configuración.")
        except Exception as e:
            logger.error(f"Error al guardar configuración de puerto: {e}")
    
    def conectar(self, puerto_override=None) -> bool:
        """Establece conexión con la mano robótica.
        
        Args:
            puerto_override: Puerto específico a usar (opcional)
        
        Returns:
            bool: True si se conectó correctamente, False en caso contrario
        """
        if not SERIAL_DISPONIBLE:
            logger.error("Serial no está disponible. No se puede conectar mano robótica.")
            return False
        
        puerto_a_usar = None
        
        # Prioridad 1: Puerto especificado manualmente en la llamada
        if puerto_override:
            puerto_a_usar = puerto_override
            logger.info(f"Usando puerto especificado manualmente: {puerto_a_usar}")
        
        # Prioridad 2: Auto-detección
        else:
            try:
                puerto_a_usar = self.identificar_puerto_mano_robotica()
                if puerto_a_usar:
                    self.puerto_auto_detectado = puerto_a_usar
                    logger.info(f"Puerto auto-detectado para mano robótica: {puerto_a_usar}")
                    
                    # Guardar el puerto detectado en la configuración para futuros usos
                    self.guardar_configuracion_puerto(puerto_a_usar)
            except Exception as e:
                logger.error(f"Error en auto-detección de puerto: {e}")
                puerto_a_usar = None
        
        # Prioridad 3: Usar puerto configurado en archivo
        if not puerto_a_usar:
            puerto_a_usar = self.puerto_configurado
            logger.info(f"Usando puerto de configuración: {puerto_a_usar}")
        
        # Intentar establecer conexión
        try:
            self.conexion = serial.Serial(
                puerto_a_usar, 
                self.baudios,
                timeout=self.timeout
            )
            time.sleep(self.timeout)  # Esperar a que se establezca la conexión
            self.conectada = True
            logger.info(f"Conexión establecida con la mano robótica en {puerto_a_usar}")
            
            # Iniciar hilo de procesamiento de mensajes
            self.hilo_envio = threading.Thread(target=self._procesar_cola_mensajes, daemon=True)
            self.hilo_envio.start()
            
            return True
        except Exception as e:
            logger.error(f"No se pudo conectar con la mano robótica en {puerto_a_usar}: {e}")
            self.conectada = False
            
            # Si falló con el puerto auto-detectado, intentar con el puerto configurado
            if puerto_a_usar == self.puerto_auto_detectado and self.puerto_auto_detectado != self.puerto_configurado:
                logger.info(f"Intentando con puerto configurado: {self.puerto_configurado}")
                return self.conectar(puerto_override=self.puerto_configurado)
            
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
    
    def reintentar_conexion(self) -> bool:
        """Reintenta la conexión con la mano robótica."""
        logger.info("Reintentando conexión con mano robótica...")
        
        # Cerrar conexión previa si existe
        self.cerrar()
        
        # Intentar conectar de nuevo
        return self.conectar()