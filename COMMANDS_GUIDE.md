# 📋 Guia de Comandos - Análise de Layout de Teclado

Este documento lista todos os comandos disponíveis para gerar gráficos e análises do sistema de otimização de layout de teclado.

---

## 📊 Gráficos e Visualizações

### 1. Heatmap de Tempos de Unigramas

**Arquivo gerado**: `outputs/unigram_timing_heatmap.png`

**Descrição**: Mostra o tempo médio (em milissegundos) para pressionar cada tecla física individualmente, baseado em dados empíricos coletados via [BagreType](https://bagretype.com). O heatmap usa gradiente de cores cyan (claro = rápido, escuro = lento) e exibe valores numéricos no centro de cada quadrado.

**Comando**:
```bash
python -m ga_keyboard.main \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --generations 1 \
  --population 10 \
  --outdir outputs
```

**Com mesclagem de dados**:
```bash
python -m ga_keyboard.main \
  --csv data/other_data.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --mix-with-typing-test \
  --generations 1 \
  --population 10 \
  --outdir outputs
```

**Informações**:
- **Fonte dos dados**: Dados coletados de participantes via plataforma BagreType
- **O que representa**: Tempo médio de reação para pressionar cada tecla física
- **Interpretação**: Valores menores (cores mais claras) indicam teclas mais rápidas. Geralmente, a home row (fileira central) apresenta valores menores
- **Validação**: Padrões ergonômicos esperados (home row mais rápida que números) validam a qualidade dos dados

---

### 2. Heatmap de Tempos de Bigramas

**Arquivo gerado**: `outputs/bigram_timing_heatmap.png`

**Descrição**: Mostra o tempo médio para digitar bigramas (pares de teclas) onde cada tecla física aparece. Calculado como média de todos os bigramas envolvendo essa tecla (como primeira ou segunda posição). Usa o mesmo gradiente cyan e exibe valores numéricos.

**Comando**:
```bash
python -m ga_keyboard.main \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --generations 1 \
  --population 10 \
  --outdir outputs
```

**Com mesclagem de dados**:
```bash
python -m ga_keyboard.main \
  --csv data/other_data.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --mix-with-typing-test \
  --generations 1 \
  --population 10 \
  --outdir outputs
```

**Informações**:
- **Fonte dos dados**: Medições de participantes digitando sequências de dois caracteres
- **O que representa**: Custo médio de bigramas envolvendo cada tecla física
- **Diferença do unigrama**: Captura dificuldade de transições, não apenas teclas isoladas
- **Relevância**: Essencial para otimização, pois o algoritmo considera transições entre teclas

---

### 3. Gráfico de Frequência de Caracteres do Corpus

**Arquivo gerado**: `outputs/corpus_character_frequencies.png`

**Descrição**: Gráfico de barras horizontal mostrando os caracteres mais frequentes no corpus de texto, ordenados por frequência (mais frequente no topo). Usa colormap viridis.

**Comando básico**:
```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --out-png-chars outputs/corpus_character_frequencies.png \
  --top-n 50
```

**Com paths padrão**:
```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --top-n 50
```

**Apenas caracteres** (sem bigramas):
```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --chars-only \
  --top-n 30
```

**Informações**:
- **Fonte dos dados**: Corpus de texto (ex.: obras de Machado de Assis para português)
- **O que representa**: Distribuição de frequência de caracteres no idioma
- **Relevância**: Caracteres frequentes têm maior impacto no custo total; o algoritmo deve priorizá-los em teclas rápidas
- **Insight**: Em português, vogais (a, e, i, o, u) dominam o topo, justificando otimização dessas posições

---

### 4. Gráfico de Frequência de Bigramas do Corpus

**Arquivo gerado**: `outputs/corpus_bigram_frequencies.png`

**Descrição**: Gráfico de barras horizontal mostrando os bigramas (pares de caracteres) mais frequentes no corpus, ordenados por frequência. Usa colormap plasma para distinguir do gráfico de caracteres.

**Comando básico**:
```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --out-png-bigrams outputs/corpus_bigram_frequencies.png \
  --top-n 50
```

**Com paths padrão**:
```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --top-n 50
```

**Apenas bigramas** (sem caracteres):
```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --bigrams-only \
  --top-n 30
```

**Informações**:
- **Fonte dos dados**: Corpus de texto processado para extrair sequências de dois caracteres
- **O que representa**: Distribuição de frequência de bigramas no idioma
- **Relevância**: Bigramas frequentes (ex.: "th", "he" em inglês; "de", "da" em português) devem ser otimizados para transições rápidas
- **Insight**: Mostra padrões linguísticos do idioma-alvo e guia o algoritmo genético para priorizar certas transições

---

### 5. Análise de Custo de uma Tecla Específica

**Arquivo gerado**: `outputs/key_cost_analysis_[tecla].png` (ex.: `key_cost_analysis_a.png`)

**Descrição**: Gráfico de barras comparando o tempo do unigrama de uma tecla específica com todos os bigramas que a envolvem (como primeira ou segunda tecla), ordenados por tempo.

**Comando básico**:
```bash
python scripts/analyze_key_cost.py \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --key a \
  --out outputs/key_cost_analysis_a.png
```

**Com mesclagem de dados**:
```bash
python scripts/analyze_key_cost.py \
  --csv data/other_data.csv \
  --csv-json-col typing_data \
  --key e \
  --mix-with-typing-test \
  --out outputs/key_cost_analysis_e.png
```

**Exemplos para outras teclas**:
```bash
# Tecla 't'
python scripts/analyze_key_cost.py --csv data/typing_test.csv --key t --out outputs/key_cost_analysis_t.png

# Tecla 'h'
python scripts/analyze_key_cost.py --csv data/typing_test.csv --key h --out outputs/key_cost_analysis_h.png

# Tecla 'e'
python scripts/analyze_key_cost.py --csv data/typing_test.csv --key e --out outputs/key_cost_analysis_e.png
```

**Informações**:
- **Fonte dos dados**: Dados de timing do CSV especificado
- **O que representa**: Análise detalhada de uma tecla específica, mostrando:
  - Barra azul: tempo do unigrama (tecla sozinha)
  - Barras laranjas: todos os bigramas envolvendo essa tecla, ordenados do mais rápido ao mais lento
- **Uso**: Útil para entender por que certas teclas foram posicionadas onde estão no layout evoluído
- **Insight**: Repetições (ex.: "aa") tendem a ser mais lentas que transições entre teclas diferentes

---

### 6. Evolução da Aptidão (Fitness)

**Arquivo gerado**: `outputs/fitness.png`

**Descrição**: Gráfico de linha mostrando a evolução da melhor aptidão ao longo das gerações do algoritmo genético. Aptidão é o inverso do custo (quanto maior, melhor).

**Comando completo**:
```bash
python -m ga_keyboard.main \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --generations 300 \
  --population 200 \
  --mutation-rate 0.1 \
  --crossover-rate 0.7 \
  --elitism 5 \
  --cost-order bi \
  --fallback-to-unigrams false \
  --outdir outputs
```

**Com mesclagem de dados**:
```bash
python -m ga_keyboard.main \
  --csv data/other_data.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --mix-with-typing-test \
  --generations 300 \
  --population 200 \
  --outdir outputs
```

**Informações**:
- **O que representa**: Progresso da otimização ao longo das gerações
- **Interpretação**: 
  - Curva ascendente = algoritmo melhorando
  - Plateau = convergência (possível ótimo local)
  - Oscilação = parâmetros instáveis (ex.: mutação muito alta)
- **Parâmetros recomendados**:
  - `--generations 300`: Suficiente para convergência
  - `--population 200`: Balance entre exploração e custo computacional
  - `--mutation-rate 0.1`: Taxa baixa para refinamento gradual
  - `--crossover-rate 0.7`: Padrão em algoritmos genéticos
  - `--elitism 5`: Preserva ~2.5% dos melhores

---

### 7. Heatmap de Custo por Tecla do Layout Evoluído

**Arquivo gerado**: `outputs/heatmap.png`

**Descrição**: Heatmap mostrando o custo aproximado por tecla física no layout evoluído, calculado como frequência × tempo de digitação. Distribui custos de bigramas igualmente entre as teclas envolvidas.

**Comando** (gerado automaticamente junto com fitness):
```bash
python -m ga_keyboard.main \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --generations 300 \
  --population 200 \
  --cost-order bi \
  --outdir outputs
```

**Informações**:
- **O que representa**: Custo aproximado por tecla física no layout final
- **Cálculo**: `custo_tecla = Σ(frequência × tempo)` para todos os caracteres/bigramas que usam essa tecla
- **Interpretação**: Cores mais escuras = maior custo. Layout otimizado deve ter caracteres frequentes em teclas rápidas (cores claras)
- **Limitação**: Aproximação que distribui custos de bigramas igualmente; não captura interações complexas

---

## 🎯 Comandos de Execução Completa

### Execução Completa do GA (Todos os Gráficos)

Este comando gera **todos** os gráficos e realiza a otimização completa:

```bash
python -m ga_keyboard.main \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --corpus data/machado.txt \
  --generations 300 \
  --population 200 \
  --mutation-rate 0.1 \
  --crossover-rate 0.7 \
  --elitism 5 \
  --use-trigrams false \
  --cost-order bi \
  --fallback-to-unigrams false \
  --seed 42 \
  --outdir outputs
```

**Outputs gerados**:
1. `unigram_timing_heatmap.png` - Heatmap de unigramas
2. `bigram_timing_heatmap.png` - Heatmap de bigramas
3. `corpus_character_frequencies.txt` - Estatísticas de caracteres
4. `corpus_character_frequencies.png` - Gráfico de frequência de caracteres
5. `corpus_bigram_frequencies.png` - Gráfico de frequência de bigramas
6. `fitness.png` - Evolução da aptidão
7. `heatmap.png` - Custo por tecla do layout evoluído
8. `best_layout.txt` - Layout ótimo em ASCII

---

## 📝 Parâmetros Importantes

### `--cost-order` (uni|bi|tri)

**Padrão**: `bi`

**Descrição**: Define qual ordem de n-grama usar **exclusivamente** para calcular o custo. Evita double-counting.

- `uni`: Usa apenas unigramas
- `bi`: Usa apenas bigramas (recomendado)
- `tri`: Usa apenas trigramas (requer dados mais completos)

**Recomendação**: Use `bi` para maioria dos casos, pois bigramas capturam transições sem ser tão esparso quanto trigramas.

### `--fallback-to-unigrams` (true/false)

**Padrão**: `false`

**Descrição**: Quando um bigrama/trigrama não tem dados de timing, se deve fazer backoff aditivo para unigramas.

- `true`: Aproxima bigramas faltantes como soma de unigramas
- `false`: Ignora bigramas faltantes (contribuem 0 ao custo)

**Recomendação**: Use `false` se tiver dados completos; `true` para dados esparsos.

### `--mix-with-typing-test`

**Descrição**: Mescla os dados do CSV fornecido com `typing_test.csv` antes de processar.

**Uso**: Útil para combinar múltiplas fontes de dados.

```bash
--mix-with-typing-test
```

---

## 🔧 Comandos de Utilidade

### Gerar Dados Sintéticos (Para Testes)

```bash
python scripts/generate_synthetic_typing_csv.py \
  --out data/synthetic_typing.csv \
  --row-base-numbers 220.0 \
  --row-base-top 170.0 \
  --row-base-home 140.0 \
  --row-base-bottom 180.0 \
  --col-penalty 1.5 \
  --same-row-penalty 12.0 \
  --diff-row-penalty 6.0 \
  --repeat-penalty 35.0 \
  --noise-std 0.0 \
  --seed 1234
```

### Mesclar Múltiplos CSVs

```bash
python scripts/fuse_typing_csvs.py \
  --out data/merged_data.csv \
  --json-col typing_data \
  data/file1.csv \
  data/file2.csv \
  data/file3.csv
```

---

## 📊 Resumo Rápido por Tipo de Gráfico

| Gráfico | Comando Principal | Gerado Automaticamente? |
|---------|------------------|-------------------------|
| Unigram Heatmap | `main --generations 1` | ✅ Sim |
| Bigram Heatmap | `main --generations 1` | ✅ Sim |
| Char Frequency | `corpus_stats --corpus` | ✅ Sim (no main) |
| Bigram Frequency | `corpus_stats --corpus` | ✅ Sim (no main) |
| Key Cost Analysis | `scripts/analyze_key_cost.py` | ❌ Não |
| Fitness Evolution | `main --generations 300` | ✅ Sim |
| Layout Heatmap | `main --generations 300` | ✅ Sim |

---

## 🎓 Exemplos de Uso

### Análise Rápida (Apenas Visualizações)

Para gerar apenas os heatmaps de timing sem rodar o GA completo:

```bash
python -m ga_keyboard.main \
  --csv data/typing_test.csv \
  --corpus data/machado.txt \
  --generations 1 \
  --population 10 \
  --outdir outputs
```

### Análise Completa do Corpus

Para gerar todos os gráficos de frequência do corpus:

```bash
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --top-n 50
```

### Análise Detalhada de uma Tecla

Para analisar profundamente uma tecla específica (ex.: 'a'):

```bash
python scripts/analyze_key_cost.py \
  --csv data/typing_test.csv \
  --key a \
  --mix-with-typing-test \
  --out outputs/key_cost_analysis_a.png
```

---

## 📚 Referências

- **Plataforma de Coleta**: [bagretype.com](https://bagretype.com)
- **Repositório Principal**: [github.com/SamuelMFS/BagreType](https://github.com/SamuelMFS/BagreType)
- **Documentação Técnica**: `Article.md` (inglês) e `Article_pt_BR.md` (português)
- **Autores**: Samuel Marcio Fonseca Santos e João Pedro de Souza Letro (UniFran)

---

**Última atualização**: [Data]
**Versão**: 1.0


