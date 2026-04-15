@echo off
REM ============================================================
REM  RDR Imports — Servidor de Produção (Windows)
REM  Usa waitress: não reinicia ao alterar arquivos
REM  Execute: start_prod.bat
REM ============================================================

cd /d "%~dp0"

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

REM Define modo produção (sem debug/reloader)
set FLASK_ENV=production
set FLASK_DEBUG=0

echo.
echo  ======================================
echo   RDR Imports — Iniciando servidor...
echo   Acesse: http://localhost:5000
echo   Para parar: Ctrl+C
echo  ======================================
echo.

waitress-serve --host=0.0.0.0 --port=5000 --threads=4 wsgi:app
