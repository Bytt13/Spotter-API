from fastapi import APIRouter, HTTPException  # type: ignore
from openai import OpenAI  # type: ignore
# pyrefly: ignore [missing-import]
from google import genai
from google.genai import types  # type: ignore
import os
import time
import uuid
from dotenv import load_dotenv  # type: ignore

from db.client import supabase
from db.models import ChatRequest, ChatResponse

load_dotenv()

router = APIRouter(prefix="/chat", tags=["Chat"])

# ── Clientes de IA ────────────────────────────────────────────────────────────

groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Prompt do agente ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "Você é o Spotter, um personal trainer de elite focado em hipertrofia. "
    "Você conhece o histórico de treinos, streaks e PRs do seu usuário. "
    "Seja direto, técnico e motivador. Use linguagem próxima mas profissional. "
    "Quando sugerir mudanças de treino, explique o motivo fisiológico brevemente."
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_conversation(user_id: str, conversation_id: str | None) -> str:
    """Retorna o ID da conversa existente ou cria uma nova."""
    if conversation_id:
        return conversation_id

    result = (
        supabase.table("chat_conversations")
        .insert({"user_id": user_id, "title": "Nova Conversa"})
        .execute()
    )
    return result.data[0]["id"]


def _load_history(conversation_id: str) -> list[dict]:
    """Carrega as últimas 20 mensagens da conversa para contexto da IA."""
    result = (
        supabase.table("chat_messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .limit(20)
        .execute()
    )
    return [{"role": row["role"], "content": row["content"]} for row in result.data]


def _save_messages(conversation_id: str, user_msg: str, assistant_msg: str):
    """Persiste a mensagem do usuário e a resposta da IA no banco."""
    supabase.table("chat_messages").insert([
        {
            "conversation_id": conversation_id,
            "role": "user",
            "content": user_msg,
            "message_type": "text",
        },
        {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_msg,
            "message_type": "text",
        },
    ]).execute()


def _call_ai(messages: list[dict]) -> tuple[str, str]:
    """
    Chama Groq primeiro, Gemini como fallback.
    Retorna (reply_text, engine_name).
    """
    # Tentativa 1 — Groq
    try:
        print("[SPOTTER] Tentando Groq (Qwen 3.8 27b)...")
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=0.7,
            max_tokens=600,
        )
        return completion.choices[0].message.content, "groq"
    except Exception as e:
        print(f"[AVISO] Groq falhou: {e}")

    # Tentativa 2 — Gemini (fallback)
    models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    for model_name in models_to_try:
        try:
            print(f"[SPOTTER] Tentando Gemini ({model_name})...")
            # Gemini não suporta role=system no contents, usamos system_instruction
            gemini_messages = [
                types.Content(
                    role=m["role"] if m["role"] != "assistant" else "model",
                    parts=[types.Part(text=m["content"])]
                )
                for m in messages
            ]
            for attempt in range(2):
                try:
                    response = gemini_client.models.generate_content(
                        model=model_name,
                        contents=gemini_messages,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.7,
                            max_output_tokens=600,
                        ),
                    )
                    return response.text, f"gemini-{model_name}"
                except Exception as e:
                    if "503" in str(e) and attempt == 0:
                        time.sleep(1)
                        continue
                    raise e
        except Exception as e:
            print(f"[AVISO] Gemini {model_name} falhou: {e}")
            continue

    raise HTTPException(status_code=503, detail="Nenhum motor de IA disponível no momento.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
def send_message(req: ChatRequest):
    """
    Endpoint principal do chat.
    - Cria ou retoma uma conversa
    - Carrega histórico para contexto
    - Chama a IA
    - Salva tudo no banco
    """
    # 1. Conversa
    conv_id = _get_or_create_conversation(req.user_id, req.conversation_id)

    # 2. Histórico para contexto
    history = _load_history(conv_id)
    history.append({"role": "user", "content": req.message})

    # 3. IA
    reply, engine = _call_ai(history)

    # 4. Persiste no banco
    _save_messages(conv_id, req.message, reply)

    return ChatResponse(
        conversation_id=conv_id,
        reply=reply,
        engine=engine,
    )


@router.get("/conversations/{user_id}")
def list_conversations(user_id: str):
    """Lista todas as conversas de um usuário (para histórico no app)."""
    result = (
        supabase.table("chat_conversations")
        .select("id, title, created_at, updated_at")
        .eq("user_id", user_id)
        .eq("is_archived", False)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: str):
    """Retorna todas as mensagens de uma conversa específica."""
    result = (
        supabase.table("chat_messages")
        .select("id, role, content, message_type, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


# ── Endpoint Legado (Compatibilidade com Flutter) ─────────────────────────────

from pydantic import BaseModel

legacy_router = APIRouter(tags=["Legacy"])

class SolicitacaoTreino(BaseModel):
    mensagem_usuario: str

@legacy_router.post("/gerar-treino")
def gerar_treino(solicitacao: SolicitacaoTreino):
    """
    Endpoint legado para manter compatibilidade com o frontend em Flutter.
    Recebe a mensagem, gera o treino e retorna sem salvar no banco de dados.
    """
    reply, engine = _call_ai([{"role": "user", "content": solicitacao.mensagem_usuario}])
    return {"treino_gerado": reply, "engine": engine}