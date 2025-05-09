#!/usr/bin/env python3
"""
Script simple para probar el motor de voz mejorado.
"""

import os
import sys
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Asegurar que podemos importar desde el directorio del proyecto
script_dir = os.path.dirname(os.path.abspath(__file__))
proyecto_dir = os.path.dirname(script_dir)
sys.path.insert(0, proyecto_dir)

def probar_voz():
    """Prueba el motor de voz mejorado."""
    print("===== PRUEBA SIMPLE DEL MOTOR DE VOZ MEJORADO =====")
    
    try:
        # Importar el motor de voz
        from sistema.voice_engine import VoiceEngine
        
        # Inicializar el motor de voz
        voice = VoiceEngine()
        
        # Verificar si se inició correctamente
        if not voice.iniciado:
            print("ERROR: No se pudo iniciar el motor de voz")
            return
        
        # Mostrar configuración actual
        conf = voice.obtener_configuracion_actual()
        print(f"Motor actual: {voice.motor_actual}")
        print(f"Idioma: {conf.get('voz_idioma')}")
        print(f"Género: {conf.get('voz_genero')}")
        
        # Texto para prueba básica
        print("\nReproduciendo mensaje de prueba...")
        voice.hablar_sincrono("Hola, esta es una prueba del sistema de voz mejorado. Si escuchas esto, el sistema está funcionando correctamente.")
        
        print("\n¿Has escuchado el mensaje? (s/n): ", end="")
        respuesta = input().lower()
        
        if respuesta == 's':
            print("\n¡Excelente! El motor de voz está funcionando correctamente.")
            
            # Preguntar si desea probar el motor pyttsx3
            print("\n¿Quieres probar el motor pyttsx3? Este motor funciona sin conexión a internet. (s/n): ", end="")
            respuesta = input().lower()
            
            if respuesta == 's':
                print("\nCambiando al motor pyttsx3...")
                if voice.cambiar_motor("pyttsx3"):
                    print("Motor cambiado correctamente.")
                    voice.hablar_sincrono("Ahora estamos usando el motor de voz pyttsx3 que funciona sin conexión a internet.")
                    print("\n¿Has escuchado el mensaje con el motor pyttsx3? (s/n): ", end="")
                    respuesta = input().lower()
                    
                    if respuesta == 's':
                        print("\n¡Perfecto! Ambos motores funcionan correctamente.")
                    else:
                        print("\nEl motor pyttsx3 no está funcionando correctamente. Podría ser necesario revisar su instalación.")
                else:
                    print("ERROR: No se pudo cambiar al motor pyttsx3")
        else:
            print("\nEl motor de voz Google TTS no está funcionando correctamente. Vamos a probar con pyttsx3...")
            
            if voice.cambiar_motor("pyttsx3"):
                print("Motor cambiado a pyttsx3.")
                voice.hablar_sincrono("Esta es una prueba con el motor de voz pyttsx3.")
                print("\n¿Has escuchado el mensaje con pyttsx3? (s/n): ", end="")
                respuesta = input().lower()
                
                if respuesta == 's':
                    print("\nEl motor pyttsx3 funciona correctamente. Puedes usar este motor como alternativa.")
                else:
                    print("\nNinguno de los motores de voz está funcionando correctamente. Verificar la instalación y la configuración.")
        
        # Cerrar el motor
        print("\nCerrando motor de voz...")
        voice.cerrar()
        print("Prueba finalizada.")
    
    except ImportError as e:
        print(f"ERROR: Falta alguna dependencia: {e}")
        print("Asegúrate de instalar todas las dependencias necesarias con:")
        print("pip install google-cloud-texttospeech pyttsx3 pygame")
    
    except Exception as e:
        print(f"ERROR: {e}")
        print("Ha ocurrido un error inesperado durante la prueba.")

if __name__ == "__main__":
    probar_voz()