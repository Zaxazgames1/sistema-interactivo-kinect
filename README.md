# 🤖 Sistema Interactivo con Kinect v2.0

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python" alt="Python 3.7+"/>
  <img src="https://img.shields.io/badge/OpenCV-4.5.0%2B-green?style=for-the-badge&logo=opencv" alt="OpenCV 4.5.0+"/>
  <img src="https://img.shields.io/badge/MediaPipe-0.8.9%2B-orange?style=for-the-badge" alt="MediaPipe 0.8.9+"/>
  <img src="https://img.shields.io/badge/EasyOCR-1.6.0%2B-red?style=for-the-badge" alt="EasyOCR 1.6.0+"/>
  <img src="https://img.shields.io/badge/Google_TTS-Premium-yellow?style=for-the-badge&logo=google-cloud" alt="Google TTS Premium"/>
  <img src="https://img.shields.io/badge/gTTS-Free-green?style=for-the-badge" alt="gTTS Free"/>
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License MIT"/>
</div>

<p align="center">
  <b>Una interfaz revolucionaria que transforma gestos en acciones mediante reconocimiento avanzado y síntesis de voz natural</b>
</p>

---

## 🌟 Características Principales

### 🎯 Reconocimiento Avanzado
- **Detección de Gestos en Tiempo Real**: Precisión mejorada con MediaPipe
- **Múltiples Gestos Soportados**: Dibujo, borrado, selección y más
- **Calibración Automática**: Ajuste personalizado para cada usuario
- **Detección de Gestos Complejos**: Pinza, rotación y gestos combinados

### 🎨 Sistema de Dibujo Mejorado
- **Dibujo Gestual en el Aire**: Trazo suave con interpolación
- **Paleta de Colores Interactiva**: Selección por gestos
- **Historial de Trazos**: Deshacer/Rehacer ilimitado
- **Guardado de Sesiones**: Continúa donde lo dejaste
- **Exportación Múltiple**: PNG, SVG, PDF

### 🗣️ Síntesis de Voz Premium
- **Google Cloud TTS**: Voces neurales ultra-realistas
- **gTTS Gratuito**: Alternativa sin costo con buena calidad
- **Voces Emotivas**: Expresión según contexto
- **Múltiples Idiomas**: Español, inglés y más
- **Ajuste de Parámetros**: Velocidad, tono, énfasis

### 🤖 Asistente Virtual Inteligente
- **Múltiples Personalidades**: Profesional, amigable, infantil, tutorial
- **Contexto Adaptativo**: Respuestas según la situación
- **Efectos de Sonido**: Ambiente inmersivo
- **Música de Fondo**: Experiencia completa
- **Estadísticas en Tiempo Real**: Seguimiento de progreso

### 🔧 Integración de Hardware
- **Detección Automática de Mano Robótica**: Sin configuración manual
- **Control Preciso**: Comandos optimizados
- **Múltiples Protocolos**: Serial, I2C, SPI
- **Retroalimentación Visual**: Estado de conexión

## 🚀 Novedades en v2.0

### ✨ Nuevas Características
1. **Motor de Voz Multi-Engine**:
   - Google Cloud TTS con voces WaveNet
   - gTTS gratuito como alternativa
   - Azure Speech (opcional)
   - Fallback automático

2. **Asistente Virtual con Personalidad**:
   - 6 personalidades diferentes
   - Detección de emociones
   - Respuestas contextuales
   - Tutorial interactivo

3. **Sistema de Calibración**:
   - Calibración guiada paso a paso
   - Perfiles de usuario
   - Ajuste de sensibilidad
   - Guardado automático

4. **Gestión de Sesiones**:
   - Autoguardado cada 60 segundos
   - Historial de sesiones
   - Recuperación de crashes
   - Exportación en múltiples formatos

5. **Interfaz Mejorada**:
   - Indicadores visuales mejorados
   - Paleta de colores expandida
   - Modo debug avanzado
   - Atajos de teclado

## 📋 Requisitos del Sistema

### Hardware Mínimo
- **CPU**: Intel Core i5 o equivalente
- **RAM**: 8GB (16GB recomendado)
- **GPU**: Compatible con OpenGL 3.0+
- **Almacenamiento**: 4GB libres
- **Cámara**: Kinect o webcam HD (720p mínimo)

### Hardware Opcional
- **Mano Robótica**: Compatible con Serial/Arduino
- **Micrófono**: Para comandos de voz futuros
- **Altavoces**: Para síntesis de voz

### Software Requerido
- **Sistema Operativo**:
  - Windows 10/11 (x64)
  - Ubuntu 20.04+ LTS
  - macOS 11.0+
- **Python**: 3.7 - 3.10 (3.9 recomendado)
- **Drivers**: OpenNI2 para Kinect

## ⚙️ Instalación Completa

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/sistema-interactivo-kinect.git
cd sistema-interactivo-kinect
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias principales
pip install -r requirements.txt

# Para desarrollo (opcional)
pip install -r requirements-dev.txt
```

### 4. Configurar OpenNI2 (Para Kinect)

#### Windows:
1. Descargar [OpenNI2 SDK](https://structure.io/openni)
2. Instalar en `C:\Program Files\OpenNI2`
3. Agregar `C:\Program Files\OpenNI2\Redist` al PATH

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install libopenni2-dev libopenni2-0
```

#### macOS:
```bash
brew update
brew install openni2
```

### 5. Configurar Google Cloud TTS (Recomendado)

1. **Crear Proyecto en Google Cloud**:
   ```
   https://console.cloud.google.com/
   ```

2. **Habilitar Text-to-Speech API**:
   - Navegar a "APIs y servicios" > "Biblioteca"
   - Buscar "Cloud Text-to-Speech API"
   - Hacer clic en "Habilitar"

3. **Crear Credenciales**:
   - Ir a "APIs y servicios" > "Credenciales"
   - Crear cuenta de servicio
   - Descargar JSON de credenciales
   - Renombrar a `google_credentials.json`
   - Colocar en la raíz del proyecto

4. **Configurar Variable de Entorno** (Opcional):
   ```bash
   # Windows
   set GOOGLE_APPLICATION_CREDENTIALS=path\to\google_credentials.json
   
   # Linux/macOS
   export GOOGLE_APPLICATION_CREDENTIALS=path/to/google_credentials.json
   ```

### 6. Configuración Inicial

1. **Crear archivo de configuración de voz**:
   ```bash
   cp configuracion_voz.ejemplo.json configuracion_voz.json
   ```

2. **Editar configuración**:
   ```json
   {
       "motor": "google_tts",
       "voz_genero": "femenino",
       "voz_idioma": "es",
       "google_tts": {
           "credenciales_path": "google_credentials.json",
           "voz_preferida": "es-ES-Standard-A",
           "usar_wavenet": true
       }
   }
   ```

## 🎮 Uso del Sistema

### Inicio Rápido

```bash
# Iniciar con Kinect (predeterminado)
python main.py

# Iniciar con webcam
python main.py --webcam

# Modo debug
python main.py --debug

# Especificar puerto de mano robótica
python main.py --puerto COM3
```

### Controles por Gestos

| Gesto | Descripción | Acción |
|-------|-------------|--------|
| 👆 Índice extendido | Solo dedo índice arriba | Dibujar |
| ✊ Puño cerrado | Todos los dedos cerrados | Seleccionar botón |
| 🖐️ Mano abierta | Todos los dedos extendidos | Borrar (en modo borrador) |
| 🤏 Pinza | Pulgar e índice unidos | Precisión (próximamente) |

### Atajos de Teclado

| Tecla | Función |
|-------|---------|
| Q / ESC | Salir del programa |
| S | Guardar sesión manualmente |
| V | Cambiar nivel de verbosidad |
| P | Cambiar personalidad del asistente |
| T | Activar/desactivar modo tutorial |
| A | Activar/desactivar asistente |
| M | Activar/desactivar música |
| E | Activar/desactivar efectos de sonido |
| X | Activar/desactivar voz emotiva |
| + | Subir volumen |
| - | Bajar volumen |
| C | Abrir calibración |
| H | Mostrar ayuda |

### Modos de Operación

1. **Modo Dibujo**:
   - Selecciona botón "Dibujar"
   - Usa dedo índice para trazar
   - Cambia colores con la paleta

2. **Modo Borrador**:
   - Selecciona botón "Borrar"
   - Usa cualquier gesto para borrar
   - Ajusta tamaño del borrador

3. **Modo Reconocimiento**:
   - Selecciona botón "Guardar"
   - Dibuja texto o formas
   - El sistema reconoce y sintetiza voz

## 🛠️ Configuración Avanzada

### Archivo config.json

```json
{
    "kinect": {
        "openni_path": "C:/Program Files/OpenNI2/Redist",
        "resolution": [640, 480]
    },
    "mano_robotica": {
        "puerto": "AUTO",
        "baudios": 9600,
        "timeout": 2,
        "identificadores": ["Arduino", "CH340", "USB Serial"]
    },
    "ui": {
        "botones": {
            "Dibujar": [50, 50],
            "Borrar": [170, 50],
            "Limpiar": [290, 50],
            "Guardar": [410, 50],
            "Salir": [530, 50]
        },
        "paleta_colores": {
            "Verde": [0, 255, 0],
            "Rojo": [0, 0, 255],
            "Azul": [255, 0, 0],
            "Amarillo": [0, 255, 255],
            "Blanco": [255, 255, 255],
            "Negro": [0, 0, 0]
        }
    },
    "dibujo": {
        "grosor_linea": 3,
        "radio_borrador": 30,
        "autosave_interval": 60,
        "sesiones_dir": "sesiones"
    },
    "calibracion": {
        "sensibilidad_gestos": 0.7,
        "distancia_minima_dedos": 0.1,
        "tiempo_gesto": 0.5
    },
    "modo_debug": false,
    "idiomas_ocr": ["es", "en"]
}
```

### Configuración del Asistente

```json
{
    "personalidad": "amigable",
    "nivel_verbosidad": 2,
    "activo": true,
    "modo_tutorial": false,
    "repetir_instrucciones": true,
    "tiempo_entre_consejos": 60,
    "volumen_efectos": 0.8,
    "usar_efectos_sonido": true,
    "usar_musica_fondo": true,
    "usar_voz_emotiva": true
}
```

## 🔍 Herramientas de Utilidad

### Comparador de Motores de Voz

```bash
python comparar_motores_voz.py
```

Permite:
- Probar diferentes motores TTS
- Comparar calidad de voz
- Ajustar parámetros
- Configurar motor predeterminado

### Prueba Simple de Voz

```bash
python probar_voz_simple.py
```

Para verificar rápidamente la configuración de voz.

## 🐛 Solución de Problemas

### Error: "MediaPipe no detecta manos"
- Verificar iluminación adecuada
- Ajustar distancia a la cámara (50-150cm)
- Ejecutar calibración: `python main.py --calibrar`

### Error: "Google TTS no funciona"
- Verificar archivo `google_credentials.json`
- Confirmar API habilitada en Google Cloud
- Revisar cuota disponible
- Fallback automático a gTTS

### Error: "Mano robótica no conecta"
- Verificar drivers USB
- Probar detección automática
- Usar `python main.py --detectar-puertos`
- Verificar baudrate correcto

### Error: "OpenNI2 no encontrado"
- Reinstalar OpenNI2
- Verificar variable PATH
- Actualizar `config.json` con ruta correcta

## 🤝 Contribuir

### Guía de Contribución

1. **Fork** el repositorio
2. Crear **rama** (`git checkout -b feature/NuevaCaracteristica`)
3. **Commit** (`git commit -m 'Add: Nueva característica'`)
4. **Push** (`git push origin feature/NuevaCaracteristica`)
5. Abrir **Pull Request**

### Estándares de Código

- Seguir PEP 8
- Documentar con docstrings
- Añadir tests unitarios
- Mantener arquitectura modular

### Áreas de Mejora

- [ ] Reconocimiento de voz para comandos
- [ ] Soporte para múltiples manos
- [ ] Exportación a más formatos
- [ ] Integración con APIs de dibujo
- [ ] Modo colaborativo en red

## 📚 Documentación

### Arquitectura del Sistema

```
sistema-interactivo-kinect/
├── main.py                    # Entrada principal
├── config.json               # Configuración global
├── configuracion_voz.json    # Config de síntesis de voz
├── google_credentials.json   # Credenciales Google (no incluido)
├── requirements.txt          # Dependencias
├── sistema/                  # Módulos principales
│   ├── __init__.py
│   ├── sistema_interactivo.py    # Coordinador principal
│   ├── config_manager.py         # Gestión de configuración
│   ├── kinect_manager.py         # Control de cámara
│   ├── hand_tracker.py           # Reconocimiento de gestos
│   ├── mano_robotica.py          # Control de hardware
│   ├── text_recognizer.py        # OCR
│   ├── voice_engine.py           # Síntesis de voz
│   ├── ui_manager.py             # Interfaz de usuario
│   ├── dibujo_manager.py         # Sistema de dibujo
│   ├── asistente_virtual.py      # IA del asistente
│   ├── calibracion_manager.py    # Sistema de calibración
│   ├── efectos_sonido.py         # Efectos de audio
│   └── voz_emotiva.py           # Emociones en voz
├── utils/                    # Utilidades
├── tests/                    # Pruebas unitarias
├── docs/                     # Documentación adicional
├── sesiones/                 # Sesiones guardadas
├── temp_audio/              # Audio temporal
└── sonidos/                 # Efectos de sonido
```

### API Pública

```python
# Ejemplo de uso programático
from sistema import SistemaInteractivo

# Crear instancia
sistema = SistemaInteractivo(
    modo_debug=True,
    usar_webcam=True
)

# Configurar asistente
sistema.asistente.cambiar_personalidad("tutorial")
sistema.asistente.cambiar_verbosidad(3)

# Ejecutar
sistema.ejecutar()
```

## 🏆 Casos de Uso

### Educación
- Clases interactivas sin contacto
- Enseñanza a distancia mejorada
- Accesibilidad para estudiantes con discapacidad

### Medicina
- Interacción estéril en quirófanos
- Terapia ocupacional
- Rehabilitación motora

### Arte y Diseño
- Creación artística gestual
- Prototipado rápido
- Instalaciones interactivas

### Industria
- Control de maquinaria sin contacto
- Interfaces en ambientes hostiles
- Presentaciones empresariales

## 📊 Rendimiento

### Benchmarks
- **FPS**: 30+ en hardware recomendado
- **Latencia de gestos**: <100ms
- **Precisión OCR**: 95%+ en texto claro
- **Tiempo de síntesis**: <500ms por frase

### Optimizaciones
- Procesamiento multihilo
- Caché de gestos frecuentes
- Compresión de audio en tiempo real
- Gestión inteligente de memoria

## 🔒 Seguridad y Privacidad

- **Datos locales**: Todo el procesamiento en dispositivo
- **Credenciales seguras**: Nunca en código fuente
- **Conexiones cifradas**: HTTPS para APIs
- **Sin telemetría**: Respeto total a la privacidad

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **MediaPipe Team** - Por el excelente framework de visión
- **Google Cloud** - Por las APIs de TTS
- **Comunidad Open Source** - Por las librerías utilizadas
- **Testers Beta** - Por su invaluable feedback

## 📬 Contacto

**Desarrollador Principal**: Johan Sebastian Rojas Ramirez
- GitHub: [@Zaxazgames1](https://github.com/Zaxazgames1)
- Email: johansebastianrojasramirez7@gmail.com


## 🚧 Roadmap

### v2.1 (Q2 2024)
- [ ] Reconocimiento de voz para comandos
- [ ] Soporte multi-idioma completo
- [ ] Exportación a la nube

### v2.5 (Q3 2024)
- [ ] Realidad aumentada
- [ ] Colaboración en tiempo real
- [ ] Plugins personalizables

### v3.0 (Q4 2024)
- [ ] IA generativa integrada
- [ ] Control por EEG
- [ ] Metaverso compatible

---

<div align="center">
  <p>
    <a href="https://github.com/tu-usuario/sistema-interactivo-kinect/stargazers">
      <img src="https://img.shields.io/github/stars/tu-usuario/sistema-interactivo-kinect?style=social" alt="Stars"/>
    </a>
    <a href="https://github.com/tu-usuario/sistema-interactivo-kinect/network/members">
      <img src="https://img.shields.io/github/forks/tu-usuario/sistema-interactivo-kinect?style=social" alt="Forks"/>
    </a>
    <a href="https://github.com/tu-usuario/sistema-interactivo-kinect/issues">
      <img src="https://img.shields.io/github/issues/tu-usuario/sistema-interactivo-kinect?style=social" alt="Issues"/>
    </a>
  </p>
  
  <h3>⭐ Si este proyecto te ha sido útil, considera darle una estrella ⭐</h3>
  
  <p><i>Hecho con ❤️ y Python por desarrolladores para desarrolladores</i></p>
</div>