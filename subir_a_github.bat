@echo off
echo === Script para subir el proyecto a GitHub ===
echo.

rem Verificar si Git está instalado
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Git no está instalado o no está en el PATH.
    echo Por favor, instala Git desde https://git-scm.com/downloads
    pause
    exit /b 1
)

rem Verificar si ya existe un repositorio Git
if not exist .git (
    echo Inicializando repositorio Git...
    git init
    echo.
)

rem Verificar si existen archivos de credenciales
if exist google_credentials.json (
    echo.
    echo ¡ADVERTENCIA! Se ha detectado el archivo google_credentials.json
    echo Este archivo contiene información sensible y NO debe subirse a GitHub.
    echo Por favor, asegúrate de que este archivo esté incluido en .gitignore.
    echo.
    pause
)

if exist configuracion_voz.json (
    echo.
    echo ¡ADVERTENCIA! Se ha detectado el archivo configuracion_voz.json
    echo Este archivo puede contener claves de API y NO debe subirse a GitHub.
    echo Por favor, asegúrate de que este archivo esté incluido en .gitignore.
    echo.
    pause
)

rem Mostrar estado actual
echo.
echo Estado actual del repositorio:
git status
echo.

rem Añadir todos los archivos excepto los ignorados por .gitignore
echo Agregando archivos al repositorio...
git add .
echo.

rem Confirmar cambios
set /p mensaje=Ingrese un mensaje para el commit: 
git commit -m "%mensaje%"
echo.

rem Configurar el repositorio remoto si no existe
git remote -v | find "origin" >nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo No se ha configurado un repositorio remoto.
    set /p repo=Ingrese la URL del repositorio GitHub (ejemplo: https://github.com/Zaxazgames1/sistema-interactivo-kinect.git): 
    git remote add origin %repo%
    echo.
)

rem Subir cambios a GitHub
echo Subiendo cambios a GitHub...
git push -u origin master
echo.

echo Proceso completado.
pause