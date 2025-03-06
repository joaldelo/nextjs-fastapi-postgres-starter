# Backend Service

This is the backend service for the NextJS-FastAPI-Postgres starter project.

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Start PostgreSQL:
```bash
brew services start postgresql
```

3. Run the development server:
```bash
poetry run uvicorn main:app --reload
```

## Development vs Production Dependencies

- Development: Uses `psycopg2-binary` for easier setup
- Production: Uses `psycopg2` with system PostgreSQL libraries

To install production dependencies:
```bash
poetry install --only main --extras production
``` 