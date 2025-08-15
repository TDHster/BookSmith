# infrastructure/database/__init__.py
from .setup import init_db as _init_db

def get_session():
    from .setup import Session  # ✅ Импортируем ВНУТРИ функции — всегда свежий Session
    if Session is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_db() сначала.")
    return Session()

init_db = _init_db