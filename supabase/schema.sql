-- Schema do "repositório online" de Hidrômetros (HD) para o app de consulta em campo.
-- Rode este script no SQL editor do seu projeto Supabase (https://app.supabase.com).

-- Extensão usada para updated_at automático
create extension if not exists moddatetime schema extensions;

-- Tabela principal: um registro por HD (hidrômetro)
create table if not exists public.hidrometros (
  matricula text primary key,          -- número/matrícula do HD, chave de busca no app
  endereco text,                       -- endereço/local do HD
  bairro text,
  economias integer not null default 0,-- quantidade de economias ligadas a esse HD
  ativo boolean not null default true, -- se o HD está ativo
  observacoes text,
  atualizado_em timestamptz not null default now()
);

comment on table public.hidrometros is 'Cadastro de hidrômetros (HDs) sincronizado a partir da planilha oficial.';

-- Histórico de consumo mensal (para calcular últimos 12 meses e média)
create table if not exists public.consumos (
  id bigint generated always as identity primary key,
  matricula text not null references public.hidrometros(matricula) on delete cascade,
  ano_mes date not null,               -- sempre gravar como primeiro dia do mês, ex: 2026-07-01
  volume_m3 numeric(12,2) not null default 0,
  unique (matricula, ano_mes)
);

create index if not exists consumos_matricula_ano_mes_idx
  on public.consumos (matricula, ano_mes desc);

-- Mantém atualizado_em em dia sempre que o HD for alterado pelo importador
drop trigger if exists set_hidrometros_updated_at on public.hidrometros;
create trigger set_hidrometros_updated_at
  before update on public.hidrometros
  for each row execute function extensions.moddatetime(atualizado_em);

-- View pronta usada pelo app: HD + consumo médio e do último mês disponível
create or replace view public.hidrometros_resumo as
select
  h.matricula,
  h.endereco,
  h.bairro,
  h.economias,
  h.ativo,
  h.atualizado_em,
  count(c.id) filter (where c.ano_mes >= (date_trunc('month', now()) - interval '11 months')) as meses_com_leitura,
  round(avg(c.volume_m3) filter (where c.ano_mes >= (date_trunc('month', now()) - interval '11 months')), 2) as consumo_medio_12m,
  (
    select c2.volume_m3 from public.consumos c2
    where c2.matricula = h.matricula
    order by c2.ano_mes desc
    limit 1
  ) as consumo_ultimo_mes
from public.hidrometros h
left join public.consumos c on c.matricula = h.matricula
group by h.matricula, h.endereco, h.bairro, h.economias, h.ativo, h.atualizado_em;

-- Segurança: o app do vistoriante só pode LER dados (nunca escrever).
-- A importação da planilha deve usar a service_role key (que ignora RLS), nunca a anon key.
alter table public.hidrometros enable row level security;
alter table public.consumos enable row level security;

drop policy if exists "Leitura publica hidrometros" on public.hidrometros;
create policy "Leitura publica hidrometros"
  on public.hidrometros for select
  using (true);

drop policy if exists "Leitura publica consumos" on public.consumos;
create policy "Leitura publica consumos"
  on public.consumos for select
  using (true);
