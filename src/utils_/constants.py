import logging
import os
import tempfile

DEBUG_DEV = False
logging.disable(logging.CRITICAL)
user = os.path.expanduser('~')
segments_dir = tempfile.mkdtemp('segs_temp')
frags_dir = tempfile.mkdtemp('frags_temp')
downloads_dir = os.path.join(os.path.expanduser('~'), 'Udemy', 'Meus Cursos')
os.makedirs(downloads_dir, exist_ok=True)
autor = 'PauloCesar-Dev404'
apoio = 'https://paulocesar-dev404.github.io/me-apoiando-online/'
version = '1.0.0.7'