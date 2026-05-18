import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes.upload import router as upload_router
from backend.routes.translate import router as translate_router
from backend.routes.download import router as download_router
from translator.logger import setup_logger

logger = setup_logger("translate_ai")

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend Tradutor AI iniciado")
    yield
    logger.info("Backend Tradutor AI encerrado")


app = FastAPI(
    title="Tradutor AI API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta as rotas da API com e sem prefixo /api
# para funcionar tanto com Vite proxy (5173) quanto em produção direta (8000)
api = APIRouter(prefix="/api")
api.include_router(upload_router)
api.include_router(translate_router)
api.include_router(download_router)
app.include_router(api)
app.include_router(upload_router)
app.include_router(translate_router)
app.include_router(download_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not found"}, status_code=404)
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return FileResponse(index)

    logger.info("Modo produção: servindo frontend de %s", FRONTEND_DIST)
