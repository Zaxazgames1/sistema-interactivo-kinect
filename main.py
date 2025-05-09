#!/usr/bin/env python3
"""
Sistema Interactivo con Kinect - Archivo Principal
Este archivo sirve como punto de entrada al sistema completo.
"""

import logging
import argparse
from sistema import SistemaInteractivo

def configurar_argumentos():
    """Configura los argumentos de línea de comandos para el sistema."""
    parser = argparse.ArgumentParser(description='Sistema Interactivo con Kinect')
    parser.add_argument('--debug', action='store_true', help='Activar modo debug')
    parser.add_argument('--config', type=str, help='Ruta al archivo de configuración')
    parser.add_argument('--webcam', action='store_true', help='Usar webcam en lugar de Kinect')
    parser.add_argument('--puerto', type=str, help='Puerto para la mano robótica')
    return parser.parse_args()

def main():
    """Función principal del programa."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("sistema_kinect.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("Main")
    
    # Procesar argumentos de línea de comandos
    args = configurar_argumentos()
    
    # Mostrar mensaje de inicio
    logger.info("Iniciando Sistema Interactivo con Kinect")
    
    try:
        # Crear y ejecutar el sistema
        sistema = SistemaInteractivo(
            modo_debug=args.debug,
            ruta_config=args.config,
            usar_webcam=args.webcam,
            puerto_mano=args.puerto
        )
        sistema.ejecutar()
    except KeyboardInterrupt:
        logger.info("Programa terminado por el usuario.")
    except Exception as e:
        logger.error(f"Error al iniciar el sistema: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Programa finalizado.")

if __name__ == "__main__":
    main()