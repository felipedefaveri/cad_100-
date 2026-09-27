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
