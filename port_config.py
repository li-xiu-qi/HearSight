import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

load_dotenv(dotenv_path=ROOT / '.env')

frontend_port = int(os.getenv('FRONTEND_PORT', '5173'))

backend_port = int(os.getenv('BACKEND_PORT', '8000'))