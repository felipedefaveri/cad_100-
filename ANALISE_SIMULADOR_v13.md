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

## v15 — base 2026 detalhada (economias, volume e tarifa por faixa × mês)

O 2026 deixa de ser três números digitados por categoria e passa a ser uma base completa, calculada com a **mesma regra escalonada** de 2027.

| Peça | O que faz |
|---|---|
| `recalcMonth(bloco, entradas)` | Refaz um mês a partir de economias, volume medido, tarifa final por faixa e volume Q x P — cópia fiel da conta de `parseTabSheet` (mínimo da faixa 1, excedentes com `round2`, Q x P). Teste: reproduz os 708 meses embutidos com diferença ≤ 1e-9. |
| `parseTabSheet(name, aoa, year)` | Com `year`, lê as colunas daquele ano (ex.: `Jan-2026 … Dez-2026`) mês a mês; meses ausentes ficam zerados. Sem `year`, além dos 12 meses de 2027 captura `tarPrev` = tarifa final do último mês do ano anterior (Dez/2026 — a **tarifa sem o reajuste de 2027**). Os dados embutidos de ÁGUA foram regenerados com `tarPrev`. |
| `S.y26[seg]["tarifa\|categoria"]` | Economias, volume medido e tarifa por faixa × mês. Guardado no navegador e embutido no "Salvar simulador" (`DEFAULT_Y26`). Entra no Desfazer. |
| `eff26()` / `effTar26()` | 2026 efetivo: quando a categoria/tarifa tem dados detalhados, MED P/ECO, FAT P/ECO e VALOR vêm do cálculo e os campos digitados ficam bloqueados; senão vale o digitado. Usado em KPIs, comparativo consolidado, comparação por tarifa, cenários, gráfico, etapas e Excel. |
| **Base já preenchida + chave de origem** | A base 2026 de cada bloco nasce com as **mesmas economias e volumes da planilha à tarifa de 2026** (`y26Default`), então qualquer ajuste é incremental e reflete na hora nos KPIs/comparativos. A chave "2026 usado nos indicadores: detalhado / digitado" (por segmento, na seção 5) escolhe a origem — sem mistura por categoria. Padrão: detalhado onde a planilha trouxe tarifa 2026 (Água), digitado onde não trouxe (Esgoto embutido, com aviso). Rótulos do KPI e do comparativo mostram a origem. |
| Seção **5 · Base 2026 por tarifa, faixa e mês** | Uma grade por tarifa/categoria: por faixa, linhas *economias*, *volume medido*, *tarifa* (editáveis, azul) e *valor faturado* (calculado); totais ECO FAT, VOL MED, VOL FAT, VALOR, MED P/ECO, FAT P/ECO; coluna ANO. A tarifa inicial é a de Dez/2026 da planilha (ou a de 2027 quando o arquivo não tem colunas de 2026 — caso do Esgoto embutido; importar o LeverPro de esgoto novamente corrige). |
| **Colar do Excel** | Ctrl+V numa célula preenche o bloco copiado para a direita (meses) e para baixo (linhas editáveis); aceita `1.234,56`, `1234.56`, `R$`. |
| **Grades 2027 (simulação)** | Nas grades faixa × mês de cada tarifa (MED P/ECO ou VOL MED), **Ctrl+V** cola um bloco copiado do Excel (a partir da célula focada, meses à direita e faixas abaixo) e cada célula passa pelo `applyEdit` normal. **Baixar modelo (Excel)** gera TARIFA, CATEGORIA, FAIXA, MÉTRICA, Jan…Dez com os valores simulados atuais (sem arredondar — reimportar sem mexer não cria ajuste); **Importar ajustes (Excel)** aplica o modelo preenchido. |
| **Importar planilha 2026** | Reconhece (a) o **modelo** gerado por "Baixar modelo (Excel)" — colunas TARIFA, CATEGORIA, FAIXA, MÉTRICA, Jan…Dez — e (b) uma planilha **LeverPro** com colunas de 2026 (os 5 meses Ago–Dez/2026 do arquivo atual entram; os demais ficam para completar; a tarifa dos meses ausentes mantém o padrão). |

Validado em Chromium headless: conta da faixa 1 com mínimo (100 eco × 8 m³ + 50 eco × 15 m³ → VOL FAT 1.750, VALOR = 1.500 × 6,11 + 250 × 14,05), campos digitados bloqueados quando há detalhado, KPI 2026 recalculado, Desfazer devolvendo o 2026, colagem 2 × 3 células, modelo exportado e reimportado (432 linhas / 32 blocos), LeverPro com 5 meses de 2026, cenários/Excel/Salvar simulador com o 2026 embutido e reabertura; regressões v13 e v14 sem erros.
