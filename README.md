# AI IT Assistant

AI IT Assistant is a small project that analyzes IT support tickets using LLMs and synchronizes with GLPI.

## Structure

- backend/: FastAPI backend and services
- frontend/: Vite + React frontend
- database/: SQL schema and migrations
- knowledge base/: Data and documentation

## Quick start (backend)

1. Create a Python virtual environment:
   python -m venv .venv
   .\.venv\Scripts\activate

2. Install dependencies:
   pip install -r backend/requirements.txt

3. Configure environment variables in `backend/.env` (do not commit secrets).

4. Start the backend:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Quick start (frontend)

1. cd frontend
2. npm install
3. npm run dev

## Tests

- Run backend tests: `pytest backend`

## Security

- **Never commit secrets**. Use `.env` (ignored) or a secrets manager (GitHub Secrets).

## Contributing

- Create a branch for your feature and open a PR.

## License

MIT
