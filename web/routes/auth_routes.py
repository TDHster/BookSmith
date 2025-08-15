# web/routes/auth_routes.py
from flask import request, session, redirect, render_template
from werkzeug.security import check_password_hash
from sqlalchemy.orm import sessionmaker
from collections import defaultdict
from time import sleep
import logging

from infrastructure.database.models import User
from logger import logger
from infrastructure.database import get_session


failed_attempts = defaultdict(int)

def init_auth_routes(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
            failed_attempts[ip] += 1
            attempts = failed_attempts[ip]

            if attempts > 1:
                delay = 2 ** (attempts - 2)
                delay = min(delay, 30)
                sleep(delay)

            session_db = get_session()
            try:
                user = session_db.query(User).filter(User.username == username).first()
                if user and check_password_hash(user.password, password):
                    failed_attempts[ip] = 0
                    session_db["user_id"] = user.id
                    logger.info(f'User {user.username} logged in from ip {ip}')
                    return redirect("/books")
                else:
                    logger.error(f'User {username} failed to log in from ip {ip}, attempt {attempts}')
                    return "<div class='alert alert-danger'>Неверный логин или пароль</div>", 401
            finally:
                session_db.close()

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        return redirect("/login")