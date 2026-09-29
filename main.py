from fastapi import FastAPI # type: ignore

app = FastAPI()

@app.get("/")
def ler_raiz():
  return {"mensagem": "API do Spotter operante. Aguardando comandos."}