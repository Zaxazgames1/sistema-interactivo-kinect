"""
Módulo para la síntesis de voz mejorada con mayor naturalidad.
"""

import logging
import threading
import time
import json
import os
import tempfile
import re
import subprocess
from typing import Optional, List, Dict, Tuple, Any
from enum import Enum

logger = logging.getLogger("SistemaKinect.VoiceEngine")

# Definir tipos de motor de voz
class MotorVoz(Enum):
    PYTTSX3 = "pyttsx3"        # Motor básico integrado
    GOOGLE_TTS = "google_tts"  # Google Cloud Text-to-Speech
    AZURE_TTS = "azure_tts"    # Microsoft Azure Text-to-Speech
    OFFLINE_TTS = "offline_tts"  # Modo offline con modelos locales

# Importación condicional para pyttsx3 (motor básico)
try:
    import pyttsx3
    PYTTSX3_DISPONIBLE = True
except ImportError:
    logger.warning("pyttsx3 no está disponible. Síntesis básica desactivada.")
    PYTTSX3_DISPONIBLE = False

# Importación condicional para Google Cloud TTS
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_DISPONIBLE = True
except ImportError:
    logger.warning("Google Cloud TTS no está disponible. Instala con: pip install google-cloud-texttospeech")
    GOOGLE_TTS_DISPONIBLE = False

# Importación condicional para Azure Speech
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_TTS_DISPONIBLE = True
except ImportError:
    logger.warning("Azure Speech no está disponible. Instala con: pip install azure-cognitiveservices-speech")
    AZURE_TTS_DISPONIBLE = False

class VoiceEngine:
    """Gestiona la síntesis de voz mejorada con múltiples motores y opciones avanzadas."""
    
    CONFIG_FILE = "configuracion_voz.json"
    DEFAULT_CONFIG = {
        # Configuración general
        "motor": "pyttsx3",  # Motor a usar: pyttsx3, google_tts, azure_tts, offline_tts
        "voz_id": None,      # Se establecerá automáticamente
        "voz_genero": "femenino",  # 'masculino' o 'femenino'
        "voz_idioma": "es",  # Código de idioma ('es', 'en', etc.)
        "velocidad": 1.0,    # Factor de velocidad (1.0 = normal)
        "volumen": 0.9,      # Volumen (0.0 a 1.0)
        "tono": 0.0,         # Factor de tono (-10.0 a 10.0)
        
        # Opciones avanzadas
        "enfasis_palabras": True,    # Énfasis en palabras clave
        "pausas_naturales": True,    # Pausas naturales entre frases
        "usar_ssml": True,           # Usar SSML para mayor control
        "efectos_audio": False,      # Aplicar efectos sutiles de audio
        
        # Configuración específica de Google TTS
        "google_tts": {
            "credenciales_path": "google_credentials.json",
            "voz_preferida": "es-ES-Standard-A",
            "usar_wavenet": False     # Usar voces WaveNet para mayor calidad
        },
        
        # Configuración específica de Azure TTS
        "azure_tts": {
            "subscription_key": "",
            "region": "eastus",
            "voz_preferida": "es-ES-ElviraNeural",
            "estilo_habla": "general",  # Estilo de habla: general, cheerful, sad, angry
            "formato_audio": "Riff16Khz16BitMonoPcm"  # Formato correcto para Azure
        },
        
        # Configuración de modo offline (modelos locales)
        "offline_tts": {
            "modelo_path": "modelos/tts_model.pth",
            "config_path": "modelos/config.json",
            "vocoder_path": "modelos/vocoder.pth"
        },
        
        # Configuración específica de pyttsx3
        "pyttsx3": {
            "optimizar_rendimiento": True,
            "verificar_voces_espanol": True,
            "usar_voz_femenina": True
        }
    }
    
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.engine = None
        self.motor_actual = None
        self.iniciado = False
        self.hablando = False
        self.cola_mensajes = []
        self.hilo_habla = None
        self.voces_disponibles = []
        self.config = self._cargar_config()
        
        # Clientes específicos para cada API
        self.google_client = None
        self.azure_speech_config = None
        self.azure_synthesizer = None
        
        # Directorio para archivos temporales de audio
        try:
            # Usar un directorio sin espacios en el nombre (evita problemas con playsound en Windows)
            temp_base = os.path.join(os.getcwd(), "temp_audio")
            os.makedirs(temp_base, exist_ok=True)
            self.temp_dir = temp_base
        except Exception as e:
            logger.warning(f"No se pudo crear directorio temporal personalizado: {e}")
            try:
                # Intentar crear en el directorio temporal del sistema
                self.temp_dir = tempfile.mkdtemp(prefix="voice_")
            except Exception as e:
                logger.warning(f"No se pudo crear directorio temporal del sistema: {e}")
                # Usar directorio actual como último recurso
                self.temp_dir = os.getcwd()
        
        logger.info(f"Usando directorio temporal: {self.temp_dir}")
        
        # Intentar iniciar con el motor configurado
        self.iniciar()
    
    def _cargar_config(self) -> Dict:
        """Carga la configuración de voz desde archivo o usa valores predeterminados."""
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Configuración de voz cargada desde {self.config_path}.")
                return config
            elif os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Configuración de voz cargada desde archivo predeterminado.")
                return config
            else:
                logger.info("Archivo de configuración de voz no encontrado. Usando valores predeterminados.")
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error al cargar configuración de voz: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def _guardar_config(self) -> bool:
        """Guarda la configuración actual de voz en archivo."""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuración de voz guardada correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración de voz: {e}")
            return False
    
    def iniciar(self) -> bool:
        """Inicia el motor de síntesis de voz según la configuración."""
        # Determinar qué motor usar según configuración
        motor = self.config.get('motor', 'pyttsx3')
        
        try:
            if motor == MotorVoz.PYTTSX3.value and PYTTSX3_DISPONIBLE:
                return self._iniciar_pyttsx3()
            elif motor == MotorVoz.GOOGLE_TTS.value and GOOGLE_TTS_DISPONIBLE:
                return self._iniciar_google_tts()
            elif motor == MotorVoz.AZURE_TTS.value and AZURE_TTS_DISPONIBLE:
                return self._iniciar_azure_tts()
            elif motor == MotorVoz.OFFLINE_TTS.value:
                return self._iniciar_offline_tts()
            else:
                # Fallback a pyttsx3 si el motor configurado no está disponible
                if PYTTSX3_DISPONIBLE:
                    logger.warning(f"Motor {motor} no disponible. Usando pyttsx3 como fallback.")
                    return self._iniciar_pyttsx3()
                else:
                    logger.error("Ningún motor de síntesis de voz disponible.")
                    return False
        except Exception as e:
            logger.error(f"Error al iniciar motor de síntesis de voz: {e}")
            return False
    
    def _iniciar_pyttsx3(self) -> bool:
        """Inicia el motor básico pyttsx3."""
        if not PYTTSX3_DISPONIBLE:
            logger.error("pyttsx3 no está disponible. No se puede iniciar síntesis básica.")
            return False
        
        try:
            self.engine = pyttsx3.init()
            
            # Obtener voces disponibles y clasificarlas
            self.voces_disponibles = self._obtener_voces_pyttsx3()
            
            # Aplicar configuración
            self._aplicar_configuracion_pyttsx3()
            
            self.motor_actual = MotorVoz.PYTTSX3
            self.iniciado = True
            
            # Iniciar hilo para procesar cola de mensajes
            self.hilo_habla = threading.Thread(target=self._procesar_cola_habla, daemon=True)
            self.hilo_habla.start()
            
            logger.info("Motor de síntesis pyttsx3 iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar motor pyttsx3: {e}")
            return False
    
    def _iniciar_google_tts(self) -> bool:
        """Inicia el motor Google Cloud Text-to-Speech."""
        if not GOOGLE_TTS_DISPONIBLE:
            logger.error("Google Cloud TTS no está disponible.")
            return False
        
        try:
            # Configurar credenciales si se especifica una ruta
            credenciales_path = self.config.get('google_tts', {}).get('credenciales_path')
            if credenciales_path and os.path.exists(credenciales_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(credenciales_path)
                logger.info(f"Usando credenciales de Google Cloud desde: {os.path.abspath(credenciales_path)}")
            else:
                logger.warning(f"Archivo de credenciales no encontrado: {credenciales_path}. Verificar configuración.")
            
            # Inicializar cliente
            self.google_client = texttospeech.TextToSpeechClient()
            
            # Obtener voces disponibles
            self.voces_disponibles = self._obtener_voces_google_tts()
            
            self.motor_actual = MotorVoz.GOOGLE_TTS
            self.iniciado = True
            
            # Iniciar hilo para procesar cola de mensajes
            self.hilo_habla = threading.Thread(target=self._procesar_cola_habla, daemon=True)
            self.hilo_habla.start()
            
            logger.info("Motor Google Cloud TTS iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar Google TTS: {e}")
            return False
    
    def _iniciar_azure_tts(self) -> bool:
        """Inicia el motor Microsoft Azure Speech."""
        if not AZURE_TTS_DISPONIBLE:
            logger.error("Azure Speech no está disponible.")
            return False
        
        try:
            # Configurar credenciales
            subscription_key = self.config.get('azure_tts', {}).get('subscription_key')
            region = self.config.get('azure_tts', {}).get('region', 'eastus')
            
            if not subscription_key:
                logger.error("Clave de suscripción de Azure no configurada.")
                return False
            
            # Configurar speech
            self.azure_speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
            self.azure_speech_config.speech_synthesis_voice_name = self.config.get('azure_tts', {}).get('voz_preferida', 'es-ES-ElviraNeural')
            
            # Configurar formato de audio (mejora para compatibilidad)
            formato_audio = self.config.get('azure_tts', {}).get('formato_audio', 'Riff16Khz16BitMonoPcm')
            try:
                # Convertir formato a enum correcto de Azure
                formato_enum = getattr(speechsdk.SpeechSynthesisOutputFormat, formato_audio)
                self.azure_speech_config.set_speech_synthesis_output_format(formato_enum)
            except (AttributeError, ValueError) as e:
                logger.warning(f"Formato de audio no válido: {formato_audio}. Usando formato predeterminado.")
                # Usar formato predeterminado
                self.azure_speech_config.set_speech_synthesis_output_format(
                    speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
                )
            
            # Obtener voces disponibles
            self.voces_disponibles = self._obtener_voces_azure()
            
            self.motor_actual = MotorVoz.AZURE_TTS
            self.iniciado = True
            
            # Iniciar hilo para procesar cola de mensajes
            self.hilo_habla = threading.Thread(target=self._procesar_cola_habla, daemon=True)
            self.hilo_habla.start()
            
            logger.info("Motor Azure TTS iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar Azure TTS: {e}")
            return False
    
    def _iniciar_offline_tts(self) -> bool:
        """Inicia el motor offline con modelos locales."""
        try:
            # Verificar si hay modelos instalados
            modelo_path = self.config.get('offline_tts', {}).get('modelo_path')
            config_path = self.config.get('offline_tts', {}).get('config_path')
            
            if not modelo_path or not os.path.exists(modelo_path):
                logger.error("Modelo TTS offline no encontrado.")
                return False
            
            # Aquí implementar la carga del modelo offline
            # (requiere una implementación específica según el modelo)
            
            self.motor_actual = MotorVoz.OFFLINE_TTS
            self.iniciado = True
            
            # Iniciar hilo para procesar cola de mensajes
            self.hilo_habla = threading.Thread(target=self._procesar_cola_habla, daemon=True)
            self.hilo_habla.start()
            
            logger.info("Motor TTS offline iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar TTS offline: {e}")
            return False
    
    def _obtener_voces_pyttsx3(self) -> List[Dict]:
        """Obtiene y clasifica las voces disponibles en pyttsx3."""
        voces = []
        try:
            for voice in self.engine.getProperty('voices'):
                # Determinar idioma
                idioma = 'es' if ('spanish' in voice.name.lower() or 'español' in voice.name.lower()) else \
                        'en' if ('english' in voice.name.lower() or 'inglés' in voice.name.lower()) else \
                        'otro'
                
                # Determinar género basado en nombres comunes y patrones
                genero = 'femenino' if any(patron in voice.name.lower() for patron in 
                        ['female', 'mujer', 'woman', 'girl', 'helena', 'laura', 'monica', 'zira', 'sabina']) else 'masculino'
                
                voces.append({
                    'id': voice.id,
                    'nombre': voice.name,
                    'idioma': idioma,
                    'genero': genero,
                    'motor': MotorVoz.PYTTSX3.value
                })
        except Exception as e:
            logger.error(f"Error al obtener voces de pyttsx3: {e}")
        return voces
    
    def _obtener_voces_google_tts(self) -> List[Dict]:
        """Obtiene las voces disponibles en Google Cloud TTS."""
        if not self.google_client:
            return []
            
        try:
            # Listar todas las voces disponibles
            respuesta = self.google_client.list_voices()
            voces = []
            
            for voice in respuesta.voices:
                for idioma in voice.language_codes:
                    # Obtener código de idioma base (ej: 'es' de 'es-ES')
                    idioma_base = idioma.split('-')[0]
                    
                    # Determinar género
                    genero = 'femenino' if voice.ssml_gender == texttospeech.SsmlVoiceGender.FEMALE else \
                            'masculino' if voice.ssml_gender == texttospeech.SsmlVoiceGender.MALE else 'neutro'
                    
                    # Verificar si es voz neural/wavenet
                    es_neural = 'Wavenet' in voice.name or 'Neural' in voice.name
                    
                    voces.append({
                        'id': voice.name,
                        'nombre': voice.name,
                        'idioma': idioma_base,
                        'idioma_completo': idioma,
                        'genero': genero,
                        'natural': es_neural,
                        'motor': MotorVoz.GOOGLE_TTS.value
                    })
            
            return voces
        except Exception as e:
            logger.error(f"Error al obtener voces de Google TTS: {e}")
            return []
    
    def _obtener_voces_azure(self) -> List[Dict]:
        """Obtiene las voces disponibles en Azure Speech."""
        if not self.azure_speech_config:
            return []
            
        try:
            # Implementar lógica para obtener voces de Azure
            # Nota: Azure requiere una API adicional para listar voces
            
            # Voces predefinidas comunes (como ejemplo)
            voces_predefinidas = [
                {
                    'id': 'es-ES-ElviraNeural',
                    'nombre': 'Elvira (Neural)',
                    'idioma': 'es',
                    'idioma_completo': 'es-ES',
                    'genero': 'femenino',
                    'natural': True,
                    'motor': MotorVoz.AZURE_TTS.value
                },
                {
                    'id': 'es-ES-AlvaroNeural',
                    'nombre': 'Alvaro (Neural)',
                    'idioma': 'es',
                    'idioma_completo': 'es-ES',
                    'genero': 'masculino',
                    'natural': True,
                    'motor': MotorVoz.AZURE_TTS.value
                },
                {
                    'id': 'es-MX-DaliaNeural',
                    'nombre': 'Dalia (Neural)',
                    'idioma': 'es',
                    'idioma_completo': 'es-MX',
                    'genero': 'femenino',
                    'natural': True,
                    'motor': MotorVoz.AZURE_TTS.value
                },
                {
                    'id': 'es-ES-EliasNeural',
                    'nombre': 'Elias (Neural)',
                    'idioma': 'es',
                    'idioma_completo': 'es-ES',
                    'genero': 'masculino',
                    'natural': True,
                    'motor': MotorVoz.AZURE_TTS.value
                }
            ]
            
            return voces_predefinidas
        except Exception as e:
            logger.error(f"Error al obtener voces de Azure: {e}")
            return []
    
    def _aplicar_configuracion_pyttsx3(self) -> None:
        """Aplica la configuración al motor pyttsx3."""
        if not self.engine:
            return
        
        # Establecer velocidad
        velocidad = int(self.config.get('velocidad', 1.0) * 150)  # 1.0 = 150 palabras por minuto
        self.engine.setProperty('rate', velocidad)
        
        # Establecer volumen
        self.engine.setProperty('volume', self.config.get('volumen', 0.9))
        
        # Seleccionar voz apropiada
        voz_id = self.config.get('voz_id')
        voz_genero = self.config.get('voz_genero', 'femenino')
        voz_idioma = self.config.get('voz_idioma', 'es')
        
        # Si no hay una voz específica configurada, elegir basado en género e idioma
        if not voz_id:
            voz_seleccionada = None
            for voz in self.voces_disponibles:
                if voz['idioma'] == voz_idioma and voz['genero'] == voz_genero:
                    voz_seleccionada = voz
                    break
            
            # Si no hay coincidencia exacta, intentar solo con idioma
            if not voz_seleccionada:
                for voz in self.voces_disponibles:
                    if voz['idioma'] == voz_idioma:
                        voz_seleccionada = voz
                        break
            
            # Si aún no hay coincidencia, usar la primera voz disponible
            if not voz_seleccionada and self.voces_disponibles:
                voz_seleccionada = self.voces_disponibles[0]
            
            if voz_seleccionada:
                voz_id = voz_seleccionada['id']
                # Actualizar config
                self.config['voz_id'] = voz_id
                self._guardar_config()
                logger.info(f"Voz seleccionada automáticamente: {voz_seleccionada['nombre']}")
        
        # Aplicar voz si existe
        if voz_id:
            try:
                self.engine.setProperty('voice', voz_id)
            except Exception as e:
                logger.error(f"Error al establecer voz: {e}")
    
    def hablar(self, texto: str, prioridad: bool = False) -> bool:
        """Sintetiza voz para un texto dado.
        
        Args:
            texto: Texto a sintetizar
            prioridad: Si es True, se coloca al principio de la cola
        """
        if not self.iniciado:
            logger.warning("Motor de síntesis de voz no iniciado. No se puede hablar.")
            return False
        
        try:
            # Preprocesar texto para mejorar naturalidad
            texto_procesado = self._preprocesar_texto(texto)
            
            # Añadir a la cola de mensajes
            if prioridad:
                self.cola_mensajes.insert(0, texto_procesado)
            else:
                self.cola_mensajes.append(texto_procesado)
            return True
        except Exception as e:
            logger.error(f"Error al agregar texto a cola de síntesis: {e}")
            return False
    
    def _preprocesar_texto(self, texto: str) -> str:
        """Preprocesa el texto para mejorar la naturalidad de la síntesis."""
        if not texto:
            return texto
        
        # Convertir números a texto extendido
        def reemplazar_numero(match):
            numero = match.group(0)
            # Mapeo para dígitos individuales
            if len(numero) == 1:
                mapeo = {"0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro", 
                       "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve"}
                return mapeo.get(numero, numero)
            return numero  # Números más complejos requieren lógica adicional
        
        texto = re.sub(r'\b\d\b', reemplazar_numero, texto)
        
        # Reemplazar abreviaturas comunes
        abreviaturas = {
            "Dr.": "Doctor",
            "Dra.": "Doctora",
            "Sr.": "Señor",
            "Sra.": "Señora",
            "Srta.": "Señorita",
            "Prof.": "Profesor",
            "No.": "Número",
            "Tel.": "Teléfono",
            "Av.": "Avenida",
            "NASA": "N A S A",  # Deletrear siglas
            "ONU": "O N U"
        }
        
        for abr, expansion in abreviaturas.items():
            texto = re.sub(r'\b' + abr + r'\b', expansion, texto)
        
        # Si está habilitado SSML y el motor lo soporta
        if self.config.get('usar_ssml', True) and self.motor_actual in [MotorVoz.GOOGLE_TTS, MotorVoz.AZURE_TTS]:
            # Añadir pausas usando SSML
            if self.config.get('pausas_naturales', True):
                texto = re.sub(r'([.!?]) ', r'\1 <break time="500ms"/> ', texto)
                texto = re.sub(r', ', r', <break time="200ms"/> ', texto)
                texto = re.sub(r';', r';<break time="300ms"/> ', texto)
            
            # Añadir énfasis en palabras importantes
            if self.config.get('enfasis_palabras', True):
                palabras_clave = ["importante", "urgente", "atención", "cuidado", "peligro"]
                for palabra in palabras_clave:
                    texto = re.sub(r'\b' + palabra + r'\b', f'<emphasis level="strong">{palabra}</emphasis>', texto)
        else:
            # Para motores que no soportan SSML, añadir pausas simples
            if self.config.get('pausas_naturales', True):
                texto = texto.replace(". ", ". <pause> ")
                texto = texto.replace("? ", "? <pause> ")
                texto = texto.replace("! ", "! <pause> ")
                texto = texto.replace(", ", ", <pause_corta> ")
        
        return texto
    
    def _convertir_a_ssml(self, texto: str) -> str:
        """Convierte texto preprocesado a formato SSML completo."""
        # Si el texto ya tiene etiquetas SSML, asegurarse de que tenga las etiquetas raíz
        if '<break' in texto or '<emphasis' in texto:
            if not texto.strip().startswith('<speak>'):
                # Configurar propiedades globales
                velocidad = self.config.get('velocidad', 1.0)
                velocidad_str = f"{int(velocidad * 100)}%"
                
                tono = self.config.get('tono', 0.0)
                tono_str = f"{int(tono * 100)}%"
                
                volumen = self.config.get('volumen', 0.9)
                volumen_str = f"{int(volumen * 100)}%"
                
                ssml = f"""<speak>
                    <prosody rate="{velocidad_str}" pitch="{tono_str}" volume="{volumen_str}">
                        {texto}
                    </prosody>
                </speak>"""
                return ssml
            return texto
        else:
            # Texto sin etiquetas SSML, envolver en formato básico
            velocidad = self.config.get('velocidad', 1.0)
            velocidad_str = f"{int(velocidad * 100)}%"
            
            tono = self.config.get('tono', 0.0)
            tono_str = f"{int(tono * 100)}%"
            
            volumen = self.config.get('volumen', 0.9)
            volumen_str = f"{int(volumen * 100)}%"
            
            ssml = f"""<speak>
                <prosody rate="{velocidad_str}" pitch="{tono_str}" volume="{volumen_str}">
                    {texto}
                </prosody>
            </speak>"""
            return ssml
    
    def _procesar_cola_habla(self) -> None:
        """Procesa la cola de mensajes para hablar en segundo plano."""
        while self.iniciado:
            try:
                if self.cola_mensajes and not self.hablando:
                    texto = self.cola_mensajes.pop(0)
                    self.hablando = True
                    
                    # Procesar según el motor activo
                    if self.motor_actual == MotorVoz.PYTTSX3:
                        self._hablar_pyttsx3(texto)
                    elif self.motor_actual == MotorVoz.GOOGLE_TTS:
                        self._hablar_google_tts(texto)
                    elif self.motor_actual == MotorVoz.AZURE_TTS:
                        self._hablar_azure_tts(texto)
                    elif self.motor_actual == MotorVoz.OFFLINE_TTS:
                        self._hablar_offline_tts(texto)
                    
                    self.hablando = False
            except Exception as e:
                logger.error(f"Error durante procesamiento de cola de habla: {e}")
                self.hablando = False
            
            time.sleep(0.1)  # Pequeña pausa para no consumir CPU
    
    def _hablar_pyttsx3(self, texto: str) -> None:
        """Sintetiza voz usando el motor pyttsx3."""
        try:
            # Manejar pausas especiales en el texto
            if '<pause>' in texto or '<pause_corta>' in texto:
                partes = texto.replace('<pause>', 'PAUSA_LARGA').replace('<pause_corta>', 'PAUSA_CORTA').split('PAUSA')
                for i, parte in enumerate(partes):
                    if parte:
                        if parte.startswith('_LARGA'):
                            time.sleep(0.5)  # Pausa larga
                            self.engine.say(parte[6:].strip())
                        elif parte.startswith('_CORTA'):
                            time.sleep(0.25)  # Pausa corta
                            self.engine.say(parte[6:].strip())
                        else:
                            self.engine.say(parte.strip())
                        if i < len(partes) - 1:
                            self.engine.runAndWait()
            else:
                self.engine.say(texto)
                self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error durante síntesis con pyttsx3: {e}")
    
    def _hablar_google_tts(self, texto: str) -> None:
        """Sintetiza voz usando Google Cloud TTS."""
        if not self.google_client:
            logger.error("Cliente Google TTS no inicializado.")
            return
            
        try:
            # Determinar si usar SSML
            usar_ssml = self.config.get('usar_ssml', True) and ('<speak>' in texto or '<break' in texto or '<emphasis' in texto)
            
            # Crear entrada de síntesis
            if usar_ssml:
                # Asegurar formato SSML completo
                texto_ssml = self._convertir_a_ssml(texto)
                synthesis_input = texttospeech.SynthesisInput(ssml=texto_ssml)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=texto)
            
            # Configurar voz
            idioma = self.config.get('voz_idioma', 'es')
            genero = self.config.get('voz_genero', 'femenino')
            
            # Seleccionar voz preferida o buscar una adecuada
            voz_preferida = self.config.get('google_tts', {}).get('voz_preferida')
            usar_wavenet = self.config.get('google_tts', {}).get('usar_wavenet', True)
            
            if not voz_preferida:
                # Buscar voz adecuada según idioma y género
                for voz in self.voces_disponibles:
                    es_neural = voz.get('natural', False)
                    if (voz['idioma'] == idioma and 
                        voz['genero'] == genero and 
                        (not usar_wavenet or (usar_wavenet and es_neural))):
                        voz_preferida = voz['id']
                        break
                
                # Si no encontró voz con los criterios exactos, buscar solo por idioma
                if not voz_preferida:
                    for voz in self.voces_disponibles:
                        if voz['idioma'] == idioma:
                            voz_preferida = voz['id']
                            break
            
            # Si aún no hay voz preferida, usar predeterminada según idioma
            if not voz_preferida:
                if idioma == 'es':
                    voz_preferida = 'es-ES-Standard-A' if genero == 'femenino' else 'es-ES-Standard-B'
                else:
                    voz_preferida = 'en-US-Standard-F' if genero == 'femenino' else 'en-US-Standard-D'
            
            # Configurar género para SSML
            ssml_gender = texttospeech.SsmlVoiceGender.FEMALE
            if genero == 'masculino':
                ssml_gender = texttospeech.SsmlVoiceGender.MALE
            
            # Crear configuración de voz
            voice = texttospeech.VoiceSelectionParams(
                language_code=idioma,
                name=voz_preferida,
                ssml_gender=ssml_gender
            )
            
            # Configuración de audio
            tono = self.config.get('tono', 0.0)
            velocidad = self.config.get('velocidad', 1.0)
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=velocidad,
                pitch=tono
            )
            
            # Realizar síntesis
            response = self.google_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Crear directorio temporal si no existe
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir, exist_ok=True)
            
            # Usar un nombre de archivo simple sin espacios (evita problemas con playsound)
            archivo_audio = f"tts_{int(time.time())}.mp3"
            ruta_audio = os.path.join(self.temp_dir, archivo_audio)
            
            # Guardar audio en archivo temporal
            with open(ruta_audio, "wb") as out:
                out.write(response.audio_content)
            
            # Aplicar efectos si están habilitados
            if self.config.get('efectos_audio', False):
                ruta_audio = self._aplicar_efectos_audio(ruta_audio)
            
            # Reproducir audio
            exito = self._reproducir_audio(ruta_audio)
            
            # Limpiar archivo temporal después de reproducir
            try:
                if os.path.exists(ruta_audio):
                    os.remove(ruta_audio)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")
                
        except Exception as e:
            logger.error(f"Error durante síntesis con Google TTS: {e}")
    
    def _hablar_azure_tts(self, texto: str) -> None:
        """Sintetiza voz usando Microsoft Azure Speech."""
        if not self.azure_speech_config:
            logger.error("Sintetizador Azure no inicializado.")
            return
            
        try:
            # Determinar si usar SSML
            usar_ssml = self.config.get('usar_ssml', True) and ('<speak>' in texto or '<break' in texto or '<emphasis' in texto)
            
            # Crear ruta para archivo de salida
            archivo_audio = f"tts_{int(time.time())}.wav"
            ruta_audio = os.path.join(self.temp_dir, archivo_audio)
            
            # Asegurar que el directorio existe
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir, exist_ok=True)
            
            # Configurar salida de audio a archivo
            audio_config = speechsdk.audio.AudioOutputConfig(filename=ruta_audio)
            
            # Crear sintetizador con configuración específica
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.azure_speech_config, 
                audio_config=audio_config
            )
            
            # Realizar síntesis con manejo detallado de errores
            if usar_ssml:
                # Asegurar formato SSML completo
                texto_ssml = self._convertir_a_ssml(texto)
                result = synthesizer.speak_ssml_async(texto_ssml).get()
            else:
                result = synthesizer.speak_text_async(texto).get()
            
            # Verificar resultado
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # El archivo ya se ha guardado por configuración
                # Reproducir audio
                exito = self._reproducir_audio(ruta_audio)
                
                # Limpiar archivo temporal después de reproducir
                try:
                    if os.path.exists(ruta_audio):
                        os.remove(ruta_audio)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal: {e}")
                    
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancelacion = speechsdk.CancellationDetails.from_result(result)
                logger.error(f"Síntesis cancelada: {cancelacion.reason}")
                logger.error(f"Detalles de error: {cancelacion.error_details}")
                
                if cancelacion.reason == speechsdk.CancellationReason.Error:
                    if "401" in cancelacion.error_details:
                        logger.error("Error de autenticación: clave de suscripción inválida o región incorrecta")
                    elif "429" in cancelacion.error_details:
                        logger.error("Se ha excedido el límite de solicitudes")
                    elif "403" in cancelacion.error_details:
                        logger.error("Acceso prohibido: verifica los permisos de la clave")
                    
                    # Intentar con Google TTS como respaldo
                    logger.info("Intentando con Google TTS como respaldo...")
                    self._hablar_google_tts(texto)
            else:
                logger.error(f"Error en síntesis de Azure: {result.reason}")
                
                # Intentar con Google TTS como respaldo
                logger.info("Intentando con Google TTS como respaldo...")
                self._hablar_google_tts(texto)
        except Exception as e:
            logger.error(f"Error durante síntesis con Azure TTS: {e}")
            
            # Intentar con Google TTS como respaldo
            logger.info("Intentando con Google TTS como respaldo tras excepción...")
            self._hablar_google_tts(texto)
    
    def _hablar_offline_tts(self, texto: str) -> None:
        """Sintetiza voz usando modelo TTS offline."""
        # Implementación básica para modelos offline
        # Requiere ajustar según el tipo de modelo utilizado
        try:
            # Aquí iría la lógica específica del modelo offline
            # Por ahora, fallback a pyttsx3 si está disponible
            if PYTTSX3_DISPONIBLE and hasattr(self, 'engine') and self.engine:
                self._hablar_pyttsx3(texto)
            else:
                logger.error("Síntesis offline no implementada y pyttsx3 no disponible.")
        except Exception as e:
            logger.error(f"Error durante síntesis offline: {e}")
    
    def _aplicar_efectos_audio(self, archivo_audio: str) -> str:
        """Aplica efectos sutiles para hacer la voz más natural."""
        try:
            # Verificar si ffmpeg está instalado
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("ffmpeg no está instalado. No se pueden aplicar efectos de audio.")
                return archivo_audio
                
            # Generar un nombre para el archivo procesado sin espacios
            archivo_base = os.path.basename(archivo_audio)
            nombre_base, extension = os.path.splitext(archivo_base)
            archivo_procesado = f"{nombre_base}_proc{extension}"
            ruta_procesado = os.path.join(self.temp_dir, archivo_procesado)
            
            # Aplicar efectos sutiles con ffmpeg
            comando = [
                'ffmpeg', '-y', '-i', archivo_audio,
                # Ecualización sutil para voz más natural
                '-af', 'equalizer=f=1000:width_type=h:width=200:g=1,equalizer=f=3000:width_type=o:width=100:g=-1',
                ruta_procesado
            ]
            
            # Ejecutar comando
            result = subprocess.run(comando, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            if result.returncode == 0 and os.path.exists(ruta_procesado):
                return ruta_procesado
            else:
                logger.warning(f"Error al aplicar efectos de audio: {result.stderr.decode()}")
                return archivo_audio
        except Exception as e:
            logger.error(f"Error al aplicar efectos de audio: {e}")
            return archivo_audio  # Devolver archivo original si hay error
    
    def _reproducir_audio(self, archivo_audio: str) -> bool:
        """Reproduce un archivo de audio usando varios métodos."""
        if not os.path.exists(archivo_audio):
            logger.error(f"Archivo de audio no encontrado: {archivo_audio}")
            return False
            
        logger.info(f"Reproduciendo audio: {archivo_audio}")
        
        # Intentar varios métodos de reproducción
        metodos_reproduccion = [
            self._reproducir_con_pygame,
            self._reproducir_con_winsound,
            self._reproducir_con_reproductor_sistema,
            self._reproducir_con_playsound,
            self._reproducir_con_subprocess
        ]
        
        for metodo in metodos_reproduccion:
            try:
                if metodo(archivo_audio):
                    return True  # Si un método fue exitoso, terminar
            except Exception as e:
                logger.debug(f"Error con método de reproducción {metodo.__name__}: {e}")
                continue
                
        logger.error("No se pudo reproducir el audio con ningún método disponible")
        return False
    
    def _reproducir_con_playsound(self, archivo_audio: str) -> bool:
        """Intenta reproducir audio con playsound."""
        try:
            # Importar playsound de forma condicional
            import playsound
            
            # Si estamos en Windows, usamos la versión 1.2.2 que funciona mejor ahí
            if os.name == 'nt':
                playsound.playsound(archivo_audio, block=True)
            else:
                # En macOS/Linux, usamos la versión normal
                playsound.playsound(archivo_audio)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Error al reproducir con playsound: {e}")
            return False
    
    def _reproducir_con_reproductor_sistema(self, archivo_audio: str) -> bool:
        """Intenta reproducir con el reproductor predeterminado del sistema."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(archivo_audio)
                time.sleep(3)  # Dar tiempo para que se reproduzca
                return True
            elif os.name == 'posix':  # Linux/Mac
                import platform
                if platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', archivo_audio])
                    time.sleep(3)
                    return True
                else:  # Linux
                    subprocess.run(['xdg-open', archivo_audio])
                    time.sleep(3)
                    return True
        except Exception as e:
            logger.warning(f"Error al reproducir con reproductor del sistema: {e}")
            return False
    
    def _reproducir_con_winsound(self, archivo_audio: str) -> bool:
        """Intenta reproducir con winsound (solo Windows y solo archivos WAV)."""
        if os.name != 'nt':
            return False
            
        try:
            import winsound
            if archivo_audio.lower().endswith('.wav'):
                winsound.PlaySound(archivo_audio, winsound.SND_FILENAME)
                return True
            else:
                # Intentar convertir a WAV si no es un archivo WAV
                try:
                    wav_file = archivo_audio.replace('.mp3', '.wav')
                    subprocess.run(['ffmpeg', '-y', '-i', archivo_audio, wav_file], 
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    winsound.PlaySound(wav_file, winsound.SND_FILENAME)
                    # Limpiar archivo convertido
                    try:
                        os.remove(wav_file)
                    except:
                        pass
                    return True
                except:
                    return False
        except Exception:
            return False
    
    def _reproducir_con_pygame(self, archivo_audio: str) -> bool:
        """Intenta reproducir con pygame."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(archivo_audio)
            pygame.mixer.music.play()
            
            # Esperar a que termine la reproducción
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            pygame.mixer.quit()
            return True
        except ImportError:
            return False
        except Exception:
            try:
                pygame.mixer.quit()
            except:
                pass
            return False
    
    def _reproducir_con_subprocess(self, archivo_audio: str) -> bool:
        """Intenta reproducir con reproductores comunes mediante subprocess."""
        try:
            # Lista de reproductores comunes
            if os.name == 'nt':  # Windows
                try:
                    subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{archivo_audio}").PlaySync()'], check=True)
                    return True
                except:
                    # Alternativa con cmd
                    subprocess.run(['cmd', '/c', f'start /wait wmplayer "{archivo_audio}"'], check=True)
                    time.sleep(3)  # Dar tiempo para que termine la reproducción
                    return True
            else:  # Linux/Mac
                reproductores = ['aplay', 'mpg123', 'mpg321', 'play', 'mplayer', 'afplay']
                for reproductor in reproductores:
                    try:
                        subprocess.run([reproductor, archivo_audio], check=True)
                        return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
            return False
        except Exception:
            return False
    
    def establecer_velocidad(self, velocidad: float) -> bool:
        """Establece la velocidad de habla del motor de voz."""
        if not self.iniciado:
            return False
            
        try:
            if 0.5 <= velocidad <= 2.0:  # Rango seguro
                self.config['velocidad'] = velocidad
                
                # Aplicar según motor actual
                if self.motor_actual == MotorVoz.PYTTSX3:
                    self.engine.setProperty('rate', int(velocidad * 150))
                
                self._guardar_config()
                logger.info(f"Velocidad de voz establecida a {velocidad}")
                return True
            else:
                logger.warning(f"Velocidad {velocidad} fuera de rango (0.5-2.0)")
                return False
        except Exception as e:
            logger.error(f"Error al establecer velocidad: {e}")
            return False
    
    def establecer_volumen(self, volumen: float) -> bool:
        """Establece el volumen del motor de voz."""
        if not self.iniciado:
            return False
            
        try:
            if 0.0 <= volumen <= 1.0:  # Rango válido
                self.config['volumen'] = volumen
                
                # Aplicar según motor actual
                if self.motor_actual == MotorVoz.PYTTSX3:
                    self.engine.setProperty('volume', volumen)
                
                self._guardar_config()
                logger.info(f"Volumen de voz establecido a {volumen}")
                return True
            else:
                logger.warning(f"Volumen {volumen} fuera de rango (0.0-1.0)")
                return False
        except Exception as e:
            logger.error(f"Error al establecer volumen: {e}")
            return False
    
    def establecer_tono(self, tono: float) -> bool:
        """Establece el tono de voz."""
        if not self.iniciado:
            return False
            
        try:
            if -10.0 <= tono <= 10.0:  # Rango seguro
                self.config['tono'] = tono
                self._guardar_config()
                logger.info(f"Tono de voz establecido a {tono}")
                return True
            else:
                logger.warning(f"Tono {tono} fuera de rango (-10.0-10.0)")
                return False
        except Exception as e:
            logger.error(f"Error al establecer tono: {e}")
            return False
    
    def cambiar_motor(self, nuevo_motor: str) -> bool:
        """Cambia el motor de síntesis de voz."""
        try:
            # Validar motor solicitado
            if nuevo_motor not in [m.value for m in MotorVoz]:
                logger.error(f"Motor '{nuevo_motor}' no válido")
                return False
            
            # Detener motor actual si está iniciado
            if self.iniciado:
                try:
                    self.detener()
                    
                    # Esperar a que termine el hilo
                    if self.hilo_habla and self.hilo_habla.is_alive():
                        self.hilo_habla.join(timeout=2)
                    
                    # Limpiar recursos específicos
                    if self.motor_actual == MotorVoz.PYTTSX3 and hasattr(self.engine, 'stop'):
                        self.engine.stop()
                    
                    # Limpiar archivos temporales
                    self._limpiar_archivos_temporales()
                    
                    self.iniciado = False
                except Exception as e:
                    logger.warning(f"Error al detener motor actual: {e}")
            
            # Actualizar configuración
            self.config['motor'] = nuevo_motor
            self._guardar_config()
            
            # Iniciar nuevo motor
            resultado = self.iniciar()
            
            if not resultado:
                logger.error(f"No se pudo iniciar el motor {nuevo_motor}")
                # Intentar volver al motor anterior si el nuevo falló
                if hasattr(self, 'motor_actual') and self.motor_actual:
                    self.config['motor'] = self.motor_actual.value
                    self.iniciar()
            
            return resultado
        except Exception as e:
            logger.error(f"Error al cambiar motor: {e}")
            return False
    
    def _limpiar_archivos_temporales(self) -> None:
        """Limpia los archivos temporales creados por el motor de voz."""
        try:
            if os.path.exists(self.temp_dir):
                for archivo in os.listdir(self.temp_dir):
                    try:
                        ruta_completa = os.path.join(self.temp_dir, archivo)
                        if os.path.isfile(ruta_completa):
                            os.remove(ruta_completa)
                    except Exception as e:
                        logger.debug(f"Error al eliminar archivo temporal {archivo}: {e}")
        except Exception as e:
            logger.warning(f"Error al limpiar archivos temporales: {e}")
    
    def seleccionar_voz(self, id_voz: str = None, idioma: str = None, genero: str = None) -> bool:
        """Selecciona una voz específica o según idioma y género."""
        if not self.iniciado:
            return False
            
        try:
            # Si se proporciona ID específico
            if id_voz:
                # Verificar si existe
                voz_existe = False
                for voz in self.voces_disponibles:
                    if voz['id'] == id_voz:
                        voz_existe = True
                        # Actualizar configuración
                        self.config['voz_id'] = id_voz
                        self.config['voz_idioma'] = voz['idioma']
                        self.config['voz_genero'] = voz['genero']
                        break
                
                if not voz_existe:
                    logger.warning(f"Voz {id_voz} no encontrada")
                    return False
            # Si no, buscar por idioma y género
            elif idioma:
                # Establecer valores
                self.config['voz_idioma'] = idioma
                if genero:
                    self.config['voz_genero'] = genero
                
                # Voz se seleccionará automáticamente en _aplicar_configuracion_*
                self.config['voz_id'] = None
            else:
                return False
            
            # Aplicar cambios según motor actual
            if self.motor_actual == MotorVoz.PYTTSX3:
                self._aplicar_configuracion_pyttsx3()
            # Para otros motores, los cambios se aplicarán en la próxima síntesis
            
            self._guardar_config()
            return True
        except Exception as e:
            logger.error(f"Error al seleccionar voz: {e}")
            return False
    
    def listar_voces(self, filtro_idioma: str = None, filtro_motor: str = None) -> List[Dict]:
        """Devuelve lista de voces disponibles con filtros opcionales."""
        if filtro_idioma or filtro_motor:
            voces_filtradas = []
            for voz in self.voces_disponibles:
                if (not filtro_idioma or voz['idioma'] == filtro_idioma) and \
                   (not filtro_motor or voz.get('motor') == filtro_motor):
                    voces_filtradas.append(voz)
            return voces_filtradas
        return self.voces_disponibles
    
    def obtener_configuracion_actual(self) -> Dict:
        """Devuelve la configuración actual del motor de voz."""
        return self.config.copy()
    
    def limpiar_cola(self) -> None:
        """Limpia la cola de mensajes pendientes de síntesis."""
        self.cola_mensajes.clear()
    
    def detener(self) -> bool:
        """Detiene la síntesis de voz actual."""
        if not self.iniciado:
            return False
            
        try:
            if self.motor_actual == MotorVoz.PYTTSX3 and hasattr(self.engine, 'stop'):
                self.engine.stop()
            
            self.hablando = False
            self.limpiar_cola()
            return True
        except Exception as e:
            logger.error(f"Error al detener síntesis de voz: {e}")
            return False
    
    def cerrar(self) -> None:
        """Cierra el motor de síntesis de voz."""
        if self.iniciado:
            try:
                # Limpiar cola de mensajes
                self.limpiar_cola()
                
                # Detener síntesis actual
                self.detener()
                
                # Guardar configuración por última vez
                self._guardar_config()
                
                # Cerrar recursos según motor actual
                if self.motor_actual == MotorVoz.PYTTSX3 and hasattr(self.engine, 'stop'):
                    self.engine.stop()
                
                # Limpiar archivos temporales
                self._limpiar_archivos_temporales()
                
                # Marcar como no iniciado para detener hilo
                self.iniciado = False
                
                # Esperar a que termine el hilo
                if self.hilo_habla and self.hilo_habla.is_alive():
                    self.hilo_habla.join(timeout=2)
                
                logger.info("Motor de síntesis de voz cerrado correctamente.")
            except Exception as e:
                logger.error(f"Error al cerrar motor de síntesis de voz: {e}")
    
    def hablar_sincrono(self, texto: str) -> bool:
        """Sintetiza voz para un texto dado de forma síncrona (bloqueante)."""
        if not self.iniciado:
            logger.warning("Motor de síntesis de voz no iniciado. No se puede hablar.")
            return False
        
        try:
            texto_procesado = self._preprocesar_texto(texto)
            self.hablando = True
            
            # Procesar según el motor activo
            if self.motor_actual == MotorVoz.PYTTSX3:
                self._hablar_pyttsx3(texto_procesado)
            elif self.motor_actual == MotorVoz.GOOGLE_TTS:
                self._hablar_google_tts(texto_procesado)
            elif self.motor_actual == MotorVoz.AZURE_TTS:
                self._hablar_azure_tts(texto_procesado)
            elif self.motor_actual == MotorVoz.OFFLINE_TTS:
                self._hablar_offline_tts(texto_procesado)
                
            self.hablando = False
            return True
        except Exception as e:
            logger.error(f"Error durante síntesis de voz síncrona: {e}")
            self.hablando = False
            return False