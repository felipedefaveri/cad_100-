-- Schema do "repositório online" de Hidrômetros (HD) para o app de consulta em campo.
-- Rode este script no SQL editor do seu projeto Supabase (https://app.supabase.com).
--
-- Se você já rodou uma versão anterior deste script (antes de existir a coluna
-- `numero_hidrometro`) e ainda não importou dados reais, pode simplesmente rodar
-- este arquivo de novo por cima: os `drop ... if exists` abaixo cuidam disso.

-- Extensão usada para updated_at automático
create extension if not exists moddatetime schema extensions;

drop view if exists public.hidrometros_resumo;
drop table if exists public.consumos;
drop table if exists public.hidrometros;

-- Tabela principal: um registro por HD (hidrômetro) físico
create table public.hidrometros (
  numero_hidrometro text primary key,  -- número de série gravado no aparelho: o que o
                                        -- vistoriante vê e digita no app em campo
  matricula text,                      -- matrícula da economia/imóvel no sistema comercial
                                        -- (pode ser diferente do nº do hidrômetro)
  endereco text,                       -- endereço/local do HD
  bairro text,
  economias integer not null default 0,-- quantidade de economias ligadas a esse HD
  ativo boolean not null default true, -- se o HD está ativo
  observacoes text,
  atualizado_em timestamptz not null default now()
);

comment on table public.hidrometros is 'Cadastro de hidrômetros (HDs) sincronizado a partir da planilha oficial.';

create index hidrometros_matricula_idx on public.hidrometros (matricula);

-- Histórico de consumo mensal (para calcular últimos 12 meses e média)
create table public.consumos (
  id bigint generated always as identity primary key,
  numero_hidrometro text not null references public.hidrometros(numero_hidrometro) on delete cascade,
  ano_mes date not null,               -- sempre gravar como primeiro dia do mês, ex: 2026-07-01
  volume_m3 numeric(12,2) not null default 0,
  unique (numero_hidrometro, ano_mes)
);

create index consumos_hidrometro_ano_mes_idx
  on public.consumos (numero_hidrometro, ano_mes desc);

-- Mantém atualizado_em em dia sempre que o HD for alterado pelo importador
drop trigger if exists set_hidrometros_updated_at on public.hidrometros;
create trigger set_hidrometros_updated_at
  before update on public.hidrometros
  for each row execute function extensions.moddatetime(atualizado_em);

-- View pronta usada pelo app: HD + consumo médio e do último mês disponível
create or replace view public.hidrometros_resumo as
select
  h.numero_hidrometro,
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
    where c2.numero_hidrometro = h.numero_hidrometro
    order by c2.ano_mes desc
    limit 1
  ) as consumo_ultimo_mes
from public.hidrometros h
left join public.consumos c on c.numero_hidrometro = h.numero_hidrometro
group by h.numero_hidrometro, h.matricula, h.endereco, h.bairro, h.economias, h.ativo, h.atualizado_em;

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
