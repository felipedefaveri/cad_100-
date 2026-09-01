# Consulta HD — app de campo para vistoriantes

App para o vistoriante consultar, em campo, dados de um HD (hidrômetro) pelo
**número gravado no aparelho**: quantas **economias** ele atende, se está
**ativo**, e o **consumo dos últimos 12 meses / média**. Os dados vêm de um
repositório online (Supabase) que é atualizado a partir da planilha oficial
exportada pela empresa.

> Número do hidrômetro × matrícula: são campos diferentes. O **número do
> hidrômetro** é o de série, gravado no aparelho físico — é o que o
> vistoriante vê no local e digita no app. A **matrícula** é o número da
> conta/economia no sistema comercial e fica só como informação
> complementar na tela de detalhe.

## Como as peças se conectam

```
planilha (.xlsx/.csv)  --import/import_hd.py-->  Supabase (repositório online)  --app-->  celular do vistoriante
```

- **`supabase/schema.sql`** — schema do banco online (tabelas `hidrometros` e
  `consumos`, mais a view `hidrometros_resumo` já com média de 12 meses).
- **`import/`** — script Python que lê a planilha exportada e atualiza o
  Supabase. Rode sempre que houver uma planilha nova.
- **`mobile/`** — app Expo (React Native) que os vistoriantes instalam no
  celular (Android/iOS) e usam para buscar um HD pelo número do aparelho.

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

O script já reconhece automaticamente o layout de exportação padrão da
concessionária (ignora acentos/pontuação/maiúsculas ao ler as colunas), por
exemplo:

- **Cadastro** (aba/arquivo `hidrometros`): `NRO.LIGAÇÃO`, `CLIENTE`,
  `ECONOMIA`, `ECO.RES.`, `ECO.COM.`, `ECO.IND.`, `ECO.PUB.`, `LOGRADOURO`,
  `LOGRADOURO_NÚMERO`, `LOGRADOURO_COMPLEMENTO`, `BAIRRO`,
  `SITUAÇÃO ÁGUA`, `Nº HIDRÔMETRO`.
  - `Nº HIDRÔMETRO` é obrigatório — é a chave de busca no app.
  - `NRO.LIGAÇÃO` vira a `matricula` (informação complementar).
  - `LOGRADOURO` + `LOGRADOURO_NÚMERO` + `LOGRADOURO_COMPLEMENTO` são
    concatenados automaticamente no endereço.
  - `SITUAÇÃO ÁGUA` define o status ativo/inativo — hoje o script reconhece
    termos como `LIGADA`/`ATIVA` (ativo) e `CORTADA`/`SUSPENSA`/`INATIVA`
    (inativo). Se aparecer um termo diferente, o script **avisa no final**
    quais termos não reconheceu (e trata como ativo por padrão, pra nunca
    esconder um HD sem querer) — é só me falar o termo que eu adiciono no
    mapeamento.
  - Quantidade de economias: se a planilha tiver `ECO.RES.`, `ECO.COM.`,
    `ECO.IND.` e/ou `ECO.PUB.`, o script soma essas colunas e usa como
    `economias` (é o que a exportação real da concessionária traz de
    confiável). Só usa a coluna `ECONOMIA` como total pronto se nenhuma
    dessas quatro existir na planilha.
  - `CLIENTE` não é importado (o app não precisa do nome do cliente, só
    dados técnicos do HD).
- **Histórico de consumo** (aba/arquivo `consumos`) — **não vem na planilha
  de cadastro**, precisa de uma exportação separada com uma linha por
  HD/mês: `numero_hidrometro | ano_mes | volume_m3` (`ano_mes` no formato
  `YYYY-MM`).

Também funciona com o layout simplificado `numero_hidrometro | matricula |
endereco | bairro | economias | ativo`, se você preferir montar a planilha
assim.

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

### Atalho para reimportar sem digitar comando (Windows)

O arquivo `import/atualizar_hidrometros.bat` já vem pronto: dê **2 cliques**
nele sempre que tiver uma planilha nova, e ele roda a importação sozinho
(usa o `.env` e o caminho de planilha já configurados). Se o caminho da
planilha mudar, edite a linha `set PLANILHA=...` dentro do arquivo (botão
direito → Editar, ou abra com o Bloco de Notas).

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

## Como o app fica sempre atualizado

O app **não guarda os dados no celular** — toda vez que o vistoriante busca
um HD, ele consulta o Supabase na hora, ao vivo. Ou seja: assim que você
reimporta a planilha (passo 2), a próxima busca no app já traz os dados
novos, sem precisar reinstalar nem atualizar o `.apk`.

Só é preciso gerar um `.apk` novo (passo 4) se o **código do app** mudar
(uma tela nova, um campo a mais, etc.) — nunca por causa de dados.

Por isso não existe (nem precisa existir) um botão de "atualizar banco de
dados" dentro do app: quem atualiza o banco é sempre o script de
importação, rodado no computador (passo 2 / atalho `.bat` acima), e o app
só lê o que estiver lá no momento da consulta. Na tela de detalhe do HD dá
pra "puxar para atualizar" (gesto de arrastar para baixo) caso queira forçar
uma nova consulta sem sair da tela.

## Segurança

- O app usa apenas a chave **anon** do Supabase, com permissão de leitura
  (Row Level Security habilitado, só `SELECT`) — o vistoriante nunca
  consegue alterar dados pelo app.
- A chave **service_role** (que tem permissão de escrita) fica só no seu
  computador/servidor, no `import/.env`, e nunca deve ser commitada nem
  colocada no app.
