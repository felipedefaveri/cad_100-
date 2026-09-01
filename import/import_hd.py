#!/usr/bin/env python3
"""Importa a planilha de HDs (hidrômetros) para o Supabase.

Mantém o "repositório online" que o app dos vistoriantes consulta sempre
atualizado. Rode este script toda vez que uma nova planilha for exportada
do sistema da empresa (pode ser manual ou agendado, ex: cron/Task Scheduler).

Reconhece automaticamente tanto o layout de exportação da concessionária
(ex: "NRO.LIGAÇÃO", "Nº HIDRÔMETRO", "SITUAÇÃO ÁGUA", "LOGRADOURO"...) quanto
um layout simplificado ("numero_hidrometro", "matricula", "endereco"...) —
o casamento de colunas ignora maiúsculas/minúsculas, acentos e pontuação.

Aba/arquivo "hidrometros" (cadastro, uma linha por HD) — colunas reconhecidas:
    - número do hidrômetro (obrigatório, chave de busca no app):
      "Nº HIDRÔMETRO", "numero_hidrometro", "hidrometro"
    - matrícula/ligação (opcional, informação complementar):
      "NRO.LIGAÇÃO", "matricula"
    - quantidade de economias:
      "ECONOMIA", "economias"
    - situação (ativo/inativo):
      "SITUAÇÃO ÁGUA", "ativo" — ver mapeamento de termos abaixo
    - endereço:
      "LOGRADOURO" (+ "LOGRADOURO_NÚMERO" + "LOGRADOURO_COMPLEMENTO" se
      existirem, concatenados automaticamente), ou "endereco" pronto
    - bairro:
      "BAIRRO", "bairro"

Aba/arquivo "consumos" (histórico mensal, uma linha por HD/mês — não vem na
planilha de cadastro da concessionária, precisa de uma exportação à parte):
    numero_hidrometro | ano_mes    | volume_m3
    HD-000123          | 2026-07    | 45.3

- "ano_mes" aceita "YYYY-MM" ou uma data completa (usa-se sempre o dia 1).
- Linhas sem número de hidrômetro são ignoradas.
- Termos de "situação água" não reconhecidos são avisados no final da
  importação (e tratados como ativo, para não esconder HDs por engano) —
  ajuste ATIVO_TERMS/INATIVO_TERMS abaixo se aparecerem termos novos.

Uso:
    python import_hd.py --file planilha.xlsx
    python import_hd.py --hidrometros-csv cadastro.csv --consumos-csv consumos.csv

Configuração (variáveis de ambiente ou arquivo .env na mesma pasta):
    SUPABASE_URL              -> ex: https://xxxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY -> chave "service_role" do projeto (Settings > API)
                                  NUNCA use a service_role key dentro do app do
                                  celular - ela é só para este script de importação.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import requests

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

CHUNK_SIZE = 500

# Termos de "SITUAÇÃO ÁGUA" (ou coluna "ativo" com texto livre) conhecidos.
# Ajuste aqui se a concessionária usar termos diferentes destes.
ATIVO_TERMS = {"LIGADA", "LIGADO", "NORMAL", "ATIVA", "ATIVO", "REGULAR", "SIM", "S", "TRUE", "1"}
INATIVO_TERMS = {
    "CORTADA", "CORTADO", "SUSPENSA", "SUSPENSO", "INATIVA", "INATIVO",
    "DESLIGADA", "DESLIGADO", "FECHADA", "FECHADO", "CANCELADA", "CANCELADO",
    "NAO", "N", "FALSE", "0",
}

# Aliases de coluna (já normalizados: maiúsculo, sem acento, só alfanumérico)
# -> nome canônico do campo interno.
COLUMN_ALIASES: dict[str, set[str]] = {
    "numero_hidrometro": {
        "NHIDROMETRO", "NOHIDROMETRO", "NUMEROHIDROMETRO", "HIDROMETRO", "NUMHIDROMETRO",
    },
    "matricula": {"MATRICULA", "NROLIGACAO", "NUMEROLIGACAO", "LIGACAO", "NLIGACAO"},
    "economias": {"ECONOMIA", "ECONOMIAS", "QTDECONOMIAS", "QUANTIDADEECONOMIAS"},
    "eco_residencial": {"ECORES", "ECONOMIASRESIDENCIAL", "ECONOMIARESIDENCIAL"},
    "eco_comercial": {"ECOCOM", "ECONOMIASCOMERCIAL", "ECONOMIACOMERCIAL"},
    "eco_industrial": {"ECOIND", "ECONOMIASINDUSTRIAL", "ECONOMIAINDUSTRIAL"},
    "eco_publica": {"ECOPUB", "ECONOMIASPUBLICA", "ECONOMIAPUBLICA"},
    "ativo": {"ATIVO", "SITUACAOAGUA", "SITUACAO"},
    "endereco": {"ENDERECO"},
    "logradouro": {"LOGRADOURO"},
    "logradouro_numero": {"LOGRADOURONUMERO"},
    "logradouro_complemento": {"LOGRADOUROCOMPLEMENTO", "COMPLEMENTO"},
    "bairro": {"BAIRRO"},
    "ano_mes": {"ANOMES", "MESREFERENCIA", "MESANO", "COMPETENCIA", "REFERENCIA"},
    "volume_m3": {"VOLUMEM3", "VOLUME", "CONSUMOM3", "CONSUMO", "M3"},
}


def normalize_header(name: str) -> str:
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", text.upper())


ATIVO_TERMS_NORM = {normalize_header(t) for t in ATIVO_TERMS}
INATIVO_TERMS_NORM = {normalize_header(t) for t in INATIVO_TERMS}


def map_columns(columns) -> dict[str, str]:
    """Retorna {campo_canonico: nome_original_da_coluna} para as colunas encontradas."""
    normalized = {normalize_header(c): c for c in columns}
    resolved: dict[str, str] = {}
    for campo, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                resolved[campo] = normalized[alias]
                break
    return resolved


def parse_int(value) -> int:
    if pd.isna(value):
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def parse_situacao(value, termos_desconhecidos: set[str]) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return True
    texto = normalize_header(value)
    if texto in ATIVO_TERMS_NORM:
        return True
    if texto in INATIVO_TERMS_NORM:
        return False
    termos_desconhecidos.add(str(value).strip())
    return True


def parse_ano_mes(value) -> str | None:
    """Converte YYYY-MM, MM/YYYY, YYYY/MM ou uma data completa para 'YYYY-MM-01'.
    Retorna None se não conseguir reconhecer o valor (linha suja/dado inválido),
    em vez de derrubar a importação inteira por causa de uma célula ruim."""
    if isinstance(value, (pd.Timestamp, date)):
        return date(value.year, value.month, 1).isoformat()

    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None

    m = re.match(r"^(\d{4})-(\d{1,2})$", text)
    if m:
        ano, mes = int(m.group(1)), int(m.group(2))
    else:
        m = re.match(r"^(\d{1,2})/(\d{4})$", text)
        if m:
            ano, mes = int(m.group(2)), int(m.group(1))
        else:
            m = re.match(r"^(\d{4})/(\d{1,2})$", text)
            if m:
                ano, mes = int(m.group(1)), int(m.group(2))
            else:
                try:
                    d = pd.to_datetime(text, dayfirst=True)
                    ano, mes = d.year, d.month
                except (ValueError, TypeError):
                    return None

    if not (1 <= mes <= 12):
        return None
    return date(ano, mes, 1).isoformat()


def read_csv_robusto(caminho: str) -> pd.DataFrame:
    """Lê CSV tentando detectar separador (',' ou ';') e codificação (utf-8/latin1)
    automaticamente, pois exportações de sistemas brasileiros costumam vir com
    ';' e Windows-1252/Latin-1 em vez do padrão internacional."""
    ultimo_erro: Exception | None = None
    for encoding in ("utf-8-sig", "latin1", "cp1252"):
        try:
            return pd.read_csv(caminho, dtype=str, sep=None, engine="python", encoding=encoding)
        except (UnicodeDecodeError, UnicodeError) as e:
            ultimo_erro = e
            continue
    raise ultimo_erro  # type: ignore[misc]


def read_sheet_or_csv(file_arg: str | None, csv_arg: str | None, sheet_name: str) -> pd.DataFrame | None:
    if csv_arg:
        return read_csv_robusto(csv_arg)
    if file_arg:
        xls = pd.ExcelFile(file_arg)
        matches = [s for s in xls.sheet_names if s.strip().lower() == sheet_name]
        if matches:
            return pd.read_excel(xls, sheet_name=matches[0], dtype=str)
        if sheet_name == "hidrometros" and len(xls.sheet_names) == 1:
            # Planilha com uma única aba de nome genérico (ex: "Planilha1"):
            # assume que é o cadastro de hidrômetros.
            print(f"  (usando a única aba da planilha, '{xls.sheet_names[0]}', como cadastro de hidrômetros)")
            return pd.read_excel(xls, sheet_name=xls.sheet_names[0], dtype=str)
        return None
    return None


def montar_endereco(row: pd.Series, col: dict[str, str]) -> str | None:
    if "endereco" in col:
        valor = str(row.get(col["endereco"], "")).strip()
        return valor or None
    rua = str(row.get(col["logradouro"], "")).strip() if "logradouro" in col else ""
    if rua.lower() == "nan":
        rua = ""

    if "logradouro_numero" in col:
        numero = str(row.get(col["logradouro_numero"], "")).strip()
        if numero and numero.lower() != "nan":
            rua = f"{rua}, {numero}" if rua else numero

    partes = [rua] if rua else []
    if "logradouro_complemento" in col:
        complemento = str(row.get(col["logradouro_complemento"], "")).strip()
        if complemento and complemento.lower() != "nan":
            partes.append(complemento)

    endereco = " - ".join(partes)
    return endereco or None


def build_hidrometros_payload(df: pd.DataFrame) -> list[dict]:
    col = map_columns(df.columns)
    if "numero_hidrometro" not in col:
        raise SystemExit(
            "Não encontrei a coluna do número do hidrômetro na planilha "
            "(esperado algo como 'Nº HIDRÔMETRO' ou 'numero_hidrometro'). "
            f"Colunas encontradas: {list(df.columns)}"
        )

    termos_desconhecidos: set[str] = set()
    rows = []
    for _, row in df.iterrows():
        numero_hidrometro = str(row.get(col["numero_hidrometro"], "")).strip()
        if not numero_hidrometro or numero_hidrometro.lower() == "nan":
            continue

        matricula = str(row.get(col.get("matricula", ""), "")).strip() if "matricula" in col else ""

        colunas_eco_por_tipo = ["eco_residencial", "eco_comercial", "eco_industrial", "eco_publica"]
        if any(c in col for c in colunas_eco_por_tipo):
            # Planilha tem o detalhamento por tipo de economia: soma esses
            # campos em vez de usar a coluna "ECONOMIA" (que na exportação da
            # concessionária costuma vir zerada/não confiável).
            economias = sum(parse_int(row.get(col[c])) for c in colunas_eco_por_tipo if c in col)
        elif "economias" in col:
            economias = parse_int(row.get(col["economias"]))
        else:
            economias = 0

        ativo = parse_situacao(row.get(col["ativo"]), termos_desconhecidos) if "ativo" in col else True

        rows.append(
            {
                "numero_hidrometro": numero_hidrometro,
                "matricula": (matricula if matricula and matricula.lower() != "nan" else None),
                "endereco": montar_endereco(row, col),
                "bairro": (str(row.get(col.get("bairro", ""), "")).strip() or None) if "bairro" in col else None,
                "economias": economias,
                "eco_residencial": parse_int(row.get(col["eco_residencial"])) if "eco_residencial" in col else 0,
                "eco_comercial": parse_int(row.get(col["eco_comercial"])) if "eco_comercial" in col else 0,
                "eco_industrial": parse_int(row.get(col["eco_industrial"])) if "eco_industrial" in col else 0,
                "eco_publica": parse_int(row.get(col["eco_publica"])) if "eco_publica" in col else 0,
                "ativo": ativo,
            }
        )

    if termos_desconhecidos:
        print(
            "  AVISO: termos de situação não reconhecidos (tratados como ATIVO por padrão): "
            + ", ".join(sorted(termos_desconhecidos))
        )
        print("  Se algum desses significar inativo, adicione-o em INATIVO_TERMS no topo do script e rode de novo.")

    return rows


def fetch_numeros_hidrometros_existentes(base_url: str, key: str) -> set[str]:
    """Busca no Supabase todos os numero_hidrometro já cadastrados, paginando.
    Usado para filtrar o CSV de consumos e não tentar gravar consumo de um HD
    que não existe em hidrometros (evita erro de foreign key)."""
    conhecidos: set[str] = set()
    endpoint = f"{base_url}/rest/v1/hidrometros?select=numero_hidrometro"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    offset = 0
    page_size = 1000
    while True:
        page_headers = {**headers, "Range": f"{offset}-{offset + page_size - 1}"}
        resp = requests.get(endpoint, headers=page_headers, timeout=60)
        if not resp.ok:
            raise RuntimeError(f"Falha ao consultar hidrômetros existentes: {resp.status_code} {resp.text}")
        pagina = resp.json()
        if not pagina:
            break
        conhecidos.update(r["numero_hidrometro"] for r in pagina)
        if len(pagina) < page_size:
            break
        offset += page_size
    return conhecidos


def build_consumos_payload(df: pd.DataFrame, numeros_conhecidos: set[str]) -> list[dict]:
    col = map_columns(df.columns)
    faltando = [c for c in ("numero_hidrometro", "ano_mes", "volume_m3") if c not in col]
    if faltando:
        raise SystemExit(
            "A aba/arquivo de consumos precisa das colunas: numero_hidrometro, ano_mes, volume_m3. "
            f"Não encontrei: {faltando}. Colunas encontradas: {list(df.columns)}"
        )
    numero_col, ano_mes_col, volume_col = col["numero_hidrometro"], col["ano_mes"], col["volume_m3"]

    rows = []
    linhas_com_data_invalida = 0
    linhas_hd_desconhecido = 0
    for _, row in df.iterrows():
        numero_hidrometro = str(row.get(numero_col, "")).strip()
        if not numero_hidrometro or numero_hidrometro.lower() == "nan" or pd.isna(row.get(ano_mes_col)):
            continue
        if numero_hidrometro not in numeros_conhecidos:
            linhas_hd_desconhecido += 1
            continue
        ano_mes = parse_ano_mes(row[ano_mes_col])
        if ano_mes is None:
            linhas_com_data_invalida += 1
            continue
        try:
            volume = float(row.get(volume_col, 0) or 0)
        except ValueError:
            volume = 0.0
        rows.append(
            {
                "numero_hidrometro": numero_hidrometro,
                "ano_mes": ano_mes,
                "volume_m3": volume,
            }
        )

    if linhas_hd_desconhecido:
        print(
            f"  AVISO: {linhas_hd_desconhecido} linha(s) de consumo citam um hidrômetro que não "
            "está cadastrado em hidrometros (removido/substituído, ou exportações de datas "
            "diferentes) - foram ignoradas."
        )
    if linhas_com_data_invalida:
        print(
            f"  AVISO: {linhas_com_data_invalida} linha(s) de consumo com data em formato não "
            "reconhecido foram ignoradas. Me mande um exemplo do valor da coluna de data se isso "
            "não for esperado."
        )

    return rows


def upsert(base_url: str, key: str, table: str, rows: list[dict], on_conflict: str) -> None:
    if not rows:
        print(f"  (nenhuma linha para {table})")
        return
    endpoint = f"{base_url}/rest/v1/{table}?on_conflict={on_conflict}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    for i in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[i : i + CHUNK_SIZE]
        resp = requests.post(endpoint, json=chunk, headers=headers, timeout=60)
        if not resp.ok:
            raise RuntimeError(f"Falha ao gravar em {table}: {resp.status_code} {resp.text}")
        print(f"  {table}: {min(i + CHUNK_SIZE, len(rows))}/{len(rows)} linhas enviadas")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", help="planilha .xlsx com abas 'hidrometros' e 'consumos'")
    parser.add_argument("--hidrometros-csv", help="CSV apenas do cadastro de hidrômetros")
    parser.add_argument("--consumos-csv", help="CSV apenas do histórico de consumo")
    parser.add_argument("--supabase-url", default=os.environ.get("SUPABASE_URL"))
    parser.add_argument("--supabase-key", default=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
    args = parser.parse_args()

    if not args.file and not (args.hidrometros_csv or args.consumos_csv):
        parser.error("informe --file (xlsx) ou --hidrometros-csv/--consumos-csv")
    if not args.supabase_url or not args.supabase_key:
        parser.error(
            "defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY (env ou .env) ou passe --supabase-url/--supabase-key"
        )

    base_url = args.supabase_url.rstrip("/")

    df_hd = read_sheet_or_csv(args.file, args.hidrometros_csv, "hidrometros")
    df_consumo = read_sheet_or_csv(args.file, args.consumos_csv, "consumos")

    numeros_conhecidos: set[str] | None = None

    if df_hd is not None:
        print(f"Lidas {len(df_hd)} linhas de hidrômetros")
        hidrometros_rows = build_hidrometros_payload(df_hd)
        numeros_conhecidos = {r["numero_hidrometro"] for r in hidrometros_rows}
        upsert(base_url, args.supabase_key, "hidrometros", hidrometros_rows, "numero_hidrometro")
    else:
        print("Nenhuma aba/arquivo de hidrômetros encontrada, pulando.")

    if df_consumo is not None:
        print(f"Lidas {len(df_consumo)} linhas de consumo")
        if numeros_conhecidos is None:
            print("  Consultando hidrômetros já cadastrados no Supabase (para não gravar consumo órfão)...")
            numeros_conhecidos = fetch_numeros_hidrometros_existentes(base_url, args.supabase_key)
            print(f"  {len(numeros_conhecidos)} hidrômetros encontrados no Supabase.")
        upsert(
            base_url,
            args.supabase_key,
            "consumos",
            build_consumos_payload(df_consumo, numeros_conhecidos),
            "numero_hidrometro,ano_mes",
        )
    else:
        print("Nenhuma aba/arquivo de consumos encontrada, pulando.")

    print("Importação concluída.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
