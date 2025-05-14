"""
Módulo para añadir emociones y expresividad a la síntesis de voz.
"""

import logging
import random
import time
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger("SistemaKinect.VozEmotiva")

class Emocion(Enum):
    NEUTRAL = "neutral"
    ALEGRE = "alegre"
    EMOCIONADO = "emocionado"
    TRANQUILO = "tranquilo"
    PREOCUPADO = "preocupado"
    SORPRENDIDO = "sorprendido"
    ORGULLOSO = "orgulloso"
    ALENTADOR = "alentador"

class GestorVozEmotiva:
    """Gestiona las emociones y expresividad en la síntesis de voz."""
    
    # Configuración de emociones para cada motor de voz
    CONFIGURACION_EMOCIONES = {
        "google_tts": {
            Emocion.NEUTRAL: {"pitch": 0.0, "speed": 1.0},
            Emocion.ALEGRE: {"pitch": 2.0, "speed": 1.1},
            Emocion.EMOCIONADO: {"pitch": 3.0, "speed": 1.2},
            Emocion.TRANQUILO: {"pitch": -1.0, "speed": 0.9},
            Emocion.PREOCUPADO: {"pitch": -2.0, "speed": 0.95},
            Emocion.SORPRENDIDO: {"pitch": 4.0, "speed": 1.15},
            Emocion.ORGULLOSO: {"pitch": 1.0, "speed": 0.95},
            Emocion.ALENTADOR: {"pitch": 1.5, "speed": 1.05}
        },
        "pyttsx3": {
            Emocion.NEUTRAL: {"pitch": 50, "speed": 150},
            Emocion.ALEGRE: {"pitch": 60, "speed": 165},
            Emocion.EMOCIONADO: {"pitch": 70, "speed": 180},
            Emocion.TRANQUILO: {"pitch": 40, "speed": 135},
            Emocion.PREOCUPADO: {"pitch": 35, "speed": 140},
            Emocion.SORPRENDIDO: {"pitch": 75, "speed": 170},
            Emocion.ORGULLOSO: {"pitch": 55, "speed": 145},
            Emocion.ALENTADOR: {"pitch": 55, "speed": 155}
        }
    }
    
    # Expresiones adicionales para cada emoción
    EXPRESIONES = {
        Emocion.ALEGRE: ["¡Qué bien!", "¡Genial!", "¡Me encanta!", "¡Fantástico!"],
        Emocion.EMOCIONADO: ["¡Wow!", "¡Increíble!", "¡Asombroso!", "¡Espectacular!"],
        Emocion.TRANQUILO: ["Muy bien...", "Perfecto...", "Así es...", "Tranquilo..."],
        Emocion.PREOCUPADO: ["Hmm...", "Oh...", "Vaya...", "Ups..."],
        Emocion.SORPRENDIDO: ["¡Oh!", "¡Vaya!", "¡No esperaba eso!", "¡Sorprendente!"],
        Emocion.ORGULLOSO: ["¡Excelente trabajo!", "¡Muy bien hecho!", "¡Estoy orgulloso!", "¡Impresionante!"],
        Emocion.ALENTADOR: ["¡Tú puedes!", "¡Sigue así!", "¡No te rindas!", "¡Vamos!"]
    }
    
    def __init__(self, voice_engine):
        self.voice_engine = voice_engine
        self.emocion_actual = Emocion.NEUTRAL
        self.intensidad_emocion = 1.0
        self.usar_expresiones = True
        self.historial_emociones = []
    
    def detectar_emocion_contextual(self, contexto: str, texto: str) -> Emocion:
        """Detecta la emoción apropiada según el contexto."""
        # Mapeo de contextos a emociones
        contexto_emocion = {
            "saludo": Emocion.ALEGRE,
            "despedida": Emocion.TRANQUILO,
            "error": Emocion.PREOCUPADO,
            "exito": Emocion.ORGULLOSO,
            "tutorial": Emocion.ALENTADOR,
            "nuevo_trazo": Emocion.ALEGRE,
            "trazo_completado": Emocion.ORGULLOSO,
            "texto_reconocido": Emocion.EMOCIONADO,
            "sin_texto": Emocion.ALENTADOR,
            "guardado": Emocion.ORGULLOSO,
            "modo_dibujo": Emocion.EMOCIONADO,
            "modo_borrador": Emocion.NEUTRAL,
            "boton_hover": Emocion.NEUTRAL
        }
        
        # Buscar palabras clave en el texto para ajustar la emoción
        palabras_emocion = {
            Emocion.EMOCIONADO: ["increíble", "asombroso", "wow", "genial", "fantástico"],
            Emocion.PREOCUPADO: ["error", "problema", "ups", "oh no", "falló"],
            Emocion.ORGULLOSO: ["excelente", "perfecto", "muy bien", "logrado"],
            Emocion.ALENTADOR: ["intenta", "prueba", "vamos", "puedes", "ánimo"]
        }
        
        # Primero revisar el contexto
        emocion = contexto_emocion.get(contexto, Emocion.NEUTRAL)
        
        # Luego ajustar según el texto
        texto_lower = texto.lower()
        for emocion_palabras, palabras in palabras_emocion.items():
            if any(palabra in texto_lower for palabra in palabras):
                emocion = emocion_palabras
                break
        
        return emocion
    
    def aplicar_emocion(self, texto: str, emocion: Emocion, motor: str = "google_tts") -> Tuple[str, Dict]:
        """Aplica la emoción al texto y devuelve el texto modificado y la configuración."""
        # Obtener configuración para la emoción y motor
        config_emocion = self.CONFIGURACION_EMOCIONES.get(motor, {}).get(emocion, {})
        
        # Aplicar intensidad a la configuración
        config_ajustada = {}
        for param, valor in config_emocion.items():
            if param in ["pitch", "speed"]:
                # Ajustar según intensidad (0.5 a 1.5)
                factor = 1 + (self.intensidad_emocion - 1) * 0.5
                config_ajustada[param] = valor * factor if isinstance(valor, float) else int(valor * factor)
        
        # Añadir expresiones si está habilitado
        texto_modificado = texto
        if self.usar_expresiones and emocion in self.EXPRESIONES:
            if random.random() < 0.3:  # 30% de probabilidad
                expresion = random.choice(self.EXPRESIONES[emocion])
                texto_modificado = f"{expresion} {texto}"
        
        # Añadir marcadores SSML para énfasis si es compatible
        if motor == "google_tts" and self.voice_engine.config.get('usar_ssml', True):
            texto_modificado = self._añadir_enfasis_ssml(texto_modificado, emocion)
        
        # Guardar en historial
        self.historial_emociones.append({
            "texto": texto,
            "emocion": emocion,
            "timestamp": time.time()
        })
        
        # Mantener historial limitado
        if len(self.historial_emociones) > 50:
            self.historial_emociones.pop(0)
        
        return texto_modificado, config_ajustada
    
    def _añadir_enfasis_ssml(self, texto: str, emocion: Emocion) -> str:
        """Añade marcadores SSML para énfasis según la emoción."""
        # Palabras a enfatizar según emoción
        palabras_enfasis = {
            Emocion.ALEGRE: ["bien", "genial", "perfecto", "excelente"],
            Emocion.EMOCIONADO: ["increíble", "asombroso", "wow", "fantástico"],
            Emocion.ORGULLOSO: ["excelente", "muy bien", "logrado", "conseguido"],
            Emocion.ALENTADOR: ["puedes", "vamos", "adelante", "sigue"]
        }
        
        palabras = palabras_enfasis.get(emocion, [])
        
        # Aplicar énfasis a palabras clave
        for palabra in palabras:
            if palabra in texto.lower():
                # Buscar la palabra sin importar mayúsculas
                import re
                patron = re.compile(r'\b' + palabra + r'\b', re.IGNORECASE)
                texto = patron.sub(lambda m: f'<emphasis level="strong">{m.group()}</emphasis>', texto)
        
        # Añadir pausas dramáticas según emoción
        if emocion in [Emocion.EMOCIONADO, Emocion.SORPRENDIDO]:
            texto = texto.replace("!", '! <break time="300ms"/>')
        elif emocion == Emocion.TRANQUILO:
            texto = texto.replace(".", '. <break time="500ms"/>')
        
        return texto
    
    def hablar_con_emocion(self, texto: str, contexto: str = "neutral", 
                          emocion_override: Optional[Emocion] = None):
        """Habla con emoción detectada o especificada."""
        # Determinar emoción
        if emocion_override:
            emocion = emocion_override
        else:
            emocion = self.detectar_emocion_contextual(contexto, texto)
        
        # Obtener motor actual
        motor = self.voice_engine.motor_actual.value if hasattr(self.voice_engine, 'motor_actual') else "pyttsx3"
        
        # Aplicar emoción
        texto_modificado, config_voz = self.aplicar_emocion(texto, emocion, motor)
        
        # Guardar configuración actual
        config_original = {
            'velocidad': self.voice_engine.config.get('velocidad', 1.0),
            'tono': self.voice_engine.config.get('tono', 0.0)
        }
        
        try:
            # Aplicar nueva configuración
            if 'speed' in config_voz:
                self.voice_engine.establecer_velocidad(config_voz['speed'])
            if 'pitch' in config_voz:
                self.voice_engine.establecer_tono(config_voz['pitch'])
            
            # Hablar con emoción
            self.voice_engine.hablar(texto_modificado)
            
            # Esperar un momento para que se procese
            time.sleep(0.1)
            
        finally:
            # Restaurar configuración original
            self.voice_engine.establecer_velocidad(config_original['velocidad'])
            self.voice_engine.establecer_tono(config_original['tono'])
    
    def cambiar_intensidad_emocion(self, intensidad: float):
        """Cambia la intensidad de las emociones (0.0 a 2.0)."""
        self.intensidad_emocion = max(0.0, min(2.0, intensidad))
    
    def obtener_estadisticas_emociones(self) -> Dict:
        """Obtiene estadísticas sobre las emociones usadas."""
        if not self.historial_emociones:
            return {}
        
        contadores = {}
        for item in self.historial_emociones:
            emocion = item['emocion']
            contadores[emocion] = contadores.get(emocion, 0) + 1
        
        total = len(self.historial_emociones)
        porcentajes = {
            emocion.value: (count / total * 100) 
            for emocion, count in contadores.items()
        }
        
        return {
            "contadores": contadores,
            "porcentajes": porcentajes,
            "total": total,
            "emocion_mas_usada": max(contadores.items(), key=lambda x: x[1])[0].value if contadores else None
        }