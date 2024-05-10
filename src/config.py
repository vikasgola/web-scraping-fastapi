import os
from dotenv import load_dotenv

# load configurations from .env file
load_dotenv()

N_PAGES = int(os.getenv("N_PAGES"))
PROXY = os.getenv("PROXY")
