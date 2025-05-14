"""
Módulo de asistente virtual con personalidad para el sistema interactivo.
"""

import logging
import random
import json
import os
from typing import Dict, List, Optional
from enum import Enum
import time

from .efectos_sonido import GestorEfectosSonido, TipoEfecto
from .voz_emotiva import GestorVozEmotiva, Emocion

logger = logging.getLogger("SistemaKinect.AsistenteVirtual")

class NivelVerbosidad(Enum):
    SILENCIOSO = 0
    MINIMO = 1
    NORMAL = 2
    DETALLADO = 3
    MAXIMO = 4

class PersonalidadAsistente(Enum):
    PROFESIONAL = "profesional"
    AMIGABLE = "amigable"
    INFANTIL = "infantil"
    TUTORIAL = "tutorial"
    ARTISTA = "artista"
    MOTIVADOR = "motivador"

class AsistenteVirtual:
    """Gestiona un asistente virtual con personalidad para el sistema."""
    
    # Frases predefinidas para diferentes situaciones
    FRASES = {
        "saludo_inicial": {
            "profesional": ["Bienvenido al Sistema Interactivo con Kinect. Estoy listo para asistirle."],
            "amigable": ["¡Hola! Bienvenido al Sistema Interactivo. Estoy aquí para ayudarte."],
            "infantil": ["¡Hola amiguito! ¡Vamos a divertirnos dibujando juntos!"],
            "tutorial": ["Bienvenido. Soy tu guía para aprender a usar este sistema paso a paso."],
            "artista": ["¡Bienvenido al lienzo digital! Vamos a crear arte juntos."],
            "motivador": ["¡Hola campeón! Hoy vamos a crear algo increíble juntos."]
        },
        "modo_dibujo": {
            "profesional": ["Modo de dibujo activado. Use el dedo índice para crear trazos."],
            "amigable": ["¡Perfecto! Ahora puedes dibujar con tu dedo índice. ¡Diviértete!"],
            "infantil": ["¡Genial! ¡Ahora puedes hacer dibujitos con tu dedito!"],
            "tutorial": ["Has activado el modo dibujo. Extiende solo tu dedo índice para empezar a dibujar."],
            "artista": ["¡El lienzo está listo! Deja fluir tu creatividad."],
            "motivador": ["¡Excelente elección! Es momento de mostrar tu talento."]
        },
        "modo_borrador": {
            "profesional": ["Modo borrador activado. Use cualquier parte de la mano para borrar."],
            "amigable": ["Ahora puedes borrar lo que quieras. Usa tu mano como un borrador."],
            "infantil": ["¡Modo borrador! Puedes borrar todo lo que no te guste."],
            "tutorial": ["El modo borrador está activo. Mueve tu mano sobre lo que quieras borrar."],
            "artista": ["Modo borrador listo. A veces hay que borrar para crear."],
            "motivador": ["¡Modo borrador activado! No hay errores, solo oportunidades de mejorar."]
        },
        "trazo_iniciado": {
            "profesional": ["Trazo iniciado."],
            "amigable": ["¡Bien! Has empezado un nuevo trazo."],
            "infantil": ["¡Mira! ¡Estás dibujando!"],
            "tutorial": ["Has iniciado un trazo. Mantén el dedo extendido mientras dibujas."],
            "artista": ["Nuevo trazo iniciado. Déjate llevar."],
            "motivador": ["¡Excelente! ¡Sigue así!"]
        },
        "trazo_completado": {
            "profesional": ["Trazo completado."],
            "amigable": ["¡Excelente trazo! Se ve muy bien."],
            "infantil": ["¡Qué bonito! ¡Me gusta tu dibujo!"],
            "tutorial": ["Trazo completado. Cierra el puño para dejar de dibujar."],
            "artista": ["Hermoso trazo. Cada línea cuenta una historia."],
            "motivador": ["¡Perfecto! ¡Cada trazo es una victoria!"]
        },
        "comentarios_dibujo": {
            "profesional": ["Trazo preciso.", "Buena técnica.", "Línea bien ejecutada."],
            "amigable": ["¡Se ve genial!", "¡Me gusta cómo va quedando!", "¡Qué bonito trazo!"],
            "infantil": ["¡Qué lindo!", "¡Me encanta tu dibujo!", "¡Está quedando súper bonito!"],
            "artista": ["Interesante composición.", "Me gusta tu estilo.", "Veo potencial artístico aquí."],
            "motivador": ["¡Así se hace!", "¡Sigue así, campeón!", "¡Cada trazo es mejor que el anterior!"]
        },
        "guardando": {
            "profesional": ["Guardando y procesando el dibujo..."],
            "amigable": ["Guardando tu obra de arte... Un momento por favor."],
            "infantil": ["¡Estoy guardando tu dibujo! ¡Espera un poquito!"],
            "tutorial": ["Ahora voy a guardar tu dibujo y reconocer el texto si hay alguno."],
            "artista": ["Preservando tu creación para la posteridad..."],
            "motivador": ["¡Guardando tu increíble trabajo!"]
        },
        "texto_reconocido": {
            "profesional": ["Texto reconocido exitosamente: {}"],
            "amigable": ["¡Genial! He reconocido este texto: {}"],
            "infantil": ["¡Mira! ¡He leído esto: {}"],
            "tutorial": ["He reconocido el siguiente texto en tu dibujo: {}"],
            "artista": ["Las palabras en tu arte dicen: {}"],
            "motivador": ["¡Increíble! Has escrito: {}"]
        },
        "sin_texto": {
            "profesional": ["No se detectó texto en el dibujo."],
            "amigable": ["No encontré texto en tu dibujo, pero se ve muy bien."],
            "infantil": ["¡Tu dibujo está muy bonito! No veo palabritas."],
            "tutorial": ["No se detectó texto. Si esperabas reconocimiento de texto, intenta escribir más grande."],
            "artista": ["Una imagen vale más que mil palabras. No hay texto, pero hay arte."],
            "motivador": ["¡Tu dibujo es perfecto tal como está!"]
        },
        "boton_hover": {
            "profesional": ["Sobre botón: {}"],
            "amigable": ["Estás sobre el botón: {}"],
            "infantil": ["¡Mira! El botón de {}"],
            "tutorial": ["Tu mano está sobre el botón {}. Cierra el puño para seleccionarlo."],
            "artista": ["Opción disponible: {}"],
            "motivador": ["¡Puedes elegir: {}!"]
        },
        "estadisticas": {
            "profesional": ["Has completado {} trazos. Tiempo de sesión: {} minutos."],
            "amigable": ["Llevas {} trazos. ¡Has estado dibujando {} minutos!"],
            "infantil": ["¡Ya hiciste {} rayitas! Llevas {} minutitos dibujando."],
            "artista": ["Tu obra tiene {} trazos. Has estado creando durante {} minutos."],
            "motivador": ["¡{} trazos completados! ¡Llevas {} minutos siendo increíble!"]
        },
        "despedida": {
            "profesional": ["Cerrando sistema. Gracias por usar nuestro servicio."],
            "amigable": ["¡Hasta luego! ¡Fue un placer ayudarte!"],
            "infantil": ["¡Adiós amiguito! ¡Vuelve pronto a dibujar!"],
            "tutorial": ["Sesión finalizada. Espero que hayas aprendido algo nuevo. ¡Hasta pronto!"],
            "artista": ["El arte nunca termina. Hasta la próxima sesión creativa."],
            "motivador": ["¡Has sido increíble! ¡Nos vemos pronto, campeón!"]
        },
        "consejo_aleatorio": [
            "Recuerda que solo necesitas extender el dedo índice para dibujar.",
            "Prueba diferentes colores usando la paleta de colores.",
            "Puedes cambiar el grosor del trazo en la configuración.",
            "El modo borrador te permite corregir errores fácilmente.",
            "Guarda tu sesión regularmente para no perder tu trabajo.",
            "Intenta escribir letras grandes para mejor reconocimiento.",
            "Puedes usar gestos para controlar todo sin tocar nada.",
            "El sistema detecta automáticamente tu mano robótica."
        ],
        "error_general": {
            "profesional": ["Ha ocurrido un error. Por favor, inténtelo de nuevo."],
            "amigable": ["Ups, algo salió mal. ¿Intentamos otra vez?"],
            "infantil": ["¡Ay! Algo no funcionó. ¡Intentemos de nuevo!"],
            "tutorial": ["Se produjo un error. Esto puede pasar a veces. Intenta repetir la acción."],
            "artista": ["A veces el arte es impredecible. Intentemos de nuevo."],
            "motivador": ["¡No pasa nada! Los errores son oportunidades de aprender."]
        }
    }
    
    def __init__(self, voice_engine, config_path="configuracion_asistente.json"):
        self.voice_engine = voice_engine
        self.config_path = config_path
        self.config = self._cargar_config()
        
        # Estado del asistente
        self.personalidad = PersonalidadAsistente(self.config.get("personalidad", "amigable"))
        self.nivel_verbosidad = NivelVerbosidad(self.config.get("nivel_verbosidad", 2))
        self.activo = self.config.get("activo", True)
        self.historial_frases = []
        self.ultima_accion = None
        self.contador_consejos = 0
        self.modo_tutorial = self.config.get("modo_tutorial", False)
        
        # Configuraciones específicas
        self.repetir_instrucciones = self.config.get("repetir_instrucciones", True)
        self.tiempo_entre_consejos = self.config.get("tiempo_entre_consejos", 60)
        self.volumen_efectos = self.config.get("volumen_efectos", 0.8)
        self.usar_efectos_sonido = self.config.get("usar_efectos_sonido", True)
        self.usar_musica_fondo = self.config.get("usar_musica_fondo", True)
        self.usar_voz_emotiva = self.config.get("usar_voz_emotiva", True)
        
        # Inicializar gestores adicionales
        self.gestor_efectos = GestorEfectosSonido()
        self.gestor_voz_emotiva = GestorVozEmotiva(voice_engine)
        
        # Estadísticas de la sesión
        self.estadisticas = {
            "trazos_completados": 0,
            "tiempo_inicio": time.time(),
            "colores_usados": set(),
            "modos_usados": set(),
            "palabras_reconocidas": []
        }
        
        # Iniciar música de fondo si está habilitada
        if self.usar_musica_fondo and self.gestor_efectos.iniciado:
            self.gestor_efectos.reproducir_musica_fondo()
        
        logger.info(f"Asistente virtual iniciado con personalidad: {self.personalidad.value}")
    
    def _cargar_config(self) -> Dict:
        """Carga la configuración del asistente desde archivo."""
        config_default = {
            "personalidad": "amigable",
            "nivel_verbosidad": 2,
            "activo": True,
            "modo_tutorial": False,
            "repetir_instrucciones": True,
            "tiempo_entre_consejos": 60,
            "volumen_efectos": 0.8,
            "usar_efectos_sonido": True,
            "usar_musica_fondo": True,
            "usar_voz_emotiva": True
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return {**config_default, **config}
            return config_default
        except Exception as e:
            logger.error(f"Error al cargar configuración del asistente: {e}")
            return config_default
    
    def _guardar_config(self) -> None:
        """Guarda la configuración actual del asistente."""
        try:
            config = {
                "personalidad": self.personalidad.value,
                "nivel_verbosidad": self.nivel_verbosidad.value,
                "activo": self.activo,
                "modo_tutorial": self.modo_tutorial,
                "repetir_instrucciones": self.repetir_instrucciones,
                "tiempo_entre_consejos": self.tiempo_entre_consejos,
                "volumen_efectos": self.volumen_efectos,
                "usar_efectos_sonido": self.usar_efectos_sonido,
                "usar_musica_fondo": self.usar_musica_fondo,
                "usar_voz_emotiva": self.usar_voz_emotiva
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Error al guardar configuración del asistente: {e}")
    
    def _obtener_frase(self, categoria: str, subcategoria: Optional[str] = None, 
                     formato_args: Optional[List] = None) -> str:
        """Obtiene una frase según la categoría y personalidad."""
        if categoria in self.FRASES:
            if isinstance(self.FRASES[categoria], dict):
                frases = self.FRASES[categoria].get(self.personalidad.value, 
                        self.FRASES[categoria].get("amigable", ["Mensaje no disponible"]))
            else:
                frases = self.FRASES[categoria]
            
            if frases:
                frase = random.choice(frases) if len(frases) > 1 else frases[0]
                
                # Formatear la frase si hay argumentos
                if formato_args:
                    try:
                        frase = frase.format(*formato_args)
                    except:
                        pass
                
                return frase
        
        return "Mensaje no disponible"
    
    def _deberia_hablar(self, prioridad: int = 2) -> bool:
        """Determina si el asistente debería hablar según la verbosidad."""
        return self.activo and prioridad >= (4 - self.nivel_verbosidad.value)
    
    def hablar(self, mensaje: str, prioridad: int = 2, categoria: Optional[str] = None, 
              emocion: Optional[Emocion] = None) -> None:
        """Hace que el asistente hable si corresponde según la configuración."""
        if not self._deberia_hablar(prioridad):
            return
        
        try:
            # Reproducir efecto de sonido asociado
            if self.usar_efectos_sonido and categoria:
                self._reproducir_efecto_categoria(categoria)
            
            # Aplicar voz emotiva si está habilitada
            if self.usar_voz_emotiva and self.gestor_voz_emotiva:
                self.gestor_voz_emotiva.hablar_con_emocion(mensaje, contexto=categoria, 
                                                         emocion_override=emocion)
            else:
                # Hablar normalmente
                self.voice_engine.hablar(mensaje, prioridad=(prioridad >= 3))
            
            # Registrar en historial
            self.historial_frases.append({
                "mensaje": mensaje,
                "categoria": categoria,
                "timestamp": time.time()
            })
            
            # Mantener historial limitado
            if len(self.historial_frases) > 100:
                self.historial_frases.pop(0)
                
        except Exception as e:
            logger.error(f"Error al hacer hablar al asistente: {e}")
    
    def _reproducir_efecto_categoria(self, categoria: str):
        """Reproduce el efecto de sonido asociado a una categoría."""
        efectos_categoria = {
            "saludo": TipoEfecto.BIENVENIDA,
            "despedida": TipoEfecto.DESPEDIDA,
            "modo": TipoEfecto.CAMBIO_MODO,
            "navegacion": TipoEfecto.HOVER,
            "accion": TipoEfecto.CLICK,
            "trazo_inicio": TipoEfecto.TRAZO_INICIO,
            "trazo_fin": TipoEfecto.TRAZO_FIN,
            "guardado": TipoEfecto.GUARDADO,
            "error": TipoEfecto.ERROR,
            "exito": TipoEfecto.EXITO
        }
        
        if categoria in efectos_categoria:
            self.gestor_efectos.reproducir_efecto(efectos_categoria[categoria])
    
    def saludar(self) -> None:
        """Saludo inicial del asistente."""
        frase = self._obtener_frase("saludo_inicial")
        
        # Reproducir melodía de bienvenida primero
        if self.usar_efectos_sonido:
            self.gestor_efectos.reproducir_efecto(TipoEfecto.BIENVENIDA)
            time.sleep(1)  # Esperar a que termine la melodía
        
        self.hablar(frase, prioridad=3, categoria="saludo", emocion=Emocion.ALEGRE)
        
        # En modo tutorial, agregar instrucción inicial
        if self.modo_tutorial:
            time.sleep(2)
            self.hablar("Empecemos seleccionando el botón 'Dibujar' con un puño cerrado.", 
                       prioridad=3, categoria="tutorial", emocion=Emocion.ALENTADOR)
    
    def despedir(self) -> None:
        """Despedida del asistente con estadísticas de la sesión."""
        # Calcular estadísticas finales
        tiempo_sesion = int((time.time() - self.estadisticas["tiempo_inicio"]) / 60)
        trazos = self.estadisticas["trazos_completados"]
        
        # Mensaje personalizado según personalidad
        formato_args = [trazos, tiempo_sesion]
        mensaje_stats = self._obtener_frase("estadisticas", formato_args=formato_args)
        
        # Compartir estadísticas
        self.hablar(mensaje_stats, prioridad=3, categoria="estadisticas", emocion=Emocion.ORGULLOSO)
        time.sleep(2)
        
        # Despedida final
        frase = self._obtener_frase("despedida")
        
        # Fade out de música si está activa
        if self.usar_musica_fondo and self.gestor_efectos.musica_activa:
            self.gestor_efectos.fade_out_musica()
        
        self.hablar(frase, prioridad=3, categoria="despedida", emocion=Emocion.TRANQUILO)
        
        # Efecto de despedida
        if self.usar_efectos_sonido:
            time.sleep(1)
            self.gestor_efectos.reproducir_efecto(TipoEfecto.DESPEDIDA)
    
    def anunciar_modo(self, modo: str) -> None:
        """Anuncia el cambio de modo con efectos."""
        if modo == "dibujar":
            frase = self._obtener_frase("modo_dibujo")
            emocion = Emocion.EMOCIONADO
        elif modo == "borrar":
            frase = self._obtener_frase("modo_borrador") 
            emocion = Emocion.NEUTRAL
        else:
            frase = f"Modo {modo} activado."
            emocion = Emocion.NEUTRAL
        
        self.hablar(frase, prioridad=2, categoria="modo", emocion=emocion)
        self.ultima_accion = f"modo_{modo}"
        
        # Actualizar estadísticas
        self.estadisticas["modos_usados"].add(modo)
    
    def anunciar_trazo(self, evento: str) -> None:
        """Anuncia eventos relacionados con trazos."""
        if evento == "inicio":
            frase = self._obtener_frase("trazo_iniciado")
            self.hablar(frase, prioridad=1, categoria="trazo_inicio", emocion=Emocion.ALEGRE)
        elif evento == "fin":
            self.estadisticas["trazos_completados"] += 1
            
            # Dar comentarios ocasionales sobre el dibujo
            if self.estadisticas["trazos_completados"] % 5 == 0:  # Cada 5 trazos
                comentario = random.choice(self._obtener_frase("comentarios_dibujo"))
                self.hablar(comentario, prioridad=1, categoria="comentario", emocion=Emocion.ORGULLOSO)
            
            frase = self._obtener_frase("trazo_completado")
            self.hablar(frase, prioridad=1, categoria="trazo_fin", emocion=Emocion.NEUTRAL)
    
    def anunciar_boton_hover(self, nombre_boton: str) -> None:
        """Anuncia cuando el cursor está sobre un botón."""
        if self.ultima_accion != f"hover_{nombre_boton}":
            frase = self._obtener_frase("boton_hover", formato_args=[nombre_boton])
            self.hablar(frase, prioridad=1, categoria="navegacion")
            self.ultima_accion = f"hover_{nombre_boton}"
    
    def anunciar_guardado(self) -> None:
        """Anuncia el proceso de guardado."""
        frase = self._obtener_frase("guardando")
        self.hablar(frase, prioridad=2, categoria="sistema")
    
    def anunciar_texto_reconocido(self, texto: Optional[str]) -> None:
        """Anuncia el resultado del reconocimiento de texto."""
        if texto:
            # Actualizar estadísticas
            self.estadisticas["palabras_reconocidas"].append(texto)
            
            frase = self._obtener_frase("texto_reconocido", formato_args=[texto])
            emocion = Emocion.EMOCIONADO
        else:
            frase = self._obtener_frase("sin_texto")
            emocion = Emocion.ALENTADOR
        
        self.hablar(frase, prioridad=3, categoria="resultado", emocion=emocion)
    
    def dar_consejo_aleatorio(self) -> None:
        """Da un consejo aleatorio al usuario."""
        self.contador_consejos += 1
        
        if self.contador_consejos % 5 == 0:  # Cada 5 consejos
            consejo = random.choice(self._obtener_frase("consejo_aleatorio"))
            self.hablar(consejo, prioridad=1, categoria="consejo")
    
    def anunciar_error(self, tipo_error: Optional[str] = None) -> None:
        """Anuncia un error al usuario."""
        frase = self._obtener_frase("error_general")
        self.hablar(frase, prioridad=3, categoria="error")
    
    def cambiar_personalidad(self, nueva_personalidad: str) -> bool:
        """Cambia la personalidad del asistente."""
        try:
            self.personalidad = PersonalidadAsistente(nueva_personalidad)
            self.config["personalidad"] = nueva_personalidad
            self._guardar_config()
            self.hablar(f"Personalidad cambiada a {nueva_personalidad}", 
                       prioridad=2, categoria="configuracion")
            return True
        except ValueError:
            return False
    
    def cambiar_verbosidad(self, nivel: int) -> bool:
        """Cambia el nivel de verbosidad del asistente."""
        try:
            self.nivel_verbosidad = NivelVerbosidad(nivel)
            self.config["nivel_verbosidad"] = nivel
            self._guardar_config()
            
            nombres_niveles = {
                0: "silencioso",
                1: "mínimo",
                2: "normal",
                3: "detallado",
                4: "máximo"
            }
            
            self.hablar(f"Nivel de verbosidad cambiado a {nombres_niveles.get(nivel, 'desconocido')}", 
                       prioridad=2, categoria="configuracion")
            return True
        except ValueError:
            return False
    
    def activar_modo_tutorial(self, activar: bool = True) -> None:
        """Activa o desactiva el modo tutorial."""
        self.modo_tutorial = activar
        self.config["modo_tutorial"] = activar
        self._guardar_config()
        
        if activar:
            self.hablar("Modo tutorial activado. Te guiaré paso a paso.", 
                       prioridad=3, categoria="configuracion")
        else:
            self.hablar("Modo tutorial desactivado.", 
                       prioridad=2, categoria="configuracion")
    
    def activar_desactivar(self, activar: bool = True) -> None:
        """Activa o desactiva el asistente completamente."""
        self.activo = activar
        self.config["activo"] = activar
        self._guardar_config()
        
        if activar:
            self.hablar("Asistente de voz activado.", prioridad=3, categoria="sistema")
        # Si se desactiva, no habla (porque está desactivado)
    
    def dar_estadisticas_periodicas(self) -> None:
        """Da estadísticas periódicas sobre la sesión."""
        tiempo_actual = time.time()
        tiempo_sesion = int((tiempo_actual - self.estadisticas["tiempo_inicio"]) / 60)
        
        # Cada 5 minutos
        if tiempo_sesion > 0 and tiempo_sesion % 5 == 0:
            trazos = self.estadisticas["trazos_completados"]
            frase = self._obtener_frase("estadisticas", 
                                       formato_args=[trazos, tiempo_sesion])
            self.hablar(frase, prioridad=1, categoria="estadisticas", 
                       emocion=Emocion.ORGULLOSO)
    
    def cambiar_configuracion_sonido(self, usar_efectos: bool = None, 
                                   usar_musica: bool = None,
                                   usar_voz_emotiva: bool = None) -> None:
        """Cambia la configuración de sonido del asistente."""
        if usar_efectos is not None:
            self.usar_efectos_sonido = usar_efectos
            
        if usar_musica is not None:
            self.usar_musica_fondo = usar_musica
            if usar_musica and not self.gestor_efectos.musica_activa:
                self.gestor_efectos.reproducir_musica_fondo()
            elif not usar_musica and self.gestor_efectos.musica_activa:
                self.gestor_efectos.detener_musica()
        
        if usar_voz_emotiva is not None:
            self.usar_voz_emotiva = usar_voz_emotiva
        
        self._guardar_config()
        self.hablar("Configuración de sonido actualizada", prioridad=2, 
                   categoria="configuracion")
    
    def ajustar_volumenes(self, volumen_efectos: Optional[float] = None,
                         volumen_musica: Optional[float] = None) -> None:
        """Ajusta los volúmenes del sistema."""
        if volumen_efectos is not None:
            self.volumen_efectos = volumen_efectos
            self.gestor_efectos.ajustar_volumen_efectos(volumen_efectos)
        
        if volumen_musica is not None:
            self.gestor_efectos.ajustar_volumen_musica(volumen_musica)
        
        self._guardar_config()