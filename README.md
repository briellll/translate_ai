# Tradutor AI

Traduz arquivos PDF ou EPUB para Português usando OpenAI (GPT). Interface web (React + Tailwind), API REST (FastAPI) e CLI.

---

## Arquitetura (monorepo)

```
translate_ai/
├── backend/              # API FastAPI
│   ├── main.py           # App principal + static files (produção)
│   ├── task_manager.py   # Tasks assíncronas com SSE
│   ├── routes/
│   │   ├── upload.py     # POST /upload
│   │   ├── translate.py  # POST /translate (SSE), cancel, status
│   │   └── download.py   # GET /download/{task_id}
│   └── Dockerfile
├── frontend/             # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.tsx       # Orquestrador de estado
│   │   ├── api.ts        # Cliente HTTP + SSE
│   │   └── components/   # FileUpload, ConfigForm, PreviewPane, etc.
│   ├── nginx.conf
│   └── Dockerfile
├── translator/           # Core (compartilhado)
│   ├── pipeline.py       # Orquestração de tradução
│   ├── openai_translator.py  # API OpenAI + retry
│   ├── chunker.py        # Chunking por chars e tokens
│   ├── pdf_reader.py     # Leitura de PDF
│   ├── epub_reader.py    # Leitura de EPUB
│   ├── exporter.py       # Exportação PDF/EPUB/TXT
│   ├── validation.py     # Validação de configuração
│   └── logger.py         # Logging estruturado
├── tests/                # 54 testes (pytest)
├── legacy/               # Desktop app (CustomTkinter) — arquivado
├── docker-compose.yml
├── pyproject.toml
└── poetry.lock
```

## Requisitos

- Python 3.11+ · Poetry
- Node.js 20+ · npm (para frontend)
- Chave da API OpenAI

## Desenvolvimento

### Backend + CLI

```bash
poetry install
poetry run python -m translator.main <input.pdf> <output.pdf>
```

### Frontend (dev)

```bash
cd frontend && npm install && npm run dev
```

Proxy automático de `/api` → `http://127.0.0.1:8000`.

### Full stack (dev)

```bash
# Terminal 1
poetry run uvicorn backend.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Acessar `http://localhost:5173`.

## Produção (Docker)

```bash
OPENAI_API_KEY=sk-... docker compose up -d
```

- Frontend: `http://localhost:8080`
- Backend (API): `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

Sem Docker, build manual:

```bash
cd frontend && npm run build
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

O backend serve automaticamente o frontend buildado.

## API Endpoints

| Método | Rota | Descrição |
|--------|------|----------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload PDF/EPUB → `file_id` |
| POST | `/translate` | Inicia tradução → `task_id` |
| GET | `/translate/{task_id}` | SSE stream (tokens + progresso) |
| GET | `/translate/{task_id}/status` | Status atual |
| POST | `/translate/{task_id}/cancel` | Cancela tradução |
| GET | `/download/{task_id}` | Download do resultado |

## Testes

```bash
poetry run pytest            # 54 testes
poetry run pytest --cov=translator,backend,tests --cov-report=term
poetry run ruff check .
poetry run mypy translator/
```

## Melhorias implementadas

- ✅ Retry com exponential backoff (tenacity)
- ✅ Chunking por tokens (tiktoken)
- ✅ Validação de inputs
- ✅ Processamento paralelo de chunks
- ✅ Persistência de progresso (resume)
- ✅ Parâmetros configuráveis (temperature, top_p, max_tokens)
- ✅ Logging estruturado
- ✅ CI/CD (GitHub Actions)
- ✅ Pre-commit hooks (ruff, mypy)
- ✅ Docker Compose
- ✅ 54 testes unitários + integração
- ✅ pypdf (substitui PyPDF2 obsoleto)
