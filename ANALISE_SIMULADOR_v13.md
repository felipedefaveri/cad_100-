# Simulador de Faturamento — varredura e v13

Arquivos analisados: `simulador_faturamento_12.html` e `LeverPro_1.1_Receita_por_economias_Água_-_CAI.xlsx`.
Resultado: `simulador_faturamento_13.html` (mesma lógica de cálculo; só apresentação, estado e fluxo de trabalho).

## O que a varredura mostrou

**Planilha × simulador**
- A planilha tem 17 abas de tarifa, todas no layout que o parser (`parseTabSheet`) espera: cabeçalho `Mmm-AAAA` na linha 1 (Ago/2026 a Dez/2027 — o simulador usa os últimos 12 = Jan–Dez/2027), blocos INDUSTRIAL / RESIDÊNCIAL / COMERCIAL / PUBLICA, seções `Nº DE ECONOMIAS`, `VOLUME CONSUMIDO`, `TARIFA (R$)`, `DESCONTO (%)`.
- As células calculadas da planilha (CONSUMO MÉDIO, VOLUME FATURADO, VALOR FATURADO) vêm **sem valor em cache** — só as fórmulas. Por isso o simulador refazer a conta a partir das entradas (e não ler RESUMO/RESUMO TARIFAS) é a decisão certa e continua valendo.
- Rodando o parser do próprio simulador na planilha: 17 tarifas, 32 blocos com dados, total 2027 = R$ 198,5 mi. Os dados **embutidos** na v12 eram de uma versão anterior (R$ 198,7 mi; AGUA NORMAL RES/COM e AGUA_ESGOTO POPULAR RES tinham economias que hoje estão zeradas; TARIFA NORMAL – ESGOTO TRATADO PUB e outros mudaram). A v13 embute os dados desta planilha.
- Os 2026 embutidos (`DEFAULT26`) continuam os mesmos — vale conferir, porque 2027 base × 2026 dá +54%, o que sugere que o 2026 de ÁGUA (R$ 139,6 mi) está numa base diferente do 2027 (R$ 198,5 mi, que inclui as abas de esgoto do arquivo de água).

**Código (sem alterar)**
- `sheetToAoa`, `clamp` e `engine` estão definidos duas vezes; a segunda `engine` (por economia média) sobrescreve a primeira. Nenhuma das duas é usada na tela — o motor real é `engineBands` + `monthDetail`. `aggregate` e `parseSummary` também não são usados pela interface. Inofensivo; ficou como está para não mexer na lógica.
- `if (at(ints[k], c) !== lim[k]) lim[k] = lim[k];` em `parseTabSheet` não faz nada (limite das faixas lido só do primeiro mês).

## O que a v13 acrescenta (sem trocar a lógica)

| Recurso | O que resolve |
|---|---|
| **Cenários** (salvar / carregar / renomear / excluir, tabela comparativa) | Comparar simulações lado a lado: total simulado, efeito sobre a base e sobre 2026, com a linha "Base (sem ajustes)" e a linha "Ajustes atuais". Cada cenário é recalculado pelo mesmo `compute()`. Guardados no navegador e embutidos no "Salvar simulador". |
| **Comparativo consolidado** | Tabela única 2026 × 2027 base × 2027 simulado por categoria, no recorte ÁGUA / ESGOTO / ambos. É o número do KPI aberto por categoria, sem precisar entrar nos painéis. |
| **Ajustes ativos** | Lista tudo o que difere da base (tarifa · categoria · faixa · mês), com fator, MED P/ECO base → simulado e Δ R$; "remover" desfaz só aquele ajuste; "Copiar lista" cola no Excel. Edições uniformes (linha anual / TOTAL) aparecem como uma linha "todas as faixas · Jan–Dez". |
| **Desfazer** (botão e Ctrl+Z) | Histórico de até 80 passos dos fatores; digitação contínua no mesmo campo vira um passo só. |
| **Barra fixa** | Base / simulado / efeito / nº de ajustes acompanham a rolagem, com Desfazer, Salvar cenário e Topo. |
| **Filtro de tarifas** | Por nome e "só ajustadas", em cada segmento. |
| **Gráfico mês a mês** | Base × simulado Jan–Dez com o Δ de cada mês, ao lado do gráfico por categoria. |
| **Salvar simulador (HTML)** | Gera uma cópia do arquivo com as planilhas importadas, os 2026 (consolidado e por tarifa) e os cenários embutidos. É o fluxo de atualização: importar planilha nova → salvar simulador → distribuir. |
| **Exportar Excel** | Ganha as abas AJUSTES e CENÁRIOS. |

## Como atualizar daqui em diante
1. Abrir `simulador_faturamento_13.html`, importar a planilha de ÁGUA e/ou ESGOTO.
2. Conferir os 2026 (resumo consolidado e por tarifa).
3. "Salvar simulador (HTML)" → o arquivo gerado já nasce com tudo embutido.

## Validação
Testado em Chromium headless (Playwright): carregamento sem erros, edição por linha e por célula, desfazer, salvar/carregar/remover cenário, remover ajuste, filtro, barra fixa, gráfico mensal, exportação Excel, "Salvar simulador" e reabertura do arquivo salvo (cenários e dados preservados), importação da planilha enviada.

## v14 — mais próximo de um sistema (só interface)

| Recurso | O que faz |
|---|---|
| **Etapas no topo** (Dados → Base 2026 → Simular → Comparar cenários → Exportar/salvar) | Mostram o andamento (✓ quando feito, com o status em texto) e levam à parte certa da tela ao clicar. |
| **Simulação rápida** | Formulário: segmento, categoria, tarifa, mês e % de variação do consumo médio (com atalhos ±1/2/5%). Prévia do efeito em R$ antes de aplicar. Usa `setUniform` + `monthDetail`, o mesmo caminho da "Variação em todas". |
| **Dicas em cada campo** | Passar o mouse (ou focar) em qualquer título de coluna, campo editável, KPI ou seção mostra o que é e como usar; campos editáveis mostram também o valor base. Pode ser desligado no cabeçalho. |
| **Passo a passo** | Tour de 13 passos com destaque na própria tela (setas ← →, Esc fecha). Oferecido na primeira abertura; botão no cabeçalho para repetir. |
| **Glossário** | Seção no fim com todos os termos (ECO FAT, MED P/ECO, VOL FAT, FAT P/ECO, faixa, Q x P, base, simulado, fator, cenário…). |

Validado em Chromium headless: regressão da v13 completa + dicas (cabeçalho, campo, KPI), simulação rápida (prévia e aplicação), tour completo, navegação por etapas, marcação da etapa 5 ao exportar, desligar dicas, importação atualizando a lista de tarifas.

## v22 — bate com a planilha ao centavo (arredondamento de 6 casas)

Conferência com o levantamento feito no Excel (Jan–Dez/2027, ÁGUA): a planilha usa `ROUND(…, 6)` na TARIFA FINAL, no consumo médio e no excedente; o motor herdado da v12 usava 2 casas. Resultado: simulador R$ 187.647.809 × planilha R$ 187.627.483,75 (+R$ 20.325, 0,011 %). Com `round2` passando a 6 casas: **R$ 187.627.483,73** — diferença de R$ 0,02 no total e todas as 17 abas iguais ao centavo (ex.: ESGOTO TRATADO 84.224.649,80; ESGOTO COLETADO 60.628.171,61; AGUA_ESGOTO NORMAL 33.049.212,92). Os dados de ÁGUA foram reembutidos a partir da planilha enviada em 29/09; os meses do ESGOTO embutido foram reprocessados com a nova regra a partir das entradas guardadas (a tarifa guardada tinha 2 casas, então o esgoto só bate ao centavo depois de reimportar o LeverPro de esgoto).

## v21 — comparativo vira diagnóstico 2026 × 2027

O card "Comparativo consolidado" passa a ser **Comparativo e diagnóstico**: por categoria e total, ECO FAT, **MED P/ECO**, **FAT P/ECO** e **VALOR** em 2026 × 2027 base × 2027 simulado, com Δ% (sim × 2026) destacado acima da tolerância (laranja) e do dobro (vermelho). Abaixo, o diagnóstico por categoria: valor simulado × meta (2026 × (1 + meta)), decomposição do desvio (economias, consumo médio, faturado por economia, tarifa média) e o **MED P/ECO de 2027 necessário** para bater a meta (`diagSolve`, bissecção sobre um fator uniforme com `monthDetail`), com botão "Aplicar em 2027" que grava o fator via `setUniform` (entra em Ajustes ativos, cenários e Desfazer). Tolerância e meta são campos persistidos. Teste: meta +5% → "MED 8,14 → 8,63 (× 1,06)"; aplicar deixou RES exatamente na meta (143.120.324); Desfazer voltou.

## v20 — campos de 2026 manuais e independentes

Os cinco campos de 2026 da seção 3 (ECO FAT, MED P/ECO, VOL MED, FAT P/ECO, VALOR — por categoria e TOTAL) e os da comparação por tarifa (ECO, MED, FAT, VALOR) são **manuais**: `S.m26[seg][cat][campo]` / `S.tar26[seg][tarifa][cat][campo]`. O que é digitado vale como está e **não recalcula os vizinhos**; campo vazio = calculado da base por faixa e mês (seção 5). `eff26Full` monta o efetivo (manual > calculado) e o TOTAL, se vazio, é a soma/média ponderada dos efetivos por categoria. Amarelo = manual; botão "Apagar campos manuais de 2026"; Desfazer, "Salvar simulador" (`DEFAULT_M26`) e localStorage preservam. As edições da seção 5 continuam mudando a base (e portanto os calculados).

## v19 — tarifas: 2026 = TARIFA (R$), 2027 = TARIFA FINAL (R$)

Conferido na planilha: `TARIFA FINAL (R$) = ROUND(TARIFA × (1 + reajuste) × (1 − desconto), 6)`; o simulador já calculava exatamente isso para 2027 (`tf`). Para 2026 o parser agora lê a linha **TARIFA (R$)** (com o desconto do cliente, sem reajuste) do último mês de 2026 da planilha (`tarPrev`, com `tarPrevSrc` = "TARIFA (R$) de Dez-2026"); sem colunas de 2026, usa a TARIFA (R$) do 1º mês de 2027 (que, pela convenção da planilha, é a tarifa antes do reajuste) e avisa. A leitura de um LeverPro pelas colunas de 2026 também usa TARIFA (R$) sem reajuste. Verificado: AGUA_ESGOTO NORMAL RES → 2026 [6,11 · 14,05 · 26,27 · 45,82 · 48,88], 2027 [6,67 · 15,33 · 28,67 · 50,00 · 53,34].

Observação: a planilha guarda a TARIFA FINAL com 6 casas (ex.: 6,667952); o motor herdado da v12 arredonda a tarifa a 2 casas (6,67) — diferença de até ~0,05 % no valor. Mantido como estava (sem trocar a lógica); trocar para 6 casas é uma linha (`round2` → `round6` na tarifa) se quiserem bater centavo a centavo com o Excel.

## v18 — FAT P/ECO e VALOR de 2026 editáveis (seção 3)

São resultados da regra escalonada, então `y26Solve` acha por bissecção o fator de volume que produz o valor digitado (economias e tarifas ficam) e aplica `y26Scale`; MED P/ECO, VOL MED e o outro campo recalculam. Abaixo do mínimo faturável (faixa 1 × economias) avisa e aplica o mínimo. Teste: VALOR RES 124,9 → 130,0 mi resolvido exato (MED 8,14 → 8,54), FAT P/ECO 12,00 exato, TOTAL 180 mi, caso inatingível avisado, Desfazer restaura.

## v17 — TARIFA FONTE ALTERNATIVA tratada à parte

`EXCLUDED_TABS = ['TARIFA FONTE ALTERNATIVA']`: em `prepSeg`, os blocos dessas abas saem de `seg.blocks` (vão para `seg.excluded`), então ficam fora de todos os somatórios, tabelas, grades, cenários, gráficos, simulação rápida, base 2026 e Excel — de ÁGUA ou ESGOTO, hoje só existe em ESGOTO. Continuam embutidos no arquivo ("Salvar simulador" preserva) e a tarifa aparece na lista com o aviso "tratada à parte". O status da importação informa quanto ficou de fora. Teste: bloco de R$ 67,9 mi injetado na aba não alterou o total de ESGOTO.

## v16 — economias faturadas editáveis (2026 e 2027)

Regra: ao mudar as economias, o **consumo médio por economia fica constante** — o volume acompanha e VOL FAT/VALOR recalculam pela regra escalonada (inclusive o mínimo da faixa 1).

| Peça | O que faz |
|---|---|
| **2027: fator `ke`** (bloco × mês × faixa, como `kf`) | `ecoAdjMonth` refaz o mês com economias × k e volume × k (`recalcMonth`); depois `monthDetail` aplica o fator de consumo. A base continua a planilha; o simulado inclui os dois efeitos. `applyEdit` usa o mês já ajustado por economias como base (`mEff`), então volume e economias não se multiplicam duas vezes. |
| **Onde editar em 2027** | Grades faixa × mês no modo **ECO FAT (editar)** (e consolidado mês a mês); coluna **ECO FAT simulado** nas linhas anuais de cada tarifa (seção 1) e por categoria/total (seção 3); **Simulação rápida** com "O que varia: economias"; colar do Excel e modelo Excel (linhas `ECO FAT`, importadas antes de MED/VOL). |
| **2026** | `y26ScaleEco`: economias e volumes escalados na base; campos ECO FAT 2026 na seção 3 (categoria/total) e na comparação por tarifa; célula a célula na seção 5. |
| **Onde aparece** | ECO FAT simulado com Δ nas tabelas, MED P/ECO = volume ÷ economias simuladas, "Ajustes ativos" (linhas marcadas *economias*), cenários (guardam `ke`), Desfazer, Excel (coluna ECO FAT simulado; AJUSTES com TIPO). |

Validado em Chromium headless: +10% de economias numa categoria → ECO 470.844 → 517.928, VOL MED +10%, MED P/ECO inalterado (8,52), VALOR +R$ 6,38 mi; célula de faixa × mês dobrada; consolidado por mês; seção 3 (2027 e 2026); simulação rápida por economias (+5% COM = +R$ 2,45 mi, prévia = aplicado); cenário salvo/recarregado com economias; modelo 2027 ida-e-volta; regressões v13–v15 sem erros.

## v15 — base 2026 detalhada (economias, volume e tarifa por faixa × mês)

O 2026 deixa de ser três números digitados por categoria e passa a ser uma base completa, calculada com a **mesma regra escalonada** de 2027.

| Peça | O que faz |
|---|---|
| `recalcMonth(bloco, entradas)` | Refaz um mês a partir de economias, volume medido, tarifa final por faixa e volume Q x P — cópia fiel da conta de `parseTabSheet` (mínimo da faixa 1, excedentes com `round2`, Q x P). Teste: reproduz os 708 meses embutidos com diferença ≤ 1e-9. |
| `parseTabSheet(name, aoa, year)` | Com `year`, lê as colunas daquele ano (ex.: `Jan-2026 … Dez-2026`) mês a mês; meses ausentes ficam zerados. Sem `year`, além dos 12 meses de 2027 captura `tarPrev` = tarifa final do último mês do ano anterior (Dez/2026 — a **tarifa sem o reajuste de 2027**). Os dados embutidos de ÁGUA foram regenerados com `tarPrev`. |
| `S.y26[seg]["tarifa\|categoria"]` | Economias, volume medido e tarifa por faixa × mês. Guardado no navegador e embutido no "Salvar simulador" (`DEFAULT_Y26`). Entra no Desfazer. |
| `eff26()` / `effTar26()` | 2026 efetivo: quando a categoria/tarifa tem dados detalhados, MED P/ECO, FAT P/ECO e VALOR vêm do cálculo e os campos digitados ficam bloqueados; senão vale o digitado. Usado em KPIs, comparativo consolidado, comparação por tarifa, cenários, gráfico, etapas e Excel. |
| **Um único 2026, ligado de ponta a ponta** | A base 2026 por faixa × mês é a **única fonte** (não há mais "2026 digitado"). Ela nasce com as mesmas economias e volumes da planilha à **tarifa de 2026** (`y26Default`; onde a planilha não trouxe tarifa 2026 — Esgoto embutido — usa a de 2027 e avisa). Editar em qualquer nível reescreve os volumes dessa base: célula (seção 5), **MED P/ECO ou VOL MED por categoria/total** (seção 3) e **MED P/ECO por tarifa** (comparação por tarifa) escalam os volumes de todas as faixas e meses do alcance (`y26Scale`). FAT P/ECO, VALOR, KPIs, comparativo consolidado, por tarifa, cenários, gráficos e Excel recalculam do mesmo número. Desfazer cobre tudo. |
| Seção **5 · Base 2026 por tarifa, faixa e mês** | Uma grade por tarifa/categoria: por faixa, linhas *economias*, *volume medido*, *tarifa* (editáveis, azul) e *valor faturado* (calculado); totais ECO FAT, VOL MED, VOL FAT, VALOR, MED P/ECO, FAT P/ECO; coluna ANO. A tarifa inicial é a de Dez/2026 da planilha (ou a de 2027 quando o arquivo não tem colunas de 2026 — caso do Esgoto embutido; importar o LeverPro de esgoto novamente corrige). |
| **Colar do Excel** | Ctrl+V numa célula preenche o bloco copiado para a direita (meses) e para baixo (linhas editáveis); aceita `1.234,56`, `1234.56`, `R$`. |
| **Grades 2027 (simulação)** | Nas grades faixa × mês de cada tarifa (MED P/ECO ou VOL MED), **Ctrl+V** cola um bloco copiado do Excel (a partir da célula focada, meses à direita e faixas abaixo) e cada célula passa pelo `applyEdit` normal. **Baixar modelo (Excel)** gera TARIFA, CATEGORIA, FAIXA, MÉTRICA, Jan…Dez com os valores simulados atuais (sem arredondar — reimportar sem mexer não cria ajuste); **Importar ajustes (Excel)** aplica o modelo preenchido. |
| **Importar planilha 2026** | Reconhece (a) o **modelo** gerado por "Baixar modelo (Excel)" — colunas TARIFA, CATEGORIA, FAIXA, MÉTRICA, Jan…Dez — e (b) uma planilha **LeverPro** com colunas de 2026 (os 5 meses Ago–Dez/2026 do arquivo atual entram; os demais ficam para completar; a tarifa dos meses ausentes mantém o padrão). |

Validado em Chromium headless: conta da faixa 1 com mínimo (100 eco × 8 m³ + 50 eco × 15 m³ → VOL FAT 1.750, VALOR = 1.500 × 6,11 + 250 × 14,05), campos digitados bloqueados quando há detalhado, KPI 2026 recalculado, Desfazer devolvendo o 2026, colagem 2 × 3 células, modelo exportado e reimportado (432 linhas / 32 blocos), LeverPro com 5 meses de 2026, cenários/Excel/Salvar simulador com o 2026 embutido e reabertura; regressões v13 e v14 sem erros.
