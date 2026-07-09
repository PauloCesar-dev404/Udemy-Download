import logging
import os

DEBUG_DEV = False
logging.disable(logging.CRITICAL)
user = os.path.expanduser('~')
CACHE_DIR = os.path.join(os.path.expanduser('~'), '.UdemyCache')
os.makedirs(CACHE_DIR, exist_ok=True)
downloads_dir = os.path.join(os.path.expanduser('~'), 'Udemy', 'Meus Cursos')
os.makedirs(downloads_dir, exist_ok=True)
autor = 'PauloCesar-Dev404'
apoio = 'https://paulocesar-dev404.github.io/me-apoiando-online/'
version = '1.0.0.9'