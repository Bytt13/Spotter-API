import os
from supabase import create_client, Client  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv()

_url: str = os.environ["SUPABASE_URL"]
_key: str = os.environ["SERVICE_ROLE_KEY"]  # Backend sempre usa service_role

# Singleton — uma única conexão para toda a aplicação
supabase: Client = create_client(_url, _key)
