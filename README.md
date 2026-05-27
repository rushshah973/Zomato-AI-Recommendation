# Zomato AI Restaurant Recommender

AI-powered restaurant recommendation system using the [Zomato Hugging Face dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) and an LLM for ranking and explanations.

## Implementation decisions

| Area | Choice |
|------|--------|
| Language | Python 3.10+ |
| UI | Streamlit |
| LLM | Google Gemini (`gemini-2.0-flash` via `google-generativeai`) |
| Config | `pydantic-settings` + `.env` |

Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Gemini LLM_API_KEY before Phase 4+
```

### Verify foundation (Phase 0)

```bash
python -m app.main
```

### Load dataset (Phase 1)

```bash
python -c "from app.data.loader import load; print(len(load()))"
python scripts/explore_data.py
```

### Run UI (placeholder until Phase 6)

```bash
streamlit run app/main.py
```

## Project layout

```
app/
  main.py           # Streamlit entry
  models.py         # Domain models
  data/
    loader.py       # DatasetLoader + RestaurantStore
    preprocessor.py # Cleaning and normalization
config/
  settings.py       # Environment settings
scripts/
  explore_data.py   # Dataset exploration
tests/
  test_preprocessor.py
```

## Environment variables

See [.env.example](.env.example) for all supported keys.

## Documentation

- [context.md](Docs/context.md) — requirements
- [architecture.md](Docs/architecture.md) — system design
- [implementation-plan.md](Docs/implementation-plan.md) — phased build plan
