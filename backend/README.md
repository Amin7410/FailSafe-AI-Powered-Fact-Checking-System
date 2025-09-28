# FailSafe Backend

- Run dev server: `poetry install && poetry run uvicorn app.main:app --reload`
- API Docs: `http://localhost:8000/docs`
- Ethical config: `app/core/ethical_config.yaml`

Folder layout mirrors the blueprint: `api/v1`, `services`, `models`, `core`.

Retrieval corpus (optional): put JSONL at `data/corpus/seed.jsonl` with lines like:
`{"id":"doc1","title":"Title","url":"https://...","text":"Body text..."}`
