from dotenv import load_dotenv  # type: ignore
load_dotenv()
import uvicorn #type: ignore
from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from routers import treino
import os

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
app.include_router(treino.legacy_router)

@app.get("/health")
def health_check():
    """Endpoint de saúde — confirma que a API está no ar."""
    return {"status": "ok", "service": "Spotter API"}

if __name__ == "__main__":
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)