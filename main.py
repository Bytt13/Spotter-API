from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def ler_raiz():
  return {"mensagem": "API do Spotter operante. Aguardando comandos."}