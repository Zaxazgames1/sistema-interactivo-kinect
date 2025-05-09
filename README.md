# 🤖 Sistema Interactivo con Kinect

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python" alt="Python 3.7+"/>
  <img src="https://img.shields.io/badge/OpenCV-4.5.0%2B-green?style=for-the-badge&logo=opencv" alt="OpenCV 4.5.0+"/>
  <img src="https://img.shields.io/badge/MediaPipe-0.8.9%2B-orange?style=for-the-badge" alt="MediaPipe 0.8.9+"/>
  <img src="https://img.shields.io/badge/EasyOCR-1.6.0%2B-red?style=for-the-badge" alt="EasyOCR 1.6.0+"/>
  <img src="https://img.shields.io/badge/Google_TTS-2.11.0%2B-yellow?style=for-the-badge&logo=google-cloud" alt="Google TTS 2.11.0+"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License MIT"/>
</div>

<p align="center">
  <b>Una interfaz innovadora que conecta el reconocimiento gestual con dispositivos físicos</b>
</p>

## 📑 Índice
- [🌟 Características](#-características)
- [🎯 Aplicaciones](#-aplicaciones)
- [🛠️ Requisitos del Sistema](#️-requisitos-del-sistema)
- [⚙️ Instalación](#️-instalación)
- [🚀 Inicio Rápido](#-inicio-rápido)
- [🧩 Arquitectura del Sistema](#-arquitectura-del-sistema)
- [✨ Gestos Soportados](#-gestos-soportados)
- [🎮 Modos de Operación](#-modos-de-operación)
- [🔊 Síntesis de Voz Mejorada](#-síntesis-de-voz-mejorada)
- [🔧 Configuración Avanzada](#-configuración-avanzada)
- [🤝 Contribuciones](#-contribuciones)
- [📄 Licencia](#-licencia)
- [📬 Contacto](#-contacto)

## 🌟 Características

Este sistema revolucionario integra tecnologías avanzadas para crear una experiencia interactiva inmersiva:

- **Reconocimiento de Gestos en Tiempo Real**: Detecta con precisión la posición y movimientos de las manos utilizando MediaPipe.
- **Dibujo Gestual en el Aire**: Convierte los gestos en trazos digitales con un sistema de dibujo intuitivo.
- **Reconocimiento Óptico de Caracteres**: Identifica texto escrito a mano con procesamiento avanzado de imágenes.
- **Síntesis de Voz Premium**: Convierte texto reconocido en audio de alta calidad mediante Google TTS.
- **Detección Automática de Puertos**: Identifica y conecta automáticamente con la mano robótica sin configuración manual.
- **Control de Mano Robótica**: Transmite comandos a dispositivos externos mediante comunicación serial.
- **Interfaz Adaptativa**: Diseño intuitivo que responde a gestos sin necesidad de dispositivos tradicionales.
- **Arquitectura Modular**: Código organizado en componentes independientes para fácil mantenimiento y expansión.
- **Compatibilidad Dual**: Funciona con Kinect o webcam estándar sin modificaciones.

<div align="center">
  <img src="docs/images/demo.png" alt="Demostración del Sistema" width="80%"/>
  <p><i>* Imagen representativa del sistema en funcionamiento</i></p>
</div>

## 🎯 Aplicaciones

Este sistema ha sido diseñado para múltiples escenarios:

- **Ambientes Educativos**: Facilita la interacción con contenido digital en aulas y laboratorios.
- **Tecnología Asistiva**: Proporciona métodos alternativos de comunicación para personas con discapacidad.
- **Entornos Médicos**: Permite interacciones sin contacto en quirófanos o áreas estériles.
- **Instalaciones Interactivas**: Crea experiencias inmersivas en museos, galerías y espacios públicos.
- **Prototipado Rápido**: Facilita la prueba de concepto para interfaces gestuales.
- **Investigación en HCI**: Plataforma para investigar nuevos paradigmas de interacción humano-computadora.

## 🛠️ Requisitos del Sistema

### Hardware
- **Dispositivo de Captura**:
  - Microsoft Kinect (recomendado) o
  - Webcam con resolución mínima 640x480
- **Especificaciones Mínimas**:
  - Procesador: Intel Core i5 o equivalente
  - RAM: 8GB
  - Espacio libre en disco: 2GB
  - Tarjeta gráfica: Compatible con OpenGL 2.0+
- **Opcional**:
  - Mano robótica o dispositivo serial compatible
  - Conexión a Internet para Google TTS (alta calidad de voz)

### Software
- **Sistema Operativo**:
  - Windows 10/11
  - Ubuntu 18.04+ o Debian-based
  - macOS 10.15+
- **Dependencias**:
  - Python 3.7 o superior
  - OpenCV 4.5.0+
  - MediaPipe 0.8.9.1+
  - OpenNI2 (para Kinect)
  - EasyOCR 1.6.0+
  - Google Cloud Text-to-Speech 2.11.0+
  - PySerial 3.5+

## ⚙️ Instalación

### 1. Preparación del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/sistema-interactivo-kinect.git
cd sistema-interactivo-kinect

# Crear y activar entorno virtual (recomendado)
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Instalación de OpenNI2 (Para Kinect)

#### Windows
1. Descargue el [SDK de OpenNI2](https://structure.io/openni)
2. Ejecute el instalador y siga las instrucciones
3. Actualice la ruta en `config.json` si es necesario

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install libopenni2-dev
```

#### macOS
```bash
brew install openni2
```

### 3. Configurar Google TTS (para síntesis de voz de alta calidad)

1. **Crear un proyecto en Google Cloud Platform**:
   - Visite [console.cloud.google.com](https://console.cloud.google.com/)
   - Cree un nuevo proyecto o seleccione uno existente

2. **Habilitar la API de Text-to-Speech**:
   - En la consola, vaya a "APIs y servicios" > "Biblioteca"
   - Busque "Cloud Text-to-Speech API" y habilítela

3. **Crear credenciales de servicio**:
   - Vaya a "APIs y servicios" > "Credenciales"
   - Haga clic en "Crear credenciales" > "Cuenta de servicio"
   - Asigne un nombre a la cuenta de servicio y haga clic en "Crear"
   - Otorgue el rol "Cloud Text-to-Speech Usuario" y luego "Continuar"
   - Haga clic en "Listo"
   - En la lista de cuentas de servicio, encuentre la cuenta recién creada
   - Haga clic en los tres puntos verticales > "Administrar claves"
   - Haga clic en "Agregar clave" > "Crear nueva clave"
   - Seleccione "JSON" y haga clic en "Crear"
   - Renombre el archivo descargado a `google_credentials.json` y colóquelo en la raíz del proyecto

### 4. Configuración del Sistema

Personalice el archivo `config.json` según sus necesidades:

```json
{
  "kinect": {
    "openni_path": "C:/Program Files/OpenNI2/Redist",
    "resolution": [640, 480]
  },
  "mano_robotica": {
    "puerto": "COM5",
    "baudios": 9600,
    "timeout": 2,
    "identificadores": ["Arduino", "CH340", "USB Serial", "FTDI", "CP210x"]
  },
  "ui": {
    "botones": {
      "Dibujar": [50, 50],
      "Borrar": [170, 50],
      "Limpiar": [290, 50],
      "Guardar": [410, 50],
      "Salir": [530, 50]
    },
    "dimensiones_boton": {
      "ancho": 100,
      "alto": 40
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
    "radio_borrador": 30,
    "autosave_interval": 60,
    "sesiones_dir": "sesiones"
  },
  "modo_debug": false,
  "idiomas_ocr": ["es", "en"]
}
```

### 5. Configurar la Síntesis de Voz

Cree un archivo `configuracion_voz.json` en la raíz del proyecto:

```json
{
    "motor": "google_tts",
    "voz_genero": "femenino",
    "voz_idioma": "es",
    "velocidad": 1.0,
    "volumen": 0.9,
    "tono": 0.0,
    "enfasis_palabras": true,
    "pausas_naturales": true,
    "usar_ssml": true,
    "efectos_audio": false,
    "google_tts": {
        "credenciales_path": "google_credentials.json",
        "voz_preferida": "es-ES-Standard-A",
        "usar_wavenet": true
    },
    "pyttsx3": {
        "optimizar_rendimiento": true,
        "verificar_voces_espanol": true,
        "usar_voz_femenina": true
    }
}
```

## 🚀 Inicio Rápido

### Ejecución Básica

```bash
# Iniciar con configuración predeterminada (Kinect)
python main.py

# Iniciar con webcam en lugar de Kinect
python main.py --webcam

# Iniciar en modo debug
python main.py --debug

# Especificar puerto de mano robótica (ahora con detección automática)
python main.py --puerto COM3
```

### Uso del Sistema

1. **Dibujo en el Aire**:
   - Seleccione el botón "Dibujar" con un puño cerrado
   - Extienda solo el dedo índice para dibujar en el aire
   - Mantenga el resto de dedos cerrados durante el dibujo

2. **Guardar y Reconocer Texto**:
   - Dibuje letras o palabras en el área de dibujo
   - Seleccione "Guardar" para procesar el texto
   - El texto reconocido se mostrará en pantalla, se leerá en voz alta con Google TTS y se enviará a la mano robótica si está conectada

3. **Borrado**:
   - Seleccione "Borrar" para activar el modo borrador
   - Utilice cualquier dedo para borrar partes específicas del dibujo
   - Seleccione "Limpiar" para borrar todo el lienzo

## 🧩 Arquitectura del Sistema

El sistema está diseñado con una arquitectura modular orientada a objetos que garantiza:

```
sistema-interactivo-kinect/
├── main.py                # Punto de entrada principal
├── config.json            # Configuración centralizada
├── configuracion_voz.json # Configuración del motor de voz
├── google_credentials.json # Credenciales para Google TTS (no incluido)
├── sistema/               # Módulo principal
│   ├── __init__.py        # Exportaciones del módulo
│   ├── sistema_interactivo.py # Clase principal coordinadora
│   ├── config_manager.py  # Gestión de configuración
│   ├── kinect_manager.py  # Control de dispositivo de captura
│   ├── hand_tracker.py    # Reconocimiento de gestos
│   ├── mano_robotica.py   # Control de mano robótica
│   ├── text_recognizer.py # Reconocimiento de texto
│   ├── voice_engine.py    # Síntesis de voz
│   ├── ui_manager.py      # Interfaz de usuario
│   └── dibujo_manager.py  # Funciones de dibujo
```

- **Alta Cohesión**: Cada módulo tiene una responsabilidad única y bien definida
- **Bajo Acoplamiento**: Los módulos interactúan a través de interfaces claras
- **Extensibilidad**: Facilita la adición de nuevas funcionalidades
- **Testabilidad**: Componentes aislados para pruebas unitarias efectivas
- **Mantenibilidad**: Organización lógica para fácil navegación y actualización

## ✨ Gestos Soportados

El sistema reconoce los siguientes gestos de mano:

| Gesto | Descripción | Acción |
|-------|-------------|--------|
| ![Índice Extendido](docs/images/index_finger.png) | Solo dedo índice extendido | Dibujar |
| ![Puño Cerrado](docs/images/fist.png) | Todos los dedos cerrados | Seleccionar botón |
| ![Mano Abierta](docs/images/open_hand.png) | Todos los dedos extendidos | Borrar (en modo borrador) |
| ![Pinza](docs/images/pinch.png) | Índice y pulgar unidos | Precisión (futura implementación) |

## 🎮 Modos de Operación

### Modo Dibujo
- Activo al seleccionar el botón "Dibujar"
- Utilice el dedo índice para trazar en el aire
- La línea seguirá su movimiento con precisión
- Ajuste el grosor y color en la configuración

### Modo Borrador
- Activo al seleccionar el botón "Borrar"
- Mueva la mano sobre el área a borrar
- Radio de borrado ajustable en configuración

### Modo Reconocimiento
- Activo al seleccionar el botón "Guardar"
- Procesa el dibujo actual para reconocer texto
- Muestra resultados en pantalla secundaria
- Sintetiza voz premium y envía a dispositivos externos

## 🔊 Síntesis de Voz Mejorada

El sistema incluye un motor de síntesis de voz avanzado con múltiples opciones:

### Google TTS (Principal)
- Alta calidad de síntesis con voces naturales
- Soporta SSML para mayor control sobre la pronunciación
- Requiere conexión a internet y credenciales de Google Cloud
- Configuración en `configuracion_voz.json`

### Respaldo Offline (pyttsx3)
- Funciona sin conexión a internet
- Menor calidad pero siempre disponible
- Activación automática si Google TTS no está disponible

### Herramienta de Comparación
Incluye una herramienta para probar diferentes motores de voz:

```bash
python comparar_motores_voz.py
```

Esta utilidad permite:
- Comparar la calidad de los diferentes motores
- Probar diferentes configuraciones (velocidad, tono)
- Configurar el motor preferido como predeterminado

## 🔧 Configuración Avanzada

### Parámetros Ajustables

Modifique estos parámetros en `config.json` para personalizar el comportamiento del sistema:

```json
{
  "dibujo": {
    "grosor_linea": 3,     // Grosor de línea de dibujo (1-10)
    "radio_borrador": 30   // Radio del borrador (10-50)
  },
  "ui": {
    "colores": {
      "dibujo": [0, 255, 0],         // Color de dibujo (Verde)
      "boton_normal": [200, 200, 200],    // Color de botones
      "boton_seleccionado": [0, 255, 255] // Color de botón activo
    }
  },
  "mano_robotica": {
    "identificadores": ["Arduino", "CH340", "USB Serial", "FTDI"] // Identificadores para detección automática
  },
  "idiomas_ocr": ["es", "en"]  // Idiomas para reconocimiento
}
```

### Configuración de Síntesis de Voz

Ajuste estos parámetros en `configuracion_voz.json`:

```json
{
    "velocidad": 1.0,      // Velocidad de habla (0.5-2.0)
    "volumen": 0.9,        // Volumen (0.0-1.0)
    "tono": 0.0,           // Ajuste de tono (-10.0 a 10.0)
    "google_tts": {
        "voz_preferida": "es-ES-Standard-A",  // ID de voz
        "usar_wavenet": true  // Usar voces de alta calidad
    }
}
```

### Opciones de Línea de Comandos

```
usage: main.py [-h] [--debug] [--config CONFIG] [--webcam] [--puerto PUERTO]

Sistema Interactivo con Kinect

optional arguments:
  -h, --help       Mostrar este mensaje de ayuda
  --debug          Activar modo debug
  --config CONFIG  Ruta al archivo de configuración
  --webcam         Usar webcam en lugar de Kinect
  --puerto PUERTO  Puerto para la mano robótica (opcional, ahora con detección automática)
```

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Siga estos pasos para contribuir:

1. **Fork** el repositorio
2. Cree una **rama de características** (`git checkout -b feature/AmazingFeature`)
3. **Commit** sus cambios (`git commit -m 'Add: amazing feature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. Abra un **Pull Request**

### Directrices de Código

- Siga PEP 8 para el estilo de código Python
- Documente las funciones usando docstrings
- Añada pruebas unitarias para nuevas funcionalidades
- Mantenga la arquitectura modular existente

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.

## 📬 Contacto

Desarrollado por: [Johan Sebastian Rojas Ramirez](https://github.com/Zaxazgames1)

¿Preguntas, problemas o sugerencias? Abra un issue o contáctenos en:
- Email: johansebastianrojasramirez7@gmail.com


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
  <p><i>Hecho con ❤️ y Python</i></p>
</div>