-- Migração aditiva: adiciona o detalhamento de economias por tipo
-- (residencial/comercial/industrial/pública) sem apagar dados já importados.
-- Rode isto no SQL Editor do Supabase (não precisa rodar o schema.sql de novo).

alter table public.hidrometros
  add column if not exists eco_residencial integer not null default 0,
  add column if not exists eco_comercial integer not null default 0,
  add column if not exists eco_industrial integer not null default 0,
  add column if not exists eco_publica integer not null default 0;

create or replace view public.hidrometros_resumo as
select
  h.numero_hidrometro,
  h.matricula,
  h.endereco,
  h.bairro,
  h.economias,
  h.eco_residencial,
  h.eco_comercial,
  h.eco_industrial,
  h.eco_publica,
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
group by h.numero_hidrometro, h.matricula, h.endereco, h.bairro, h.economias,
  h.eco_residencial, h.eco_comercial, h.eco_industrial, h.eco_publica, h.ativo, h.atualizado_em;
