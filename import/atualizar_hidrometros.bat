@echo off
setlocal

rem Atalho para reimportar a planilha de hidrometros no Supabase.
rem So precisa dar 2 cliques neste arquivo sempre que sair uma planilha nova.
rem Ajuste o caminho da planilha abaixo se ele mudar.

set PLANILHA=C:\Users\felipe.defaveri\OneDrive - Grupo Aguas do Brasil\Documentos\hidrometros.csv

cd /d "%~dp0"

echo Importando "%PLANILHA%" para o Supabase...
echo.

python import_hd.py --hidrometros-csv "%PLANILHA%"

echo.
echo Concluido. Feche esta janela ou pressione qualquer tecla.
pause >nul
