@echo off
REM ===============================================
REM Script de Fine-Tuning para GPT-2 Español
REM ===============================================

echo.
echo ============================================
echo  FINE-TUNING GPT-2 ESPAÑOL
echo ============================================
echo.

REM Activar entorno virtual
echo [1/3] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Verificar que se activó correctamente
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual
    echo Verifica que existe la carpeta 'venv'
    pause
    exit /b 1
)

echo.
echo [2/3] Iniciando entrenamiento...
echo.
echo CONFIGURACION:
echo - Modelo: DeepESP/gpt2-spanish
echo - Epocas: 5
echo - Batch Size: 4
echo - Learning Rate: 3e-5
echo.
echo Este proceso tomara 1-3 horas...
echo.

REM Ejecutar entrenamiento
python app/training/train_gpt2_spanish.py --epochs 5 --batch_size 4

REM Verificar si tuvo éxito
if errorlevel 1 (
    echo.
    echo ERROR: El entrenamiento fallo
    echo Revisa los logs arriba para mas detalles
    pause
    exit /b 1
)

echo.
echo [3/3] Entrenamiento completado!
echo.
echo ============================================
echo  SIGUIENTE PASO
echo ============================================
echo.
echo Actualiza tu archivo .env con:
echo MODEL_NAME=app/training/models/gpt2-spanish-medical
echo.
echo Luego reinicia la aplicacion FastAPI
echo.
pause
