@echo off
REM ===============================================
REM Script de Comparación: Base vs Fine-Tuned
REM ===============================================

echo.
echo ============================================
echo  COMPARAR MODELOS GPT-2
echo ============================================
echo.

REM Activar entorno virtual
echo [1/2] Activando entorno virtual...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo.
echo [2/2] Comparando modelos...
echo.

REM Ejecutar comparación
python app/training/compare_gpt2_models.py

if errorlevel 1 (
    echo.
    echo ERROR: La comparacion fallo
    pause
    exit /b 1
)

echo.
echo Comparacion completada!
pause
