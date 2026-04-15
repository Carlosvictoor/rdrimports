"""
Arquivo de entrada para servidores WSGI de produção (waitress, gunicorn, etc.)
Uso:
  waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
"""
from app import create_app

app = create_app()
