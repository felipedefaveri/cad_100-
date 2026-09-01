-- Remove a trava de integridade referencial entre consumos e hidrometros.
-- Motivo: a planilha de consumo pode citar hidrometros que nao aparecem na
-- planilha de cadastro atual (removidos, substituidos, exportacoes feitas em
-- datas diferentes). Esses registros "orfaos" ficam gravados em consumos mas
-- simplesmente nao aparecem no app (a view usa LEFT JOIN a partir de
-- hidrometros), entao nao ha problema em manter esses dados sem a trava.
-- Rode isto no SQL Editor do Supabase.

alter table public.consumos drop constraint if exists consumos_numero_hidrometro_fkey;
