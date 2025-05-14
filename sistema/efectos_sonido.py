"""
Módulo para gestionar efectos de sonido y música de fondo.
"""

import logging
import os
import threading
import time
from typing import Dict, Optional
from enum import Enum
import numpy as np

logger = logging.getLogger("SistemaKinect.EfectosSonido")

# Importación condicional para pygame
try:
    import pygame
    PYGAME_DISPONIBLE = True
except ImportError:
    logger.warning("pygame no está disponible. Efectos de sonido desactivados.")
    PYGAME_DISPONIBLE = False

class TipoEfecto(Enum):
    CLICK = "click"
    HOVER = "hover"
    EXITO = "exito"
    ERROR = "error"
    TRAZO_INICIO = "trazo_inicio"
    TRAZO_FIN = "trazo_fin"
    CAMBIO_MODO = "cambio_modo"
    GUARDADO = "guardado"
    BIENVENIDA = "bienvenida"
    DESPEDIDA = "despedida"

class GestorEfectosSonido:
    """Gestiona efectos de sonido y música de fondo."""
    
    def __init__(self, directorio_sonidos="sonidos"):
        self.directorio_sonidos = directorio_sonidos
        self.efectos_cargados = {}
        self.volumen_efectos = 0.7
        self.volumen_musica = 0.3
        self.musica_activa = False
        self.iniciado = False
        
        # Crear directorio si no existe
        if not os.path.exists(directorio_sonidos):
            try:
                os.makedirs(directorio_sonidos)
                self._generar_efectos_basicos()
            except Exception as e:
                logger.error(f"Error al crear directorio de sonidos: {e}")
        
        # Inicializar pygame mixer
        if PYGAME_DISPONIBLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.iniciado = True
                self._cargar_efectos()
            except Exception as e:
                logger.error(f"Error al inicializar pygame mixer: {e}")
                self.iniciado = False
    
    def _generar_efectos_basicos(self):
        """Genera efectos de sonido básicos usando síntesis."""
        if not self.iniciado:
            return
        
        try:
            # Generar click
            self._generar_tono("click.wav", 3000, 0.1, fade_out=True)
            
            # Generar hover
            self._generar_tono("hover.wav", 1500, 0.15, fade_in=True)
            
            # Generar éxito
            self._generar_melodia("exito.wav", [523, 659, 784], [0.2, 0.2, 0.3])
            
            # Generar error
            self._generar_melodia("error.wav", [200, 150], [0.2, 0.3])
            
            # Generar inicio de trazo
            self._generar_tono("trazo_inicio.wav", 2000, 0.2, fade_in=True)
            
            # Generar fin de trazo
            self._generar_tono("trazo_fin.wav", 1000, 0.2, fade_out=True)
            
            # Generar cambio de modo
            self._generar_melodia("cambio_modo.wav", [440, 523], [0.15, 0.15])
            
            # Generar guardado
            self._generar_melodia("guardado.wav", [659, 784, 880], [0.1, 0.1, 0.2])
            
            # Generar bienvenida
            self._generar_melodia("bienvenida.wav", [261, 329, 392, 523], [0.2, 0.2, 0.2, 0.4])
            
            # Generar despedida
            self._generar_melodia("despedida.wav", [523, 392, 329, 261], [0.2, 0.2, 0.2, 0.4])
            
        except Exception as e:
            logger.error(f"Error al generar efectos básicos: {e}")
    
    def _generar_tono(self, nombre_archivo: str, frecuencia: float, duracion: float, 
                     fade_in: bool = False, fade_out: bool = False):
        """Genera un tono simple con fade in/out opcionales."""
        try:
            sample_rate = 22050
            samples = int(sample_rate * duracion)
            
            # Generar onda sinusoidal
            t = np.linspace(0, duracion, samples)
            wave = 0.3 * np.sin(2 * np.pi * frecuencia * t)
            
            # Aplicar fade in
            if fade_in:
                fade_samples = int(samples * 0.1)
                for i in range(fade_samples):
                    wave[i] *= i / fade_samples
            
            # Aplicar fade out
            if fade_out:
                fade_samples = int(samples * 0.1)
                for i in range(fade_samples):
                    wave[-(i+1)] *= i / fade_samples
            
            # Guardar como WAV
            self._guardar_wav(nombre_archivo, wave, sample_rate)
            
        except Exception as e:
            logger.error(f"Error al generar tono {nombre_archivo}: {e}")
    
    def _generar_melodia(self, nombre_archivo: str, frecuencias: list, duraciones: list):
        """Genera una melodía simple combinando varios tonos."""
        try:
            sample_rate = 22050
            wave_final = np.array([])
            
            for freq, dur in zip(frecuencias, duraciones):
                samples = int(sample_rate * dur)
                t = np.linspace(0, dur, samples)
                wave = 0.3 * np.sin(2 * np.pi * freq * t)
                
                # Aplicar fade in/out para suavizar
                fade_samples = int(samples * 0.05)
                for i in range(fade_samples):
                    wave[i] *= i / fade_samples
                    wave[-(i+1)] *= i / fade_samples
                
                wave_final = np.concatenate([wave_final, wave])
            
            # Guardar como WAV
            self._guardar_wav(nombre_archivo, wave_final, sample_rate)
            
        except Exception as e:
            logger.error(f"Error al generar melodía {nombre_archivo}: {e}")
    
    def _guardar_wav(self, nombre_archivo: str, wave: np.ndarray, sample_rate: int):
        """Guarda un array numpy como archivo WAV."""
        try:
            # Convertir a 16 bits
            wave = (wave * 32767).astype(np.int16)
            
            # Crear cabecera WAV
            import struct
            with open(os.path.join(self.directorio_sonidos, nombre_archivo), 'wb') as f:
                # Escribir cabecera RIFF
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(wave) * 2))
                f.write(b'WAVE')
                
                # Escribir formato
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))  # Tamaño del chunk fmt
                f.write(struct.pack('<H', 1))   # Formato PCM
                f.write(struct.pack('<H', 1))   # Canales mono
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))   # Block align
                f.write(struct.pack('<H', 16))  # Bits por muestra
                
                # Escribir datos
                f.write(b'data')
                f.write(struct.pack('<I', len(wave) * 2))
                f.write(wave.tobytes())
                
        except Exception as e:
            logger.error(f"Error al guardar WAV {nombre_archivo}: {e}")
    
    def _cargar_efectos(self):
        """Carga todos los efectos de sonido disponibles."""
        if not self.iniciado:
            return
        
        try:
            archivos_efectos = {
                TipoEfecto.CLICK: "click.wav",
                TipoEfecto.HOVER: "hover.wav",
                TipoEfecto.EXITO: "exito.wav",
                TipoEfecto.ERROR: "error.wav",
                TipoEfecto.TRAZO_INICIO: "trazo_inicio.wav",
                TipoEfecto.TRAZO_FIN: "trazo_fin.wav",
                TipoEfecto.CAMBIO_MODO: "cambio_modo.wav",
                TipoEfecto.GUARDADO: "guardado.wav",
                TipoEfecto.BIENVENIDA: "bienvenida.wav",
                TipoEfecto.DESPEDIDA: "despedida.wav"
            }
            
            for tipo_efecto, archivo in archivos_efectos.items():
                ruta_completa = os.path.join(self.directorio_sonidos, archivo)
                if os.path.exists(ruta_completa):
                    try:
                        self.efectos_cargados[tipo_efecto] = pygame.mixer.Sound(ruta_completa)
                    except Exception as e:
                        logger.warning(f"No se pudo cargar {archivo}: {e}")
                        
        except Exception as e:
            logger.error(f"Error al cargar efectos: {e}")
    
    def reproducir_efecto(self, tipo_efecto: TipoEfecto, volumen_override: Optional[float] = None):
        """Reproduce un efecto de sonido."""
        if not self.iniciado or tipo_efecto not in self.efectos_cargados:
            return
        
        try:
            efecto = self.efectos_cargados[tipo_efecto]
            volumen = volumen_override if volumen_override is not None else self.volumen_efectos
            efecto.set_volume(volumen)
            efecto.play()
        except Exception as e:
            logger.error(f"Error al reproducir efecto {tipo_efecto}: {e}")
    
    def reproducir_musica_fondo(self, archivo_musica: str = "musica_fondo.mp3", loop: bool = True):
        """Reproduce música de fondo."""
        if not self.iniciado:
            return
        
        try:
            ruta_musica = os.path.join(self.directorio_sonidos, archivo_musica)
            if not os.path.exists(ruta_musica):
                self._generar_musica_fondo_basica(archivo_musica)
            
            if os.path.exists(ruta_musica):
                pygame.mixer.music.load(ruta_musica)
                pygame.mixer.music.set_volume(self.volumen_musica)
                pygame.mixer.music.play(-1 if loop else 0)
                self.musica_activa = True
                
        except Exception as e:
            logger.error(f"Error al reproducir música de fondo: {e}")
    
    def _generar_musica_fondo_basica(self, nombre_archivo: str):
        """Genera una música de fondo básica procedural."""
        try:
            sample_rate = 22050
            duracion = 30  # 30 segundos
            samples = int(sample_rate * duracion)
            
            # Crear una melodía ambiente simple
            t = np.linspace(0, duracion, samples)
            
            # Frecuencias base para acordes
            acordes = [
                [261.63, 329.63, 392.00],  # C mayor
                [220.00, 277.18, 329.63],  # A menor
                [196.00, 246.94, 293.66],  # G mayor
                [174.61, 220.00, 261.63]   # F mayor
            ]
            
            wave_final = np.zeros(samples)
            
            # Crear patrón de acordes
            for i, acorde in enumerate(acordes):
                start = int(i * samples / 4)
                end = int((i + 1) * samples / 4)
                t_segmento = t[start:end]
                
                for freq in acorde:
                    # Añadir cada nota del acorde con volumen reducido
                    wave_segmento = 0.05 * np.sin(2 * np.pi * freq * (t_segmento - t_segmento[0]))
                    
                    # Aplicar envolvente
                    fade_samples = int(0.1 * len(wave_segmento))
                    for j in range(fade_samples):
                        wave_segmento[j] *= j / fade_samples
                        wave_segmento[-(j+1)] *= j / fade_samples
                    
                    wave_final[start:end] += wave_segmento
            
            # Añadir un poco de reverb básico
            delay_samples = int(0.5 * sample_rate)
            wave_reverb = np.zeros_like(wave_final)
            wave_reverb[delay_samples:] = 0.3 * wave_final[:-delay_samples]
            wave_final += wave_reverb
            
            # Normalizar
            wave_final = wave_final / np.max(np.abs(wave_final)) * 0.5
            
            # Guardar como WAV (luego se puede convertir a MP3)
            self._guardar_wav(nombre_archivo.replace('.mp3', '.wav'), wave_final, sample_rate)
            
        except Exception as e:
            logger.error(f"Error al generar música de fondo: {e}")
    
    def pausar_musica(self):
        """Pausa la música de fondo."""
        if self.iniciado and self.musica_activa:
            pygame.mixer.music.pause()
    
    def reanudar_musica(self):
        """Reanuda la música de fondo."""
        if self.iniciado and self.musica_activa:
            pygame.mixer.music.unpause()
    
    def detener_musica(self):
        """Detiene la música de fondo."""
        if self.iniciado and self.musica_activa:
            pygame.mixer.music.stop()
            self.musica_activa = False
    
    def ajustar_volumen_efectos(self, volumen: float):
        """Ajusta el volumen de los efectos de sonido."""
        self.volumen_efectos = max(0.0, min(1.0, volumen))
    
    def ajustar_volumen_musica(self, volumen: float):
        """Ajusta el volumen de la música de fondo."""
        self.volumen_musica = max(0.0, min(1.0, volumen))
        if self.iniciado and self.musica_activa:
            pygame.mixer.music.set_volume(self.volumen_musica)
    
    def fade_out_musica(self, tiempo_ms: int = 2000):
        """Aplica fade out a la música de fondo."""
        if self.iniciado and self.musica_activa:
            pygame.mixer.music.fadeout(tiempo_ms)
            self.musica_activa = False
    
    def cerrar(self):
        """Cierra el gestor de efectos de sonido."""
        if self.iniciado:
            self.detener_musica()
            pygame.mixer.quit()
            self.iniciado = False