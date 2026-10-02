import os
import numpy as np
import subprocess
import glob
import pandas as pd


# Caminhos
caminho_relacao_clientes_excel = r"I:\GSC\Relação_Clientes\Relação de Clientes.xlsx"
caminho_servicos_executados = r"I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\ARQUIVOS XLSX"
caminho_saida_parquet = r"I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\ARQUIVOS PARQUET"
caminho_saida_excel = r"I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\ARQUIVOS XLSX\Relação de Clientes.xlsx"

#------------------------SERVIÇOS EXECUTADOS--------------------------------------------#

# 1. Ajustar cabeçalho e salvar em Excel após excluir as 10 primeiras linhas
def ajustar_cabecalho_relacao_clientes(caminho_arquivo, caminho_saida):
    relacao_clientes = pd.read_excel(caminho_arquivo, skiprows=10)
    if 'NRO.LIGAÇÃO' in relacao_clientes.columns:
        relacao_clientes.rename(columns={'NRO.LIGAÇÃO': 'Nº Ligação'}, inplace=True)
        print("Cabeçalho ajustado: 'NRO.LIGAÇÃO' -> 'Nº Ligação'.")
    else:
        print("A coluna 'NRO.LIGAÇÃO' não foi encontrada no arquivo.")
    relacao_clientes.to_excel(caminho_saida, index=False)
    print(f"Arquivo com cabeçalho ajustado salvo em: {caminho_saida}")

# 2. Converter para Parquet
def converter_relacao_clientes_para_parquet(caminho_arquivo_excel, caminho_saida):
    # Carregar o arquivo com o cabeçalho ajustado (sem excluir linhas)
    relacao_clientes = pd.read_excel(caminho_arquivo_excel)

# 2. Converter para Parquet
def converter_relacao_clientes_para_parquet(caminho_arquivo_excel, caminho_saida):
    relacao_clientes = pd.read_excel(caminho_arquivo_excel)
    nome_arquivo_parquet = os.path.join(caminho_saida, "Relação_Clientes.parquet")
    relacao_clientes.to_parquet(nome_arquivo_parquet, index=False)
    print(f"Arquivo convertido para Parquet e salvo em: {nome_arquivo_parquet}")
    return nome_arquivo_parquet

# 3. Processar os arquivos de serviços executados
def processar_servicos_executados(caminho_servicos, caminho_relacao_clientes_parquet, caminho_saida):
    # Carregar a base de clientes em formato Parquet
    relacao_clientes = pd.read_parquet(caminho_relacao_clientes_parquet)

    # Verificar arquivos na pasta de serviços executados que começam com "REL_ORDEM_SERVICO"
    arquivos_servicos = [f for f in os.listdir(caminho_servicos) if f.startswith("REL_ORDEM_SERVICO")]
    if not arquivos_servicos:
        print("Nenhum arquivo encontrado com o nome REL_ORDEM_SERVICO.")
        return

    for arquivo in arquivos_servicos:
        arquivo_servico_path = os.path.join(caminho_servicos, arquivo)
        print(f"Lendo arquivo: {arquivo_servico_path}")

        # Carregar a base de serviços executados
        servicos_executados = pd.read_excel(arquivo_servico_path)

        # Remover linhas com "suspen" no 'Serviço Solicitado' e preenchimento na coluna 'Nº O.S. Pai'
        servicos_executados = servicos_executados[~(
            servicos_executados['Serviço Solicitado'].str.contains('suspen', case=False, na=False) &
            servicos_executados['Nº O.S. Pai'].notna()
        )]

        # Merge as duas bases de dados pela coluna 'Nº Ligação'
        df = servicos_executados.merge(relacao_clientes, on='Nº Ligação', how='left')

        # Garantir que as colunas de data estão no formato correto
        df['Data Agendamento'] = pd.to_datetime(df['Data Agendamento'], errors='coerce')

        # Criar a coluna 'Tarifa' com base nas condições
        condicoes = [
            (df['SITUAÇÃO ESGOTO'] == 'ATIVA'),
            (df['SITUAÇÃO ÁGUA'] == 'CORTADA POR DÉBITO') &
            (df['SITUAÇÃO ESGOTO'] == 'FACTÍVEL ') &
            (df['PERC.ESGOTO FATURADO'] == '100'),
            (df['SITUAÇÃO ÁGUA'] == 'CORTADA POR DÉBITO') &
            (df['SITUAÇÃO ESGOTO'] == 'FACTÍVEL ') &
            (df['PERC.ESGOTO FATURADO'] == '100'),
        ]

        resultados = [
            'ÁGUA/ESGOTO',
            'ÁGUA/ESGOTO',
            'ÁGUA/ESGOTO'
        ]

        # Adiciona 'SÓ ÁGUA' como valor padrão para as demais condições
        df['Tarifa'] = np.select(condicoes, resultados, default='SÓ ÁGUA')

        def classificar_servico(row):

            servico = str(row['Serviço Solicitado'])
            obs = str(row['Observação para execução do serviço'])
            usuario = str(row['Usuário de Inclusão'])

            if 'LIGAÇÃO NOVA DE ÁGUA' in servico:
                return 'LNA'
            elif 'FISCALIZAÇÃO DE CORTE' in servico:
                return 'FISCALIZAÇÃO'
            elif 'RELIGAÇÃO NO HD' in servico:
                return 'RELIGAÇÃO HD'
            elif 'RELIGAÇÃO NO RAMAL' in servico:
                return 'RELIGAÇÃO RAMAL'
            elif 'RELIGAÇÃO NA REDE' in servico:
                return 'RELIGAÇÃO REDE'
            elif 'SUSPENSÃO DE FORNECIMENTO NO HD' in servico:
                return 'SUSPENSÃO HD'
            elif 'SUSPENSÃO DE FORNECIMENTO NO RAMAL' in servico:
                return 'SUSPENSÃO RAMAL'
            elif 'VISTORIA PERIÓDICA' in servico:
                return 'VISTORIA PERIÓDICA'
            elif 'AUTO DE INFRACAO' in servico:
                return 'AUTO DE INFRACAO'
            elif 'RETIRADA DE BYPASS' in servico:
                return 'IRREGULARIDADE/ NOTIFICAÇÃO'
            elif 'RETIRADA DE IRREGULARIDADE' in servico:
                return 'IRREGULARIDADE/ NOTIFICAÇÃO'
            elif 'RETIRADA DE VIOLAÇÃO' in servico:
                return 'IRREGULARIDADE/ NOTIFICAÇÃO'
            elif '18073' in servico:
                return 'IRREGULARIDADE/ NOTIFICAÇÃO'
            elif 'RETIRADA DE LIGAÇÃO CLANDESTINA' in servico:
                return 'IRREGULARIDADE/ NOTIFICAÇÃO'
            elif 'DESLIGAMENTO' in servico:
                return 'DESLIGAMENTO'
            elif 'LIGAÇÃO NOVA DE ESGOTO' in servico:
                return 'LNE'
            elif 'ATIVAÇÃO DE LIGAÇÃO DE ESGOTO' in servico:
                return 'LNE'
            elif 'CORTE NEGOCIADO' in servico:
                return 'NEGOCIAÇÃO'
            elif 'PROJETO PADR' in obs and ('NATANY SOARES DE CASTRO' in usuario or 'SILAS' in usuario or 'FLAVIO' in usuario or 'ESTEFANO' in usuario):
                return 'PADRONIZAÇÃO'
            elif 'PAD. DE LIGAÇÃO' in servico and ('NATANY SOARES DE CASTRO' in usuario or 'SILAS' in usuario or 'FLAVIO' in usuario or 'ESTEFANO' in usuario):
                return 'PADRONIZAÇÃO_V2'
            else:
                return 'OUTROS'

        df['Categoria Serviço'] = df.apply(classificar_servico, axis=1)

        # Salvar o arquivo completo em Parquet
        caminho_arquivo_saida = os.path.join(caminho_saida, f"{os.path.splitext(arquivo)[0]}.parquet")
        df.to_parquet(caminho_arquivo_saida, index=False)
        print(f"Arquivo completo salvo em: {caminho_arquivo_saida}")

        # Filtrar apenas os serviços LNA
        df_lna = df[df['Categoria Serviço'] == 'LNA']
        if not df_lna.empty:
            nome_base = os.path.splitext(arquivo)[0]  # Obter o nome base do arquivo
            caminho_arquivo_lna = os.path.join(caminho_saida, f"LNAS_{nome_base[16:]}.parquet")
            df_lna.to_parquet(caminho_arquivo_lna, index=False)
            print(f"Arquivo LNAS salvo em: {caminho_arquivo_lna}")

# Execução do script completo
ajustar_cabecalho_relacao_clientes(caminho_relacao_clientes_excel, caminho_saida_excel)
caminho_parquet_clientes = converter_relacao_clientes_para_parquet(caminho_saida_excel, caminho_saida_parquet)
processar_servicos_executados(caminho_servicos_executados, caminho_parquet_clientes, caminho_saida_parquet)

#------------------------substituição HDs--------------------------------------------#

import os
import pandas as pd

# Caminhos das planilhas
caminho_substi_hd = r'I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\substi_hd.xlsx'
caminho_controle_plano = r'I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\v1_Controle_plano_substituições_GSC_2026.xlsm'
aba_controle = 'V1'

# ========================
# FUNÇÕES AUXILIARES
# ========================

def normalizar_chave(serie):
    """Padroniza a ligação (texto, sem espaços, sem '.0' e sem zeros à esquerda)
    para que a comparação não falhe por diferença de tipo entre as planilhas."""
    return (
        serie.astype(str)
        .str.strip()
        .str.replace(r'\.0$', '', regex=True)
        .str.lstrip('0')
    )

def ler_excel(caminho, aba=None):
    try:
        if aba:
            return pd.read_excel(caminho, sheet_name=aba, engine='openpyxl')
        else:
            return pd.read_excel(caminho, engine='openpyxl')
    except Exception as e:
        print(f"Erro ao ler {caminho}: {e}")
        return None

df_substi_hd = ler_excel(caminho_substi_hd)
df_controle_plano = ler_excel(caminho_controle_plano, aba_controle)

# ========================
# PROCESSAMENTO
# ========================
# Regra: se a ligação consta no plano (v1_Controle_plano), a substituição é
# PREVENTIVA, independentemente do dimensionamento do HD instalado.
# Se não consta no plano, é CORRETIVA.
# Cada ligação é contada uma única vez (mantém a instalação mais recente).

if df_substi_hd is not None and df_controle_plano is not None:

    # Ligações que constam no plano (só a chave importa)
    chaves_plano = set(normalizar_chave(df_controle_plano['LIGAÇÃO'].dropna()))

    # Ignora linhas sem ligação e cria a chave normalizada
    df_substi_hd = df_substi_hd[df_substi_hd['Ligação'].notna()].copy()
    df_substi_hd['_chave'] = normalizar_chave(df_substi_hd['Ligação'])

    # Remover duplicidade: mesma ligação conta uma vez só (fica a instalação mais recente)
    total_antes = len(df_substi_hd)
    df_substi_hd['_data_ord'] = pd.to_datetime(df_substi_hd['Data Instalação'], errors='coerce')
    df_substi_hd = (
        df_substi_hd
        .sort_values('_data_ord', na_position='first')
        .drop_duplicates(subset='_chave', keep='last')
        .sort_index()
    )
    print(f"Duplicidades removidas em substi_hd: {total_antes - len(df_substi_hd)}")

    no_plano = df_substi_hd['_chave'].isin(chaves_plano)

    # ========================
    # RESULTADOS
    # ========================

    colunas_saida = [
        'Ligação', 'Bairro', 'Data Instalação',
        'Sit. Água', 'Sit. Esgoto', 'Categoria'
    ]

    dados_cruzados = df_substi_hd[no_plano][colunas_saida].copy()
    dados_nao_cruzados = df_substi_hd[~no_plano][colunas_saida].copy()

    # Tarifas
    for d in (dados_cruzados, dados_nao_cruzados):
        d['TARIFA'] = (
            d['Sit. Esgoto'].astype(str).str.strip().str.upper()
            .map(lambda x: 'ÁGUA/ESGOTO' if x == 'ATIVA' else 'SÓ ÁGUA')
        )

    dados_cruzados['Serviço'] = 'SUBSTITUIÇÃO PREVENTIVA'
    dados_nao_cruzados['Serviço'] = 'SUBSTITUIÇÃO CORRETIVA'

    print(f"Preventivas: {len(dados_cruzados)} | Corretivas: {len(dados_nao_cruzados)}")

    # ========================
    # SAÍDA
    # ========================

    caminho_saida = r'I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI'

    arquivo_cruzados = os.path.join(caminho_saida, 'SUBSTITUIÇÃO_PREVENTIVA.xlsx')
    arquivo_nao_cruzados = os.path.join(caminho_saida, 'SUBSTITUIÇÃO_CORRETIVA.xlsx')

    try:
        dados_cruzados.to_excel(arquivo_cruzados, index=False)
        dados_nao_cruzados.to_excel(arquivo_nao_cruzados, index=False)
        print("✔ Substituições de HD processadas (preventiva = ligação no plano).")
    except PermissionError as e:
        print(f"Erro ao gravar (feche os arquivos abertos no Excel): {e}")

else:
    print("Erro ao carregar os arquivos.")

#------------------------Corte Negociado--------------------------------------------#

# Pasta onde estão os arquivos Excel
input_folder = r'I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\ARQUIVOS XLSX'
output_file = r'I:\GSC\FELIPE\BI PLURI\ARQUIVOS PARQUET PLURI\ARQUIVOS PARQUET\REL_ORDEM_Corte_Negociado.parquet'

# Pegar todos os arquivos que começam com "Corte_Negociado"
files = glob.glob(os.path.join(input_folder, 'Corte_Negociado*.xlsx'))

# Lista para acumular os dataframes
dfs = []

for file in files:
    df = pd.read_excel(file)

    # Filtrar apenas CORTE NEGOCIADO
    df = df[df['Motivo'] == 'CORTE NEGOCIADO']

    # Ajustes de colunas
    df['Data Exec.'] = df['Data Não Exec.']
    df['Serviço Solicitado'] = 'CORTE NEGOCIADO'
    df['Serviço Executado'] = 'CORTE NEGOCIADO'
    df['Serviço'] = 'NEGOCIAÇÃO'

    dfs.append(df)

# Concatenar
df_final = pd.concat(dfs, ignore_index=True)

for col in df_final.columns:
    if df_final[col].dtype == 'object':
        df_final[col] = (
            df_final[col]
            .astype('string')
            .fillna('')
        )

# Salvar Parquet único
df_final.to_parquet(output_file, index=False)

print(f"{len(files)} arquivos processados. Parquet gerado com sucesso.")




# -------------------------------------------------------------------------------------------#

# Caminho para o executável do Power BI Desktop
caminho_power_bi = r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"

# Caminho para o arquivo PBIX que você deseja abrir
caminho_arquivo_pbix = r"I:\GSC\FELIPE\BI PLURI\BI PLURI v2.pbix"

def abrir_power_bi(caminho_executavel, caminho_pbix):
    try:
        subprocess.Popen([caminho_executavel, caminho_pbix])
        print(f"Power BI aberto com o arquivo: {caminho_pbix}")
    except Exception as e:
        print(f"Erro ao tentar abrir o Power BI: {e}")

# Executar a função ao final do script
abrir_power_bi(caminho_power_bi, caminho_arquivo_pbix)
