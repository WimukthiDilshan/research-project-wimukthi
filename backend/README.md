# Backend Folder

This folder contains a backend-only copy of the project, separated from the frontend folder.

## Included

- config/
- models/
- repositories/
- routers/
- services/
- scripts/
- main.py
- requirements.txt
- .env.example

## Run backend only

1. Open terminal in this folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run API:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

API routes remain under `/api/v1/*`.
