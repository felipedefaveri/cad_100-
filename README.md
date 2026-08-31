# Consulta HD — app de campo para vistoriantes

App para o vistoriante consultar, em campo, dados de um HD (hidrômetro) pela
matrícula: quantas **economias** ele atende, se está **ativo**, e o
**consumo dos últimos 12 meses / média**. Os dados vêm de um repositório
online (Supabase) que é atualizado a partir da planilha oficial exportada
pela empresa.

## Como as peças se conectam

```
planilha (.xlsx/.csv)  --import/import_hd.py-->  Supabase (repositório online)  --app-->  celular do vistoriante
```

- **`supabase/schema.sql`** — schema do banco online (tabelas `hidrometros` e
  `consumos`, mais a view `hidrometros_resumo` já com média de 12 meses).
- **`import/`** — script Python que lê a planilha exportada e atualiza o
  Supabase. Rode sempre que houver uma planilha nova.
- **`mobile/`** — app Expo (React Native) que os vistoriantes instalam no
  celular (Android/iOS) e usam para buscar um HD pela matrícula.

## 1. Criar o repositório online (Supabase)

1. Crie uma conta gratuita em https://supabase.com e um novo projeto.
2. Em **SQL Editor**, cole o conteúdo de `supabase/schema.sql` e execute.
3. Em **Settings → API**, anote:
   - `Project URL`
   - `anon public` key (vai no app)
   - `service_role` key (vai **só** no script de importação — nunca no app)

## 2. Importar a planilha

```bash
cd import
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY
```

Monte a planilha `.xlsx` com duas abas (ou use dois `.csv` separados):

- **`hidrometros`**: `matricula | endereco | bairro | economias | ativo`
- **`consumos`**: `matricula | ano_mes | volume_m3` (uma linha por HD/mês,
  `ano_mes` no formato `YYYY-MM`)

Rode a importação:

```bash
python import_hd.py --file caminho/para/planilha.xlsx
# ou
python import_hd.py --hidrometros-csv cadastro.csv --consumos-csv consumos.csv
```

O script faz *upsert* (atualiza quem já existe, cria quem é novo) — pode
rodar quantas vezes quiser, sempre que sair uma planilha nova. Se quiser
automatizar, agende esse comando (cron, Task Scheduler, GitHub Actions,
etc.) para rodar todo dia/semana.

## 3. Configurar e rodar o app

```bash
cd mobile
npm install
cp .env.example .env   # preencha EXPO_PUBLIC_SUPABASE_URL e EXPO_PUBLIC_SUPABASE_ANON_KEY
npm start
```

Abra no celular com o app **Expo Go** (escaneando o QR code) para testar
rapidamente durante o desenvolvimento, sem precisar gerar instalador.

## 4. Gerar o app instalável no celular

O app é feito em Expo/React Native, então o mesmo código vira um app
**nativo de verdade** para Android e iOS. Para instalar sem passar pela
loja, use o **EAS Build** (serviço gratuito da Expo para builds na nuvem):

```bash
cd mobile
npm install -g eas-cli
eas login                 # crie uma conta gratuita em expo.dev se não tiver
eas build:configure       # na primeira vez, para vincular o projeto
```

**Android** (gera um `.apk` instalável direto no celular, sem Play Store):

```bash
npm run build:android
```

Ao terminar, o EAS mostra um link/QR code — abra no celular e instale o
`.apk` (é preciso permitir "instalar de fontes desconhecidas" uma vez).

**iOS**: build nativo de iOS exige uma conta paga da Apple Developer
Program (US$99/ano), mesmo para instalar só no celular do time (via ad hoc
ou TestFlight) — isso é uma exigência da Apple, não desta ferramenta.
Com a conta criada:

```bash
npm run build:ios
```

e distribua via **TestFlight** (o app aparece na App Store apenas para
quem você convidar).

> Antes do primeiro build, edite em `mobile/app.json` os campos
> `ios.bundleIdentifier` e `android.package` (ex: `br.com.suaempresa.consultahd`)
> para usar o domínio/nome real da sua empresa, e troque os ícones em
> `mobile/assets/`.

## Segurança

- O app usa apenas a chave **anon** do Supabase, com permissão de leitura
  (Row Level Security habilitado, só `SELECT`) — o vistoriante nunca
  consegue alterar dados pelo app.
- A chave **service_role** (que tem permissão de escrita) fica só no seu
  computador/servidor, no `import/.env`, e nunca deve ser commitada nem
  colocada no app.
