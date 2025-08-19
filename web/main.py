# web/main.py
from flask import Flask
from config.settings import settings
from infrastructure.database import init_db, get_session

# Инициализируем БД
Session = init_db(settings.DATABASE_URL)  # возвращает Session из setup.py

app = Flask(__name__)
app.secret_key = settings.WEB_APP_SECRET_KEY

# 🔥 Только после init_db импортируем маршруты
from web.routes.auth_routes import init_auth_routes
from web.routes.book_routes import init_book_routes
from web.routes.chapter_routes import init_chapter_routes
from web.routes.outline_routes import init_outline_routes
from web.routes.delete_routes import init_delete_routes
from web.routes.admin_routes import init_admin_routes

# Регистрируем все маршруты
init_auth_routes(app)
init_book_routes(app)
init_chapter_routes(app)
init_outline_routes(app)
init_delete_routes(app)
init_admin_routes(app)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", debug=False, use_reloader=False, port=8000)
    
    
if __name__ == "__main__":
    debug_mode = settings.FLASK_ENV == 'development'
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=debug_mode,
        use_reloader=debug_mode
    )