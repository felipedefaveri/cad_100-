#!/usr/bin/env python3
"""Importa a planilha de HDs (hidrômetros) para o Supabase.

Mantém o "repositório online" que o app dos vistoriantes consulta sempre
atualizado. Rode este script toda vez que uma nova planilha for exportada
do sistema da empresa (pode ser manual ou agendado, ex: cron/Task Scheduler).

Formato esperado da planilha (.xlsx ou .csv):

Aba/arquivo "hidrometros" (cadastro, uma linha por HD):
    matricula   | endereco        | bairro   | economias | ativo
    123456      | Rua A, 100      | Centro   | 8         | sim

Aba/arquivo "consumos" (histórico mensal, uma linha por HD/mês):
    matricula   | ano_mes    | volume_m3
    123456      | 2026-07    | 45.3

- "ano_mes" aceita "YYYY-MM" ou uma data completa (usa-se sempre o dia 1).
- "ativo" aceita sim/não, s/n, true/false, 1/0 (case-insensitive).
- Linhas com matrícula vazia são ignoradas.

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
import sys
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

TRUE_VALUES = {"sim", "s", "true", "1", "ativo", "yes", "y"}
FALSE_VALUES = {"nao", "não", "n", "false", "0", "inativo", "no"}


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return True
    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return True


def parse_ano_mes(value) -> str:
    if isinstance(value, (pd.Timestamp, date)):
        d = value
    else:
        text = str(value).strip()
        if len(text) == 7:  # YYYY-MM
            text = f"{text}-01"
        d = pd.to_datetime(text)
    return date(d.year, d.month, 1).isoformat()


def read_sheet_or_csv(file_arg: str | None, csv_arg: str | None, sheet_name: str) -> pd.DataFrame | None:
    if csv_arg:
        return pd.read_csv(csv_arg, dtype=str)
    if file_arg:
        xls = pd.ExcelFile(file_arg)
        matches = [s for s in xls.sheet_names if s.strip().lower() == sheet_name]
        if not matches:
            return None
        return pd.read_excel(xls, sheet_name=matches[0], dtype=str)
    return None


def build_hidrometros_payload(df: pd.DataFrame) -> list[dict]:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns})
    rows = []
    for _, row in df.iterrows():
        matricula = str(row.get("matricula", "")).strip()
        if not matricula or matricula.lower() == "nan":
            continue
        economias_raw = row.get("economias", 0)
        try:
            economias = int(float(economias_raw)) if pd.notna(economias_raw) else 0
        except ValueError:
            economias = 0
        rows.append(
            {
                "matricula": matricula,
                "endereco": (str(row.get("endereco", "")).strip() or None),
                "bairro": (str(row.get("bairro", "")).strip() or None),
                "economias": economias,
                "ativo": parse_bool(row.get("ativo")),
            }
        )
    return rows


def build_consumos_payload(df: pd.DataFrame) -> list[dict]:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns})
    rows = []
    for _, row in df.iterrows():
        matricula = str(row.get("matricula", "")).strip()
        if not matricula or matricula.lower() == "nan" or pd.isna(row.get("ano_mes")):
            continue
        try:
            volume = float(row.get("volume_m3", 0) or 0)
        except ValueError:
            volume = 0.0
        rows.append(
            {
                "matricula": matricula,
                "ano_mes": parse_ano_mes(row["ano_mes"]),
                "volume_m3": volume,
            }
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

    if df_hd is not None:
        print(f"Lidas {len(df_hd)} linhas de hidrômetros")
        upsert(base_url, args.supabase_key, "hidrometros", build_hidrometros_payload(df_hd), "matricula")
    else:
        print("Nenhuma aba/arquivo de hidrômetros encontrada, pulando.")

    if df_consumo is not None:
        print(f"Lidas {len(df_consumo)} linhas de consumo")
        upsert(base_url, args.supabase_key, "consumos", build_consumos_payload(df_consumo), "matricula,ano_mes")
    else:
        print("Nenhuma aba/arquivo de consumos encontrada, pulando.")

    print("Importação concluída.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
