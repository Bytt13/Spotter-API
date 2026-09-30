from dotenv import load_dotenv  # type: ignore
load_dotenv()

from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from routers import treino

app = FastAPI(
    title="Spotter API",
    version="1.0",
    description="Backend do app Spotter — Assistente de Treino com IA",
)

# CORS — permite o frontend (mobile/web) chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Em produção: coloca o domínio do app aqui
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(treino.router)

@app.get("/health")
def health_check():
    """Endpoint de saúde — confirma que a API está no ar."""
    return {"status": "ok", "service": "Spotter API"}