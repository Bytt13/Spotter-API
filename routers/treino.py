from fastapi import APIRouter, HTTPException #type: ignore
from pydantic import BaseModel #type: ignore
import os
import time
from dotenv import load_dotenv #type: ignore
from openai import OpenAI #type: ignore
from google import genai
from google.genai import types

load_dotenv()

router = APIRouter()

# 1. Inicializa o cliente Primário (Groq)
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

# 2. Inicializa o cliente Secundário (Google Gemini)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class SolicitacaoTreino(BaseModel):
    mensagem_usuario: str

@router.post("/gerar-treino")
def gerar_treino(solicitacao: SolicitacaoTreino):
    system_prompt = (
        "Você é o Spotter, um personal trainer de elite sarcástico e focado em hipertrofia. "
        "Responda de forma curta, técnica e direta ao criar treinos."
    )
    
    # --- TENTATIVA 1: GROQ ---
    try:
        print("[SPOTTER] Tentando Groq (Qwen 3.8 27b)...")
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": solicitacao.mensagem_usuario}
            ],
            temperature=0.7,
        )
        return {"treino_gerado": completion.choices[0].message.content, "engine": "groq"}
        
    except Exception as e_groq:
        print(f"[AVISO] Groq falhou: {e_groq}")
        
        # --- TENTATIVA 2: GEMINI (Fallback) ---
        # Modelos atualizados da API Gemini
        modelos_para_tentar = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
        
        for nome_modelo in modelos_para_tentar:
            try:
                print(f"[SPOTTER] Tentando Gemini ({nome_modelo})...")
                
                # Adicionamos um pequeno retry manual para erro 503
                for tentativa in range(2): 
                    try:
                        response = gemini_client.models.generate_content(
                            model=nome_modelo,
                            contents=solicitacao.mensagem_usuario,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.7,
                                max_output_tokens=500,
                            ),
                        )
                        return {"treino_gerado": response.text, "engine": f"gemini-{nome_modelo}"}
                    except Exception as e:
                        if "503" in str(e) and tentativa == 0:
                            print("Servidor instável (503), tentando novamente em 1s...")
                            time.sleep(1)
                            continue
                        raise e # Se não for 503 ou segunda tentativa, lança o erro para o próximo modelo

            except Exception as e_gemini:
                print(f"[AVISO] Erro no modelo {nome_modelo}: {e_gemini}")
                continue # Pula para o próximo modelo da lista (resolve o 404)

        # Se chegar aqui, tudo falhou
        raise HTTPException(
            status_code=500, 
            detail="Nenhum motor de IA disponível no momento."
        )