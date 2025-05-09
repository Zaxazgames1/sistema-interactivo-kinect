#!/usr/bin/env python3
"""
Script mejorado para comparar los diferentes motores de voz disponibles.
"""

import os
import sys
import time
import logging
from enum import Enum

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Asegurar que podemos importar desde el directorio del proyecto
script_dir = os.path.dirname(os.path.abspath(__file__))
proyecto_dir = os.path.dirname(script_dir)
sys.path.insert(0, proyecto_dir)

# Asegúrate de que existe el directorio temp_audio
os.makedirs("temp_audio", exist_ok=True)

# Textos de prueba para los motores
TEXTO_PRUEBA_CORTO = "Hola, esta es una prueba del sistema de voz mejorado. ¿Cómo suena este motor?"
TEXTO_PRUEBA_LARGO = """Este es un texto más largo para probar las capacidades avanzadas de cada motor de voz.
Podemos evaluar la naturalidad de la voz, la entonación en frases largas, y cómo maneja pausas.
También es importante ver cómo pronuncia palabras técnicas como: algoritmo, interfaz y kinect.
¿Te parece natural esta voz? ¿Suena como una persona real?"""

TEXTO_SALUDOS = "Hola, bienvenido al Sistema Interactivo con Kinect. Estoy aquí para ayudarte con tus proyectos."

class OpcionMotor(Enum):
    PYTTSX3 = "pyttsx3"
    GOOGLE = "google_tts"
    AZURE = "azure_tts"

def probar_motor(motor, texto, usar_config_predeterminada=True):
    """Prueba un motor de voz específico con el texto dado."""
    try:
        # Importar el motor de voz
        from sistema.voice_engine import VoiceEngine
        
        if usar_config_predeterminada:
            # Usar el archivo de configuración predeterminado
            voice = VoiceEngine()
            
            # Cambiar al motor deseado
            if voice.motor_actual.value != motor:
                print(f"Cambiando motor a {motor}...")
                voice.cambiar_motor(motor)
        else:
            # Configuración específica para el motor
            import json
            config_temp = "configuracion_voz_temp.json"
            
            # Crear config temporal con el motor específico
            with open("configuracion_voz.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            config["motor"] = motor
            
            with open(config_temp, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            
            # Inicializar con la config temporal
            voice = VoiceEngine(config_path=config_temp)
        
        if not voice.iniciado:
            print(f"ERROR: No se pudo iniciar el motor {motor}")
            return False
        
        # Mostrar información
        print(f"\nProbando motor: {motor}")
        print(f"Motor actual: {voice.motor_actual}")
        
        # Intentar hablar
        print("Reproduciendo mensaje...")
        voice.hablar_sincrono(texto)
        
        # Cerrar el motor
        voice.cerrar()
        
        # Limpiar archivo temporal si se creó
        if not usar_config_predeterminada:
            try:
                os.remove(config_temp)
            except:
                pass
            
        return True
    except Exception as e:
        print(f"ERROR al probar {motor}: {e}")
        return False

def comparar_motores():
    """Función principal para comparar los diferentes motores de voz."""
    print("===== COMPARACIÓN DE MOTORES DE VOZ MEJORADA =====")
    print("Este script te permitirá probar y comparar los diferentes motores de voz disponibles.")
    
    # Verificar si existe el archivo de configuración
    if not os.path.exists("configuracion_voz.json"):
        print("ADVERTENCIA: No se encontró el archivo configuracion_voz.json")
        print("Creando archivo de configuración básico...")
        
        import json
        config_basica = {
            "motor": "pyttsx3",
            "voz_genero": "femenino",
            "voz_idioma": "es",
            "velocidad": 1.0,
            "volumen": 0.9,
            "tono": 0.0,
            "enfasis_palabras": True,
            "pausas_naturales": True,
            "usar_ssml": True,
            "efectos_audio": False,
            "google_tts": {
                "credenciales_path": "google_credentials.json",
                "voz_preferida": "es-ES-Standard-A",
                "usar_wavenet": False
            },
            "azure_tts": {
                "subscription_key": "",
                "region": "eastus",
                "voz_preferida": "es-ES-ElviraNeural",
                "estilo_habla": "general"
            }
        }
        
        with open("configuracion_voz.json", "w", encoding="utf-8") as f:
            json.dump(config_basica, f, indent=4)
    
    # Verificar dependencias
    try:
        import pyttsx3
        pyttsx3_disponible = True
    except ImportError:
        pyttsx3_disponible = False
        print("NOTA: pyttsx3 no está instalado. Instálalo con: pip install pyttsx3")
    
    try:
        from google.cloud import texttospeech
        google_tts_disponible = True
        
        # Verificar credenciales
        credenciales_path = None
        try:
            import json
            with open("configuracion_voz.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                credenciales_path = config.get("google_tts", {}).get("credenciales_path")
        except:
            pass
            
        if credenciales_path and not os.path.exists(credenciales_path):
            print(f"ADVERTENCIA: No se encontró el archivo de credenciales {credenciales_path}")
            print("Verifica que el archivo existe y está en la ubicación correcta.")
    except ImportError:
        google_tts_disponible = False
        print("NOTA: google-cloud-texttospeech no está instalado. Instálalo con: pip install google-cloud-texttospeech")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        azure_tts_disponible = True
        
        # Verificar clave de Azure
        try:
            import json
            with open("configuracion_voz.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                subscription_key = config.get("azure_tts", {}).get("subscription_key")
                if not subscription_key:
                    print("ADVERTENCIA: No se encontró clave de suscripción de Azure en configuracion_voz.json")
        except:
            pass
    except ImportError:
        azure_tts_disponible = False
        print("NOTA: azure-cognitiveservices-speech no está instalado. Instálalo con: pip install azure-cognitiveservices-speech")
    
    # Mostrar motores disponibles
    print("\nMotores disponibles:")
    print(f" - pyttsx3: {'Disponible' if pyttsx3_disponible else 'No disponible'}")
    print(f" - Google TTS: {'Disponible' if google_tts_disponible else 'No disponible'}")
    print(f" - Azure TTS: {'Disponible' if azure_tts_disponible else 'No disponible'}")
    
    # Menú de prueba
    while True:
        print("\n===== MENÚ DE COMPARACIÓN =====")
        print("1. Probar pyttsx3 (voz básica, sin internet)")
        print("2. Probar Google TTS (alta calidad, requiere internet)")
        print("3. Probar Azure TTS (alta calidad, requiere internet y clave de API)")
        print("4. Comparación directa de todos los motores disponibles")
        print("5. Prueba avanzada (texto largo)")
        print("6. Prueba de saludos del sistema")
        print("7. Modificar velocidad/tono")
        print("8. Salir")
        
        try:
            opcion = int(input("\nSelecciona una opción (1-8): "))
            
            if opcion == 1:
                if pyttsx3_disponible:
                    probar_motor(OpcionMotor.PYTTSX3.value, TEXTO_PRUEBA_CORTO)
                    valoracion = input("\n¿Cómo calificarías esta voz del 1 al 10? ")
                    print(f"Has valorado pyttsx3 con: {valoracion}/10")
                else:
                    print("pyttsx3 no está disponible. Instálalo con: pip install pyttsx3")
            
            elif opcion == 2:
                if google_tts_disponible:
                    probar_motor(OpcionMotor.GOOGLE.value, TEXTO_PRUEBA_CORTO)
                    valoracion = input("\n¿Cómo calificarías esta voz del 1 al 10? ")
                    print(f"Has valorado Google TTS con: {valoracion}/10")
                else:
                    print("Google TTS no está disponible. Instálalo con: pip install google-cloud-texttospeech")
            
            elif opcion == 3:
                if azure_tts_disponible:
                    probar_motor(OpcionMotor.AZURE.value, TEXTO_PRUEBA_CORTO)
                    valoracion = input("\n¿Cómo calificarías esta voz del 1 al 10? ")
                    print(f"Has valorado Azure TTS con: {valoracion}/10")
                else:
                    print("Azure TTS no está disponible. Instálalo con: pip install azure-cognitiveservices-speech")
            
            elif opcion == 4:
                print("\n===== COMPARACIÓN DIRECTA =====")
                print("Se reproducirá el mismo texto con cada motor disponible.")
                
                resultados = {}
                
                if pyttsx3_disponible:
                    print("\n----- pyttsx3 -----")
                    probar_motor(OpcionMotor.PYTTSX3.value, TEXTO_PRUEBA_CORTO)
                    valoracion = input("Valoración (1-10): ")
                    resultados["pyttsx3"] = valoracion
                
                if google_tts_disponible:
                    print("\n----- Google TTS -----")
                    probar_motor(OpcionMotor.GOOGLE.value, TEXTO_PRUEBA_CORTO)
                    valoracion = input("Valoración (1-10): ")
                    resultados["Google TTS"] = valoracion
                
                if azure_tts_disponible:
                    print("\n----- Azure TTS -----")
                    probar_motor(OpcionMotor.AZURE.value, TEXTO_PRUEBA_CORTO)
                    valoracion = input("Valoración (1-10): ")
                    resultados["Azure TTS"] = valoracion
                
                # Mostrar resultados
                print("\n===== RESULTADOS DE LA COMPARACIÓN =====")
                for motor, valor in resultados.items():
                    print(f"{motor}: {valor}/10")
                
                # Determinar el mejor
                if resultados:
                    try:
                        mejor_motor = max(resultados.items(), key=lambda x: int(x[1]))
                        print(f"\nEl mejor motor según tu valoración es: {mejor_motor[0]} con {mejor_motor[1]}/10")
                        
                        guardar_mejor = input("\n¿Quieres configurar este motor como predeterminado? (s/n): ").lower()
                        if guardar_mejor == 's':
                            motor_config = None
                            if mejor_motor[0] == "pyttsx3":
                                motor_config = "pyttsx3"
                            elif mejor_motor[0] == "Google TTS":
                                motor_config = "google_tts"
                            elif mejor_motor[0] == "Azure TTS":
                                motor_config = "azure_tts"
                                
                            if motor_config:
                                import json
                                try:
                                    with open("configuracion_voz.json", "r", encoding="utf-8") as f:
                                        config = json.load(f)
                                    
                                    config["motor"] = motor_config
                                    
                                    with open("configuracion_voz.json", "w", encoding="utf-8") as f:
                                        json.dump(config, f, indent=4)
                                    
                                    print(f"Motor {motor_config} configurado como predeterminado.")
                                except Exception as e:
                                    print(f"Error al guardar configuración: {e}")
                    except:
                        print("No se pudo determinar el mejor motor.")
            
            elif opcion == 5:
                print("\n===== PRUEBA AVANZADA =====")
                print("Se reproducirá un texto más largo con cada motor.")
                
                motor_elegido = input("¿Qué motor quieres probar? (1: pyttsx3, 2: Google TTS, 3: Azure TTS): ")
                
                if motor_elegido == "1" and pyttsx3_disponible:
                    probar_motor(OpcionMotor.PYTTSX3.value, TEXTO_PRUEBA_LARGO)
                elif motor_elegido == "2" and google_tts_disponible:
                    probar_motor(OpcionMotor.GOOGLE.value, TEXTO_PRUEBA_LARGO)
                elif motor_elegido == "3" and azure_tts_disponible:
                    probar_motor(OpcionMotor.AZURE.value, TEXTO_PRUEBA_LARGO)
                else:
                    print("Opción no válida o motor no disponible.")
            
            elif opcion == 6:
                print("\n===== PRUEBA DE SALUDOS DEL SISTEMA =====")
                
                motor_elegido = input("¿Qué motor quieres probar? (1: pyttsx3, 2: Google TTS, 3: Azure TTS): ")
                
                if motor_elegido == "1" and pyttsx3_disponible:
                    probar_motor(OpcionMotor.PYTTSX3.value, TEXTO_SALUDOS)
                elif motor_elegido == "2" and google_tts_disponible:
                    probar_motor(OpcionMotor.GOOGLE.value, TEXTO_SALUDOS)
                elif motor_elegido == "3" and azure_tts_disponible:
                    probar_motor(OpcionMotor.AZURE.value, TEXTO_SALUDOS)
                else:
                    print("Opción no válida o motor no disponible.")
            
            elif opcion == 7:
                print("\n===== MODIFICAR VELOCIDAD/TONO =====")
                
                # Importar motor de voz
                from sistema.voice_engine import VoiceEngine
                voice = VoiceEngine()
                
                if not voice.iniciado:
                    print("ERROR: No se pudo iniciar el motor de voz")
                    continue
                
                print(f"Motor actual: {voice.motor_actual}")
                print(f"Velocidad actual: {voice.config.get('velocidad', 1.0)}")
                print(f"Tono actual: {voice.config.get('tono', 0.0)}")
                
                # Modificar parámetros
                try:
                    nueva_velocidad = float(input("Nueva velocidad (0.5-2.0, 1.0=normal): "))
                    nuevo_tono = float(input("Nuevo tono (-10.0-10.0, 0.0=normal): "))
                    
                    voice.establecer_velocidad(nueva_velocidad)
                    voice.establecer_tono(nuevo_tono)
                    
                    print("Reproduciendo con nuevos parámetros...")
                    voice.hablar_sincrono(TEXTO_PRUEBA_CORTO)
                    
                    guardar = input("¿Guardar estos parámetros como predeterminados? (s/n): ").lower()
                    if guardar == 's':
                        # Ya se ha guardado en el motor
                        print("Parámetros guardados como predeterminados.")
                except ValueError:
                    print("Error: Introduce valores numéricos válidos.")
                except Exception as e:
                    print(f"Error: {e}")
                
                voice.cerrar()
            
            elif opcion == 8:
                print("Saliendo del programa...")
                break
            
            else:
                print("Opción no válida. Intenta de nuevo.")
        
        except ValueError:
            print("Por favor, introduce un número del 1 al 8.")
        except Exception as e:
            print(f"Error: {e}")
    
    # Limpiar archivos temporales
    try:
        if os.path.exists("configuracion_voz_temp.json"):
            os.remove("configuracion_voz_temp.json")
    except:
        pass

if __name__ == "__main__":
    comparar_motores()