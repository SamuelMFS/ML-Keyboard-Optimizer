Place your files here.

- typing.csv → must contain a column named `typing_data` with JSON arrays of timing records.
- corpus.txt → raw text corpus used to compute uni/bi/tri-gram frequencies.

Example JSON for `typing_data` cells is shown in the top-level README.

``` bash
python scripts/analyze_key_cost.py \
  --csv data/typing_test.csv \
  --csv-json-col typing_data \
  --key a \
  --out outputs/key_cost_analysis_a.png
```
This is for graph making