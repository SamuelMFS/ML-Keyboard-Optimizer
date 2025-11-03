# Genetic Algorithm: Keyboard Layout Optimization

## Quick Start

1) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Prepare your data:
- CSV file in `data/` with a column named `typing_data` containing JSON arrays of timing records (see example below).
- A text corpus in `data/corpus.txt` (or any path you pass via CLI).

3) Run the optimizer:

```bash
python -m ga_keyboard.main \
  --csv /ML-Keyboard-Optimizer/data/typing.csv \
  --csv-json-col typing_data \
  --corpus /ML-Keyboard-Optimizer/data/corpus.txt \
  --generations 300 \
  --population 200 \
  --mutation-rate 0.1 \
  --crossover-rate 0.7 \
  --elitism 5 \
  --use-trigrams false
```

Outputs (saved to `outputs/`):
- Best layout string (46 chars)
- ASCII rendering of the best layout
- Fitness evolution plot (`fitness.png`) and ASCII sparkline
- Heatmap (`heatmap.png`)

## Typing data JSON example

```json
[
  {
    "sequence": "h",
    "letterTimings": [
      {"letter": "h", "reactionTime": 834}
    ],
    "totalSequenceTime": 834
  },
  {
    "sequence": "th",
    "letterTimings": [
      {"letter": "t", "reactionTime": 210},
      {"letter": "h", "reactionTime": 230}
    ],
    "totalSequenceTime": 440
  }
]
```

The parser aggregates averages into:
- `avg_time_unigram[c]`
- `avg_time_bigram[c1+c2]`
- (optional) `avg_time_trigram[c1+c2+c3]`

## Notes
- Fitness is the inverse of the corpus typing cost computed from observed timings.
- GA uses tournament selection, OX crossover, and swap mutation.
- Heatmap approximates per-key contribution (shares n-gram costs equally among involved keys).
