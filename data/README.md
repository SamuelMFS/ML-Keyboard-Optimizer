Place your files here.

- typing.csv → must contain a column named `typing_data` with JSON arrays of timing records.
- corpus.txt → raw text corpus used to compute uni/bi/tri-gram frequencies.

Example JSON for `typing_data` cells is shown in the top-level README.

``` bash
python scripts/analyze_key_cost.py \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --key a \
  --mix-with-typing-test \
  --out outputs/key_cost_analysis_a.png
```
This is for graph making

```bash
# Gerar ambos os gráficos (caracteres e bigramas)
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --top-n 50

# Apenas bigramas
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --bigrams-only \
  --out-png-bigrams outputs/bigram_freq.png \
  --top-n 50

# Apenas caracteres
python -m ga_keyboard.corpus_stats \
  --corpus data/machado.txt \
  --chars-only \
  --out-png-chars outputs/char_freq.png
```