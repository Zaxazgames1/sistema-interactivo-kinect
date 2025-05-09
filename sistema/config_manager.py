"""
Módulo para gestionar la configuración del sistema.
"""

import os
import json
import logging
from typing import Dict, Optional, Union

logger = logging.getLogger("SistemaKinect.ConfigManager")

class ConfigManager:
    """Gestiona la configuración del sistema."""
    
    CONFIG_FILE = "config.json"
    DEFAULT_CONFIG = {
        "kinect": {
            "openni_path": "C:/Program Files/OpenNI2/Redist",
            "resolution": [640, 480]
        },
        "mano_robotica": {
            "puerto": "COM5",
            "baudios": 9600,
            "timeout": 2
        },
        "ui": {
            "botones": {
                "Dibujar": [50, 50],
                "Borrar": [200, 50],
                "Guardar": [350, 50],
                "Configuración": [500, 50],
                "Salir": [650, 50]
            },
            "colores": {
                "dibujo": [0, 255, 0],
                "borrador": [0, 0, 0],
                "fondo": [0, 0, 0],
                "boton_normal": [200, 200, 200],
                "boton_seleccionado": [0, 255, 255],
                "texto": [255, 255, 255]
            }
        },
        "dibujo": {
            "grosor_linea": 3,
            "radio_borrador": 30
        },
        "modo_debug": False,
        "idiomas_ocr": ["es", "en"]
    }
    
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = self.cargar_config()
    
    def cargar_config(self) -> Dict:
        """Carga la configuración desde archivo o usa valores predeterminados."""
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Configuración cargada desde {self.config_path}.")
                return config
            elif os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Configuración cargada desde archivo predeterminado.")
                return config
            else:
                logger.info("Archivo de configuración no encontrado. Usando valores predeterminados.")
                return self.DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return self.DEFAULT_CONFIG
    
    def guardar_config(self) -> bool:
        """Guarda la configuración actual en archivo."""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuración guardada correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False
    
    def obtener_config(self, seccion: Optional[str] = None) -> Union[Dict, any]:
        """Obtiene toda la configuración o una sección específica."""
        if seccion:
            return self.config.get(seccion, {})
        return self.config
    
    def actualizar_config(self, seccion: str, clave: str, valor: any) -> None:
        """Actualiza un valor específico en la configuración."""
        if seccion in self.config:
            if isinstance(self.config[seccion], dict):
                self.config[seccion][clave] = valor
            else:
                self.config[seccion] = {clave: valor}
        else:
            self.config[seccion] = {clave: valor}