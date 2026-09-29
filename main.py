from dotenv import load_dotenv # type: ignore
load_dotenv()

from fastapi import FastAPI # type: ignore
from routers import treino # Importa o nosso novo andar

# 2. Inicia o aplicativo
app = FastAPI(title="Spotter API", version="1.0")

# 3. Pluga o roteador de treinos no aplicativo principal
app.include_router(treino.router)