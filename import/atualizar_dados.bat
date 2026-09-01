@echo off
setlocal

rem Atalho para reimportar as planilhas de hidrometros e consumos no Supabase.
rem So precisa dar 2 cliques neste arquivo sempre que sair planilha nova.
rem Ajuste os caminhos abaixo se os arquivos mudarem de nome/lugar.

set HD_CSV=C:\Users\felipe.defaveri\OneDrive - Grupo Aguas do Brasil\Documentos\hidrometros.csv
set CONSUMO_CSV=C:\Users\felipe.defaveri\OneDrive - Grupo Aguas do Brasil\Documentos\consumos.csv

cd /d "%~dp0"

echo.
if exist "%CONSUMO_CSV%" (
    echo Importando hidrometros e consumos...
    echo.
    python import_hd.py --hidrometros-csv "%HD_CSV%" --consumos-csv "%CONSUMO_CSV%"
) else (
    echo Arquivo de consumos nao encontrado em:
    echo   "%CONSUMO_CSV%"
    echo Importando so o cadastro de hidrometros por enquanto.
    echo.
    python import_hd.py --hidrometros-csv "%HD_CSV%"
)

echo.
echo Concluido. Feche esta janela ou pressione qualquer tecla.
pause >nul
