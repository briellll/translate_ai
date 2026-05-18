# Tradutor AI

Traduz arquivos PDF ou EPUB para Português usando OpenAI (GPT). Interface web (React + Tailwind), API REST (FastAPI) e CLI.

---

## Arquitetura

```
translate_ai/
├── backend/
│   ├── translator/        # Core
│   │   ├── pipeline.py    # Orquestração
│   │   ├── openai_translator.py  # API OpenAI + retry + prompt
│   │   ├── chunker.py     # Chunking por chars e tokens
│   │   ├── pdf_reader.py  # Leitura básica de PDF (pypdf)
│   │   ├── rich_pdf_reader.py  # Leitura avançada (PyMuPDF)
│   │   ├── epub_reader.py # Leitura de EPUB
│   │   ├── markup_reader.py    # Extração com marcadores
│   │   ├── exporter.py    # Exportação PDF/EPUB/TXT
│   │   ├── validation.py  # Validação de config
│   │   ├── types.py       # Dataclasses
│   │   └── logger.py      # Logging
│   ├── routes/            # API endpoints
│   ├── task_manager.py    # Tasks assíncronas
│   ├── main.py            # FastAPI app
│   └── Dockerfile
├── frontend/              # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.tsx        # Orquestrador (grid + sidebar)
│   │   ├── api.ts         # Cliente HTTP + SSE
│   │   ├── types.ts       # Tipos + provedores
│   │   └── components/
│   │       ├── FileUpload.tsx
│   │       ├── ConfigForm.tsx
│   │       ├── LimitationsBanner.tsx  # Painel de limitações
│   │       ├── PreviewPane.tsx
│   │       ├── ProgressPanel.tsx
│   │       └── Toast.tsx
│   ├── nginx.conf
│   └── Dockerfile
├── tests/                 # 71 testes (pytest)
├── legacy/                # App desktop arquivado
├── docker-compose.yml
├── pyproject.toml
└── poetry.lock
```

## Recursos

- Leitura de `.pdf` e `.epub`
- Tradução com OpenAI / Groq / Together / DeepSeek / Custom
- **Preservação de formatação** (negrito, itálico, headings, código) em PDF e EPUB
- Chunking inteligente por caracteres ou tokens (tiktoken)
- Streaming em tempo real (SSE)
- Múltiplos provedores de IA (OpenAI, Groq, Together, DeepSeek, Custom)
- Progresso com ETA, velocidade, tempo decorrido
- Cancelamento seguro
- Retry com exponential backoff
- Persistência de progresso (resume)
- Processamento paralelo de chunks
- Parâmetros configuráveis (temperature, top_p, max_tokens)
- Logging estruturado
- Validação de inputs
- CI/CD (GitHub Actions)
- Pre-commit hooks (ruff, mypy)

## Limitações

- **PDFs escaneados (imagem)** não funcionam — sem OCR
- **Imagens e tabelas** são ignoradas
- **Layout de página e numeração** não são preservados
- **Cabeçalhos/rodapés** podem aparecer no meio do texto
- Só traduz para português
- Máx 200 MB por arquivo

## Requisitos

- Python 3.11+ · Poetry
- Node.js 20+ · npm
- Chave de API de um provedor compatível

## Desenvolvimento

```bash
poetry install
cd frontend && npm install
```

### Backend + CLI

```bash
poetry run uvicorn backend.main:app --reload --port 8000
# ou CLI:
poetry run python -m translator.main <input.pdf> <output.pdf>
```

### Frontend

```bash
cd frontend && npm run dev   # → http://localhost:5173
```

Proxy automático de `/api` → backend :8000.

## Produção (Docker)

```bash
OPENAI_API_KEY=sk-... docker compose up -d
```

- Frontend: `http://localhost:8080`
- Backend (API): `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

Sem Docker:

```bash
cd frontend && npm run build
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

O backend serve o frontend buildado automaticamente.

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

## Provedores suportados

| Provedor | Modelos |
|----------|---------|
| OpenAI | gpt-4o-mini, gpt-4o, gpt-4-turbo, o3-mini |
| Groq | llama-3.3-70b-versatile, mixtral-8x7b, gemma2-9b-it |
| Together AI | Mixtral-8x7B, Llama-3.3-70B |
| DeepSeek | deepseek-chat, deepseek-reasoner |
| Custom | Qualquer URL + modelo compatível com OpenAI |

## Preservação de formatação

Quando ativada (`preserve_formatting=True`), a ferramenta:

1. **PDF**: Usa PyMuPDF para detectar automaticamente negrito, itálico, código e headings (pelo nome da fonte e tamanho). O texto extraído é marcado com `**bold**`, `*italic*`, etc.
2. **EPUB**: Preserva o HTML original e traduz apenas os text nodes, mantendo toda a estrutura de tags.
3. **Prompt**: O modelo recebe instrução para preservar os marcadores na tradução.
4. **Exportador**: ReportLab renderiza os marcadores como formatação real no PDF; EPUB usa `<b>`, `<i>`, `<h1>` nativos.

## Testes

```bash
poetry run pytest                    # 71 testes
poetry run pytest --cov=translator --cov-report=term
poetry run ruff check .
poetry run mypy backend/translator/
```
