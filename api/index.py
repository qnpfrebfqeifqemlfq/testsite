from flask import Flask, render_template, request, redirect, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
import re
import os

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///database.db")

socketio = SocketIO(app, cors_allowed_origins="*")

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

bcrypt = Bcrypt(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    is_admin = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        nullable=False
    )

    text = db.Column(
        db.String(500),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda:
        datetime.now(timezone.utc)
    )

@socketio.on("send_message")
def handle_message(data):
    if not current_user.is_authenticated:
        return
    
    if len(data) > 500:
        return
    
    msg = Message(username=current_user.username, text=data)
    db.session.add(msg)
    db.session.commit()

    socketio.emit(
        "new_message",
        {
            "username": current_user.username,
            "message": data,
            "time": (msg.created_at + timedelta(hours=9)).strftime("%H:%M")
        },
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clock")
def clock():
    return render_template("clock.html", target="2026-05-25T16:36:48")

@app.route("/stock")
@login_required
def stock():
    messages = Message.query.order_by(Message.id.desc()).limit(100).all()
    messages.reverse()

    for msg in messages:
        msg.korea_time = (msg.created_at + timedelta(hours=9))

    return render_template("stock.html", messages=messages)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if (not user) or (not bcrypt.check_password_hash(user.password, password)):
            flash("존재하지 않는 아이디이거나 비밀번호가 일치하지 않습니다")
            return redirect("/login")

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        idpattern = r'^[a-zA-Z0-9_]+$'

        if not re.match(idpattern, username):
            flash("아이디에는 영어, 숫자만 허용됩니다")
            return redirect("/register")

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if len(username) < 4:
            flash("아이디는 최소 4글자 이상이여야 합니다")
            return redirect("/register")
        
        if len(password) < 8:
            flash("비밀번호는 최소 8글자 이상이여야 합니다")
            return redirect("/register")

        if existing_user:
            flash("이미 존재하는 아이디입니다")
            return redirect("/register")
        
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        if username == "ddongmanggem":
            admin = True
        else:
            admin = False

        new_user = User(username = username, password = hashed_pw, is_admin = admin)

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return redirect("/register")

        return redirect("/login")
    
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.all()
    return render_template("admin.html", users=users)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if os.getenv("DATABASE_URL") is None:
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=True)
