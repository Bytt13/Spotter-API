from pydantic import BaseModel  # type: ignore
from typing import Optional


# ---------- Chat ----------

class ChatRequest(BaseModel):
    """Payload enviado pelo frontend para o endpoint de chat."""
    user_id: str           # UUID do usuário autenticado
    conversation_id: Optional[str] = None   # None = nova conversa
    message: str           # Texto ou transcrição do áudio


class ChatResponse(BaseModel):
    """Resposta do endpoint de chat."""
    conversation_id: str
    reply: str
    engine: str            # 'groq' ou 'gemini-...'


# ---------- Treino ----------

class WorkoutGenerationRequest(BaseModel):
    """Payload para geração inicial de treino (onboarding)."""
    user_id: str
    days_per_week: int
    level: str             # 'beginner' | 'intermediate' | 'advanced'
    custom_notes: Optional[str] = None
